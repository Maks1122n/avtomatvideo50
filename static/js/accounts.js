// Accounts Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadAccountsPage();
    setupAccountsEventListeners();
});

function setupAccountsEventListeners() {
    // Форма добавления аккаунта
    const addAccountForm = document.getElementById('addAccountForm');
    if (addAccountForm) {
        addAccountForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const accountData = Object.fromEntries(formData);
            window.mediaFluxDashboard.addAccount(accountData);
        });
    }
}

function showAddAccountForm() {
    document.getElementById('addAccountSection').classList.remove('hidden');
}

function hideAddAccountForm() {
    document.getElementById('addAccountSection').classList.add('hidden');
}

async function testConnection() {
    const form = document.getElementById('addAccountForm');
    const formData = new FormData(form);
    const accountData = Object.fromEntries(formData);
    
    await window.mediaFluxDashboard.testConnection(accountData);
}

async function loadAccountsPage() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();
        
        // Обновляем счетчики
        document.getElementById('activeAccountsCount').textContent = data.active;
        document.getElementById('limitedAccountsCount').textContent = data.limited;
        
        // Рендерим список аккаунтов
        renderAccountsList(data.accounts);
        
    } catch (error) {
        console.error('Ошибка загрузки аккаунтов:', error);
    }
}

function renderAccountsList(accounts) {
    const accountsList = document.getElementById('accountsList');
    
    if (!accounts || accounts.length === 0) {
        accountsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>Нет добавленных аккаунтов</h3>
                <p>Добавьте свой первый Instagram аккаунт</p>
                <button class="btn btn-primary" onclick="showAddAccountForm()">
                    Добавить аккаунт
                </button>
            </div>
        `;
        return;
    }
    
    accountsList.innerHTML = accounts.map(account => `
        <div class="account-card ${account.status}" onclick="showAccountDetails('${account.id}')">
            <div class="account-header">
                <span class="account-username">@${account.username}</span>
                <span class="account-status ${account.status}">${getStatusText(account.status)}</span>
            </div>
            
            <div class="account-stats">
                <div class="account-stat">
                    <span class="account-stat-value">${account.posts_today}</span>
                    <span class="account-stat-label">Сегодня</span>
                </div>
                <div class="account-stat">
                    <span class="account-stat-value">${account.followers || 0}</span>
                    <span class="account-stat-label">Подписчиков</span>
                </div>
            </div>
            
            <div class="account-info">
                <p><i class="fas fa-clock"></i> ${account.last_activity}</p>
                <p><i class="fas fa-wifi"></i> ${account.proxy_status}</p>
                <p><i class="fas fa-chart-line"></i> ${account.engagement_rate || 0}% вовлечённость</p>
            </div>
            
            <div class="account-actions" onclick="event.stopPropagation()">
                <button class="account-action" onclick="testAccountConnection('${account.id}')">
                    <i class="fas fa-wifi"></i>
                </button>
                <button class="account-action" onclick="editAccount('${account.id}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="account-action" onclick="deleteAccount('${account.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function getStatusText(status) {
    const statusTexts = {
        'active': 'Активен',
        'limited': 'Ограничен',
        'banned': 'Заблокирован',
        'error': 'Ошибка'
    };
    return statusTexts[status] || status;
}

async function showAccountDetails(accountId) {
    try {
        const response = await fetch(`/api/accounts/${accountId}`);
        const account = await response.json();
        
        const modalContent = document.getElementById('accountModalContent');
        modalContent.innerHTML = `
            <div class="account-details">
                <div class="detail-header">
                    <h3>@${account.username}</h3>
                    <span class="account-status ${account.status}">${getStatusText(account.status)}</span>
                </div>
                
                <div class="detail-stats">
                    <div class="stat-item">
                        <span class="stat-label">Подписчиков:</span>
                        <span class="stat-value">${account.followers || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Подписки:</span>
                        <span class="stat-value">${account.following || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Публикаций:</span>
                        <span class="stat-value">${account.total_posts || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Вовлечённость:</span>
                        <span class="stat-value">${account.engagement_rate || 0}%</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Расписание</h4>
                    <p>Постов в день: ${account.schedule?.posts_per_day || 0}</p>
                    <p>Время: ${account.schedule?.time_slots?.join(', ') || 'Не настроено'}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Прокси</h4>
                    <p>Статус: ${account.proxy?.status || 'Не настроен'}</p>
                    <p>Локация: ${account.proxy?.location || 'Не определена'}</p>
                </div>
            </div>
        `;
        
        document.getElementById('accountModal').classList.remove('hidden');
        
    } catch (error) {
        window.mediaFluxDashboard.showNotification('Ошибка загрузки деталей аккаунта', 'error');
    }
}

function closeAccountModal() {
    document.getElementById('accountModal').classList.add('hidden');
}

async function testAccountConnection(accountId) {
    try {
        const response = await fetch(`/api/accounts/${accountId}/test-connection`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.connection_status === 'success') {
            window.mediaFluxDashboard.showNotification('Соединение успешно', 'success');
        } else {
            window.mediaFluxDashboard.showNotification('Ошибка соединения', 'error');
        }
    } catch (error) {
        window.mediaFluxDashboard.showNotification('Ошибка проверки соединения', 'error');
    }
}

function editAccount(accountId) {
    window.mediaFluxDashboard.showNotification('Редактирование аккаунта в разработке', 'info');
}

function deleteAccount(accountId) {
    if (confirm('Вы уверены, что хотите удалить этот аккаунт?')) {
        window.mediaFluxDashboard.showNotification('Удаление аккаунта в разработке', 'info');
    }
} 