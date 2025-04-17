import os
import logging
from flask import Flask, request

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "app-selector-secret")

# Define app selector translations
app_selector_translations = {
    "en": {
        "title": "Application Selector",
        "webmux_title": "WebMuxValidator",
        "webmux_desc": "Dash Validator Withdrawals Monitor",
        "roi_title": "EvoServerROICalculator",
        "roi_desc": "Server ROI Calculator",
        "launch": "Launch",
        "footer": "© 2025 Applications"
    },
    "ru": {
        "title": "Выбор Приложения",
        "webmux_title": "WebMuxValidator",
        "webmux_desc": "Мониторинг выплат валидаторов Dash",
        "roi_title": "EvoServerROICalculator",
        "roi_desc": "Калькулятор ROI серверов",
        "launch": "Запустить",
        "footer": "© 2025 Приложения"
    }
}

@app.route('/')
def index():
    """Main menu page to choose between applications"""
    # Get language from request or default to Russian
    lang = request.args.get('lang', 'ru')
    
    # Validate language
    if lang not in app_selector_translations:
        lang = 'ru'
    
    # Render the main menu page
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{app_selector_translations[lang]["title"]}</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
        <style>
            body {{
                background-color: #1c1e22;
                color: #c8c9ca;
            }}
            .app-card {{
                background-color: #2d2f34;
                border: 1px solid #444;
                transition: transform 0.2s;
            }}
            .app-card:hover {{
                transform: translateY(-5px);
            }}
            .card-header {{
                background-color: #212328;
                border-bottom: 1px solid #444;
            }}
            .btn-app {{
                background-color: #3a3d44;
                border-color: #444;
                color: #fff;
            }}
            .btn-app:hover {{
                background-color: #4b4e57;
            }}
            .language-switcher {{
                position: absolute;
                top: 10px;
                right: 10px;
            }}
            .lang-switch {{
                text-decoration: none;
                margin-left: 5px;
            }}
            .active span {{
                background-color: #0d6efd !important;
            }}
        </style>
    </head>
    <body class="d-flex flex-column min-vh-100">
        <header class="bg-dark py-3 position-relative">
            <div class="container">
                <h1 class="h3 mb-0 text-light text-center">
                    <i class="bi bi-grid-fill me-2"></i>
                    {app_selector_translations[lang]["title"]}
                </h1>
                <div class="language-switcher">
                    <a href="?lang=en" class="lang-switch {'active' if lang == 'en' else ''}" data-lang="en">
                        <span class="badge bg-secondary">EN</span>
                    </a>
                    <a href="?lang=ru" class="lang-switch {'active' if lang == 'ru' else ''}" data-lang="ru">
                        <span class="badge bg-secondary">RU</span>
                    </a>
                </div>
            </div>
        </header>

        <main class="container py-4 flex-grow-1">
            <div class="row justify-content-center g-4">
                <div class="col-md-5">
                    <div class="card app-card shadow h-100">
                        <div class="card-header">
                            <h2 class="h5 mb-0">
                                <i class="bi bi-bar-chart-fill me-2"></i>
                                {app_selector_translations[lang]["webmux_title"]}
                            </h2>
                        </div>
                        <div class="card-body d-flex flex-column">
                            <p>{app_selector_translations[lang]["webmux_desc"]}</p>
                            <div class="mt-auto d-grid">
<!--                                 <a href="http://46.19.66.201:5001" class="btn btn-app"> -->
								<a href="https://evocalc.ru/webmux/" class="btn btn-app">
                                    <i class="bi bi-arrow-right-circle me-1"></i>
                                    {app_selector_translations[lang]["launch"]}
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-5">
                    <div class="card app-card shadow h-100">
                        <div class="card-header">
                            <h2 class="h5 mb-0">
                                <i class="bi bi-calculator me-2"></i>
                                {app_selector_translations[lang]["roi_title"]}
                            </h2>
                        </div>
                        <div class="card-body d-flex flex-column">
                            <p>{app_selector_translations[lang]["roi_desc"]}</p>
                            <div class="mt-auto d-grid">
<!--                                 <a href="http://46.19.66.201:5002" class="btn btn-app"> -->
								<a href="https://evocalc.ru/roi/" class="btn btn-app">
                                    <i class="bi bi-arrow-right-circle me-1"></i>
                                    {app_selector_translations[lang]["launch"]}
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <footer class="bg-dark text-light py-3 mt-auto">
            <div class="container text-center">
                <p class="mb-0">{app_selector_translations[lang]["footer"]}</p>
            </div>
        </footer>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)