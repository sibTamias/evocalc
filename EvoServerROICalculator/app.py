import streamlit as st
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
import os

# Page configuration
# st.set_page_config(
#     page_title="Dash Evonode ROI Calculator",
#     page_icon="💰",
#     layout="wide"
# )

st.set_page_config(
    page_title="Dash Evonode ROI Calculator",
    page_icon="favicon.ico",
    layout="wide"
)

# Localization / Локализация
LANG = {
    'title': {
        'eng': 'Dash Evonode ROI Calculator',
        'rus': 'Калькулятор доходности Dash Evonode'
    },
    'description': {
        'eng': 'Calculate annual ROI for Dash cryptocurrency investments in Evonodes, considering Core (L1) and Platform (L2) blockchain payouts and server hosting expenses.',
        'rus': 'Расчет годовой доходности при инвестировании Dash в Evonodes, с учетом выплат на блокчейнах Core (L1) и Platform (L2), а также расходов на хостинг серверов.'
    },
    'menu': {
        'choose_lang': {
            'eng': 'Choose language:', 
            'rus': 'Выберите язык:'
        },
        'lang_options': {
            'eng': ['English', 'Russian'],
            'rus': ['Английский', 'Русский']
        },
        'currency_choice': {
            'eng': 'Select server rent currency:',
            'rus': 'Выберите валюту для оплаты аренды:'
        },
        'currency_options': {
            'eng': ['USD ($)', 'RUB (₽)'],
            'rus': ['Доллар ($)', 'Рубль (₽)']
        }
    },
    'inputs': {
        'default_values': {'eng': 'Enter data (default values are pre-filled):', 'rus': 'Введите данные (значения по умолчанию уже заполнены):'},
        'servers': {'eng': 'Number of servers (Evo)', 'rus': 'Количество серверов (Evo)'},
        'investment': {'eng': 'Dash investment per server', 'rus': 'Инвестиция в Dash на 1 сервер'},
        'profit1': {'eng': 'Platform payments (Dash)', 'rus': 'Выплаты на Platform (Dash)'},
        'days1': {'eng': 'Platform interval (days)', 'rus': 'Периодичность Platform (дней)'},
        'profit2': {'eng': 'Core profit (Dash)', 'rus': 'Прибыль Core (Dash)'},
        'days2': {'eng': 'Core interval (days)', 'rus': 'Периодичность Core (дней)'},
        'ssl': {'eng': 'SSL cost per server ($)', 'rus': 'Стоимость SSL на 1 сервер ($)'},
        'ssl_months': {'eng': 'SSL validity period (months)', 'rus': 'Срок действия SSL (месяцев)'},
        'discount': {'eng': 'Annual server discount (%)', 'rus': 'Годовая скидка на аренду серверов (%)'},
        'main_rent': {
            '$': {'eng': 'Main server rent ($/month)', 'rus': 'Аренда основного сервера ($/мес)'},
            '₽': {'eng': 'Main server rent (₽/month)', 'rus': 'Аренда основного сервера (₽/мес)'}
        },
        'add_rent': {
            '$': {'eng': 'Additional servers rent ($/month)', 'rus': 'Общая аренда доп. серверов ($/мес)'},
            '₽': {'eng': 'Additional servers rent (₽/month)', 'rus': 'Общая аренда доп. серверов (₽/мес)'}
        }
    },
    'results': {
        'header': {'eng': 'Results', 'rus': 'Результаты'},
        'dash_rate': {'eng': 'Current Dash rate: {} $/DASH', 'rus': 'Текущий курс Dash: {} $/DASH'},
        'usd_rate': {'eng': 'Current USD rate: {} ₽/$', 'rus': 'Текущий курс USD: {} ₽/$'},
        'total_invest': {'eng': 'Total investment: {} Dash ({:.2f} $)', 'rus': 'Общие инвестиции: {} Dash ({:.2f} $)'},
        'annual_income': {'eng': 'Annual income: {:.2f} $', 'rus': 'Годовой доход: {:.2f} $'},
        'annual_expenses': {'eng': 'Annual expenses: {:.2f} $', 'rus': 'Годовые расходы: {:.2f} $'},
        'net_profit': {'eng': 'Net profit: {:.2f} $', 'rus': 'Чистая прибыль: {:.2f} $'},
        'roi': {'eng': 'ROI: {:.2f}%', 'rus': 'Прибыль в процентах: {:.2f}%'}
    },
    'errors': {
        'cbr': {'eng': 'CBR rate error: Using default rate of 84.21 ₽/$', 'rus': 'Ошибка курса ЦБ: Используется курс по умолчанию 84.21 ₽/$'},
        'dash': {'eng': 'Dash rate error: Using default rate of 28.50 $/DASH', 'rus': 'Ошибка курса Dash: Используется курс по умолчанию 28.50 $/DASH'}
    },
    'calculate': {'eng': 'Calculate', 'rus': 'Рассчитать'}
}

# Default values
DEFAULT_VALUES = {
    'servers_count': 5,
    'investment_per_server': 4000,
    'profit1': 9,
    'days1': 9.5,
    'profit2': 0.89,
    'days2': 4.5,
    'ssl_cost': 81,
    'ssl_months': 36,
    'discount_rate': 10,
    'rent_main': {'$': 50, '₽': 4350},
    'add_servers': {'$': 45, '₽': 7655}
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_usd_rate():
    """Get USD/RUB rate from CBR"""
    try:
        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp', timeout=10)
        response.encoding = 'windows-1251'
        root = ET.fromstring(response.text)
        
        for valute in root.findall('Valute'):
            if valute.find('CharCode').text == 'USD':
                return round(float(valute.find('Value').text.replace(',', '.')), 2)
        st.warning("USD rate not found in CBR data, using default value of 84.21 ₽/$")
        return 84.21  # Default value if not found
    except Exception as e:
        st.warning(f"Error getting USD rate from CBR: {e}. Using default value of 84.21 ₽/$")
        return 84.21  # Default value in case of error

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_dash_rate():
    """Get Dash/USD rate"""
    try:
        response = requests.get("https://chainz.cryptoid.info/dash/api.dws?q=ticker.usd", timeout=10)
        return round(float(response.text), 2)
    except Exception as e:
        st.warning(f"Error getting Dash rate: {e}. Using default value of 28.50 $/DASH")
        return 28.50  # Default value in case of error

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'lang' not in st.session_state:
        st.session_state.lang = 'eng'
    if 'currency' not in st.session_state:
        st.session_state.currency = '$'
    if 'dash_usd' not in st.session_state:
        st.session_state.dash_usd = get_dash_rate()
    if 'usd_rub' not in st.session_state:
        st.session_state.usd_rub = get_usd_rate()
    if 'calculation_done' not in st.session_state:
        st.session_state.calculation_done = False
    if 'calculation_results' not in st.session_state:
        st.session_state.calculation_results = {}

def change_language():
    """Change the language of the application"""
    lang_option = st.session_state.language_selector
    if lang_option == LANG['menu']['lang_options']['eng'][0] or lang_option == LANG['menu']['lang_options']['rus'][0]:
        st.session_state.lang = 'eng'
    else:
        st.session_state.lang = 'rus'
#     st.rerun()

def change_currency():
    """Change the currency for server rent"""
    currency_option = st.session_state.currency_selector
    if currency_option == LANG['menu']['currency_options']['eng'][0] or currency_option == LANG['menu']['currency_options']['rus'][0]:
        st.session_state.currency = '$'
    else:
        st.session_state.currency = '₽'
#     st.rerun()

def calculate_profit():
    """Calculate profit based on user inputs"""
    lang = st.session_state.lang
    currency = st.session_state.currency
    dash_usd = st.session_state.dash_usd
    usd_rub = st.session_state.usd_rub
    
    # Get input values from session state
    servers_count = st.session_state.servers_count
    investment_per_server = st.session_state.investment_per_server
    profit1 = st.session_state.profit1
    days1 = st.session_state.days1
    profit2 = st.session_state.profit2
    days2 = st.session_state.days2
    ssl_cost = st.session_state.ssl_cost
    ssl_months = st.session_state.ssl_months
    discount_rate = st.session_state.discount_rate / 100
    
    rent_main = st.session_state.rent_main
    add_servers = st.session_state.add_servers

    # Currency conversion
    if currency == '₽':
        rent_main_usd = rent_main / usd_rub
        add_servers_usd = add_servers / usd_rub
    else:
        rent_main_usd = rent_main
        add_servers_usd = add_servers

    # Calculations
    total_investment = investment_per_server * servers_count
    ssl_annual_per_server = (ssl_cost / ssl_months) * 12  # Annual cost per server
    ssl_total = ssl_annual_per_server * servers_count      # Total annual cost
    
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

    # Store results
    st.session_state.calculation_results = {
        'dash_usd': dash_usd,
        'usd_rub': usd_rub,
        'total_investment': total_investment,
        'initial_investment_usd': initial_investment_usd,
        'total_usd_income': total_usd_income,
        'total_usd_expenses': total_usd_expenses,
        'net_profit': net_profit,
        'profit_percent': profit_percent
    }
    
    st.session_state.calculation_done = True
    st.rerun()

def main():
    # Initialize session state
    initialize_session_state()
    
    lang = st.session_state.lang
    currency = st.session_state.currency
    
    # Добавляем кнопку меню здесь (перед всем остальным содержимым)
    btn_text = "Меню" if lang == "rus" else "Menu"
    st.markdown(f"""
    <style>
        /* Добавляем пространство для кнопки */
        .stApp {{
            padding-top: 50px;
        }}
        /* Фиксированная кнопка меню в стиле языкового переключателя */
        .menu-btn {{
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 999999;
            background-color: #2d3035 !important;
            color: #c8c9ca !important;
            padding: 5px 10px !important;
            border-radius: 4px !important;
            text-decoration: none !important;
            border: 1px solid #444 !important;
            font-size: 14px !important;
            font-weight: normal !important;
            display: inline-flex;
            align-items: center;
            transition: all 0.2s ease;
        }}
        .menu-btn:hover {{
            background-color: #3a3d44 !important;
            color: #fff !important;
            transform: translateY(-1px);
        }}
        .menu-btn i {{
            margin-right: 5px;
        }}
    </style>

    <a href="https://evocalc.ru?lang={'ru' if lang == 'rus' else 'en'}" class="menu-btn" target="_self">
        <i class="bi bi-house-door"></i> {btn_text}
    </a>

    <!-- Подключаем иконки Bootstrap -->
<!--     <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"> -->
    """, unsafe_allow_html=True)

    # Title and description
    st.title(LANG['title'][lang])
    st.write(LANG['description'][lang])
    
    # Language and currency selection at the top of the page
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(LANG['menu']['choose_lang'][lang])
        st.selectbox(
            label="Language / Язык",
            options=LANG['menu']['lang_options'][lang],
            key='language_selector',
            on_change=change_language,
            index=0 if lang == 'eng' else 1
        )
    
    with col2:
        st.subheader(LANG['menu']['currency_choice'][lang])
        st.selectbox(
            label="Currency / Валюта",
            options=LANG['menu']['currency_options'][lang],
            key='currency_selector',
            on_change=change_currency,
            index=0 if currency == '$' else 1
        )
    
    # Display current rates
    rate_col1, rate_col2 = st.columns(2)
    with rate_col1:
        dash_usd = st.session_state.dash_usd
        st.info(LANG['results']['dash_rate'][lang].format(dash_usd))
    
    if currency == '₽':
        with rate_col2:
            usd_rub = st.session_state.usd_rub
            st.info(LANG['results']['usd_rate'][lang].format(usd_rub))
    
    st.divider()
    
    # Main form for inputs
    st.header(LANG['inputs']['default_values'][lang])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            LANG['inputs']['servers'][lang],
            min_value=1,
            value=int(DEFAULT_VALUES['servers_count']),
            step=1,
            key='servers_count'
        )
        
        st.number_input(
            LANG['inputs']['investment'][lang],
            min_value=1.0,
            value=float(DEFAULT_VALUES['investment_per_server']),
            step=1.0,
            key='investment_per_server'
        )
        
        st.number_input(
            LANG['inputs']['profit1'][lang],
            min_value=0.1,
            value=float(DEFAULT_VALUES['profit1']),
            step=0.1,
            key='profit1'
        )
        
        st.number_input(
            LANG['inputs']['days1'][lang],
            min_value=0.1,
            value=float(DEFAULT_VALUES['days1']),
            step=0.1,
            key='days1'
        )
        
        st.number_input(
            LANG['inputs']['profit2'][lang],
            min_value=0.01,
            value=float(DEFAULT_VALUES['profit2']),
            step=0.01,
            key='profit2'
        )
    
    with col2:
        st.number_input(
            LANG['inputs']['days2'][lang],
            min_value=0.1,
            value=float(DEFAULT_VALUES['days2']),
            step=0.1,
            key='days2'
        )
        
        st.number_input(
            LANG['inputs']['ssl'][lang],
            min_value=1.0,
            value=float(DEFAULT_VALUES['ssl_cost']),
            step=1.0,
            key='ssl_cost'
        )
        
        st.number_input(
            LANG['inputs']['ssl_months'][lang],
            min_value=1,
            value=int(DEFAULT_VALUES['ssl_months']),
            step=1,
            key='ssl_months'
        )
        
        st.number_input(
            LANG['inputs']['discount'][lang],
            min_value=0.0,
            max_value=100.0,
            value=float(DEFAULT_VALUES['discount_rate']),
            step=1.0,
            key='discount_rate'
        )
        
        st.number_input(
            LANG['inputs']['main_rent'][currency][lang],
            min_value=1.0,
            value=float(DEFAULT_VALUES['rent_main'][currency]),
            step=1.0,
            key='rent_main'
        )
    
    st.number_input(
        LANG['inputs']['add_rent'][currency][lang],
        min_value=0.0,
        value=float(DEFAULT_VALUES['add_servers'][currency]),
        step=1.0,
        key='add_servers'
    )
    
    # Calculate button
    st.button(
        LANG['calculate'][lang],
        type="primary",
        on_click=calculate_profit
    )
    
    # Results section
    if st.session_state.calculation_done:
        st.header(LANG['results']['header'][lang])
        
        results = st.session_state.calculation_results
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label=LANG['results']['total_invest'][lang].format(
                    results['total_investment'], 
                    results['initial_investment_usd']
                ).split(':')[0],
                value=f"{results['total_investment']} Dash (${results['initial_investment_usd']:.2f})"
            )
            
            st.metric(
                label=LANG['results']['annual_income'][lang].format(0).split(':')[0],
                value=f"${results['total_usd_income']:.2f}"
            )
        
        with col2:
            st.metric(
                label=LANG['results']['annual_expenses'][lang].format(0).split(':')[0],
                value=f"${results['total_usd_expenses']:.2f}"
            )
            
            st.metric(
                label=LANG['results']['net_profit'][lang].format(0).split(':')[0],
                value=f"${results['net_profit']:.2f}"
            )
        
        # ROI with color indicator
        roi_value = results['profit_percent']
        st.metric(
            label=LANG['results']['roi'][lang].format(0).split(':')[0],
            value=f"{roi_value:.2f}%",
            delta=f"{roi_value:.2f}%" if roi_value > 0 else f"-{abs(roi_value):.2f}%",
            delta_color="normal" if roi_value > 0 else "inverse"
        )

if __name__ == "__main__":
    main()
