document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the results page
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
		// Добавьте перед запросом:
		if (navigator.userAgent.includes('Safari') && window.devToolsOpen) {
			window.location.reload(true);
			return;
		}
        fetchWithdrawalsData();
    }

    // Switch language
    const langSwitchers = document.querySelectorAll('.lang-switch');
    langSwitchers.forEach(switcher => {
        switcher.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            
            // Update URL with new language
            const url = new URL(window.location);
            url.searchParams.set('lang', lang);
            window.location = url.toString();
        });
    });

    // Form submission
    const validatorForm = document.getElementById('validator-form');
    if (validatorForm) {
        validatorForm.addEventListener('submit', function() {
            const submitBtn = document.getElementById('submit-btn');
            const loadingSpinner = document.getElementById('loading-spinner');
            
            submitBtn.disabled = true;
            loadingSpinner.classList.remove('d-none');
        });
    }
});

function fetchWithdrawalsData(preloadedValidators = null) {
    const resultsContainer = document.getElementById('results-container');
    const loadingContainer = document.getElementById('loading-container');
    const errorContainer = document.getElementById('error-container');
    const tableContainer = document.getElementById('withdrawals-table-container');
    const loadingDetails = document.getElementById('loading-details');
    
    if (!resultsContainer || !tableContainer) {
        console.error('Required containers not found');
        return;
    }
    
    // Get validators from parameter or data attribute
    let validators = [];
    
    if (preloadedValidators && Array.isArray(preloadedValidators)) {
        // Use preloaded validators if provided
        validators = preloadedValidators;
        console.log('Using preloaded validators:', validators);
    } else {
        // Fallback to data attribute (but this path is now less preferred)
        try {
            console.log("Falling back to data attribute for validators");
            const validatorsJson = tableContainer.dataset.validators || '[]';
            validators = JSON.parse(validatorsJson);
            console.log('Parsed validators from data attribute:', validators);
        } catch (e) {
            console.error('Error parsing validators from data attribute:', e);
        }
    }
    
    if (!validators.length) {
        console.error('No validators found');
        showError('No validators found. Please enter validator hashes and try again.');
        return;
    }
    
    const lang = tableContainer.dataset.lang || 'en';
    
    // Get the start_epoch from data attribute
    let start_epoch = 21; // Default
    try {
        const startEpochValue = tableContainer.dataset.startEpoch;
        if (startEpochValue) {
            start_epoch = parseInt(startEpochValue);
            if (isNaN(start_epoch) || start_epoch < 1) {
                start_epoch = 21;
            }
        }
    } catch (e) {
        console.error('Error parsing start_epoch:', e);
    }
    console.log(`Using start_epoch: ${start_epoch}`);
    
    console.log(`Fetching withdrawals data for ${validators.length} validators...`);
    loadingContainer.classList.remove('d-none');
    resultsContainer.classList.add('d-none');
    errorContainer.classList.add('d-none');
    
    // Set initial loading message
    if (loadingDetails) {
        loadingDetails.textContent = lang === 'ru' 
            ? 'Соединение с API Dash Platform и получение данных валидатора...' 
            : 'Connecting to the Dash Platform API and retrieving validator data...';
    }
    
	fetch('/webmux/api/fetch_withdrawals', {  // Добавлен префикс /webmux
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            validators: validators,
            lang: lang,
            start_epoch: start_epoch
        }),
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('API response status:', response.status);
        
        // Update loading message to show progress
        if (loadingDetails) {
            loadingDetails.textContent = lang === 'ru' 
                ? 'Получены данные от API, обработка результатов...' 
                : 'API data received, processing results...';
        }
        
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error(errData.error || 'Network response was not ok');
            }).catch(e => {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data);
        if (data.error) {
            console.error('Error in data:', data.error);
            showError(data.error);
            return;
        }
        // Check for API connection errors
        if (data.api_error) {
            console.error('API connection error:', data.api_error);
            showError(data.api_error);
            return;
        }
        renderWithdrawalsTable(data, validators);
        loadingContainer.classList.add('d-none');
        resultsContainer.classList.remove('d-none');
    })
    .catch(error => {
        console.error('Error fetching withdrawals data:', error);
        showError(error.message || 'An unknown error occurred');
    });
}

function showError(message, options = {}) {
    const {
        isDebug = false,    // Режим отладки (показывать в console.error)
        isWarning = false,  // Это предупреждение (не ошибка)
        showToUser = true   // Показывать пользователю
    } = options;

    // Получаем элементы
    const loadingContainer = document.getElementById('loading-container');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');

    // Скрываем индикатор загрузки
    if (loadingContainer) loadingContainer.classList.add('d-none');

    // Показываем сообщение пользователю
    if (showToUser && errorContainer && errorMessage) {
        errorContainer.classList.remove('d-none');
        errorMessage.textContent = message;
        
        // Добавляем класс в зависимости от типа сообщения
        errorContainer.className = isWarning ? 'alert alert-warning' : 'alert alert-danger';
    }

    // Логируем только в режиме отладки или для реальных ошибок
    if (isDebug || !isWarning) {
        console[isWarning ? 'warn' : 'error']('Validator App:', message);
    }
}

function renderWithdrawalsTable(data, originalValidatorsList) {
    const tableContainer = document.getElementById('withdrawals-table-container');
    if (!tableContainer) return;
    
    const { withdrawals, identities, validator_totals, grand_total, epoch_range, current_epoch, validator_ips } = data;
    
    // Get translations from HTML data attributes
    const translations = {
        validator: tableContainer.dataset.translatorValidator || 'Validator',
        total: tableContainer.dataset.translatorTotal || 'TOTAL',
        grandTotal: tableContainer.dataset.translatorGrandTotal || 'GRAND TOTAL',
        epoch: tableContainer.dataset.translatorEpoch || 'Epoch',
        noData: tableContainer.dataset.translatorNoData || 'No data available'
    };

    // Рассчитываем суммы по эпохам
    const epochTotals = {};
    epoch_range.forEach(epoch => {
        epochTotals[epoch] = 0;
        Object.values(withdrawals).forEach(validatorData => {
            epochTotals[epoch] += validatorData[epoch] || 0;
        });
    });

    // Store the original list of validators for proper ordering
    if (!originalValidatorsList || !originalValidatorsList.length) {
        originalValidatorsList = window.validatorsList || [];
        
        // If still not available, try to get from data attribute (fallback)
        if (!originalValidatorsList || !originalValidatorsList.length) {
            try {
                const validatorsJson = tableContainer.dataset.validators || '[]';
                if (!validatorsJson.trim()) {
                    throw new Error('Empty validators data');
                }
                originalValidatorsList = JSON.parse(validatorsJson);
            } catch (e) {
                console.error('Error parsing validators:', e);
                if (window.validatorsList && Array.isArray(window.validatorsList)) {
                    originalValidatorsList = window.validatorsList;
                } else {
                    showError('Error loading validator data');
                    return;
                }
            }                        
        }
    }
    
    // Create table HTML
    let tableHtml = `
    <div class="table-responsive">
        <table class="table table-dark table-bordered table-hover">
            <thead class="bg-dark">
                <tr>
                    <th>${translations.validator}</th>`;
    
    // Add epoch headers
    epoch_range.forEach((epoch, index) => {
        const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
        tableHtml += `<th class="${bgClass}">${epoch}</th>`;
    });
    
    tableHtml += `<th class="bg-dark">${translations.total}</th></tr></thead><tbody>`;
    
    // Check if we have any data
    if (Object.keys(withdrawals).length === 0) {
        tableHtml += `<tr><td colspan="${epoch_range.length + 2}" class="text-center">${translations.noData}</td></tr>`;
    } else {
        // Iterate through validators
        originalValidatorsList.forEach(validator => {
            if (!withdrawals[validator]) return;
            
            const validatorData = withdrawals[validator];
            const serverIP = validator_ips && validator_ips[validator];
            const validatorName = serverIP || identities[validator] || validator.substring(0, 8) + '...';
            
            tableHtml += `<tr><td class="validator-cell">${validatorName}</td>`;
            
            epoch_range.forEach((epoch, index) => {
                const amount = validatorData[epoch] || 0;
                const formattedAmount = amount > 0 ? (amount / 1000).toFixed(1) : '—';
                const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
                tableHtml += `<td class="text-end ${bgClass}">${formattedAmount}</td>`;
            });
            
            const validatorTotal = validator_totals[validator] || 0;
            tableHtml += `<td class="text-end bg-dark fw-bold">${(validatorTotal / 1000).toFixed(1)}</td></tr>`;
        });
    }
    
    // Add grand total row
    tableHtml += `
        </tbody>
        <tfoot>
            <tr class="bg-dark text-white">
                <td class="fw-bold">${translations.grandTotal}</td>`;
    
    epoch_range.forEach((epoch, index) => {
        const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
        tableHtml += `<td class="text-end ${bgClass} fw-bold">${(epochTotals[epoch] / 1000).toFixed(1)}</td>`;
    });
    
    tableHtml += `<td class="text-end fw-bold bg-dark">${(grand_total / 1000).toFixed(1)}</td></tr>
        </tfoot>
        </table>
    </div>
    <div class="d-flex justify-content-end mt-3">
        <button id="copy-table-btn" class="btn btn-outline-secondary" title="Copy table to clipboard">
            <i class="bi bi-clipboard"></i> Copy Table
        </button>
    </div>`;
    
    tableContainer.innerHTML = tableHtml;
    
    // Initialize DataTable if available
    if (typeof DataTable !== 'undefined') {
        try {
            new DataTable('table', {
                paging: false,
                ordering: false,
                info: false,
                searching: false
            });
        } catch (error) {
            console.error('DataTable init error:', error);
        }
    }
    
    // Set up copy button
    const copyButton = document.getElementById('copy-table-btn');
    if (copyButton) {
        copyButton.addEventListener('click', () => {
            try {
                const table = tableContainer.querySelector('table');
                navigator.clipboard.writeText(table.outerHTML)
                    .then(() => {
                        const toast = document.getElementById('copy-toast');
                        if (toast) toast.style.display = 'block';
                    });
            } catch (error) {
                console.error('Copy failed:', error);
            }
        });
    }
}
// function showError(message) {
//     const loadingContainer = document.getElementById('loading-container');
//     const errorContainer = document.getElementById('error-container');
//     const errorMessage = document.getElementById('error-message');
//     
//     loadingContainer.classList.add('d-none');
//     errorContainer.classList.remove('d-none');
//     errorMessage.textContent = message;
// }

function renderWithdrawalsTable(data, originalValidatorsList) {
    const tableContainer = document.getElementById('withdrawals-table-container');
    if (!tableContainer) return;
    
    const { withdrawals, identities, validator_totals, grand_total, epoch_range, current_epoch, validator_ips } = data;
    
    // Store the original list of validators for proper ordering
    // If not provided, try to get from window object or data attribute
    if (!originalValidatorsList || !originalValidatorsList.length) {
        originalValidatorsList = window.validatorsList || [];
        
        // If still not available, try to get from data attribute (fallback)
        if (!originalValidatorsList || !originalValidatorsList.length) {

			try {
				const validatorsJson = tableContainer.dataset.validators || '[]';
				if (!validatorsJson || validatorsJson.trim() === '') {
					throw new Error('Empty validators data');
				}
				validators = JSON.parse(validatorsJson);
			} catch (e) {
				console.error('Error parsing validators:', e);
				// Fallback to window object if available
				if (window.validatorsList && Array.isArray(window.validatorsList)) {
					validators = window.validatorsList;
				} else {
					showError(lang === 'ru' ? 
						'Ошибка загрузки данных валидаторов' : 
						'Error loading validator data');
					return;
				}
			}                        
//             try {
//                 const validatorsJson = tableContainer.dataset.validators || '[]';
//                 originalValidatorsList = JSON.parse(validatorsJson);
//             } catch (e) {
//                 console.error('Error getting original validators list:', e);
//                 originalValidatorsList = Object.keys(withdrawals);
//             }
        }
    }
    
    // Get translations from HTML data attributes
    const translations = {
        validator: tableContainer.dataset.translatorValidator || 'Validator',
        total: tableContainer.dataset.translatorTotal || 'TOTAL',
        grandTotal: tableContainer.dataset.translatorGrandTotal || 'GRAND TOTAL',
        epoch: tableContainer.dataset.translatorEpoch || 'Epoch',
        noData: tableContainer.dataset.translatorNoData || 'No data available'
    };
    
    // Create table with gray styles (no striped rows)
    let tableHtml = `
    <div class="table-responsive">
        <table class="table table-dark table-bordered table-hover">
            <thead class="bg-dark">
                <tr>
                    <th>${translations.validator}</th>
    `;
    
    // Add epoch headers with subtle alternating colors
    epoch_range.forEach((epoch, index) => {
        const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
        tableHtml += `<th class="${bgClass}">${epoch}</th>`;
    });
    
    // Add total header
    tableHtml += `<th class="bg-dark">${translations.total}</th></tr></thead><tbody>`;
    
    // Check if we have any data
    if (Object.keys(withdrawals).length === 0) {
        tableHtml += `<tr><td colspan="${epoch_range.length + 2}" class="text-center">${translations.noData}</td></tr>`;
    } else {
        // Iterate through validators in their original input order
        originalValidatorsList.forEach(validator => {
            // Skip if we don't have withdrawal data for this validator
            if (!withdrawals[validator]) return;
            
            const validatorData = withdrawals[validator];
            // Use server IP from validator_ips if available, otherwise use identity or truncated hash
            const serverIP = validator_ips && validator_ips[validator];
            const validatorName = serverIP || identities[validator] || validator.substring(0, 8) + '...';
            
            tableHtml += `<tr><td class="validator-cell">${validatorName}</td>`;
            
            // Add cells for each epoch with very subtle alternating column colors
            epoch_range.forEach((epoch, index) => {
                const amount = validatorData[epoch] || 0;
                // Divide by 1000 and format with 1 decimal place
                const formattedAmount = amount > 0 ? (amount / 1000).toFixed(1) : '—';
                // Using custom classes with very subtle color difference
                const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
                tableHtml += `<td class="text-end ${bgClass}">${formattedAmount}</td>`;
            });
            
            // Add total for this validator (divided by 1000 and rounded to 1 decimal place)
            const validatorTotal = validator_totals[validator] || 0;
            const formattedTotal = (validatorTotal / 1000).toFixed(1);
            tableHtml += `<td class="text-end bg-dark fw-bold">${formattedTotal}</td></tr>`;
        });
    }
    
    // Add grand total row
    tableHtml += `
        </tbody>
        <tfoot>
            <tr class="bg-dark text-white">
                <td class="fw-bold">${translations.grandTotal}</td>
    `;
    
    // Empty cells for each epoch with subtle alternating colors
    epoch_range.forEach((_, index) => {
        const bgClass = index % 2 === 0 ? 'bg-dark-subtle' : 'bg-dark';
        tableHtml += `<td class="${bgClass}"></td>`;
    });
    
    // Grand total value (divided by 1000 and rounded to 1 decimal place)
    const formattedGrandTotal = (grand_total / 1000).toFixed(1);
    tableHtml += `<td class="text-end fw-bold bg-dark">${formattedGrandTotal}</td></tr>
        </tfoot>
        </table>
    </div>`;
    
    // Add copy button below the table
    tableHtml += `
    <div class="d-flex justify-content-end mt-3">
        <button id="copy-table-btn" class="btn btn-outline-secondary" title="Copy table to clipboard">
            <i class="bi bi-clipboard"></i> Copy Table
        </button>
    </div>`;
    
    // Render the table
    tableContainer.innerHTML = tableHtml;
    
    // Check if DataTable is available
    if (typeof DataTable !== 'undefined') {
        try {
            // Initialize DataTable for improved functionality
            const dataTable = new DataTable('table', {
                paging: false,
                ordering: false,
                info: false,
                searching: false
            });
            console.log('DataTable initialized');
        } catch (error) {
            console.error('Error initializing DataTable:', error);
        }
    } else {
        console.warn('DataTable library not loaded');
    }
    
    // Set up copy button functionality
    const copyButton = document.getElementById('copy-table-btn');
    if (copyButton) {
        copyButton.addEventListener('click', function() {
            try {
                const tableElement = tableContainer.querySelector('table');
                const range = document.createRange();
                range.selectNode(tableElement);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand('copy');
                window.getSelection().removeAllRanges();
                
                // Show toast notification if available
                const toastElement = document.getElementById('copy-toast');
                if (toastElement && typeof bootstrap !== 'undefined') {
                    const toast = new bootstrap.Toast(toastElement);
                    toast.show();
                } else {
                    // Fallback notification
                    alert('Table copied to clipboard!');
                }
            } catch (error) {
                console.error('Error copying table:', error);
                alert('Failed to copy table to clipboard');
            }
        });
    } else {
        console.warn('Copy button not found');
    }
}