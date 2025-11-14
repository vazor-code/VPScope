import psutil
import platform
from datetime import datetime

def get_summary_metrics():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)  # Интервал важен для точности
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

    # Network
    net = psutil.net_io_counters()
    net_sent = net.bytes_sent
    net_recv = net.bytes_recv

    # Boot time
    boot_time = datetime.fromtimestamp(psutil.boot_time())

    # Uptime
    uptime_seconds = (datetime.now() - boot_time).total_seconds()

    # Load average (Linux only)
    load_avg = None
    if platform.system() != 'Windows':
        load_avg = psutil.getloadavg()

    # Processes
    processes_count = len(psutil.pids())

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
        'net_sent': net_sent,
        'net_recv': net_recv,
        'boot_time': boot_time.isoformat(),
        'uptime_seconds': int(uptime_seconds),
        'load_avg': load_avg,
        'processes_count': processes_count,
        'os': platform.system(),
        'hostname': platform.node(),
        'machine': platform.machine(),
        'version': platform.version()
    }
