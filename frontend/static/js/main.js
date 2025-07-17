/**
 * MediaFlux Hub - Main JavaScript
 * Главный JavaScript файл приложения
 */

class MediaFluxHub {
    constructor() {
        this.version = '1.0.0';
        this.isOnline = navigator.onLine;
        this.lastActivity = Date.now();
        this.init();
    }

    /**
     * Инициализация приложения
     */
    init() {
        console.log(`🚀 MediaFlux Hub v${this.version} - Instagram Reels Automation Platform`);
        
        this.setupGlobalErrorHandler();
        this.setupNetworkMonitoring();
        this.setupActivityTracking();
        this.setupServiceWorker();
        this.setupKeyboardShortcuts();
        this.checkAuthentication();
    }

    /**
     * Глобальный обработчик ошибок
     */
    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            
            // Не показываем уведомления для мелких ошибок
            if (event.error && !event.error.message.includes('Script error')) {
                ui.showNotification('Произошла ошибка. Попробуйте обновить страницу.', 'error');
            }
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            
            // Показываем уведомление только для критических ошибок
            if (event.reason && event.reason.message && !event.reason.message.includes('NetworkError')) {
                ui.showNotification('Ошибка сети. Проверьте подключение к интернету.', 'warning');
            }
        });
    }

    /**
     * Мониторинг сетевого подключения
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            ui.showNotification('Подключение восстановлено', 'success', 3000);
            
            // Обновляем данные после восстановления сети
            if (window.dashboard) {
                dashboard.refreshDashboard();
            }
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            ui.showNotification('Нет подключения к интернету', 'warning', 5000);
        });
    }

    /**
     * Отслеживание активности пользователя
     */
    setupActivityTracking() {
        const updateActivity = () => {
            this.lastActivity = Date.now();
        };

        // События активности
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'].forEach(event => {
            document.addEventListener(event, updateActivity, { passive: true });
        });

        // Проверяем неактивность каждые 5 минут
        setInterval(() => {
            const inactiveTime = Date.now() - this.lastActivity;
            const maxInactiveTime = 30 * 60 * 1000; // 30 минут

            if (inactiveTime > maxInactiveTime) {
                this.handleInactivity();
            }
        }, 5 * 60 * 1000);
    }

    /**
     * Обработка длительной неактивности
     */
    handleInactivity() {
        if (MediaFluxAPI.isAuthenticated()) {
            ui.showNotification('Долгое время неактивности. Рекомендуется перезайти в систему.', 'warning', 10000);
        }
    }

    /**
     * Настройка Service Worker для кэширования
     */
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', async () => {
                try {
                    const registration = await navigator.serviceWorker.register('/sw.js');
                    console.log('ServiceWorker registered:', registration);
                } catch (error) {
                    console.log('ServiceWorker registration failed:', error);
                }
            });
        }
    }

    /**
     * Глобальные горячие клавиши
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Игнорируем если фокус на input элементах
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            const isCtrlCmd = e.ctrlKey || e.metaKey;

            // Ctrl/Cmd + K - поиск
            if (isCtrlCmd && e.key === 'k') {
                e.preventDefault();
                this.openSearch();
            }

            // Escape - закрыть модальные окна
            if (e.key === 'Escape') {
                ui.closeModal();
            }

            // ? - показать помощь по горячим клавишам
            if (e.key === '?' && !isCtrlCmd) {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }
        });
    }

    /**
     * Открытие поиска
     */
    openSearch() {
        ui.showNotification('Поиск пока не реализован', 'info', 2000);
    }

    /**
     * Показ справки по горячим клавишам
     */
    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Ctrl/Cmd + R', action: 'Обновить dashboard' },
            { key: 'Ctrl/Cmd + N', action: 'Добавить аккаунт' },
            { key: 'Ctrl/Cmd + K', action: 'Поиск' },
            { key: 'Escape', action: 'Закрыть модальное окно' },
            { key: '?', action: 'Показать эту справку' }
        ];

        const shortcutsHTML = shortcuts.map(shortcut => 
            `<div class="shortcut-item">
                <kbd>${shortcut.key}</kbd>
                <span>${shortcut.action}</span>
            </div>`
        ).join('');

        // Создаем временное модальное окно
        const modal = document.createElement('div');
        modal.className = 'modal-overlay show';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>Горячие клавиши</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="shortcuts-list">
                        ${shortcutsHTML}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Автоматическое закрытие через 10 секунд
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 10000);
    }

    /**
     * Проверка авторизации
     */
    async checkAuthentication() {
        if (!MediaFluxAPI.isAuthenticated()) {
            return;
        }

        try {
            await MediaFluxAPI.verifyToken();
        } catch (error) {
            console.warn('Token verification failed:', error);
            MediaFluxAPI.handleAuthError();
        }
    }

    /**
     * Форматирование размера файла
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Проверка поддержки браузера
     */
    checkBrowserSupport() {
        const requiredFeatures = {
            'Fetch API': 'fetch' in window,
            'LocalStorage': 'localStorage' in window,
            'CSS Grid': CSS.supports('display', 'grid'),
            'ES6 Classes': true // Если этот код выполняется, то поддержка есть
        };

        const unsupportedFeatures = Object.entries(requiredFeatures)
            .filter(([feature, supported]) => !supported)
            .map(([feature]) => feature);

        if (unsupportedFeatures.length > 0) {
            ui.showNotification(
                `Ваш браузер не поддерживает: ${unsupportedFeatures.join(', ')}. Обновите браузер для корректной работы.`,
                'warning',
                10000
            );
        }
    }

    /**
     * Получение информации об устройстве
     */
    getDeviceInfo() {
        const ua = navigator.userAgent;
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
        const isTablet = /iPad|Android/i.test(ua) && !/Mobile/i.test(ua);
        const isDesktop = !isMobile && !isTablet;

        return {
            isMobile,
            isTablet,
            isDesktop,
            touchSupport: 'ontouchstart' in window,
            platform: navigator.platform,
            userAgent: ua
        };
    }

    /**
     * Оптимизация производительности
     */
    optimizePerformance() {
        // Предзагрузка критических ресурсов
        const criticalResources = [
            '/static/css/main.css',
            '/static/css/dashboard.css'
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = resource;
            document.head.appendChild(link);
        });

        // Ленивая загрузка некритических скриптов
        this.lazyLoadScripts();
    }

    /**
     * Ленивая загрузка скриптов
     */
    lazyLoadScripts() {
        const lazyScripts = [
            // Здесь можно добавить некритические скрипты
        ];

        // Загружаем скрипты после загрузки страницы
        window.addEventListener('load', () => {
            lazyScripts.forEach(script => {
                const scriptElement = document.createElement('script');
                scriptElement.src = script;
                scriptElement.async = true;
                document.head.appendChild(scriptElement);
            });
        });
    }

    /**
     * Дебаг информация
     */
    getDebugInfo() {
        return {
            version: this.version,
            isOnline: this.isOnline,
            lastActivity: new Date(this.lastActivity).toLocaleString(),
            authenticated: MediaFluxAPI.isAuthenticated(),
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            device: this.getDeviceInfo()
        };
    }
}

// Утилитарные функции

/**
 * Глобальная функция для логирования
 */
window.log = function(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] MediaFlux Hub:`;
    
    switch (level) {
        case 'error':
            console.error(prefix, message);
            break;
        case 'warn':
            console.warn(prefix, message);
            break;
        case 'debug':
            console.debug(prefix, message);
            break;
        default:
            console.log(prefix, message);
    }
};

/**
 * Глобальная функция для получения дебаг информации
 */
window.getDebugInfo = function() {
    if (window.mediaFluxHub) {
        return mediaFluxHub.getDebugInfo();
    }
    return null;
};

/**
 * Экспорт дебаг информации
 */
window.exportDebugInfo = function() {
    const debugInfo = getDebugInfo();
    if (debugInfo) {
        const dataStr = JSON.stringify(debugInfo, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `mediaflux-debug-${Date.now()}.json`;
        link.click();
        
        ui.showNotification('Дебаг информация экспортирована', 'success');
    }
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    window.mediaFluxHub = new MediaFluxHub();
    
    // Проверяем поддержку браузера
    mediaFluxHub.checkBrowserSupport();
    
    // Оптимизируем производительность
    mediaFluxHub.optimizePerformance();
    
    // Добавляем дебаг команды в консоль
    if (process?.env?.NODE_ENV === 'development') {
        console.log('%c🚀 MediaFlux Hub Debug Commands:', 'color: #667eea; font-weight: bold;');
        console.log('%cgetDebugInfo() - Получить дебаг информацию', 'color: #10b981;');
        console.log('%cexportDebugInfo() - Экспортировать дебаг информацию', 'color: #10b981;');
        console.log('%cMediaFluxAPI - Объект для работы с API', 'color: #10b981;');
        console.log('%cui - Объект для управления UI', 'color: #10b981;');
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MediaFluxHub;
} 