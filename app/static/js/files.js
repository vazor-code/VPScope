document.addEventListener('DOMContentLoaded', function() {
    const fileList = document.getElementById('file-list');
    const currentPathDiv = document.getElementById('current-path');
    const uploadBtn = document.getElementById('upload-btn');
    const mkdirBtn = document.getElementById('mkdir-btn');
    const fileInput = document.getElementById('file-input');
    const newDirNameInput = document.getElementById('new-dir-name');

    let currentPath = '/';

    function listDirectory(path) {
        fetch(`/files/list?path=${encodeURIComponent(path)}`)
            .then(response => response.json())
            .then(data => {
                currentPathDiv.textContent = data.path;
                currentPath = data.path;
                fileList.innerHTML = '';
                data.entries.forEach(entry => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `file-item ${entry.is_dir ? 'directory' : 'file'}`;
                    itemDiv.innerHTML = `
                        <span>${entry.is_dir ? '📁' : '📄'}</span>
                        <div>
                            <strong>${entry.name}</strong>
                            <small>${entry.is_dir ? 'Directory' : `Size: ${entry.size} bytes`}</small>
                        </div>
                        <div class="file-actions">
                            ${!entry.is_dir ? `<button class="download-btn" data-path="${entry.path}">Download</button>` : ''}
                            <button class="delete-btn" data-path="${entry.path}">Delete</button>
                        </div>
                    `;
                    fileList.appendChild(itemDiv);

                    // Добавляем обработчик для директорий
                    if (entry.is_dir) {
                        itemDiv.querySelector('div').addEventListener('click', () => listDirectory(entry.path));
                    }

                    // Обработчик для скачивания
                    itemDiv.querySelector('.download-btn')?.addEventListener('click', (e) => {
                        e.stopPropagation();
                        window.location.href = `/files/download/${encodeURIComponent(entry.name)}`;
                    });

                    // Обработчик для удаления
                    itemDiv.querySelector('.delete-btn').addEventListener('click', (e) => {
                        e.stopPropagation();
                        if (confirm(`Are you sure you want to delete "${entry.name}"?`)) {
                            fetch('/files/delete', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({path: entry.path})
                            }).then(() => listDirectory(currentPath));
                        }
                    });
                });
            });
    }

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
        }).then(() => {
            fileInput.value = '';
            listDirectory(currentPath);
        });
    });

    mkdirBtn.addEventListener('click', () => {
        const name = newDirNameInput.value.trim();
        if (!name) return;
        const fullPath = currentPath === '/' ? `/${name}` : `${currentPath}/${name}`;
        fetch('/files/mkdir', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path: fullPath})
        }).then(() => {
            newDirNameInput.value = '';
            listDirectory(currentPath);
        });
    });

    listDirectory(currentPath);
});