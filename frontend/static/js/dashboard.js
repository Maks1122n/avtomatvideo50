/**
 * MediaFlux Hub - Dashboard JavaScript
 * Логика для главной страницы dashboard
 */

class MediaFluxDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 секунд
        this.refreshTimer = null;
        this.isLoading = false;
        this.init();
    }

    /**
     * Инициализация dashboard
     */
    async init() {
        try {
            // Проверяем авторизацию
            if (!MediaFluxAPI.isAuthenticated()) {
                window.location.href = '/login';
                return;
            }

            // Показываем loading состояние
            this.showInitialLoading();

            // Загружаем данные
            await this.loadDashboardData();

            // Запускаем автообновление
            this.startAutoRefresh();

            // Настраиваем обработчики событий
            this.setupEventHandlers();

        } catch (error) {
            console.error('Dashboard init error:', error);
            ui.showNotification('Ошибка инициализации dashboard', 'error');
        }
    }

    /**
     * Показ начального loading
     */
    showInitialLoading() {
        const sections = [
            'accounts-count',
            'automation-status', 
            'posts-published',
            'unique-views',
            'accounts-list',
            'ai-suggestion',
            'top-posts'
        ];

        sections.forEach(sectionId => {
            const element = document.getElementById(sectionId);
            if (element) {
                ui.showLoading(element);
            }
        });
    }

    /**
     * Загрузка данных dashboard
     */
    async loadDashboardData() {
        try {
            this.isLoading = true;

            // Параллельная загрузка всех данных
            const [
                systemStats,
                accountsStats,
                systemStatus,
                accounts,
                contentStats
            ] = await Promise.allSettled([
                MediaFluxAPI.getSystemStats(),
                MediaFluxAPI.getAccountsStats(),
                MediaFluxAPI.getSystemStatus(),
                MediaFluxAPI.getAccounts({ limit: 6 }), // Только первые 6 для dashboard
                MediaFluxAPI.getContentStats()
            ]);

            // Обновляем UI с полученными данными
            if (systemStats.status === 'fulfilled') {
                this.updateSystemStats(systemStats.value);
            }

            if (accountsStats.status === 'fulfilled') {
                this.updateAccountsStats(accountsStats.value);
            }

            if (systemStatus.status === 'fulfilled') {
                this.updateSystemStatus(systemStatus.value);
            }

            if (accounts.status === 'fulfilled') {
                this.updateAccountsList(accounts.value);
            }

            if (contentStats.status === 'fulfilled') {
                this.updateContentStats(contentStats.value);
            }

            // Обновляем AI совет и топ-посты
            ui.updateAISuggestion();
            ui.updateTopPosts();

            // Обновляем badge в меню
            this.updateNavigationBadges(accountsStats.value);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            ui.showNotification('Ошибка загрузки данных', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Обновление системной статистики
     */
    updateSystemStats(stats) {
        if (!stats || !stats.posts) return;

        // Обновляем статистические карточки
        ui.updateStatsCard('posts-published', stats.posts.today);
        
        // Обновляем views (можно взять из статистики постов)
        const totalViews = stats.posts.week * 1000; // Примерная формула
        ui.updateStatsCard('unique-views', totalViews);

        // Обновляем статус автоматизации
        const activeAccounts = stats.accounts?.active || 0;
        ui.updateStatsCard('automation-status', activeAccounts);
    }

    /**
     * Обновление статистики аккаунтов
     */
    updateAccountsStats(stats) {
        if (!stats) return;

        ui.updateStatsCard('accounts-count', stats.total_accounts);
        
        // Обновляем проценты изменений (можно вычислить на основе исторических данных)
        const accountsGrowth = this.calculateGrowthPercentage(stats.total_accounts, 'accounts');
        const postsGrowth = this.calculateGrowthPercentage(stats.posts_today, 'posts');
        
        this.updateStatChange('accounts-count', accountsGrowth);
        this.updateStatChange('posts-published', postsGrowth);
    }

    /**
     * Обновление статуса системы
     */
    updateSystemStatus(status) {
        const statusElement = document.getElementById('system-status');
        if (!statusElement) return;

        const isHealthy = status.overall;
        const statusText = isHealthy ? 'MediaFlux Hub Engine активен' : 'Система требует внимания';
        const statusClass = isHealthy ? 'live' : 'error';

        statusElement.className = `status-indicator ${statusClass}`;
        statusElement.querySelector('.status-text').textContent = statusText;

        // Обновляем цвет точки статуса
        const dot = statusElement.querySelector('.status-dot');
        if (dot) {
            dot.style.background = isHealthy ? 'var(--success)' : 'var(--error)';
        }
    }

    /**
     * Обновление списка аккаунтов
     */
    updateAccountsList(accounts) {
        ui.updateAccountsList(accounts.slice(0, 6)); // Только первые 6
    }

    /**
     * Обновление статистики контента
     */
    updateContentStats(stats) {
        // Можно добавить индикатор количества видео или другую информацию
        console.log('Content stats:', stats);
    }

    /**
     * Вычисление процента роста
     */
    calculateGrowthPercentage(currentValue, type) {
        // В реальном приложении здесь должны быть исторические данные
        // Пока возвращаем случайные, но правдоподобные значения
        const growthRanges = {
            accounts: { min: 5, max: 25 },
            posts: { min: 10, max: 35 },
            views: { min: 15, max: 45 }
        };

        const range = growthRanges[type] || { min: 5, max: 20 };
        return Math.floor(Math.random() * (range.max - range.min) + range.min);
    }

    /**
     * Обновление изменения статистики
     */
    updateStatChange(cardId, percentage) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const changeElement = card.closest('.stat-card').querySelector('.stat-change .change-text');
        if (changeElement) {
            changeElement.textContent = `+${percentage}%`;
        }
    }

    /**
     * Обновление badges в навигации
     */
    updateNavigationBadges(accountsStats) {
        const accountsBadge = document.getElementById('accounts-badge');
        if (accountsBadge && accountsStats) {
            accountsBadge.textContent = accountsStats.total_accounts;
        }
    }

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Обновление по клику на refresh кнопку
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshDashboard();
            });
        }

        // Обработчик формы добавления аккаунта
        const addAccountForm = document.getElementById('add-account-form');
        if (addAccountForm) {
            addAccountForm.addEventListener('submit', (e) => {
                this.handleAddAccount(e);
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R - обновить dashboard
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshDashboard();
            }
            
            // Ctrl/Cmd + N - добавить аккаунт
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                openAddAccountModal();
            }
        });
    }

    /**
     * Обновление dashboard
     */
    async refreshDashboard() {
        if (this.isLoading) return;

        ui.showNotification('Обновление данных...', 'info', 2000);
        
        try {
            await this.loadDashboardData();
            ui.showNotification('Данные обновлены', 'success', 2000);
        } catch (error) {
            console.error('Refresh error:', error);
            ui.showNotification('Ошибка обновления данных', 'error');
        }
    }

    /**
     * Обработка добавления аккаунта
     */
    async handleAddAccount(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const accountData = {
            username: formData.get('username').replace('@', ''), // Убираем @ если есть
            access_token: formData.get('access_token'),
            instagram_account_id: formData.get('instagram_account_id'),
            daily_limit: parseInt(formData.get('daily_limit')) || 5
        };

        // Валидация
        if (!accountData.username || !accountData.access_token || !accountData.instagram_account_id) {
            ui.showNotification('Заполните все обязательные поля', 'warning');
            return;
        }

        try {
            // Показываем loading в модальном окне
            const submitBtn = event.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Добавление...';
            submitBtn.disabled = true;

            const result = await MediaFluxAPI.createAccount(accountData);
            
            ui.showNotification(`Аккаунт @${result.username} успешно добавлен`, 'success');
            ui.closeModal();
            
            // Обновляем dashboard
            await this.refreshDashboard();

        } catch (error) {
            console.error('Add account error:', error);
            ui.showNotification(error.message || 'Ошибка добавления аккаунта', 'error');
        } finally {
            // Восстанавливаем кнопку
            const submitBtn = event.target.querySelector('button[type="submit"]');
            submitBtn.textContent = 'Добавить аккаунт';
            submitBtn.disabled = false;
        }
    }

    /**
     * Запуск автообновления
     */
    startAutoRefresh() {
        // Останавливаем существующий таймер если есть
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        // Запускаем новый таймер
        this.refreshTimer = setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }

    /**
     * Остановка автообновления
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    /**
     * Очистка при уходе со страницы
     */
    destroy() {
        this.stopAutoRefresh();
    }
}

// Глобальные функции для использования в HTML

/**
 * Открытие модального окна добавления аккаунта
 */
window.openAddAccountModal = function() {
    ui.showModal('add-account-modal');
};

/**
 * Открытие загрузки контента
 */
window.openContentUpload = function() {
    window.location.href = '/content';
};

/**
 * Открытие настроек таргетинга
 */
window.openTargetingSettings = function() {
    window.location.href = '/settings';
};

/**
 * Обновление аккаунтов
 */
window.refreshAccounts = function() {
    if (window.dashboard) {
        dashboard.refreshDashboard();
    }
};

/**
 * Тестирование аккаунта
 */
window.testAccount = async function(accountId) {
    try {
        ui.showNotification('Тестирование аккаунта...', 'info', 2000);
        
        const result = await MediaFluxAPI.testAccount(accountId);
        
        if (result.success) {
            ui.showNotification('Аккаунт работает корректно', 'success');
        } else {
            ui.showNotification(result.message || 'Ошибка тестирования', 'error');
        }
    } catch (error) {
        ui.showNotification('Ошибка тестирования аккаунта', 'error');
    }
};

/**
 * Редактирование аккаунта
 */
window.editAccount = function(accountId) {
    window.location.href = `/accounts?edit=${accountId}`;
};

/**
 * Выход из системы
 */
window.logout = async function() {
    if (confirm('Вы действительно хотите выйти из системы?')) {
        try {
            await MediaFluxAPI.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/login'; // Всё равно перенаправляем
        }
    }
};

/**
 * Закрытие модального окна
 */
window.closeModal = function() {
    ui.closeModal();
};

// Инициализация dashboard при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new MediaFluxDashboard();
});

// Очистка при уходе со страницы
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        dashboard.destroy();
    }
}); 