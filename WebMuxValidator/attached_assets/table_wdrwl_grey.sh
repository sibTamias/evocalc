#!/bin/bash
# set -x

####################################################################################################
# SCRIPT FUNCTIONALITY [EN]                                                                        #
# - Aggregates validator withdrawals per epoch starting from epoch 6                               #
# - Sums multiple withdrawals per validator/epoch into single value                                #
# - Parallel API requests via xargs for faster data fetching                                       #
# - Caching system reduces API calls (validator metadata, withdrawal tables)                       #
# - Color-highlighted totals for better readability                                                #
# - Auto-updates data on validator list/epoch changes                                              #
#                                                                                                  #
# ОСНОВНАЯ ФУНКЦИОНАЛЬНОСТЬ [RU]                                                                   #
# - Агрегация выплат валидаторов по эпохам (начиная с эпохи 6)                                     #
# - Суммирование нескольких выплат валидатора в эпохе в одно значение                              #
# - Параллельные API-запросы через xargs для ускорения загрузки                                    #
# - Кэширование уменьшает количество запросов (метаданные, таблицы выплат)                         #
# - Цветовая подсветка итоговых сумм                                                               #
# - Автообновление данных при изменении списка валидаторов/эпохи                                   #
####################################################################################################

####################################################################################################
# SCRIPT STRUCTURE [EN]                                                                            #
# 1. Configuration:                                                                                #
#    - SAVE_DIR ($HOME/tmp), VALIDATORS_FILE, IDENTITIES_FILE, WITHDRAWAL_TABLE_FILE               #
#    - VALIDATORS array with validator hashes                                                      #
# 2. Data Management:                                                                              #
#    - load_array/save_array functions for data persistence                                        #
#    - API data rebuild only on validator list changes                                             #
# 3. Epoch Processing:                                                                             #
#    - timestamp_to_epoch converter using epoch_intervals.txt                                      #
#    - fetch_epoch (single epoch) and fetch_all_epochs (parallel)                                  #
#    - Auto-update epoch intervals file                                                            #
# 4. Table Generation:                                                                             #
#    - generate_header (epoch numbers + TOTAL)                                                     #
#    - generate_row (validator data with ---/colored totals)                                       #
#    - generate_footer (summary row with colored grand total)                                      #
# 5. Output Control:                                                                               #
#    - Uses cached table if no changes detected                                                    #
#    - CUR_EPOCH_FILE for epoch tracking                                                           #
#                                                                                                  #
# СТРУКТУРА СКРИПТА [RU]                                                                           #
# 1. Конфигурация:                                                                                 #
#    - SAVE_DIR ($HOME/tmp), VALIDATORS_FILE, IDENTITIES_FILE, WITHDRAWAL_TABLE_FILE               #
#    - Массив VALIDATORS с хэшами валидаторов                                                      #
# 2. Управление данными:                                                                           #
#    - Функции load_array/save_array для сохранения данных                                         #
#    - Перестройка данных через API только при изменении списка валидаторов                        #
# 3. Обработка эпох:                                                                               #
#    - Конвертер timestamp_to_epoch с использованием epoch_intervals.txt                           #
#    - fetch_epoch (одна эпоха) и fetch_all_epochs (параллельный режим)                            #
#    - Автообновление файла интервалов эпох                                                        #
# 4. Генерация таблиц:                                                                             #
#    - generate_header (номера эпох + ИТОГО)                                                       #
#    - generate_row (данные валидатора с ---/цветными итогами)                                     #
#    - generate_footer (итоговая строка с цветным общим итогом)                                    #
# 5. Управление выводом:                                                                           #
#    - Использует кэшированную таблицу при отсутствии изменений                                    #
#    - CUR_EPOCH_FILE для отслеживания эпох                                                        #
####################################################################################################


###############################################################################
#                              Configuration / Настройка                     #
###############################################################################

COLUMN_COLOR1='\033[48;5;235m\033[38;5;255m'  # Темный фон + белый текст
COLUMN_COLOR2='\033[48;5;240m\033[38;5;255m'  # Чуть светлее фон + белый текст
RESET_COLOR='\033[0m'                         # Сброс цвета
HEADER_COLOR='\033[1;37m\033[44m'             # Белый жирный на синем фоне
TOTAL_COLOR='\033[1;33m\033[48;5;94m'         # Желтый на темно-желтом фоне
LIGHT_GRAY='\033[38;5;250m'     # Светло-серый
DARK_GRAY='\033[38;5;240m'      # Темно-серый
RESET_COLOR='\033[0m'           # Сброс цвета
HEADER_COLOR='\033[1;37m'       # Белый жирный для заголовков
TOTAL_COLOR='\033[1;33m'        # Желтый для итогов
export LC_ALL=en_US.UTF-8

# Validator Hashes / Хэши валидаторов
VALIDATORS=(
907cc91548d2e7448b82203a225c4d228f89b467733136219f3b3fd67a076fd5
# ... (other hashes) / ... (остальные хэши)
)

###############################################################################
#                              Configuration / Настройка                     #
###############################################################################

SAVE_DIR="$HOME/tmp"                          			# Storage directory / Директория для данных
mkdir -p "$SAVE_DIR"                          			# Create dir if missing / Создать при отсутствии

VALIDATORS_FILE="$SAVE_DIR/validators.txt"     			# Validator hashes file / Файл хэшей валидаторов
IDENTITIES_FILE="$SAVE_DIR/identities.txt"    		 	# Validator IDs file / Файл идентификаторов
IDENTITYBALANCE_FILE="$SAVE_DIR/identityBalance.txt"
WITHDRAWAL_TABLE_FILE="$SAVE_DIR/withdrawal_table.txt" 	# Cached withdrawal table / Кэшированная таблица выплат
CUR_EPOCH_FILE="$SAVE_DIR/cur_epoch.txt"       			# Current epoch cache / Кэш текущей эпохи
CUR_EPOCH_BLOCKS_FILE="$SAVE_DIR/cur_epoch_blocks.txt"   # Блоки текущей эпохи
LIST_BLOCKS_FILE="$SAVE_DIR/listProposedBlocks.txt"      # Список предложенных блоков

if [[ ${#VALIDATORS[@]} -eq 0 ]]; then
    echo "=============================================="
    echo -e "\n‼️ Validator list is empty! / Список валидаторов пустой!"
    echo "➤ Add your node's proTxHash / Заполните хэшами (proTxHash) ваших нод:"
    echo
    echo -e "Example / Пример:\n"
    cat <<EOF
VALIDATORS=(
    907cc91548d2e7448b82203a225c4d228f89b467733136219f3b3fd67a076fd5
    a9234ee0e18829e382274c6aa03a3863cc24f3fc43eb1dfc4977bd2fbb988391
    # Add more hashes / Добавьте другие хэши
    # ...
)
EOF
    echo -e "\n=============================================="
    exit 1
fi

###############################################################################
#                  APY data availability check /                              #
#                  Проверка доступности данных для APY                       #
###############################################################################

dashuser=$(ps -o user= -C dashd | head -n1 | tr -d '[:space:]')
dashd_available=1

if [[ -z "$dashuser" ]]; then
    echo -e "\n⚠️  dashd not running! Table will be displayed without masternode yield (APY) data."
    echo -e "⚠️  dashd не запущен! Таблица будет выведена без данных о доходности мастернод (APY)."
    echo -e "➤ Check if the node is running. / Убедитесь, что нода запущена.\n"
    dashd_available=0
fi

###############################################################################
#                   Dashd environment detection functions /                  #
#                   Функции определения окружения dashd                       #
###############################################################################

pid=$(pidof dashd)
[[ -z "$pid" ]] && return 1
if grep -qi docker /proc/$pid/cgroup 2>/dev/null; then
	container=$(docker ps --filter "name=mainnet-core" --format "{{.ID}}" 2>/dev/null | head -n1)
	dash_cli="docker exec "$container""
else
	dash_cli="sudo -i -u $dashuser"
fi

###############################################################################
#                          Data Loading Functions /                          #
#                       Функции работы с данными                              #
###############################################################################

load_array() {
  local file="$1"
  [[ -f "$file" ]] && mapfile -t array < "$file" || echo ""
  echo "${array[@]}"
}

save_array() {
  local file="$1"
  shift
  printf "%s\n" "$@" > "$file"
}

###############################################################################
#                     Validator Data Management /                             #
#                   Управление данными валидаторов                            #
###############################################################################

SAVED_VALIDATORS=($(load_array "$VALIDATORS_FILE"))
IDENTITIES=($(load_array "$IDENTITIES_FILE"))
IDENTITYBALANCE=($(load_array "$IDENTITYBALANCE_FILE"))

if (( dashd_available )); then
    REGISTERED_TIMES=($(load_array "$SAVE_DIR/registered_times.txt"))
    COLLATERALS=($(load_array "$SAVE_DIR/collaterals.txt"))
else
    REGISTERED_TIMES=()
    COLLATERALS=()
fi

rebuild_arrays() {
  echo "Rebuilding arrays... / Перестраиваем массивы..."
  IDENTITIES=()
  IDENTITYBALANCE=()
  SERVICES=()
  REGISTERED_TIMES=()   
  COLLATERALS=()        

  for validator in "${VALIDATORS[@]}"; do
    response=$(curl -sX GET "https://platform-explorer.pshenmic.dev/validator/$validator")
    identityBalance=$(echo "$response" | jq -r '.identityBalance')
    identity=$(echo "$response" | jq -r '.identity')
    service=$(echo "$response" | jq -r '.proTxInfo.state.service' | cut -d':' -f1)

    registeredHeight=$(echo "$response" | jq -r '.proTxInfo.state.registeredHeight')
    BLOCK_HASH=$($dash_cli bash -c "dash-cli getblockhash $registeredHeight" | tr -d '\r')
    if [[ -z "$BLOCK_HASH" || "$BLOCK_HASH" == *"error"* ]]; then
        echo "Error getting BLOCK_HASH for height $registeredHeight" >&2
        BLOCK_HASH=""
    fi
    registeredTime=$($dash_cli bash -c "dash-cli getblock $BLOCK_HASH" | jq -r '.time' || echo 0)
    collateral=$(echo "$response" | jq -r '.proTxInfo.state.collateral.amount? // 400000000000000' | bc -l)

    [[ -n "$identity" ]] && 
      IDENTITIES+=("$identity") &&
      IDENTITYBALANCE+=("$identityBalance") &&
      SERVICES+=("$service") &&
      REGISTERED_TIMES+=("$registeredTime") &&   
      COLLATERALS+=("$collateral")               
  done

  save_array "$VALIDATORS_FILE" "${VALIDATORS[@]}"
  save_array "$IDENTITIES_FILE" "${IDENTITIES[@]}"
  save_array "$IDENTITYBALANCE_FILE" "${IDENTITYBALANCE[@]}"
  save_array "$SAVE_DIR/registered_times.txt" "${REGISTERED_TIMES[@]}"   
  save_array "$SAVE_DIR/collaterals.txt" "${COLLATERALS[@]}"             
}

if [[ "${VALIDATORS[*]}" != "${SAVED_VALIDATORS[*]}" ]]; then
  echo "VALIDATORS changed. Rebuilding arrays... / VALIDATORS изменились. Перестраиваем массивы..."
  rebuild_arrays
else
  echo "VALIDATORS unchanged. Choose action:"
  echo "1) Load cached data / Загрузить кэш"
  echo "2) Rebuild arrays / Перестроить массивы"
  read -p "Enter choice / Введите выбор [1/2]: " choice
  
case "$choice" in
    2)	
        rm -f "$VALIDATORS_FILE" "$SAVE_DIR/epoch_intervals.txt" "$WITHDRAWAL_TABLE_FILE"
        rebuild_arrays
        
        curEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/status" | jq .epoch.number)
        echo "$curEpoch" > "$CUR_EPOCH_FILE"
        
        rm -f "$WITHDRAWAL_TABLE_FILE"
        ;;
    *)
      echo "Loading cached data... / Загружаем кэшированные данные"
      IDENTITIES=($(load_array "$IDENTITIES_FILE"))
      REGISTERED_TIMES=($(load_array "$SAVE_DIR/registered_times.txt"))
      COLLATERALS=($(load_array "$SAVE_DIR/collaterals.txt"))
      ;;
  esac
fi

###############################################################################
#                     Epoch Functions / Функции для работы с эпохами          #
###############################################################################

timestamp_to_epoch() {
  local timestamp="$1"
  unix_time=$(date -d "$timestamp" +%s%3N)

  epoch_intervals_file="./tmp/epoch_intervals.txt"
  [[ ! -f "$epoch_intervals_file" ]] && exit 1

  declare -a epoch_intervals
  mapfile -t epoch_intervals < "$epoch_intervals_file"

  found_epoch=""
  for interval in "${epoch_intervals[@]}"; do
    epoch_number=$(echo "$interval" | awk '{print $2}' | tr -d ':')
    startTime=$(echo "$interval" | awk '{print $3}')
    endTime=$(echo "$interval" | awk '{print $5}')
    
    (( unix_time >= startTime && unix_time <= endTime )) && found_epoch="$epoch_number" && break
  done
  [[ -n "$found_epoch" ]] && echo "$found_epoch" || echo " Epoch not found."
}

fetch_epoch() {
  local epoch=$1
  response=$(curl -sX GET "https://platform-explorer.pshenmic.dev/epoch/$epoch" | jq -r '.epoch | [.startTime, .endTime] | @tsv')
  printf "Epoch %2d: %s - %s\n" "$epoch" "$(echo "$response" | awk '{print $1}')" "$(echo "$response" | awk '{print $2}')"
}

fetch_all_epochs() {
  local curEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/status" | jq .epoch.number)
  export -f fetch_epoch
  declare -a results
  mapfile -t results < <(seq 1 "$curEpoch" | xargs -P 8 -I {} bash -c 'fetch_epoch "$@"' _ {})
  printf "%s\n" "${results[@]}" | sort -n
}

get_existing_epochs() {
  local epoch_intervals_file=$1
  [[ -f "$epoch_intervals_file" ]] && awk -F'[: -]' '{print $2}' "$epoch_intervals_file" || echo ""
}

epoch_intervals_file="./tmp/epoch_intervals.txt"

curEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/status" | jq .epoch.number)

if [[ ! -f "$epoch_intervals_file" ]] || [[ $(get_existing_epochs "$epoch_intervals_file" | wc -l) -eq 0 ]]; then
  fetch_all_epochs > "$epoch_intervals_file"
else
  lastEpochInFile=$(get_existing_epochs "$epoch_intervals_file" | tail -1)
  if (( curEpoch > lastEpochInFile )); then
    for epoch in $(seq $((lastEpochInFile + 1)) "$curEpoch"); do
      fetch_epoch "$epoch" >> "$epoch_intervals_file"
    done
  fi
fi

###############################################################################
#                     Функции для подсчета блоков из credit.sh                #
###############################################################################

validatorProposedBlocksInEpoch() {
  local validator_hash=$1
  local epoch=$2
  firstBlockEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/epoch/$epoch" | jq .epoch.firstBlockHeight)
  lastBlockEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/status" | jq .api.block.height)
  
  > "$LIST_BLOCKS_FILE"
  totalProposedBlocks=$(curl -sX GET "https://platform-explorer.pshenmic.dev/validator/$validator_hash/blocks?" | jq .pagination.total)
  limit=100
  numPage=$(( (totalProposedBlocks+limit)/limit ))
  
  for (( j=1; j <= numPage; j++ )); do
    curl -sX GET "https://platform-explorer.pshenmic.dev/validator/$validator_hash/blocks?page=$j&limit=100&order=asc" | 
      jq .resultSet[].header.height >> "$LIST_BLOCKS_FILE"
  done
  
  listBlocks=($(awk -v b="$firstBlockEpoch" -v c="$lastBlockEpoch" '{if ($1 > b && $1 < c) print $0}' "$LIST_BLOCKS_FILE"))
  echo ${#listBlocks[@]}
}

get_current_epoch_blocks() {
  curEpoch=$(curl -sX GET "https://platform-explorer.pshenmic.dev/status" | jq .epoch.number)
  > "$CUR_EPOCH_BLOCKS_FILE"
  
  for validator in "${VALIDATORS[@]}"; do
    blocks=$(validatorProposedBlocksInEpoch "$validator" "$curEpoch")
    if (( blocks == 0 )); then
      echo "---" >> "$CUR_EPOCH_BLOCKS_FILE"
    else
      # Записываем просто число без ведущих нулей и без форматирования
      echo "$blocks" >> "$CUR_EPOCH_BLOCKS_FILE"
    fi
  done
}

###############################################################################
#                     Обновленные функции генерации таблицы                  #
###############################################################################

format_number() {
    local num=$1
    # Для нуля
    if (( $(echo "$num == 0" | bc -l) )); then
        echo "0"
    # Для целых чисел
    elif (( $(echo "$num == ${num%.*}" | bc -l) )); then
        echo "${num%.*}"
    else
        # Для чисел с плавающей точкой - 3 значащих цифры
        awk -v n="$num" 'BEGIN {
            if (n < 1) {
                printf "%.3g", n
            } else if (n < 10) {
                printf "%.2f", n | "sed \"s/\\.0$//\""
            } else if (n < 100) {
                printf "%.1f", n | "sed \"s/\\.0$//\""
            } else {
                printf "%.0f", n
            }
        }' | sed 's/^\./0./;s/\.$//'
    fi
}

generate_row() {
    local identity=$1
    local n=$2
    m=$((n-1))
    local service=${SERVICES[$((n-1))]}
    
    declare -A epoch_amounts
    local total=0
    
    response=$(curl -sfX GET "https://platform-explorer.pshenmic.dev/identity/$identity/withdrawals?page=1&limit=100")
    while IFS=$'\t' read -r timestamp amount; do
        [[ -z "$timestamp" ]] && continue
        nEpoch=$(timestamp_to_epoch "$timestamp" 2>/dev/null)
        [[ -z "$nEpoch" ]] && continue
        epoch_amounts[$nEpoch]=$((${epoch_amounts[$nEpoch]:-0} + amount))
        total=$((total + amount))
    done < <(echo "$response" | jq -r '.resultSet[]? | [.timestamp, .amount] | @tsv' 2>/dev/null)
    total=$((total + ${IDENTITYBALANCE[m]}))
    
    apy="---"
    if (( dashd_available )); then
        current_time=$(date +%s)
        registered_time=${REGISTERED_TIMES[$((n-1))]}
        period=$(bc <<< "$current_time - $registered_time")
        period_years=$(bc -l <<< "scale=6; $period / 31536000")
        collateral=${COLLATERALS[$((n-1))]}
        apy=$(bc -l <<< "scale=10; result=($total/($collateral+0.000001))/$period_years * 100; scale=2; result/1")
        apy_array+=("$apy")
    fi

    # IP-адрес (без фона)
    printf "\033[38;5;255m%-17s" " $service"
    
    # Данные по эпохам с чередованием цветов
    local color_flag=0
    for epoch in $(seq 5 "$curEpoch"); do
        ((color_flag ^= 1))  # Чередуем 0 и 1
        
        if (( color_flag )); then
            printf "${COLUMN_COLOR1}"
        else
            printf "${COLUMN_COLOR2}"
        fi
        
        amount=${epoch_amounts[$epoch]:-0}
        if (( amount == 0 )); then
            printf "%5s" "---"
        else
            # Форматируем число с 1 десятичным знаком (всего 3 знака)
            value=$(awk "BEGIN {printf \"%.1f\", $amount/100000000000}")
            printf "%5s" "$value"
        fi
    done
    
    # Текущая эпоха (серый фон)
    printf "\033[48;5;238m\033[38;5;255m"
    current_epoch_blocks=$(sed -n "${n}p" "$CUR_EPOCH_BLOCKS_FILE" | tr -cd '[:digit:]')
    if [[ -z "$current_epoch_blocks" ]]; then
        printf "%6s" "---"
    else
        current_epoch_blocks=$(echo "$current_epoch_blocks" | sed 's/^0*//')
        [[ -z "$current_epoch_blocks" ]] && current_epoch_blocks=0
        printf "%6s" "$current_epoch_blocks"
    fi
    
    # TOTAL (специальный цвет)
    if (( total == 0 )); then
        printf "${TOTAL_COLOR}%12s" "---"
    else
        printf "${TOTAL_COLOR}%12.2f" $(awk "BEGIN {printf \"%.2f\", $total/100000000000}")
    fi

    # APY (специальный цвет)
    if (( dashd_available )); then
        printf "%12s${RESET_COLOR}\n" "$apy%"
    else
        printf "${RESET_COLOR}\n"
    fi
}

generate_header() {
    hedEpoch=$((curEpoch+1))
    printf "%-17s" " IP \\ Epoch"
    
    # Заголовки эпох с чередованием цветов
    local color_flag=0
    for epoch in $(seq 4 $((curEpoch-1))); do
        ((color_flag ^= 1))  # Чередуем 0 и 1
        
        if (( color_flag )); then
            printf "${COLUMN_COLOR1}"
        else
            printf "${COLUMN_COLOR2}"
        fi
        
        printf "%5s" "$(printf "%02d" $epoch)"
    done
    
    # Остальные заголовки (нейтральные)
    printf "${RESET_COLOR}"
    if (( dashd_available )); then
        printf "%6s%12s%12s\n" "$curEpoch" "TOTAL" "APY"
    else
        printf "%12s\n" "TOTAL"
    fi
    
    # Разделительная линия
    printf "%-17s" "-----------------"
    color_flag=0
    for _ in $(seq 4 "$curEpoch"); do
        ((color_flag ^= 1))
        
        if (( color_flag )); then
            printf "${COLUMN_COLOR1}"
        else
            printf "${COLUMN_COLOR2}"
        fi
        
        printf "%5s" "-----"
    done
    printf "${RESET_COLOR}"
    if (( dashd_available )); then
        printf "%6s%12s%12s\n" "------" "------------" "----------"
    else
        printf "%12s\n" "------------"
    fi
}

generate_footer() {
    local -a column_sums
    local total_sum=0
    local credit_total=0
    local apy_sum=0
    local apy_count=0
    local -a valid_apy_values=()

    # Суммируем данные кредитов из файла
    while read -r blocks; do
        blocks=$(echo "$blocks" | tr -cd '[:digit:]')
        [[ -n "$blocks" ]] && credit_total=$((credit_total + blocks))
    done < "$CUR_EPOCH_BLOCKS_FILE"

    # Инициализируем суммы для всех колонок
    for epoch in $(seq 5 $((hedEpoch))); do
        column_sums[$epoch]=0
    done

    # Собираем все валидные APY (>0) из apy_array
    for apy in "${apy_array[@]}"; do
        if (( $(echo "$apy > 0" | bc -l) )); then
            valid_apy_values+=("$apy")
            apy_sum=$(echo "$apy_sum + $apy" | bc -l)
            ((apy_count++))
        fi
    done

    # Суммируем выплаты по эпохам
    for identity in "${IDENTITIES[@]}"; do
        response=$(curl -sfX GET "https://platform-explorer.pshenmic.dev/identity/$identity/withdrawals?page=1&limit=100")
        while IFS=$'\t' read -r timestamp amount; do
            nEpoch=$(timestamp_to_epoch "$timestamp" 2>/dev/null)
            [[ -z "$nEpoch" ]] && continue
            column_sums[$nEpoch]=$((${column_sums[$nEpoch]} + amount))
            total_sum=$((total_sum + amount))
        done < <(echo "$response" | jq -r '.resultSet[]? | [.timestamp, .amount] | @tsv' 2>/dev/null)
    done

    # Итоговая строка
    printf "\033[1;33m%-17s\033[0m" " TOTAL / ИТОГО   "
    
    # Суммы по эпохам (3 значащих цифры)
    for epoch in $(seq 5 $((hedEpoch - 1))); do
        amount=${column_sums[$epoch]:-0}
        if (( amount == 0 )); then
            printf "\033[1;33m%5s\033[0m" "---"
        else
            formatted=$(format_number $(awk "BEGIN {printf \"%.2f\", $amount/100000000000}"))
            printf "\033[1;33m%5s\033[0m" "$formatted"
        fi
    done
    
    # Кредиты текущей эпохи
    if (( credit_total == 0 )); then
        printf "\033[1;33m%6s\033[0m" "---"
    else
        printf "\033[1;33m%6d\033[0m" "$credit_total"
    fi

    # Общий TOTAL (5 цифр)
    formatted_total=$(awk "BEGIN {printf \"%5.2f\", $total_sum/100000000000}" | sed 's/\.00$//;s/\.0$//')
    printf "\033[1;36m%12s\033[0m" "$formatted_total"

    # Средний APY (только по валидным значениям)
    if (( dashd_available )); then
        if (( apy_count > 0 )); then
            avg_apy=$(echo "scale=2; $apy_sum/$apy_count" | bc -l)
            # Форматируем до 3 значащих цифр
            formatted_apy=$(format_number $avg_apy)
            printf "\033[1;36m%12s\033[0m\n" "${formatted_apy}%"
        else
            printf "\033[1;36m%12s\033[0m\n" "---"
        fi
    else
        printf "\n"
    fi
    # Только убедитесь, что в конце сбрасываем цвет:
    printf "${RESET_COLOR}\n"
}

generate_table() {
    get_current_epoch_blocks
    generate_header
    local counter=1
    for identity in "${IDENTITIES[@]}"; do
        generate_row "$identity" "$counter"
        ((counter++))
    done
    generate_footer
}

###############################################################################
#                          Withdrawal Table Output /                          #
#                          Вывод таблицы выплат                               #
###############################################################################

if [[ -f "$CUR_EPOCH_FILE" ]]; then
  CACHED_CUR_EPOCH=$(cat "$CUR_EPOCH_FILE")
else
  CACHED_CUR_EPOCH=""
fi

if (( choice != 2 )); then
	if [[ "${VALIDATORS[*]}" == "${SAVED_VALIDATORS[*]}" && "$curEpoch" == "$CACHED_CUR_EPOCH" && -f "$WITHDRAWAL_TABLE_FILE" ]]; then
	  echo "VALIDATORS and curEpoch unchanged. Loading cached table..."
	  echo
	  cat "$WITHDRAWAL_TABLE_FILE"
	  exit 0
	fi
fi

echo "$curEpoch" > "$CUR_EPOCH_FILE"
echo "Generating withdrawal report... / Генерация отчёта о выплатах..."
echo
generate_table | column -t -s $'\t' | tee "$WITHDRAWAL_TABLE_FILE"