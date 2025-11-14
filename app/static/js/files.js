document.addEventListener('DOMContentLoaded', function() {
    const fileList = document.getElementById('file-list');
    const currentPathDiv = document.getElementById('current-path');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const newItemNameInput = document.getElementById('new-item-name');
    const createItemBtn = document.getElementById('create-item-btn');
    const drivesContainer = document.createElement('div');
    drivesContainer.id = 'drives-container';
    drivesContainer.style.marginBottom = '1rem';
    currentPathDiv.parentNode.insertBefore(drivesContainer, currentPathDiv.nextSibling);

    // Контейнер для кнопок навигации
    const navContainer = document.createElement('div');
    navContainer.id = 'nav-container';
    navContainer.style.marginBottom = '1rem';
    drivesContainer.parentNode.insertBefore(navContainer, drivesContainer);

    let currentPath = '/';
    let pathHistory = []; // История посещенных директорий
    let currentIndex = -1; // Текущий индекс в истории
    let socket; // Переменная для хранения WebSocket-соединения

    // Подключаемся к WebSocket
    function connectWebSocket() {
        // Используем тот же протокол, что и текущая страница
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/file_updates`;
        
        try {
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                console.log('WebSocket connected for file updates');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.path) {
                    // Обновляем список файлов, если текущая директория совпадает с измененной
                    if (data.path.startsWith(currentPath) || currentPath.startsWith(data.path)) {
                        console.log('File change detected, refreshing directory');
                        listDirectory(currentPath);
                    }
                }
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            socket.onclose = function(event) {
                console.log('WebSocket disconnected, attempting to reconnect...');
                // Пытаемся переподключиться через 3 секунды
                setTimeout(connectWebSocket, 3000);
            };
        } catch (e) {
            console.error('Failed to connect WebSocket:', e);
            // Пытаемся переподключиться через 3 секунды
            setTimeout(connectWebSocket, 3000);
        }
    }

    // Запускаем WebSocket-соединение
    connectWebSocket();

    // Функция для обновления навигационных кнопок
    function updateNavButtons() {
        navContainer.innerHTML = '';
        
        const navDiv = document.createElement('div');
        navDiv.style.display = 'flex';
        navDiv.style.gap = '0.5rem';
        navDiv.style.marginBottom = '1rem';
        
        // Кнопка "Назад"
        const backBtn = document.createElement('button');
        backBtn.textContent = '← Back';
        backBtn.disabled = currentIndex <= 0;
        backBtn.style.padding = '0.5rem 1rem';
        backBtn.style.backgroundColor = currentIndex <= 0 ? '#bdc3c7' : '#3498db';
        backBtn.style.color = 'white';
        backBtn.style.border = 'none';
        backBtn.style.borderRadius = '4px';
        backBtn.style.cursor = currentIndex <= 0 ? 'not-allowed' : 'pointer';
        backBtn.addEventListener('click', goBack);
        
        // Кнопка "Вперед"
        const forwardBtn = document.createElement('button');
        forwardBtn.textContent = 'Forward →';
        forwardBtn.disabled = currentIndex >= pathHistory.length - 1;
        forwardBtn.style.padding = '0.5rem 1rem';
        forwardBtn.style.backgroundColor = currentIndex >= pathHistory.length - 1 ? '#bdc3c7' : '#3498db';
        forwardBtn.style.color = 'white';
        forwardBtn.style.border = 'none';
        forwardBtn.style.borderRadius = '4px';
        forwardBtn.style.cursor = currentIndex >= pathHistory.length - 1 ? 'not-allowed' : 'pointer';
        forwardBtn.addEventListener('click', goForward);
        
        // Кнопка "Вверх" (к родительской директории)
        const upBtn = document.createElement('button');
        upBtn.textContent = '↑ Up';
        upBtn.style.padding = '0.5rem 1rem';
        upBtn.style.backgroundColor = '#9b59b6';
        upBtn.style.color = 'white';
        upBtn.style.border = 'none';
        upBtn.style.borderRadius = '4px';
        upBtn.style.cursor = 'pointer';
        upBtn.addEventListener('click', goToParentDirectory);
        
        navDiv.appendChild(backBtn);
        navDiv.appendChild(forwardBtn);
        navDiv.appendChild(upBtn);
        navContainer.appendChild(navDiv);
    }

    // Функция для добавления пути в историю
    function addToHistory(path) {
        // Удаляем все элементы после текущего индекса
        pathHistory = pathHistory.slice(0, currentIndex + 1);
        // Добавляем новый путь
        pathHistory.push(path);
        // Обновляем индекс
        currentIndex = pathHistory.length - 1;
        updateNavButtons();
    }

    // Функция для перехода назад
    function goBack() {
        if (currentIndex > 0) {
            currentIndex--;
            const path = pathHistory[currentIndex];
            listDirectory(path, false); // Не добавляем в историю при возврате
        }
    }

    // Функция для перехода вперед
    function goForward() {
        if (currentIndex < pathHistory.length - 1) {
            currentIndex++;
            const path = pathHistory[currentIndex];
            listDirectory(path, false); // Не добавляем в историю при переходе вперед
        }
    }

    // Функция для перехода к родительской директории
    function goToParentDirectory() {
        if (currentPath === '/' || currentPath === '.' || currentPath === '') {
            // Если мы в корне, покажем доступные диски
            showDrives();
            return;
        }
        
        // Получаем родительскую директорию
        const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/'));
        if (parentPath === '') {
            listDirectory('/', true);
        } else {
            listDirectory(parentPath, true);
        }
    }

    // Функция для получения расширения файла
    function getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }

    // Функция для определения типа файла по расширению
    function getFileType(filename) {
        const ext = getFileExtension(filename);
        const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'];
        const audioExtensions = ['mp3', 'wav', 'ogg', 'aac', 'flac'];
        const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'];
        const documentExtensions = ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt'];

        if (imageExtensions.includes(ext)) return 'image';
        if (audioExtensions.includes(ext)) return 'audio';
        if (videoExtensions.includes(ext)) return 'video';
        if (documentExtensions.includes(ext)) return 'document';
        return 'text';
    }

    // Функция для отображения предпросмотра файла
    function showPreview(path, name, isDir) {
        if (isDir) {
            // При переходе в директорию добавляем путь в историю
            addToHistory(path);
            listDirectory(path, false);
            return;
        }

        const fileType = getFileType(name);
        
        // Для текстовых файлов открываем редактор
        if (fileType === 'text') {
            openEditor(path, name);
        } else if (fileType === 'document') {
            // Для документов открываем просмотрщик
            showDocumentPreview(path, name);
        } else {
            // Для мультимедийных файлов показываем предпросмотр
            showMediaPreview(path, name, fileType);
        }
    }

    // Функция для просмотра документов
    function showDocumentPreview(path, name) {
        const ext = getFileExtension(name);
        
        if (ext === 'pdf') {
            // Для PDF используем встроенный просмотрщик браузера
            const previewWindow = window.open('', '_blank', 'width=1000,height=700');
            previewWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Preview ${name}</title>
                    <style>
                        body { margin: 0; padding: 0; background: #f5f5f5; height: 100vh; }
                        .container { height: 100vh; display: flex; flex-direction: column; }
                        .controls { padding: 10px; background: #fff; border-bottom: 1px solid #ddd; }
                        button { padding: 5px 10px; margin-right: 10px; }
                        .viewer { flex: 1; }
                        .pdf-container { width: 100%; height: 100%; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="controls">
                            <button onclick="window.close()">Close</button>
                            <button onclick="downloadFile()">Download</button>
                        </div>
                        <div class="viewer">
                            <iframe class="pdf-container" src="/files/view/${encodeURIComponent(path)}" type="application/pdf"></iframe>
                        </div>
                    </div>
                    <script>
                        function downloadFile() {
                            window.open('/files/download/${encodeURIComponent(path)}', '_blank');
                        }
                    </script>
                </body>
                </html>
            `);
        } else {
            // Для других документов показываем сообщение
            alert('Document preview is not supported for this file type (' + ext + '). You can download the file to view it.');
        }
    }

    // Функция для открытия редактора
    function openEditor(filePath, fileName) {
        fetch(`/files/read?path=${encodeURIComponent(filePath)}`)
            .then(response => response.text())
            .then(content => {
                const editorWindow = window.open('', '_blank', 'width=800,height=600');
                editorWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Edit ${fileName}</title>
                        <style>
                            body { font-family: monospace; margin: 0; padding: 0; }
                            textarea { width: 100%; height: 90vh; font-family: monospace; padding: 10px; }
                            .controls { padding: 10px; background: #f5f5f5; display: flex; gap: 10px; }
                            button { padding: 5px 10px; }
                        </style>
                    </head>
                    <body>
                        <div class="controls">
                            <button onclick="saveFile()">Save</button>
                            <button onclick="window.close()">Close</button>
                        </div>
                        <textarea id="editor-content">${content.replace(/</g, '<').replace(/>/g, '>')}</textarea>
                        <script>
                            function saveFile() {
                                const content = document.getElementById('editor-content').value;
                                fetch('/files/write', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({
                                        path: '${filePath.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;')}',
                                        content: content
                                    })
                                }).then(response => {
                                    if(response.ok) {
                                        alert('File saved successfully!');
                                    } else {
                                        response.json().then(data => {
                                            alert('Error saving file: ' + data.error);
                                        });
                                    }
                                }).catch(error => {
                                    alert('Network error: ' + error.message);
                                });
                            }
                        </script>
                    </body>
                    </html>
                `);
            });
    }

    // Функция для показа медиа-предпросмотра
    function showMediaPreview(path, name, type) {
        const previewWindow = window.open('', '_blank', 'width=800,height=600');
        let content = '';
        
        if (type === 'image') {
            content = `<img src="/files/view/${encodeURIComponent(path)}" style="max-width: 100%; max-height: 90vh; display: block; margin: 20px auto;">`;
        } else if (type === 'audio') {
            content = `<audio controls style="width: 100%; margin: 20px;">
                <source src="/files/view/${encodeURIComponent(path)}" type="audio/${getFileExtension(name)}">
                Your browser does not support the audio element.
            </audio>`;
        } else if (type === 'video') {
            content = `<video controls style="width: 100%; max-height: 90vh; display: block; margin: 20px auto;">
                <source src="/files/view/${encodeURIComponent(path)}" type="video/${getFileExtension(name)}">
                Your browser does not support the video element.
            </video>`;
        }

        previewWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Preview ${name}</title>
                <style>
                    body { margin: 0; padding: 0; background: #f5f5f5; }
                    .container { padding: 20px; }
                    .controls { padding: 10px; background: #fff; border-top: 1px solid #ddd; }
                    button { padding: 5px 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    ${content}
                </div>
                <div class="controls">
                    <button onclick="window.close()">Close</button>
                </div>
            </body>
            </html>
        `);
    }

    // Функция для переименования файла/папки
    function renameItem(oldPath, newName) {
        const newPath = oldPath.substring(0, oldPath.lastIndexOf('/') + 1) + newName;
        fetch('/files/rename', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                old_path: oldPath,
                new_path: newPath
            })
        }).then(response => {
            if(response.ok) {
                listDirectory(currentPath, false);
            } else {
                response.json().then(data => {
                    alert('Error renaming item: ' + data.error);
                });
            }
        }).catch(error => {
            alert('Network error: ' + error.message);
        });
    }

    // Функция для отображения доступных дисков
    function showDrives() {
        fetch('/files/drives')
            .then(response => response.json())
            .then(data => {
                if (data.drives) {
                    drivesContainer.innerHTML = '<div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">' + 
                        data.drives.map(drive => 
                            `<button class="drive-btn" data-drive="${drive}" style="
                                padding: 0.25rem 0.5rem; 
                                background-color: #3498db; 
                                color: white; 
                                border: none; 
                                border-radius: 4px; 
                                cursor: pointer;
                                transition: var(--transition);
                            ">${drive}</button>`
                        ).join('') + '</div>';

                    // Добавляем обработчики для кнопок дисков
                    document.querySelectorAll('.drive-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const drive = e.target.getAttribute('data-drive');
                            addToHistory(drive); // Добавляем диск в историю
                            listDirectory(drive, false);
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error loading drives:', error);
            });
    }

    // Основная функция для отображения содержимого директории
    function listDirectory(path, addToHist = true) {
        if (addToHist && (pathHistory[currentIndex] !== path)) {
            addToHistory(path);
        } else {
            // Обновляем текущий путь, но не добавляем в историю
            currentPath = path;
            updateNavButtons();
        }
        
        fetch(`/files/list?path=${encodeURIComponent(path)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('API Error:', data.error);
                    alert('Error loading directory: ' + data.error);
                    return;
                }

                // Ensure data.entries is an array
                data.entries = data.entries || [];

                currentPathDiv.textContent = data.path;
                currentPath = data.path.replace(/\\/g, '/'); // Normalize to forward slashes for JS

                // Показываем доступные диски
                if (data.drives) {
                    drivesContainer.innerHTML = '<div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">' +
                        data.drives.map(drive =>
                            `<button class="drive-btn" data-drive="${drive}" style="
                                padding: 0.25rem 0.5rem;
                                background-color: ${drive === currentPath.substring(0, 2) ? '#e74c3c' : '#3498db'};
                                color: white;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                transition: var(--transition);
                            ">${drive}</button>`
                        ).join('') + '</div>';

                    // Добавляем обработчики для кнопок дисков
                    document.querySelectorAll('.drive-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const drive = e.target.getAttribute('data-drive');
                            addToHistory(drive); // Добавляем диск в историю
                            listDirectory(drive, false);
                        });
                    });
                }

                fileList.innerHTML = '';

                // Создаем заголовок списка
                const headerDiv = document.createElement('div');
                headerDiv.className = 'file-list-header';
                headerDiv.innerHTML = `
                    <div class="file-item-header">
                        <span class="file-name">Name</span>
                        <span class="file-type">Type</span>
                        <span class="file-size">Size</span>
                        <span class="file-actions">Actions</span>
                    </div>
                `;
                fileList.appendChild(headerDiv);

                data.entries.forEach(entry => {
                    entry.path = entry.path.replace(/\\/g, '/'); // Normalize paths
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `file-item ${entry.is_dir ? 'directory' : 'file'}`;
                    
                    // Определяем иконку в зависимости от типа файла
                    let icon = entry.is_dir ? '📁' : '📄';
                    const ext = entry.name.split('.').pop().toLowerCase();
                    if (!entry.is_dir) {
                        if (['pdf'].includes(ext)) icon = '📋';
                        else if (['doc', 'docx'].includes(ext)) icon = '📝';
                        else if (['xls', 'xlsx'].includes(ext)) icon = '📊';
                        else if (['ppt', 'pptx'].includes(ext)) icon = '📽️';
                        else if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(ext)) icon = '🖼️';
                        else if (['mp3', 'wav', 'ogg'].includes(ext)) icon = '🎵';
                        else if (['mp4', 'avi', 'mov'].includes(ext)) icon = '🎬';
                    }
                    
                    // Создаем HTML элемент в виде строки
                    const itemHTML = `
                        <span class="file-icon">${icon}</span>
                        <span class="file-name">${entry.name}</span>
                        <span class="file-type">${entry.is_dir ? 'Directory' : ext.toUpperCase() || 'File'}</span>
                        <span class="file-size">${entry.is_dir ? '-' : entry.size + ' bytes'}</span>
                        <span class="file-actions">
                            ${!entry.is_dir ? `<button class="download-btn" data-path="${entry.path}">Download</button>` : ''}
                            <button class="rename-btn" data-path="${entry.path}" data-name="${entry.name}">Rename</button>
                            <button class="delete-btn" data-path="${entry.path}">Delete</button>
                        </span>
                    `;
                    
                    itemDiv.innerHTML = itemHTML;
                    fileList.appendChild(itemDiv);

                    // Обработчик клика на элемент (для перехода в папку или открытия файла)
                    itemDiv.addEventListener('click', () => {
                        showPreview(entry.path, entry.name, entry.is_dir);
                    });

                    // Обработчик для скачивания
                    itemDiv.querySelector('.download-btn')?.addEventListener('click', (e) => {
                        e.stopPropagation();
                        window.location.href = `/files/download/${encodeURIComponent(entry.path)}`;
                    });

                    // Обработчик для переименования
                    itemDiv.querySelector('.rename-btn').addEventListener('click', (e) => {
                        e.stopPropagation();
                        const newName = prompt('Enter new name:', entry.name);
                        if (newName && newName.trim()) {
                            renameItem(entry.path, newName.trim());
                        }
                    });

                    // Обработчик для удаления
                    itemDiv.querySelector('.delete-btn').addEventListener('click', (e) => {
                        e.stopPropagation();
                        if (confirm(`Are you sure you want to delete "${entry.name}"?`)) {
                            fetch('/files/delete', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({path: entry.path})
                            }).then(response => {
                                if(response.ok) {
                                    listDirectory(currentPath, false);
                                } else {
                                    alert('Error deleting item');
                                }
                            }).catch(error => {
                                alert('Network error: ' + error.message);
                            });
                        }
                    });
                });
            }).catch(error => {
                console.error('Error loading directory:', error);
                alert('Error loading directory: ' + error.message);
            });
    }

    // Обработчик загрузки файлов
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        const formData = new FormData();
        for (let file of e.target.files) {
            formData.append('file', file);
        }
        formData.append('path', currentPath);

        fetch('/files/upload', {
            method: 'POST',
            body: formData
        }).then(response => {
            if(response.ok) {
                fileInput.value = '';
                listDirectory(currentPath, false);
            } else {
                alert('Error uploading file');
            }
        }).catch(error => {
            alert('Network error: ' + error.message);
        });
    });

    // Обработчик создания нового файла или папки
    createItemBtn.addEventListener('click', () => {
        const name = newItemNameInput.value.trim();
        if (!name) return;
        
        // Проверяем, содержит ли имя точку - если да, то это файл, иначе папка
        const isFile = name.includes('.');
        const fullPath = currentPath === '/' ? `/${name}` : `${currentPath}/${name}`;
        
        if (isFile) {
            // Создаем пустой файл
            fetch('/files/write', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    path: fullPath,
                    content: ''
                })
            }).then(response => {
                if(response.ok) {
                    newItemNameInput.value = '';
                    listDirectory(currentPath, false);
                } else {
                    alert('Error creating file');
                }
            }).catch(error => {
                alert('Network error: ' + error.message);
            });
        } else {
            // Создаем папку
            fetch('/files/mkdir', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: fullPath})
            }).then(response => {
                if(response.ok) {
                    newItemNameInput.value = '';
                    listDirectory(currentPath, false);
                } else {
                    alert('Error creating directory');
                }
            }).catch(error => {
                alert('Network error: ' + error.message);
            });
        }
    });

    // Инициализация: показываем содержимое корневой директории и диски
    updateNavButtons(); // Инициализируем кнопки навигации
    showDrives();
    addToHistory(currentPath); // Добавляем начальный путь в историю
    listDirectory(currentPath, false);
});