import xml.etree.ElementTree as ET
import requests
from datetime import datetime

# Локализация / Localization
LANG = {
    'menu': {
        'choose_lang': {
            'eng': 'Choose language:\n1. Eng\n2. Rus\nEnter 1 or 2: ', 
            'rus': 'Выбери язык:\n1. Английский\n2. Русский\nВведи 1 или 2: '
        },
        'invalid_lang': {
            'eng': 'Invalid choice! Enter 1 or 2', 
            'rus': 'Неверный выбор! Введите 1 или 2'
        },
        'currency_choice': {
            'eng': 'Select server rent currency:\n1. USD ($)\n2. RUB (₽)\nEnter 1 or 2: ',
            'rus': 'Выбери валюту для оплаты аренды:\n1. Доллар ($)\n2. Рубль (₽)\nВведи 1 или 2: '
        },
        'invalid_currency': {
            'eng': 'Error! Enter 1 or 2', 
            'rus': 'Ошибка! Введите 1 или 2'
        }
    },
    'inputs': {
        'default_values': {'eng': 'Enter data (press Enter for defaults):', 'rus': 'Введите данные (Enter для значений по умолчанию):'},
        'servers': {'eng': 'Number of servers (Evo) (default 5): ', 'rus': 'Количество серверов(Evo) (по умолчанию 5): '},
        'investment': {'eng': 'Dash investment per server (default 4000): ', 'rus': 'Инвестиция в Dash на 1 сервер (по умолчанию 4000): '},
        'profit1': {'eng': 'Platform payments (default 9 Dash): ', 'rus': 'Выплаты на Platform (по умолчанию 9 Dash): '},
        'days1': {'eng': 'Platform interval (default 9.5 days): ', 'rus': 'Периодичность Platform (по умолчанию 9.5 дней): '},
        'profit2': {'eng': 'Core profit (default 0.89 Dash): ', 'rus': 'Прибыль Core (по умолчанию 0.89 Dash): '},
        'days2': {'eng': 'Core interval (default 4.5 days): ', 'rus': 'Периодичность Core (по умолчанию 4.5 дней): '},
        'ssl': {'eng': 'SSL cost per server ($, default 81): ', 'rus': 'Стоимость SSL на 1 сервер ($, по умолчанию 81): '},
        'ssl_months': {'eng': 'SSL validity period (months, default 36): ', 'rus': 'Срок действия SSL (месяцев, по умолчанию 36): '},
        'discount': {'eng': 'Annual server discount (%, default 10): ', 'rus': 'Годовая скидка на аренду серверов (%, по умолчанию 10): '},
        'main_rent': {
            '$': {'eng': 'Main server rent (default 50 $/month): ', 'rus': 'Аренда основного сервера (по умолчанию 50 $/мес): '},
            '₽': {'eng': 'Main server rent (default 4350 ₽/month): ', 'rus': 'Аренда основного сервера (по умолчанию 4350 ₽/мес): '}
        },
        'add_rent': {
            '$': {'eng': 'Additional servers rent (default 45 $/month): ', 'rus': 'Общая аренда доп. серверов (по умолчанию 45 $/мес): '},
            '₽': {'eng': 'Additional servers rent (default 7655 ₽/month): ', 'rus': 'Общая аренда доп. серверов (по умолчанию 7655 ₽/мес): '}
        }
    },
    'results': {
        'header': {'eng': '\nResults:', 'rus': '\nРезультаты:'},
        'dash_rate': {'eng': 'Current Dash rate: {} $/DASH', 'rus': 'Текущий курс Dash: {} $/DASH'},
        'usd_rate': {'eng': 'Current USD rate: {} ₽/$', 'rus': 'Текущий курс USD: {} ₽/$'},
        'total_invest': {'eng': 'Total investment: {} Dash ({:.2f} $)', 'rus': 'Общие инвестиции: {} Dash ({:.2f} $)'},
        'annual_income': {'eng': 'Annual income: {:.2f} $', 'rus': 'Годовой доход: {:.2f} $'},
        'annual_expenses': {'eng': 'Annual expenses: {:.2f} $', 'rus': 'Годовые расходы: {:.2f} $'},
        'net_profit': {'eng': 'Net profit: {:.2f} $', 'rus': 'Чистая прибыль: {:.2f} $'},
        'roi': {'eng': 'ROI: {:.2f}%', 'rus': 'Прибыль в процентах: {:.2f}%'}
    },
    'errors': {
        'cbr': {'eng': 'CBR rate error: {}', 'rus': 'Ошибка курса ЦБ: {}'},
        'dash': {'eng': 'Dash rate error: {}', 'rus': 'Ошибка курса Dash: {}'}
    }
}

def get_usd_rate(lang):
    """Get USD/RUB rate from CBR / Получение курса USD от ЦБ РФ"""
    try:
        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp', timeout=10)
        response.encoding = 'windows-1251'
        root = ET.fromstring(response.text)
        
        for valute in root.findall('Valute'):
            if valute.find('CharCode').text == 'USD':
                return round(float(valute.find('Value').text.replace(',', '.')), 2)
        return None
    except Exception as e:
        print(LANG['errors']['cbr'][lang].format(e))
        return None

def get_dash_rate(lang):
    """Get Dash/USD rate / Получение курса Dash к USD"""
    try:
        response = requests.get("https://chainz.cryptoid.info/dash/api.dws?q=ticker.usd", timeout=10)
        return round(float(response.text), 2)
    except Exception as e:
        print(LANG['errors']['dash'][lang].format(e))
        return None

def calculate_profit():
    # Выбор языка / Language selection
    lang_choice = input(LANG['menu']['choose_lang']['eng']).strip()
    while lang_choice not in ['1', '2']:
        print("Invalid choice! Enter 1 or 2 / Неверный выбор! Введите 1 или 2")
        lang_choice = input(LANG['menu']['choose_lang']['rus']).strip()
    
    lang = 'eng' if lang_choice == '1' else 'rus'
    
    # Получение курсов / Get rates
    dash_usd = get_dash_rate(lang) or 28.50
    
    # Выбор валюты аренды / Currency selection
    currency_choice = input(LANG['menu']['currency_choice'][lang]).strip()
    while currency_choice not in ['1', '2']:
        print(LANG['menu']['invalid_currency'][lang])
        currency_choice = input(LANG['menu']['currency_choice'][lang]).strip()
    
    currency = '$' if currency_choice == '1' else '₽'
    
    # Конфигурация по умолчанию / Default configuration
    usd_rub = None
    if currency == '₽':
        usd_rub = get_usd_rate(lang) or 84.21

    # Ввод данных / Data input
    print(LANG['inputs']['default_values'][lang])
    
    rent_main = float(input(
        LANG['inputs']['main_rent'][currency][lang]
    ) or ('50' if currency == '$' else '4350'))
    
    add_servers_total = float(input(
        LANG['inputs']['add_rent'][currency][lang]
    ) or ('45' if currency == '$' else '7655'))

    # Конвертация валюты / Currency conversion
    if currency == '₽':
        rent_main_usd = rent_main / usd_rub
        add_servers_usd = add_servers_total / usd_rub
    else:
        rent_main_usd = rent_main
        add_servers_usd = add_servers_total

    # Остальные параметры / Other parameters
    servers_count = float(input(LANG['inputs']['servers'][lang]) or 5)
    discount_rate = float(input(LANG['inputs']['discount'][lang]) or 10) / 100
    investment_per_server = float(input(LANG['inputs']['investment'][lang]) or 4000)
    profit1 = float(input(LANG['inputs']['profit1'][lang]) or 9)
    days1 = float(input(LANG['inputs']['days1'][lang]) or 9.5)
    profit2 = float(input(LANG['inputs']['profit2'][lang]) or 0.89)
    days2 = float(input(LANG['inputs']['days2'][lang]) or 4.5)
    ssl_cost = float(input(LANG['inputs']['ssl'][lang]) or 81)
    ssl_months = float(input(LANG['inputs']['ssl_months'][lang]) or 36)

    # Расчеты / Calculations
    total_investment = investment_per_server * servers_count
    ssl_annual_per_server = (ssl_cost / ssl_months) * 12  # Годовая стоимость на 1 сервер
    ssl_total = ssl_annual_per_server * servers_count      # Общая годовая стоимость
    
    annual_payouts1 = 365 / days1
    annual_dash1 = annual_payouts1 * profit1 * servers_count
    
    annual_payouts2 = 365 / days2
    annual_dash2 = annual_payouts2 * profit2 * servers_count
    
    total_dash = annual_dash1 + annual_dash2
    total_usd_income = total_dash * dash_usd

    rent_total_usd = (rent_main_usd * servers_count + add_servers_usd) * 12 * (1 - discount_rate)
    total_usd_expenses = rent_total_usd + ssl_total

    initial_investment_usd = total_investment * dash_usd
    net_profit = total_usd_income - total_usd_expenses
    profit_percent = (net_profit / initial_investment_usd) * 100

    # Вывод результатов / Results output
    print(LANG['results']['header'][lang])
    print(LANG['results']['dash_rate'][lang].format(dash_usd))
    if currency == '₽':
        print(LANG['results']['usd_rate'][lang].format(usd_rub))
    print(LANG['results']['total_invest'][lang].format(total_investment, initial_investment_usd))
    print(LANG['results']['annual_income'][lang].format(total_usd_income))
    print(LANG['results']['annual_expenses'][lang].format(total_usd_expenses))
    print(LANG['results']['net_profit'][lang].format(net_profit))
    print(LANG['results']['roi'][lang].format(profit_percent))

if __name__ == "__main__":
    calculate_profit()