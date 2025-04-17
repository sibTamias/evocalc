import os
import json
import time
import logging
import requests
import concurrent.futures
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
import multiprocessing

from utils import (
    timestamp_to_epoch, 
    load_cached_data, 
    save_cached_data, 
    fetch_validator_identity,
    fetch_withdrawal_data,
    calculate_totals
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# было:
# app = Flask(__name__)
# app.secret_key = os.environ.get("SESSION_SECRET", "dash-validator-withdrawals-secret")
# стало:
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/webmux'  # Добавьте эту строку!
app.secret_key = os.environ.get("SESSION_SECRET", "dash-validator-withdrawals-secret")

# Cache directory
SAVE_DIR = os.path.join(os.path.expanduser("~"), "tmp")
os.makedirs(SAVE_DIR, exist_ok=True)

# Cache files
VALIDATORS_FILE = os.path.join(SAVE_DIR, "validators.txt")
IDENTITIES_FILE = os.path.join(SAVE_DIR, "identities.txt")
IDENTITYBALANCE_FILE = os.path.join(SAVE_DIR, "identityBalance.txt")
WITHDRAWAL_TABLE_FILE = os.path.join(SAVE_DIR, "withdrawal_table.txt")
CUR_EPOCH_FILE = os.path.join(SAVE_DIR, "cur_epoch.txt")
CUR_EPOCH_BLOCKS_FILE = os.path.join(SAVE_DIR, "cur_epoch_blocks.txt")
LIST_BLOCKS_FILE = os.path.join(SAVE_DIR, "listProposedBlocks.txt")

# Global variables for translations
translations = {
    "en": {
        "title": "Dash Validator Withdrawals Monitor",
        "enter_validators": "Enter Validator Hashes (one per line)",
        "submit": "Generate Withdrawal Table",
        "validators_placeholder": "Enter validator hashes here...",
        "empty_validators": "Please enter at least one validator hash",
        "loading": "Loading data, please wait...",
        "validator": "Validator",
        "total": "TOTAL",
        "grand_total": "GRAND TOTAL",
        "epoch": "Epoch",
        "no_data": "No data available for the specified validators",
        "error_fetching": "Error fetching data",
        "success": "Success",
        "copy_success": "Table has been copied to clipboard",
        "loading_validators": "Connecting to the Dash API and retrieving validator data...",
        "start_epoch_label": "Starting Epoch:",
        "start_epoch_hint": "Select the epoch number to start the display from (default: 21)"
    },
    "ru": {
        "title": "Мониторинг Выплат Валидаторов Dash",
        "enter_validators": "Введите Хэши Валидаторов (по одному в строке)",
        "submit": "Сгенерировать Таблицу Выплат",
        "validators_placeholder": "Введите хэши валидаторов здесь...",
        "empty_validators": "Пожалуйста, введите хотя бы один хэш валидатора",
        "loading": "Загрузка данных, пожалуйста, подождите...",
        "validator": "Валидатор",
        "total": "ИТОГО",
        "grand_total": "ОБЩИЙ ИТОГ",
        "epoch": "Эпоха",
        "no_data": "Нет данных для указанных валидаторов",
        "error_fetching": "Ошибка при получении данных",
        "success": "Успешно",
        "copy_success": "Таблица скопирована в буфер обмена",
        "loading_validators": "Соединение с API Dash и получение данных валидатора...",
        "start_epoch_label": "Начальная Эпоха:",
        "start_epoch_hint": "Выберите номер эпохи, с которой начать отображение (по умолчанию: 21)"
    }
}

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    
    # Get current epoch for the max value in the epoch input field
    try:
        from utils import get_current_epoch
        current_epoch = get_current_epoch()
    except Exception as e:
        logger.error(f"Error getting current epoch: {e}")
        current_epoch = 24  # Fallback value
    
    return render_template('index.html', lang=lang, translations=translations[lang], current_epoch=current_epoch)

@app.route('/process_validators', methods=['POST'])
def process_validators():
    # Set default language
    lang = 'en'
    
    try:
        lang = request.form.get('lang', 'en')
        if lang not in translations:
            lang = 'en'
            
        validators_text = request.form.get('validators', '')
        logger.debug(f"Received validators text: {validators_text}")
        
        # Get the starting epoch (default to 21 if not specified)
        start_epoch = request.form.get('start_epoch', '21')
        try:
            start_epoch = int(start_epoch)
            if start_epoch < 1:
                start_epoch = 21  # Fallback to default if invalid
        except:
            start_epoch = 21  # Fallback to default if not a valid number
            
        logger.debug(f"Starting epoch set to: {start_epoch}")
        
        # Split by newline and filter out empty lines
        validators = [v.strip() for v in validators_text.split('\n') if v.strip()]
        logger.debug(f"Parsed validators: {validators}")
        
        if not validators:
            logger.warning("No validators provided")
            flash(translations[lang]["empty_validators"], "danger")
            return redirect(url_for('index', lang=lang))
        
        # Convert validators list to JSON string to ensure correct format
        import json
        validators_json = json.dumps(validators)
        logger.debug(f"Validators JSON: {validators_json}")
        
        # Instead of redirecting, render the results template directly
        return render_template('results.html', 
                               lang=lang, 
                               translations=translations[lang], 
                               validators=validators,
                               validators_json=validators_json,
                               validators_text=validators_text,
                               start_epoch=start_epoch)
    except Exception as e:
        logger.exception(f"Error in process_validators: {e}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('index', lang=lang))

# Removed results route as we're rendering the results page directly

# добавил webmux:
@app.route('/api/fetch_withdrawals', methods=['POST'])  # Измените путь!
def api_fetch_withdrawals():
    logger.debug("API fetch_withdrawals called")
    
    try:
        # Get data from POST request with better error handling
        try:
            data = request.get_json() or {}
        except Exception as e:
            logger.error(f"Error parsing JSON from request: {e}")
            data = {}
            
        validators = data.get('validators', [])
        lang = data.get('lang', 'en')
        start_epoch = data.get('start_epoch', 21)
        
        # Ensure start_epoch is an integer
        try:
            start_epoch = int(start_epoch)
            if start_epoch < 1:
                start_epoch = 21
        except:
            start_epoch = 21
            
        logger.debug(f"API: Using start_epoch={start_epoch}")
        
        if not validators:
            # Try to get from form data if not in JSON
            validators_text = request.form.get('validators', '')
            if validators_text:
                validators = [v.strip() for v in validators_text.split('\n') if v.strip()]
            else:
                validators = []
        
        logger.debug(f"API: Received {len(validators)} validators, lang={lang}")
        
        if not validators:
            logger.warning("API: No validators provided")
            return jsonify({"error": translations[lang]["empty_validators"]}), 400
        
        # Save validators list to file for caching
        save_cached_data(VALIDATORS_FILE, validators)
        logger.debug(f"Saved validators to {VALIDATORS_FILE}")
        
        # Get validator identities and IPs
        identities = {}
        validator_ips = {}
        logger.debug(f"Fetching identities for {len(validators)} validators")
        for validator in validators:
            # Get validator identity
            identity = fetch_validator_identity(validator)
            if identity:
                identities[validator] = identity
                logger.debug(f"Got identity for {validator}: {identity}")
            else:
                logger.warning(f"No identity found for validator {validator}")
                
            # Check for cached IP address
            ip_cache_file = os.path.join(SAVE_DIR, f"validator_ip_{validator}.txt")
            try:
                if os.path.exists(ip_cache_file):
                    with open(ip_cache_file, 'r') as f:
                        server_ip = f.read().strip()
                        if server_ip:
                            validator_ips[validator] = server_ip
                            logger.debug(f"Using cached IP for {validator}: {server_ip}")
            except Exception as e:
                logger.error(f"Error reading validator IP from cache: {e}")
        
        # Save identities to cache
        if identities:
            save_cached_data(IDENTITIES_FILE, identities)
            logger.debug(f"Saved {len(identities)} identities to {IDENTITIES_FILE}")
            
        # Save IPs to cache
        if validator_ips:
            save_cached_data(os.path.join(SAVE_DIR, "validator_ips.json"), validator_ips)
            logger.debug(f"Saved {len(validator_ips)} validator IPs")
            
        # Get current epoch
        current_epoch = None
        try:
            logger.debug("Fetching current epoch from API")
            response = requests.get("https://platform-explorer.pshenmic.dev/status")
            data = response.json()
            current_epoch = data.get('epoch', {}).get('number', 6)
            logger.debug(f"Current epoch is {current_epoch}")
        except Exception as e:
            logger.error(f"Error fetching current epoch: {e}")
            current_epoch = 6  # Default to start from epoch 6
            logger.debug(f"Using default epoch: {current_epoch}")
        
        # Save current epoch to cache
        save_cached_data(CUR_EPOCH_FILE, current_epoch)
        logger.debug(f"Saved current epoch {current_epoch} to {CUR_EPOCH_FILE}")
        
        # Fetch withdrawal data for the specified epochs
        withdrawals_data = {}
        
        # Use the provided start_epoch instead of the default calculation
        # But ensure it's not before epoch 6 (the earliest with data)
        start_epoch = max(6, start_epoch)
        
        # Using ThreadPoolExecutor with very limited parallelism
        logger.debug(f"Starting fetch for withdrawal data from epoch {start_epoch} to {current_epoch}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for validator in validators:
                for epoch in range(start_epoch, current_epoch + 1):
                    # Check if we already have this data in cache
                    cache_file = os.path.join(SAVE_DIR, f"withdrawal_{validator}_{epoch}.json")
                    cached_data = load_cached_data(cache_file)
                    
                    if cached_data:
                        logger.debug(f"Using cached data for {validator} at epoch {epoch}")
                        if cached_data[0] == validator and cached_data[1] == epoch:
                            if validator not in withdrawals_data:
                                withdrawals_data[validator] = {}
                            withdrawals_data[validator][epoch] = cached_data[2]
                    else:
                        futures.append(
                            executor.submit(
                                fetch_withdrawal_data, 
                                validator, 
                                epoch
                            )
                        )
                        # Longer delay between tasks to avoid API rate limiting
                        time.sleep(0.5)
            
            logger.debug(f"Created {len(futures)} fetch tasks")
            
            # Variables to track API connection errors
            api_connection_errors = []
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    validator, epoch, amount = result
                    
                    # Check for special error markers
                    if isinstance(amount, str) and amount.startswith("API_"):
                        if amount == "API_CONNECTION_ERROR" and "connection" not in api_connection_errors:
                            api_connection_errors.append("connection")
                        elif amount == "API_TIMEOUT_ERROR" and "timeout" not in api_connection_errors:
                            api_connection_errors.append("timeout")
                        continue
                    
                    if validator not in withdrawals_data:
                        withdrawals_data[validator] = {}
                    withdrawals_data[validator][epoch] = amount
                    logger.debug(f"Got withdrawal for {validator} at epoch {epoch}: {amount}")
            
            # Check if we encountered API connection errors
            if api_connection_errors:
                error_msg = "Не удалось подключиться к серверу Dash Platform API. " if lang == 'ru' else "Could not connect to Dash Platform API server. "
                if "connection" in api_connection_errors:
                    error_msg += "Пожалуйста, проверьте подключение к интернету и попробуйте позже." if lang == 'ru' else "Please check your internet connection and try again later."
                elif "timeout" in api_connection_errors:
                    error_msg += "Превышено время ожидания. Пожалуйста, попробуйте позже." if lang == 'ru' else "Request timed out. Please try again later."
                
                logger.warning(f"API connection issues detected: {api_connection_errors}")
                
                # Continue with empty data but include error message
                result = {
                    "withdrawals": {},
                    "identities": {},
                    "validator_totals": {},
                    "grand_total": 0,
                    "epoch_range": [6],
                    "current_epoch": 6,
                    "api_error": error_msg
                }
                return jsonify(result)
        
        # Calculate totals but only show the epochs we actually fetched data for
        logger.debug("Calculating totals")
        validator_totals, grand_total, epoch_range = calculate_totals(
            withdrawals_data, 
            validators, 
            current_epoch,
            start_epoch
        )
        
        # Format the data for the frontend
        result = {
            "withdrawals": withdrawals_data,
            "identities": identities,
            "validator_totals": validator_totals,
            "grand_total": grand_total,
            "epoch_range": epoch_range,
            "current_epoch": current_epoch,
            "validator_ips": validator_ips  # Add the validator IPs to the response
        }
        
        logger.debug(f"API response ready with data for {len(withdrawals_data)} validators")
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Error processing withdrawals: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
