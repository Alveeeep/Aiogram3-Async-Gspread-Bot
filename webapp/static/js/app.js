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

// Получаем информацию о пользователе
console.log('Telegram User:', tg.initDataUnsafe.user);
console.log('Init Data:', tg.initData);

// Переключение табов
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');

        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        button.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Вибрация при переключении
        tg.HapticFeedback.impactOccurred('light');
    });
});

// Показ/скрытие поля "Фиат счёт" в форме USDT
document.getElementById('usdt-transaction-type').addEventListener('change', (e) => {
    const fiatAccountGroup = document.getElementById('fiat-account-group');
    if (e.target.value === 'Покупка USDT') {
        fiatAccountGroup.style.display = 'block';
        document.getElementById('fiat-account').required = true;
    } else {
        fiatAccountGroup.style.display = 'none';
        document.getElementById('fiat-account').required = false;
    }
});

// Функция показа уведомлений
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Функция отправки формы
async function submitForm(formId, endpoint) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const submitButton = form.querySelector('.btn-submit');

    // Блокируем кнопку
    submitButton.disabled = true;
    submitButton.textContent = 'Отправка...';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                // Отправляем данные от Telegram для проверки
                'Authorization': tg.initData || '',
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification(data.message, 'success');
            form.reset();

            // Вибрация успеха
            tg.HapticFeedback.notificationOccurred('success');

            // Показываем главную кнопку Telegram
            tg.MainButton.setText('Закрыть');
            tg.MainButton.show();
            tg.MainButton.onClick(() => tg.close());

            // Автоматически закрываем через 2 секунды
            setTimeout(() => {
                tg.close();
            }, 2000);
        } else {
            showNotification(data.message, 'error');
            tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (error) {
        showNotification('Ошибка соединения с сервером', 'error');
        tg.HapticFeedback.notificationOccurred('error');
        console.error('Error:', error);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Отправить';
    }
}

// Обработчики форм
document.getElementById('usdt-form').addEventListener('submit', (e) => {
    e.preventDefault();
    tg.HapticFeedback.impactOccurred('medium');
    submitForm('usdt-form', '/api/usdt-exchange');
});

document.getElementById('currency-form').addEventListener('submit', (e) => {
    e.preventDefault();
    tg.HapticFeedback.impactOccurred('medium');
    submitForm('currency-form', '/api/currency-exchange');
});

document.getElementById('transfer-form').addEventListener('submit', (e) => {
    e.preventDefault();
    tg.HapticFeedback.impactOccurred('medium');
    submitForm('transfer-form', '/api/internal-transfer');
});

document.getElementById('oborotka-form').addEventListener('submit', (e) => {
    e.preventDefault();
    tg.HapticFeedback.impactOccurred('medium');
    submitForm('oborotka-form', '/api/oborotka');
});

// Сообщаем Telegram, что приложение готово
tg.ready();

// Debug информация
console.log('WebApp version:', tg.version);
console.log('Platform:', tg.platform);
console.log('Color scheme:', tg.colorScheme);