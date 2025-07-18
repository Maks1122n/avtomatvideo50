// MediaFlux Hub Dashboard JavaScript
class MediaFluxDashboard {
    constructor() {
        this.currentPage = 'dashboard';
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.loadInitialData();
        this.startAutoRefresh();
        
        // Show welcome notification
        this.showNotification('Добро пожаловать в MediaFlux Hub!', 'success');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Action buttons
        document.getElementById('start-automation')?.addEventListener('click', () => {
            this.startAutomation();
        });

        document.getElementById('add-account')?.addEventListener('click', () => {
            this.showAddAccountModal();
        });

        document.getElementById('upload-content')?.addEventListener('click', () => {
            this.showUploadContentModal();
        });

        document.getElementById('create-schedule')?.addEventListener('click', () => {
            this.showCreateScheduleModal();
        });

        document.getElementById('refresh-activity')?.addEventListener('click', () => {
            this.refreshActivity();
        });

        // Chart filter
        document.querySelector('.chart-filter')?.addEventListener('change', (e) => {
            this.updateChart(e.target.value);
        });
    }

    setupNavigation() {
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            const page = e.state?.page || 'dashboard';
            this.navigateToPage(page, false);
        });
    }

    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load dashboard statistics
            await this.loadDashboardStats();
            
            // Load system status
            await this.checkSystemHealth();
            
            // Load recent activity
            await this.loadRecentActivity();
            
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
            this.showNotification('Ошибка загрузки данных', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadDashboardStats() {
        try {
            // Загрузка реальных данных из API
            const response = await fetch('/api/dashboard/stats');
            const stats = await response.json();

            // Update stats cards
            this.updateStatsCards(stats);
            
            // Update badges
            document.getElementById('accounts-count').textContent = stats.active_accounts;
            document.getElementById('content-count').textContent = '156';
            document.getElementById('proxies-count').textContent = stats.proxies_active;
            
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            this.showNotification('Ошибка загрузки статистики', 'error');
        }
    }

    updateStatsCards(stats) {
        document.getElementById('total-accounts').textContent = stats.active_accounts;
        document.getElementById('total-posts').textContent = stats.posts_today;
        document.getElementById('scheduled-posts').textContent = stats.posts_scheduled;
        document.getElementById('total-views').textContent = this.formatNumber(stats.total_views);
    }

    async checkSystemHealth() {
        try {
            // Проверяем как базовое здоровье, так и детальный статус
            const healthResponse = await fetch('/health');
            const health = await healthResponse.json();
            
            // Пытаемся получить детальный статус системы
            let systemStatus = null;
            try {
                const statusResponse = await fetch('/api/dashboard/system-status');
                systemStatus = await statusResponse.json();
            } catch (e) {
                console.log('Детальный статус недоступен');
            }
            
            const statusElement = document.getElementById('system-status');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('span:last-child');
            
            if (health.status === 'healthy') {
                statusDot.className = 'status-dot online';
                statusText.textContent = systemStatus ? 
                    `Online (${systemStatus.uptime})` : 'Online';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Offline';
            }
            
        } catch (error) {
            console.error('Ошибка проверки статуса:', error);
            const statusElement = document.getElementById('system-status');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('span:last-child');
            
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Offline';
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/api/dashboard/recent-activity');
            const activities = await response.json();
            const activityList = document.getElementById('activity-list');

            // Map activity types to icons and colors
            const typeConfig = {
                post: { icon: 'fa-check', type: 'success' },
                upload: { icon: 'fa-upload', type: 'info' },
                schedule: { icon: 'fa-calendar', type: 'info' },
                proxy: { icon: 'fa-exchange-alt', type: 'warning' },
                account: { icon: 'fa-user-plus', type: 'success' },
                error: { icon: 'fa-exclamation-triangle', type: 'error' }
            };

            activityList.innerHTML = activities.map(activity => {
                const config = typeConfig[activity.type] || typeConfig.info;
                return `
                    <div class="activity-item">
                        <div class="activity-icon ${config.type}">
                            <i class="fas ${config.icon}"></i>
                        </div>
                        <div class="activity-content">
                            <p>${activity.action}${activity.account ? ` в ${activity.account}` : ''}</p>
                            <small>${activity.time}</small>
                            ${activity.details ? `<small class="text-muted d-block">${activity.details}</small>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
        } catch (error) {
            console.error('Ошибка загрузки активности:', error);
            this.showNotification('Ошибка загрузки активности', 'error');
        }
    }

    navigateToPage(page, updateHistory = true) {
        // Hide all content sections
        document.querySelectorAll('.content').forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected content
        const targetContent = document.getElementById(`${page}-content`);
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeItem = document.querySelector(`[data-page="${page}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }

        // Update page title and breadcrumb
        const titles = {
            dashboard: 'Dashboard',
            accounts: 'Управление аккаунтами',
            content: 'Управление контентом',
            scheduler: 'Планировщик публикаций',
            analytics: 'Аналитика и отчеты',
            proxies: 'Управление прокси',
            settings: 'Настройки системы'
        };

        document.getElementById('page-title').textContent = titles[page] || 'Dashboard';
        document.querySelector('.breadcrumb').textContent = `Главная / ${titles[page] || 'Dashboard'}`;

        // Update browser history
        if (updateHistory) {
            history.pushState({ page }, '', `#${page}`);
        }

        this.currentPage = page;
    }

    async startAutomation() {
        const button = document.getElementById('start-automation');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Запуск...';
        button.disabled = true;

        try {
            // Simulated API call
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.showNotification('Автоматизация успешно запущена!', 'success');
            
            button.innerHTML = '<i class="fas fa-stop"></i> Остановить автоматизацию';
            
        } catch (error) {
            console.error('Ошибка запуска автоматизации:', error);
            this.showNotification('Ошибка запуска автоматизации', 'error');
            button.innerHTML = originalText;
        } finally {
            button.disabled = false;
        }
    }

    showAddAccountModal() {
        // Переключаемся на страницу аккаунтов
        this.navigateToPage('accounts');
        this.showNotification('Перейдите на страницу аккаунтов для добавления', 'info');
    }

    showUploadContentModal() {
        // Переключаемся на страницу контента
        this.navigateToPage('content');
        this.showNotification('Перейдите на страницу контента для загрузки', 'info');
    }

    showCreateScheduleModal() {
        // Переключаемся на планировщик
        this.navigateToPage('scheduler');
        this.showNotification('Перейдите в планировщик для создания расписания', 'info');
    }

    async loadAccountsData() {
        try {
            const response = await fetch('/api/accounts');
            const data = await response.json();
            
            // Обновляем счетчики
            document.getElementById('accounts-count').textContent = data.active;
            
            return data.accounts;
        } catch (error) {
            console.error('Ошибка загрузки аккаунтов:', error);
            return [];
        }
    }

    async testAccountConnection(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/test-connection`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (result.connection_status === 'success') {
                this.showNotification('Соединение с аккаунтом успешно', 'success');
            } else {
                this.showNotification('Ошибка соединения с аккаунтом', 'error');
            }
            
            return result;
        } catch (error) {
            this.showNotification('Ошибка проверки соединения', 'error');
            return null;
        }
    }

    async refreshActivity() {
        const button = document.getElementById('refresh-activity');
        const icon = button.querySelector('i');
        
        icon.style.animation = 'none';
        setTimeout(() => {
            icon.style.animation = '';
        }, 10);
        
        icon.classList.add('fa-spin');
        
        try {
            await this.loadRecentActivity();
            this.showNotification('Активность обновлена', 'success');
        } catch (error) {
            this.showNotification('Ошибка обновления активности', 'error');
        } finally {
            setTimeout(() => {
                icon.classList.remove('fa-spin');
            }, 1000);
        }
    }

    updateChart(period) {
        // Placeholder for chart update logic
        console.log(`Обновление графика для периода: ${period}`);
        this.showNotification(`График обновлен для периода: ${period}`, 'info');
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.updateInterval = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardStats();
                this.checkSystemHealth();
            }
        }, 30000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.2rem;">×</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Добавление аккаунта
    async addAccount(formData) {
        try {
            const response = await fetch('/api/accounts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Аккаунт успешно добавлен!', 'success');
                this.loadAccounts();
            } else {
                this.showNotification('Ошибка добавления аккаунта', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка добавления аккаунта', 'error');
        }
    }
    
    // Тестирование соединения
    async testConnection(accountData) {
        this.showNotification('Проверка соединения...', 'info');
        try {
            const response = await fetch('/api/accounts/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(accountData)
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Соединение успешно!', 'success');
            } else {
                this.showNotification('Ошибка соединения с Instagram', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка соединения с Instagram', 'error');
        }
    }
    
    // Загрузка видео
    async uploadVideos(files, category) {
        const formData = new FormData();
        for (let file of files) {
            formData.append('videos', file);
        }
        formData.append('category', category);
        
        try {
            const response = await fetch('/api/content/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(`Загружено ${files.length} видео!`, 'success');
                this.loadFolders();
            } else {
                this.showNotification('Ошибка загрузки видео', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка загрузки видео', 'error');
        }
    }
    
    // Создание расписания
    async createSchedule(scheduleData) {
        try {
            const response = await fetch('/api/schedule/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(scheduleData)
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Расписание создано!', 'success');
                this.loadCalendar();
            } else {
                this.showNotification('Ошибка создания расписания', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка создания расписания', 'error');
        }
    }

    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add mobile menu button if on mobile
    if (window.innerWidth <= 768) {
        const header = document.querySelector('.header-left');
        const menuButton = document.createElement('button');
        menuButton.innerHTML = '<i class="fas fa-bars"></i>';
        menuButton.className = 'mobile-menu-btn';
        menuButton.onclick = toggleMobileMenu;
        header.insertBefore(menuButton, header.firstChild);
    }

    // Initialize MediaFlux Dashboard
    console.log('📱 Initializing MediaFlux Dashboard...');
    try {
        window.mediaFluxDashboard = new MediaFluxDashboard();
        console.log('✅ MediaFlux Dashboard initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize MediaFlux Dashboard:', error);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.mediaFluxDashboard) {
        window.mediaFluxDashboard.destroy();
    }
});

// Handle mobile menu toggle (if needed)
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
} 