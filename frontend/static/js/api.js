/**
 * MediaFlux Hub - API Client
 * Клиент для работы с MediaFlux Hub API
 */

class MediaFluxHubAPI {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('mediaflux_token');
        this.refreshPromise = null;
    }

    /**
     * Выполнение HTTP запроса
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Добавляем токен авторизации
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            // Обработка ошибок авторизации
            if (response.status === 401) {
                this.handleAuthError();
                throw new Error('Необходима авторизация');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('MediaFlux Hub API Error:', error);
            throw error;
        }
    }

    /**
     * GET запрос
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams(params);
        const url = searchParams.toString() ? `${endpoint}?${searchParams}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST запрос
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT запрос
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE запрос
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Авторизация
     */
    async login(username, password) {
        try {
            const response = await this.post('/auth/login', {
                username,
                password
            });

            this.token = response.access_token;
            localStorage.setItem('mediaflux_token', this.token);
            
            return response;
        } catch (error) {
            throw new Error('Неверные учетные данные');
        }
    }

    /**
     * Выход из системы
     */
    async logout() {
        try {
            if (this.token) {
                await this.post('/auth/logout');
            }
        } catch (error) {
            console.warn('Logout error:', error);
        } finally {
            this.token = null;
            localStorage.removeItem('mediaflux_token');
        }
    }

    /**
     * Получение информации о текущем пользователе
     */
    async getCurrentUser() {
        return this.get('/auth/me');
    }

    /**
     * Проверка токена
     */
    async verifyToken() {
        return this.get('/auth/verify');
    }

    /**
     * Обработка ошибок авторизации
     */
    handleAuthError() {
        this.token = null;
        localStorage.removeItem('mediaflux_token');
        
        // Перенаправляем на страницу входа если не на ней
        if (!window.location.pathname.includes('login')) {
            window.location.href = '/login';
        }
    }

    // === АККАУНТЫ ===

    /**
     * Получение списка аккаунтов
     */
    async getAccounts(filters = {}) {
        return this.get('/accounts', filters);
    }

    /**
     * Создание аккаунта
     */
    async createAccount(accountData) {
        return this.post('/accounts', accountData);
    }

    /**
     * Получение аккаунта по ID
     */
    async getAccount(accountId) {
        return this.get(`/accounts/${accountId}`);
    }

    /**
     * Обновление аккаунта
     */
    async updateAccount(accountId, data) {
        return this.put(`/accounts/${accountId}`, data);
    }

    /**
     * Удаление аккаунта
     */
    async deleteAccount(accountId) {
        return this.delete(`/accounts/${accountId}`);
    }

    /**
     * Тестирование аккаунта
     */
    async testAccount(accountId) {
        return this.post(`/accounts/${accountId}/test`);
    }

    /**
     * Статистика аккаунтов
     */
    async getAccountsStats() {
        return this.get('/accounts/stats/summary');
    }

    /**
     * Сброс дневного лимита
     */
    async resetAccountDailyLimit(accountId) {
        return this.post(`/accounts/${accountId}/reset-daily-limit`);
    }

    // === КОНТЕНТ ===

    /**
     * Получение папок контента
     */
    async getContentFolders() {
        return this.get('/content/folders');
    }

    /**
     * Сканирование контента
     */
    async scanContent() {
        return this.post('/content/scan');
    }

    /**
     * Статистика контента
     */
    async getContentStats() {
        return this.get('/content/stats');
    }

    /**
     * Удаление папки контента
     */
    async deleteContentFolder(folderId) {
        return this.delete(`/content/folders/${folderId}`);
    }

    // === ЗАДАЧИ ===

    /**
     * Получение задач публикации
     */
    async getTasks(filters = {}) {
        return this.get('/tasks', filters);
    }

    /**
     * Удаление задачи
     */
    async deleteTask(taskId) {
        return this.delete(`/tasks/${taskId}`);
    }

    // === СИСТЕМА ===

    /**
     * Статус системы
     */
    async getSystemStatus() {
        return this.get('/system/status');
    }

    /**
     * Статистика системы
     */
    async getSystemStats() {
        return this.get('/system/stats');
    }

    /**
     * Системные логи
     */
    async getSystemLogs(filters = {}) {
        return this.get('/system/logs', filters);
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/system/health');
    }

    // === ПРОКСИ ===

    /**
     * Получение списка прокси
     */
    async getProxies(filters = {}) {
        return this.get('/proxies', filters);
    }

    /**
     * Синхронизация прокси
     */
    async syncProxies() {
        return this.post('/proxies/sync');
    }

    /**
     * Тестирование прокси
     */
    async testAllProxies() {
        return this.post('/proxies/test');
    }

    /**
     * Статистика прокси
     */
    async getProxyStats() {
        return this.get('/proxies/stats');
    }

    /**
     * Удаление прокси
     */
    async deleteProxy(proxyId) {
        return this.delete(`/proxies/${proxyId}`);
    }

    // === УТИЛИТЫ ===

    /**
     * Проверка авторизации
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Форматирование числа
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Форматирование даты
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMinutes < 1) return 'только что';
        if (diffMinutes < 60) return `${diffMinutes} мин назад`;
        if (diffHours < 24) return `${diffHours} ч назад`;
        if (diffDays < 7) return `${diffDays} дн назад`;
        
        return date.toLocaleDateString('ru-RU');
    }

    /**
     * Получение статуса аккаунта на русском
     */
    getAccountStatusText(status) {
        const statusMap = {
            'active': 'Активен',
            'limited': 'Ограничен',
            'banned': 'Заблокирован',
            'error': 'Ошибка'
        };
        return statusMap[status] || status;
    }

    /**
     * Получение цвета статуса
     */
    getStatusColor(status) {
        const colorMap = {
            'active': '#10b981',
            'limited': '#f59e0b',
            'banned': '#ef4444',
            'error': '#6b7280'
        };
        return colorMap[status] || '#6b7280';
    }
}

// Создаем глобальный экземпляр API
window.MediaFluxAPI = new MediaFluxHubAPI(); 