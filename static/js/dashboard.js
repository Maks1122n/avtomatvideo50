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
            // Simulated API calls - replace with real endpoints
            const stats = {
                totalAccounts: 12,
                totalPosts: 45,
                scheduledPosts: 23,
                totalViews: 125000
            };

            // Update stats cards
            this.updateStatsCards(stats);
            
            // Update badges
            document.getElementById('accounts-count').textContent = stats.totalAccounts;
            document.getElementById('content-count').textContent = '156';
            document.getElementById('proxies-count').textContent = '8';
            
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }

    updateStatsCards(stats) {
        document.getElementById('total-accounts').textContent = stats.totalAccounts;
        document.getElementById('total-posts').textContent = stats.totalPosts;
        document.getElementById('scheduled-posts').textContent = stats.scheduledPosts;
        document.getElementById('total-views').textContent = this.formatNumber(stats.totalViews);
    }

    async checkSystemHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            const statusElement = document.getElementById('system-status');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('span:last-child');
            
            if (health.status === 'healthy') {
                statusDot.className = 'status-dot online';
                statusText.textContent = 'Online';
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
        const activityList = document.getElementById('activity-list');
        
        // Simulated activity data
        const activities = [
            {
                type: 'success',
                icon: 'fa-check',
                message: 'Публикация в @lifestyle_account успешно завершена',
                time: '2 минуты назад'
            },
            {
                type: 'info',
                icon: 'fa-clock',
                message: 'Запланирована публикация на 16:45',
                time: '8 минут назад'
            },
            {
                type: 'warning',
                icon: 'fa-exclamation-triangle',
                message: 'Прокси proxy-us-01 требует проверки',
                time: '15 минут назад'
            },
            {
                type: 'success',
                icon: 'fa-upload',
                message: 'Загружено 5 новых видео в папку motivation',
                time: '23 минуты назад'
            }
        ];

        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i class="fas ${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <p>${activity.message}</p>
                    <small>${activity.time}</small>
                </div>
            </div>
        `).join('');
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
        this.showNotification('Функция добавления аккаунта в разработке', 'info');
    }

    showUploadContentModal() {
        this.showNotification('Функция загрузки контента в разработке', 'info');
    }

    showCreateScheduleModal() {
        this.showNotification('Функция создания расписания в разработке', 'info');
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

    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mediaFluxDashboard = new MediaFluxDashboard();
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

// Add mobile menu button if on mobile
if (window.innerWidth <= 768) {
    const header = document.querySelector('.header-left');
    const menuButton = document.createElement('button');
    menuButton.innerHTML = '<i class="fas fa-bars"></i>';
    menuButton.className = 'mobile-menu-btn';
    menuButton.onclick = toggleMobileMenu;
    header.insertBefore(menuButton, header.firstChild);
} 