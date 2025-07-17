/**
 * MediaFlux Hub - UI Manager
 * Управление пользовательским интерфейсом
 */

class MediaFluxHubUI {
    constructor() {
        this.modals = new Map();
        this.notifications = [];
        this.animationDuration = 300;
        this.init();
    }

    /**
     * Инициализация UI
     */
    init() {
        this.setupModals();
        this.setupMobileMenu();
        this.setupNotifications();
        this.bindEvents();
    }

    /**
     * Настройка модальных окон
     */
    setupModals() {
        const modalOverlay = document.getElementById('modal-overlay');
        if (!modalOverlay) return;

        // Закрытие модального окна по клику на оверлей
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                this.closeModal();
            }
        });

        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modalOverlay.classList.contains('show')) {
                this.closeModal();
            }
        });
    }

    /**
     * Настройка мобильного меню
     */
    setupMobileMenu() {
        // Кнопка мобильного меню создается в CSS
        document.addEventListener('click', (e) => {
            const sidebar = document.querySelector('.sidebar');
            
            // Если клик по кнопке меню (созданной через CSS)
            if (e.target.closest('.page-header::before')) {
                sidebar?.classList.toggle('open');
            }
            
            // Закрытие меню при клике вне его
            if (!e.target.closest('.sidebar') && sidebar?.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    /**
     * Настройка системы уведомлений
     */
    setupNotifications() {
        const container = document.getElementById('notifications-container');
        if (!container) {
            // Создаем контейнер если его нет
            const notificationContainer = document.createElement('div');
            notificationContainer.id = 'notifications-container';
            notificationContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(notificationContainer);
        }
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Плавная прокрутка для навигации
        document.querySelectorAll('.nav-link[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Lazy loading для изображений
        this.setupLazyLoading();
    }

    /**
     * Показ уведомления
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notifications-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const id = Date.now().toString();
        notification.setAttribute('data-id', id);

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    ${this.getNotificationIcon(type)}
                </div>
                <div class="notification-message">${message}</div>
                <button class="notification-close" onclick="ui.closeNotification('${id}')">
                    ×
                </button>
            </div>
        `;

        container.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                this.closeNotification(id);
            }, duration);
        }

        this.notifications.push({ id, element: notification, type });
        return id;
    }

    /**
     * Закрытие уведомления
     */
    closeNotification(id) {
        const notification = document.querySelector(`[data-id="${id}"]`);
        if (!notification) return;

        notification.classList.remove('show');
        
        setTimeout(() => {
            notification.remove();
            this.notifications = this.notifications.filter(n => n.id !== id);
        }, this.animationDuration);
    }

    /**
     * Получение иконки для уведомления
     */
    getNotificationIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Показ модального окна
     */
    showModal(modalId) {
        const modalOverlay = document.getElementById('modal-overlay');
        const modal = document.getElementById(modalId);
        
        if (!modalOverlay || !modal) return;

        modalOverlay.classList.add('show');
        modal.style.display = 'block';
        
        // Фокус на первый input
        const firstInput = modal.querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }

        // Блокируем скролл страницы
        document.body.style.overflow = 'hidden';
    }

    /**
     * Закрытие модального окна
     */
    closeModal() {
        const modalOverlay = document.getElementById('modal-overlay');
        if (!modalOverlay) return;

        modalOverlay.classList.remove('show');
        
        // Скрываем все модальные окна
        modalOverlay.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });

        // Восстанавливаем скролл
        document.body.style.overflow = '';

        setTimeout(() => {
            // Очищаем формы
            modalOverlay.querySelectorAll('form').forEach(form => {
                form.reset();
            });
        }, this.animationDuration);
    }

    /**
     * Показ состояния загрузки
     */
    showLoading(element, text = 'Загрузка...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;

        const loadingHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <div class="loading-text">${text}</div>
            </div>
        `;

        element.innerHTML = loadingHTML;
        element.classList.add('loading');
    }

    /**
     * Скрытие состояния загрузки
     */
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;

        element.classList.remove('loading');
    }

    /**
     * Обновление статистических карточек
     */
    updateStatsCard(cardId, value, change = null) {
        const card = document.getElementById(cardId);
        if (!card) return;

        // Анимация изменения числа
        this.animateNumber(card, value);

        // Обновление изменения если передано
        if (change !== null) {
            const changeElement = card.closest('.stat-card').querySelector('.stat-change .change-text');
            if (changeElement) {
                changeElement.textContent = change > 0 ? `+${change}%` : `${change}%`;
                changeElement.parentElement.className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
            }
        }
    }

    /**
     * Анимация числа
     */
    animateNumber(element, targetValue, duration = 1000) {
        const startValue = parseInt(element.textContent) || 0;
        const difference = targetValue - startValue;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOut = 1 - Math.pow(1 - progress, 3);
            
            const currentValue = Math.round(startValue + (difference * easeOut));
            element.textContent = MediaFluxAPI.formatNumber(currentValue);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Создание карточки аккаунта
     */
    createAccountCard(account) {
        return `
            <div class="account-card" data-account-id="${account.id}">
                <div class="account-avatar" style="background: ${this.getAccountAvatarGradient(account.username)}">
                    ${account.username.charAt(0).toUpperCase()}
                </div>
                <div class="account-info">
                    <div class="account-name">@${account.username}</div>
                    <div class="account-status">
                        <span class="status-dot" style="background: ${MediaFluxAPI.getStatusColor(account.status)}"></span>
                        <span class="status-text">${MediaFluxAPI.getAccountStatusText(account.status)}</span>
                        <span class="account-platform">Instagram</span>
                    </div>
                    <div class="account-stats">
                        <span class="posts-today">${account.current_daily_posts}/${account.daily_limit} постов</span>
                        ${account.last_activity ? `<span class="last-activity">${MediaFluxAPI.formatDate(account.last_activity)}</span>` : ''}
                    </div>
                </div>
                <div class="account-actions">
                    <button class="action-btn-small" onclick="testAccount('${account.id}')" title="Тестировать">
                        🧪
                    </button>
                    <button class="action-btn-small" onclick="editAccount('${account.id}')" title="Редактировать">
                        ✏️
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Получение градиента для аватара
     */
    getAccountAvatarGradient(username) {
        const gradients = [
            'var(--gradient-blue)',
            'var(--gradient-green)',
            'var(--gradient-purple)',
            'var(--gradient-red)',
            'var(--gradient-orange)'
        ];
        
        // Выбираем градиент на основе хеша имени пользователя
        const hash = username.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        return gradients[Math.abs(hash) % gradients.length];
    }

    /**
     * Обновление списка аккаунтов
     */
    updateAccountsList(accounts) {
        const container = document.getElementById('accounts-list');
        if (!container) return;

        if (accounts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">👥</div>
                    <div class="empty-text">Аккаунты не найдены</div>
                    <div class="empty-subtitle">Добавьте первый аккаунт для начала работы</div>
                    <button class="btn btn-primary" onclick="openAddAccountModal()">
                        Добавить аккаунт
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = accounts.map(account => this.createAccountCard(account)).join('');
        
        // Анимация появления
        container.querySelectorAll('.account-card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

    /**
     * Обновление AI совета
     */
    updateAISuggestion(suggestion) {
        const container = document.getElementById('ai-suggestion');
        if (!container) return;

        const suggestions = [
            "Лучшее время для публикации: 18:00-21:00. Engagement на 34% выше 📈",
            "Рекомендуется добавить больше контента в категорию 'motivation' 💪",
            "Проверьте аккаунт @example - превышен дневной лимит ошибок ⚠️",
            "Отличная работа! Прирост подписчиков +12% за неделю 🎉",
            "Рекомендуем обновить прокси для 3 аккаунтов 🔄"
        ];

        const randomSuggestion = suggestion || suggestions[Math.floor(Math.random() * suggestions.length)];
        
        container.innerHTML = `
            <div class="ai-suggestion-content">
                <div class="suggestion-text">${randomSuggestion}</div>
                <div class="suggestion-time">${new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
        `;
    }

    /**
     * Обновление топ-постов
     */
    updateTopPosts(posts) {
        const container = document.getElementById('top-posts');
        if (!container) return;

        if (!posts || posts.length === 0) {
            posts = [
                { username: '@example1', engagement: '+23%', type: 'Motivation' },
                { username: '@example2', engagement: '+18%', type: 'Lifestyle' },
                { username: '@example3', engagement: '+15%', type: 'Business' }
            ];
        }

        container.innerHTML = posts.map(post => `
            <div class="top-post-item">
                <div class="post-account">
                    <div class="post-avatar">${post.username.charAt(1).toUpperCase()}</div>
                    <div class="post-info">
                        <div class="post-username">${post.username}</div>
                        <div class="post-category">${post.type}</div>
                    </div>
                </div>
                <div class="post-engagement ${post.engagement.startsWith('+') ? 'positive' : 'negative'}">
                    ${post.engagement}
                </div>
            </div>
        `).join('');
    }

    /**
     * Настройка Lazy Loading
     */
    setupLazyLoading() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback для старых браузеров
            lazyImages.forEach(img => {
                img.src = img.dataset.src;
                img.classList.remove('lazy');
            });
        }
    }

    /**
     * Плавная прокрутка к элементу
     */
    scrollToElement(selector, offset = 0) {
        const element = document.querySelector(selector);
        if (!element) return;

        const elementPosition = element.offsetTop;
        const offsetPosition = elementPosition - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }

    /**
     * Копирование текста в буфер обмена
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Скопировано в буфер обмена', 'success', 2000);
        } catch (err) {
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showNotification('Скопировано в буфер обмена', 'success', 2000);
        }
    }

    /**
     * Debounce функция
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle функция
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Создаем глобальный экземпляр UI
window.ui = new MediaFluxHubUI(); 