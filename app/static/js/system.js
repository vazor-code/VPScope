document.addEventListener('DOMContentLoaded', function() {
    const cpuValue = document.getElementById('cpu-value');
    const ramValue = document.getElementById('ram-value');
    const diskValue = document.getElementById('disk-value');
    const cpuBar = document.getElementById('cpu-bar');
    const ramBar = document.getElementById('ram-bar');
    const diskBar = document.getElementById('disk-bar');

    // Дополнительные метрики
    const cpuCount = document.getElementById('cpu-count');
    const cpuFreq = document.getElementById('cpu-freq');
    const ramUsed = document.getElementById('ram-used');
    const ramTotal = document.getElementById('ram-total');
    const diskUsed = document.getElementById('disk-used');
    const diskTotal = document.getElementById('disk-total');
    const uptime = document.getElementById('uptime');
    const processesList = document.getElementById('processes-list');
    const disksList = document.getElementById('disks-list');
    const netSent = document.getElementById('net-sent');
    const netRecv = document.getElementById('net-recv');
    const tempDisplay = document.getElementById('temperature');

    // Кэш для подсчёта сети
    let lastNetSent = 0;
    let lastNetRecv = 0;
    let lastTime = Date.now();

    // Создаем график
    const ctx = document.getElementById('systemChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {  // ← Добавлено 'data:'
            labels: Array(10).fill(''),
            datasets: [
                {
                    label: 'CPU %',
                    data: Array(10).fill(0),  // ← Исправлено
                    borderColor: '#ff6b6b',
                    tension: 0.1
                },
                {
                    label: 'RAM %',
                    data: Array(10).fill(0),
                    borderColor: '#4ecdc4',
                    tension: 0.1
                },
                {
                    label: 'Disk %',
                    data: Array(10).fill(0),  // ← Исправлено
                    borderColor: '#ffa502',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'System Metrics Over Time'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatUptime(seconds) {
        const days = Math.floor(seconds / (3600 * 24));
        const hours = Math.floor((seconds % (3600 * 24)) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${days}d ${hours}h ${minutes}m`;
    }

    function fetchMetrics() {
        fetch('/system/metrics')
            .then(response => response.json())
            .then(data => {
                // Обновляем основные метрики
                cpuValue.textContent = `${data.cpu_percent.toFixed(1)}%`;
                ramValue.textContent = `${data.ram_percent.toFixed(1)}%`;
                diskValue.textContent = `${data.disk_percent.toFixed(1)}%`;

                // Обновляем прогресс-бары
                cpuBar.style.width = `${data.cpu_percent}%`;
                ramBar.style.width = `${data.ram_percent}%`;
                diskBar.style.width = `${data.disk_percent}%`;

                // Обновляем дополнительные метрики
                if (cpuCount) cpuCount.textContent = data.cpu_count;
                if (cpuFreq) cpuFreq.textContent = `${data.cpu_freq_current} MHz`;
                if (ramUsed) ramUsed.textContent = formatBytes(data.ram_used);
                if (ramTotal) ramTotal.textContent = formatBytes(data.ram_total);
                if (diskUsed) diskUsed.textContent = formatBytes(data.disk_used);
                if (diskTotal) diskTotal.textContent = formatBytes(data.disk_total);
                if (uptime) uptime.textContent = formatUptime(data.uptime_seconds);

                // Обновляем процессы
                if (processesList) {
                    processesList.innerHTML = '';
                    data.processes.forEach(proc => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${proc.pid}</td>
                            <td>${proc.name}</td>
                            <td>${proc.cpu_percent.toFixed(1)}%</td>
                            <td>${proc.memory_percent.toFixed(1)}%</td>
                        `;
                        processesList.appendChild(row);
                    });
                }

                // Обновляем диски
                if (disksList) {
                    disksList.innerHTML = '';
                    data.all_disks.forEach(disk => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${disk.device}</td>
                            <td>${disk.mountpoint}</td>
                            <td>${formatBytes(disk.used)}</td>
                            <td>${formatBytes(disk.total)}</td>
                            <td>${disk.percent}%</td>
                        `;
                        disksList.appendChild(row);
                    });
                }

                // Обновляем сеть (в байтах/с)
                const currentTime = Date.now();
                const timeDiff = (currentTime - lastTime) / 1000; // в секундах

                const sentRate = timeDiff > 0 ? (data.net_sent - lastNetSent) / timeDiff : 0;
                const recvRate = timeDiff > 0 ? (data.net_recv - lastNetRecv) / timeDiff : 0;

                if (netSent) netSent.textContent = formatBytes(sentRate) + '/s';
                if (netRecv) netRecv.textContent = formatBytes(recvRate) + '/s';

                lastNetSent = data.net_sent;
                lastNetRecv = data.net_recv;
                lastTime = currentTime;

                // Температура
                if (tempDisplay && Object.keys(data.temperatures).length > 0) {
                    tempDisplay.innerHTML = '';
                    for (const [name, sensors] of Object.entries(data.temperatures)) {
                        sensors.forEach(sensor => {
                            const div = document.createElement('div');
                            div.textContent = `${sensor.label}: ${sensor.current.toFixed(1)}°C`;
                            tempDisplay.appendChild(div);
                        });
                    }
                } else if (tempDisplay) {
                    tempDisplay.textContent = 'N/A';
                }

                // Обновляем график
                chart.data.datasets[0].data.push(data.cpu_percent);
                chart.data.datasets[1].data.push(data.ram_percent);
                chart.data.datasets[2].data.push(data.disk_percent);

                chart.data.labels.push('');
                if (chart.data.datasets[0].data.length > 10) {
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                    chart.data.datasets[2].data.shift();
                    chart.data.labels.shift();
                }

                chart.update();
            })
            .catch(error => {
                console.error('Error fetching metrics:', error);
            });
    }

    fetchMetrics();
    setInterval(fetchMetrics, 2000); // Обновлять каждые 2 секунды
});