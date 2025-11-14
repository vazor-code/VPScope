import psutil
import platform
from datetime import datetime

def get_summary_metrics():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    cpu_freq_current = cpu_freq.current if cpu_freq else 0
    cpu_freq_max = cpu_freq.max if cpu_freq else 0

    # RAM
    ram = psutil.virtual_memory()
    ram_used = ram.used
    ram_total = ram.total
    ram_percent = ram.percent

    # Disk
    disk = psutil.disk_usage('/')
    disk_used = disk.used
    disk_total = disk.total
    disk_percent = disk.percent

    # Все диски
    disk_parts = psutil.disk_partitions()
    all_disks = []
    for part in disk_parts:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            all_disks.append({
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            })
        except:
            continue

    # Network
    net = psutil.net_io_counters()
    net_sent = net.bytes_sent
    net_recv = net.bytes_recv

    # Boot time
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.now() - boot_time).total_seconds()

    # Load average (Linux only)
    load_avg = None
    if platform.system() != 'Windows':
        load_avg = psutil.getloadavg()

    # Processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            # Пропускаем System Idle Process
            if info['name'] == 'System Idle Process':
                continue
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Сортируем по CPU
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

    # Нормализуем CPU % процессов, чтобы сумма не превышала 100%
    total_cpu = sum(p['cpu_percent'] for p in processes)
    if total_cpu > 100:
        for proc in processes:
            proc['cpu_percent'] = (proc['cpu_percent'] / total_cpu) * 100

    # Добавляем сумму CPU процессов в метрики
    total_cpu_processes = sum(p['cpu_percent'] for p in processes)

    # Temperature (если доступна)
    temps = {}
    if hasattr(psutil, "sensors_temperatures"):
        temp_data = psutil.sensors_temperatures()
        if temp_data:
            for name, entries in temp_data.items():
                temps[name] = []
                for entry in entries:
                    temps[name].append({
                        'label': entry.label or name,
                        'current': entry.current,
                        'high': entry.high,
                        'critical': entry.critical
                    })

    return {
        'cpu_percent': cpu_percent,
        'cpu_count': cpu_count,
        'cpu_freq_current': round(cpu_freq_current, 2),
        'cpu_freq_max': round(cpu_freq_max, 2),
        'ram_used': ram_used,
        'ram_total': ram_total,
        'ram_percent': ram_percent,
        'disk_used': disk_used,
        'disk_total': disk_total,
        'disk_percent': disk_percent,
        'all_disks': all_disks,
        'net_sent': net_sent,
        'net_recv': net_recv,
        'boot_time': boot_time.isoformat(),
        'uptime_seconds': int(uptime_seconds),
        'load_avg': load_avg,
        'processes': processes[:20],
        'temperatures': temps,
        'os': platform.system(),
        'hostname': platform.node(),
        'machine': platform.machine(),
        'version': platform.version(),
        'total_cpu_processes': total_cpu_processes  # ← Добавлено
    }
