// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// Применяем тему Telegram
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f4f4f5');

// Кэш опций
let OPTIONS_CACHE = null;

// Вспомогательные функции
function vibrate(type = 'light') {
    if (tg?.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred(type);
    }
}

function notify(type = 'error') {
    if (tg?.HapticFeedback?.notificationOccurred) {
        tg.HapticFeedback.notificationOccurred(type);
    }
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    setTimeout(() => notification.classList.remove('show'), 3000);
}

// Загрузка справочников
async function loadOptions() {
    if (OPTIONS_CACHE) return OPTIONS_CACHE;

    try {
        const response = await fetch('/api/options', {
            method: 'GET',
            headers: {
                'Authorization': tg.initData
            }
        });

        if (!response.ok) throw new Error('Не удалось загрузить данные');
        OPTIONS_CACHE = await response.json();
        return OPTIONS_CACHE;
    } catch (error) {
        console.error('Ошибка загрузки options:', error);
        notify('error');
        showNotification('Не удалось загрузить списки. Проверьте соединение.', 'error');
        return null;
    }
}

// Заполнение select
function populateSelect(selectId, items, placeholder = 'Выберите...') {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = `<option value="" disabled selected>${placeholder}</option>`;
    items?.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = item.name;
        select.appendChild(opt);
    });
}

// Инициализация select'ов
async function initializeSelects() {
    const options = await loadOptions();
    if (!options) return;

    // USDT форма
    populateSelect('source', options.sources, 'Источник сделки');
    populateSelect('from-bot-usdt', options.bots, 'Из бота');
    populateSelect('manager-usdt', options.managers, 'Менеджер');

    // Валютная форма
    populateSelect('manager-currency', options.managers, 'Менеджер');
    populateSelect('from-bot-currency', options.bots, 'Из бота');
}

// Переключение табов
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        vibrate('light');
    });
});

// Показ/скрытие поля "Фиат счёт"
document.getElementById('usdt-transaction-type')?.addEventListener('change', (e) => {
    const group = document.getElementById('fiat-account-group');
    const input = document.getElementById('fiat-account');
    if (e.target.value === 'Покупка USDT') {
        group.style.display = 'block';
        input.required = true;
    } else {
        group.style.display = 'none';
        input.required = false;
    }
});

// Преобразование формы в JSON
function formToJSON(form) {
    const data = {};
    for (const [key, value] of new FormData(form).entries()) {
        if (value !== '') data[key] = value;
    }
    return data;
}

// Отправка формы
async function submitForm(formId, endpoint) {
    const form = document.getElementById(formId);
    const btn = form.querySelector('.btn-submit');
    if (!form.checkValidity()) {
        form.reportValidity();
        notify('error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Отправка...';

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    try {
        const jsonData = {
            ...formToJSON(form),
            initData: tg.initData
        };

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jsonData),
            signal: controller.signal
        });

        clearTimeout(timeout);
        if (!res.ok) throw new Error(`Ошибка: ${res.status}`);

        const result = await res.json();
        if (result.success) {
            showNotification(result.message || 'Успешно!', 'success');
            form.reset();
            form.querySelectorAll('select').forEach(s => s.selectedIndex = 0);
            notify('success');

            tg.MainButton.hide();
            tg.MainButton.setText('Закрыть');
            tg.MainButton.show();
            tg.MainButton.onClick(() => {
                tg.MainButton.hide();
                tg.close();
            });
            setTimeout(() => tg.close(), 2000);
        } else {
            showNotification(result.message || 'Ошибка', 'error');
            notify('error');
        }
    } catch (err) {
        console.error(err);
        if (err.name === 'AbortError') {
            showNotification('Таймаут: сервер не отвечает', 'error');
        } else {
            showNotification(err.message || 'Ошибка сети', 'error');
        }
        notify('error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Отправить';
        clearTimeout(timeout);
    }
}

// Обработчики форм
document.getElementById('usdt-form')?.addEventListener('submit', e => {
    e.preventDefault();
    vibrate('medium');
    submitForm('usdt-form', '/api/usdt-exchange');
});

document.getElementById('currency-form')?.addEventListener('submit', e => {
    e.preventDefault();
    vibrate('medium');
    submitForm('currency-form', '/api/currency-exchange');
});

document.getElementById('transfer-form')?.addEventListener('submit', e => {
    e.preventDefault();
    vibrate('medium');
    submitForm('transfer-form', '/api/internal-transfer');
});

document.getElementById('oborotka-form')?.addEventListener('submit', e => {
    e.preventDefault();
    vibrate('medium');
    submitForm('oborotka-form', '/api/oborotka');
});

// Готовность
tg.ready();
initializeSelects();