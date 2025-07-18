// Schedule Page JavaScript
let currentDate = new Date();

document.addEventListener('DOMContentLoaded', function() {
    loadSchedulePage();
    setupScheduleEventListeners();
});

function setupScheduleEventListeners() {
    // Форма создания расписания
    const scheduleForm = document.getElementById('scheduleForm');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const scheduleData = Object.fromEntries(formData);
            
            // Собираем выбранные аккаунты
            const selectedAccounts = Array.from(
                document.querySelectorAll('input[name="accounts"]:checked')
            ).map(cb => cb.value);
            
            // Собираем выбранные дни недели
            const selectedWeekdays = Array.from(
                document.querySelectorAll('input[name="weekdays"]:checked')
            ).map(cb => cb.value);
            
            scheduleData.accounts = selectedAccounts;
            scheduleData.weekdays = selectedWeekdays;
            
            window.mediaFluxDashboard.createSchedule(scheduleData);
        });
    }
}

function showScheduleForm() {
    document.getElementById('scheduleFormSection').classList.remove('hidden');
    loadAccountsForSchedule();
}

function hideScheduleForm() {
    document.getElementById('scheduleFormSection').classList.add('hidden');
}

async function loadSchedulePage() {
    await loadScheduleStats();
    await loadCalendar();
    await loadScheduledPosts();
}

async function loadScheduleStats() {
    try {
        const response = await fetch('/api/tasks/schedule');
        const stats = await response.json();
        
        document.getElementById('postsToday').textContent = stats.today;
        document.getElementById('postsTomorrow').textContent = stats.tomorrow;
        document.getElementById('postsThisWeek').textContent = stats.this_week;
        
        // Найти следующую публикацию
        const nextPost = findNextPost(stats.next_7_days);
        document.getElementById('nextPost').textContent = nextPost || '--:--';
        
    } catch (error) {
        console.error('Ошибка загрузки статистики расписания:', error);
    }
}

function findNextPost(schedule) {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    
    // Это упрощённая логика - в реальности нужно будет получать детальное расписание
    return '14:30'; // Заглушка
}

async function loadAccountsForSchedule() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();
        
        const checkboxesContainer = document.getElementById('accountsCheckboxes');
        checkboxesContainer.innerHTML = data.accounts.map(account => `
            <label class="checkbox-item">
                <input type="checkbox" name="accounts" value="${account.id}" 
                       ${account.status === 'active' ? 'checked' : ''}>
                <span>@${account.username}</span>
                <small>${account.status === 'active' ? 'Активен' : 'Неактивен'}</small>
            </label>
        `).join('');
        
    } catch (error) {
        console.error('Ошибка загрузки аккаунтов:', error);
    }
}

async function loadCalendar() {
    try {
        // Обновляем заголовок календаря
        const monthNames = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ];
        
        document.getElementById('currentMonth').textContent = 
            `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
        
        // Генерируем календарь
        renderCalendar();
        
    } catch (error) {
        console.error('Ошибка загрузки календаря:', error);
    }
}

function renderCalendar() {
    const calendar = document.getElementById('calendar');
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Получаем первый день месяца и количество дней
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Создаём сетку календаря
    let calendarHTML = `
        <div class="calendar-grid">
            <div class="calendar-header-day">Пн</div>
            <div class="calendar-header-day">Вт</div>
            <div class="calendar-header-day">Ср</div>
            <div class="calendar-header-day">Чт</div>
            <div class="calendar-header-day">Пт</div>
            <div class="calendar-header-day">Сб</div>
            <div class="calendar-header-day">Вс</div>
    `;
    
    // Добавляем пустые ячейки для дней предыдущего месяца
    const startDay = startingDayOfWeek === 0 ? 6 : startingDayOfWeek - 1;
    for (let i = 0; i < startDay; i++) {
        const prevDate = new Date(year, month, 0 - (startDay - i - 1));
        calendarHTML += `
            <div class="calendar-day other-month">
                <div class="day-number">${prevDate.getDate()}</div>
            </div>
        `;
    }
    
    // Добавляем дни текущего месяца
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const currentDay = new Date(year, month, day);
        const isToday = currentDay.toDateString() === today.toDateString();
        
        const posts = generateDayPosts(day, month); // Генерируем постыв для дня
        
        calendarHTML += `
            <div class="calendar-day ${isToday ? 'today' : ''}" onclick="selectCalendarDay(${day})">
                <div class="day-number">${day}</div>
                <div class="day-posts">
                    ${posts.map(post => `
                        <div class="post-item ${post.category}" title="${post.title}">
                            ${post.time}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Добавляем дни следующего месяца для заполнения сетки
    const totalCells = Math.ceil((startDay + daysInMonth) / 7) * 7;
    const remainingCells = totalCells - (startDay + daysInMonth);
    for (let i = 1; i <= remainingCells; i++) {
        calendarHTML += `
            <div class="calendar-day other-month">
                <div class="day-number">${i}</div>
            </div>
        `;
    }
    
    calendarHTML += '</div>';
    calendar.innerHTML = calendarHTML;
}

function generateDayPosts(day, month) {
    // Генерируем случайные посты для демонстрации
    const posts = [];
    const postCount = Math.floor(Math.random() * 4) + 1;
    const categories = ['motivation', 'business', 'lifestyle', 'entertainment'];
    
    for (let i = 0; i < postCount; i++) {
        const hour = 9 + Math.floor(Math.random() * 12);
        const minute = Math.floor(Math.random() * 60);
        posts.push({
            time: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
            category: categories[Math.floor(Math.random() * categories.length)],
            title: `Публикация ${i + 1}`
        });
    }
    
    return posts.sort((a, b) => a.time.localeCompare(b.time));
}

function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    loadCalendar();
}

function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    loadCalendar();
}

function selectCalendarDay(day) {
    const selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    window.mediaFluxDashboard.showNotification(
        `Выбран день: ${selectedDate.toLocaleDateString('ru-RU')}`, 
        'info'
    );
}

async function loadScheduledPosts() {
    try {
        const response = await fetch('/api/tasks?status=pending');
        const data = await response.json();
        
        renderScheduledPosts(data.tasks);
        
    } catch (error) {
        console.error('Ошибка загрузки запланированных публикаций:', error);
    }
}

function renderScheduledPosts(posts) {
    const postsList = document.getElementById('postsList');
    
    if (!posts || posts.length === 0) {
        postsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar-times"></i>
                <h3>Нет запланированных публикаций</h3>
                <p>Создайте первое расписание</p>
                <button class="btn btn-primary" onclick="showScheduleForm()">
                    Создать расписание
                </button>
            </div>
        `;
        return;
    }
    
    postsList.innerHTML = posts.map(post => `
        <div class="post-card">
            <div class="post-header">
                <span class="post-account">${post.account}</span>
                <span class="post-time">${formatDateTime(post.scheduled_time)}</span>
            </div>
            
            <div class="post-content">
                <div class="post-video">
                    <i class="fas fa-play"></i>
                </div>
                
                <div class="post-details">
                    <h4>${getVideoName(post.video)}</h4>
                    <p>${post.caption || 'Описание будет сгенерировано автоматически'}</p>
                </div>
                
                <div class="post-actions">
                    <button class="post-action" onclick="editPost('${post.task_id}')" title="Редактировать">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="post-action" onclick="deletePost('${post.task_id}')" title="Удалить">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="post-action" onclick="executePost('${post.task_id}')" title="Опубликовать сейчас">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getVideoName(videoPath) {
    return videoPath.split('/').pop().replace('.mp4', '');
}

function filterPosts() {
    const filter = document.getElementById('postsFilter').value;
    window.mediaFluxDashboard.showNotification(`Фильтр: ${filter}`, 'info');
    // Здесь можно реализовать фильтрацию постов
}

async function previewSchedule() {
    const form = document.getElementById('scheduleForm');
    const formData = new FormData(form);
    
    // Собираем данные формы
    const scheduleData = {
        period: formData.get('period'),
        start_time: formData.get('start_time'),
        end_time: formData.get('end_time'),
        posts_per_day: formData.get('posts_per_day'),
        accounts: Array.from(document.querySelectorAll('input[name="accounts"]:checked')).map(cb => cb.value),
        weekdays: Array.from(document.querySelectorAll('input[name="weekdays"]:checked')).map(cb => cb.value)
    };
    
    // Генерируем превью
    const previewContent = generateSchedulePreview(scheduleData);
    
    document.getElementById('schedulePreviewContent').innerHTML = previewContent;
    document.getElementById('schedulePreviewModal').classList.remove('hidden');
}

function generateSchedulePreview(data) {
    const accountsCount = data.accounts.length;
    const daysCount = data.period === 'week' ? 7 : 30;
    const totalPosts = accountsCount * data.posts_per_day * daysCount;
    
    return `
        <div class="preview-summary">
            <h4>Предварительный просмотр расписания</h4>
            <div class="summary-stats">
                <div class="summary-item">
                    <span class="summary-label">Аккаунтов:</span>
                    <span class="summary-value">${accountsCount}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Период:</span>
                    <span class="summary-value">${data.period === 'week' ? 'Неделя' : 'Месяц'}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Постов в день:</span>
                    <span class="summary-value">${data.posts_per_day}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Всего публикаций:</span>
                    <span class="summary-value">${totalPosts}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Время:</span>
                    <span class="summary-value">${data.start_time} - ${data.end_time}</span>
                </div>
            </div>
        </div>
        
        <div class="preview-timeline">
            <h5>Пример расписания на завтра:</h5>
            ${generateSampleTimeline(data)}
        </div>
    `;
}

function generateSampleTimeline(data) {
    const timeline = [];
    const startHour = parseInt(data.start_time.split(':')[0]);
    const endHour = parseInt(data.end_time.split(':')[0]);
    const postsPerDay = parseInt(data.posts_per_day);
    
    // Генерируем времена публикаций
    for (let i = 0; i < postsPerDay; i++) {
        const hour = startHour + Math.floor((endHour - startHour) * i / postsPerDay);
        const minute = Math.floor(Math.random() * 60);
        timeline.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
    
    return timeline.map(time => `
        <div class="timeline-item">
            <span class="timeline-time">${time}</span>
            <span class="timeline-action">Публикация в случайном аккаунте</span>
        </div>
    `).join('');
}

function closeSchedulePreview() {
    document.getElementById('schedulePreviewModal').classList.add('hidden');
}

function editPost(taskId) {
    window.mediaFluxDashboard.showNotification('Редактирование публикации в разработке', 'info');
}

function deletePost(taskId) {
    if (confirm('Удалить эту запланированную публикацию?')) {
        window.mediaFluxDashboard.showNotification('Удаление публикации в разработке', 'info');
    }
}

function executePost(taskId) {
    if (confirm('Опубликовать сейчас?')) {
        window.mediaFluxDashboard.showNotification('Немедленная публикация в разработке', 'info');
    }
} 