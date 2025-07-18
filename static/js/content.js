// Content Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadContentPage();
    setupContentEventListeners();
});

function setupContentEventListeners() {
    // Drag & Drop для загрузки видео
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('click', () => {
            document.getElementById('videoFiles').click();
        });
    }
    
    // Обработка выбора файлов
    const videoFiles = document.getElementById('videoFiles');
    if (videoFiles) {
        videoFiles.addEventListener('change', handleFileSelect);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    const videoFiles = files.filter(file => file.type.startsWith('video/'));
    
    if (videoFiles.length > 0) {
        uploadVideos(videoFiles);
    } else {
        window.mediaFluxDashboard.showNotification('Пожалуйста, выберите видео файлы', 'warning');
    }
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        uploadVideos(files);
    }
}

function showUploadArea() {
    const uploadSection = document.getElementById('uploadSection');
    uploadSection.scrollIntoView({ behavior: 'smooth' });
}

async function uploadVideos(files) {
    const category = document.getElementById('videoCategory').value;
    const autoCaption = document.getElementById('autoCaption').checked;
    
    // Показываем прогресс
    const progressSection = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    progressSection.classList.remove('hidden');
    
    // Симуляция загрузки
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress > 90) progress = 90;
        
        progressFill.style.width = progress + '%';
        progressText.textContent = `Загрузка: ${Math.round(progress)}%`;
    }, 500);
    
    try {
        // Реальная загрузка через API
        await window.mediaFluxDashboard.uploadVideos(files, category);
        
        // Завершаем прогресс
        clearInterval(interval);
        progressFill.style.width = '100%';
        progressText.textContent = 'Загрузка завершена!';
        
        setTimeout(() => {
            progressSection.classList.add('hidden');
            progressFill.style.width = '0%';
        }, 2000);
        
        // Обновляем список папок
        loadFolders();
        
    } catch (error) {
        clearInterval(interval);
        progressSection.classList.add('hidden');
        window.mediaFluxDashboard.showNotification('Ошибка загрузки видео', 'error');
    }
}

async function loadContentPage() {
    await loadFolders();
    await loadContentStats();
}

async function loadFolders() {
    try {
        const response = await fetch('/api/content/folders');
        const data = await response.json();
        
        // Обновляем статистику
        document.getElementById('totalVideos').textContent = data.total_videos;
        document.getElementById('totalSize').textContent = data.total_size;
        
        // Рендерим папки
        renderFolders(data.folders);
        
    } catch (error) {
        console.error('Ошибка загрузки папок:', error);
    }
}

function renderFolders(folders) {
    const foldersGrid = document.getElementById('foldersGrid');
    
    foldersGrid.innerHTML = folders.map(folder => `
        <div class="folder-card" onclick="openFolder('${folder.name}')">
            <div class="folder-header">
                <div class="folder-icon">
                    <i class="fas ${getFolderIcon(folder.name)}"></i>
                </div>
                <div class="folder-info">
                    <h3>${folder.display_name}</h3>
                    <p>${folder.video_count} видео</p>
                </div>
            </div>
            
            <div class="folder-stats">
                <div class="folder-stat">
                    <span class="folder-stat-value">${folder.video_count}</span>
                    <span class="folder-stat-label">Видео</span>
                </div>
                <div class="folder-stat">
                    <span class="folder-stat-value">${folder.total_size}</span>
                    <span class="folder-stat-label">Размер</span>
                </div>
            </div>
            
            <div class="folder-footer">
                <span class="folder-last-upload">${folder.last_upload}</span>
                <span class="folder-status ${folder.status}">Активна</span>
            </div>
        </div>
    `).join('');
}

function getFolderIcon(folderName) {
    const icons = {
        'motivation': 'fa-fire',
        'business': 'fa-briefcase',
        'lifestyle': 'fa-heart',
        'entertainment': 'fa-laugh'
    };
    return icons[folderName] || 'fa-folder';
}

async function openFolder(folderName) {
    try {
        const response = await fetch(`/api/content/videos?folder=${folderName}`);
        const videos = await response.json();
        
        // Показываем секцию видео
        document.querySelector('.content-folders').classList.add('hidden');
        document.getElementById('videosSection').classList.remove('hidden');
        document.getElementById('currentFolderName').textContent = folderName;
        
        renderVideos(videos);
        
    } catch (error) {
        window.mediaFluxDashboard.showNotification('Ошибка загрузки видео', 'error');
    }
}

function renderVideos(videos) {
    const videosGrid = document.getElementById('videosGrid');
    
    if (videos.length === 0) {
        videosGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-video"></i>
                <h3>Папка пуста</h3>
                <p>Загрузите видео в эту папку</p>
            </div>
        `;
        return;
    }
    
    videosGrid.innerHTML = videos.map(video => `
        <div class="video-card" onclick="previewVideo('${video.id}')">
            <div class="video-thumbnail">
                <i class="fas fa-play-circle"></i>
                <div class="video-duration">${video.duration}</div>
            </div>
            
            <div class="video-content">
                <div class="video-title">${video.filename}</div>
                <div class="video-meta">
                    <span class="video-size">${video.size}</span>
                    <span class="video-used">Использовано: ${video.used_count} раз</span>
                </div>
            </div>
        </div>
    `).join('');
}

function backToFolders() {
    document.querySelector('.content-folders').classList.remove('hidden');
    document.getElementById('videosSection').classList.add('hidden');
}

async function previewVideo(videoId) {
    try {
        const response = await fetch(`/api/content/videos/${videoId}`);
        const video = await response.json();
        
        // Показываем модальное окно с превью
        const modal = document.getElementById('videoModal');
        const title = document.getElementById('videoModalTitle');
        const preview = document.getElementById('videoPreview');
        const info = document.getElementById('videoInfo');
        
        title.textContent = video.filename;
        preview.src = `/static/videos/${video.filename}`; // Путь к видео
        
        info.innerHTML = `
            <div class="info-row">
                <span class="info-label">Размер:</span>
                <span class="info-value">${video.size}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Длительность:</span>
                <span class="info-value">${video.duration}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Загружено:</span>
                <span class="info-value">${video.uploaded}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Использовано:</span>
                <span class="info-value">${video.used_count} раз</span>
            </div>
            <div class="info-row">
                <span class="info-label">Последнее использование:</span>
                <span class="info-value">${video.last_used}</span>
            </div>
        `;
        
        modal.classList.remove('hidden');
        
    } catch (error) {
        window.mediaFluxDashboard.showNotification('Ошибка загрузки видео', 'error');
    }
}

function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    const preview = document.getElementById('videoPreview');
    
    modal.classList.add('hidden');
    preview.pause();
    preview.src = '';
}

async function loadContentStats() {
    // Загружаем общую статистику контента
    try {
        const response = await fetch('/api/content/stats');
        const stats = await response.json();
        
        // Обновляем статистику на странице
        // Это можно расширить для отображения дополнительной информации
        
    } catch (error) {
        console.error('Ошибка загрузки статистики контента:', error);
    }
} 