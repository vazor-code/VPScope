import psutil
import platform
import os
import time
from datetime import datetime
from threading import Lock

# Cache for metrics
_metrics_cache = None
_cache_timestamp = 0
_cache_lock = Lock()
_CACHE_TTL = 3  # seconds

def get_summary_metrics():
    global _metrics_cache, _cache_timestamp
    current_time = time.time()
    with _cache_lock:
        if _metrics_cache and (current_time - _cache_timestamp) < _CACHE_TTL:
            return _metrics_cache

    # CPU (non-blocking)
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    cpu_freq_current = cpu_freq.current if cpu_freq else 0
    cpu_freq_max = cpu_freq.max if cpu_freq else 0

    # RAM
    ram = psutil.virtual_memory()
    ram_used = ram.used
    ram_total = ram.total
    ram_percent = ram.percent

    # All disks and summary using psutil if possible, fallback to WMI on Windows
    all_disks = []
    summary_disk = None
    current_drive_letter = os.path.splitdrive(os.getcwd())[0].upper()  # e.g., 'D:'
    disk_used = 0
    disk_total = 0
    disk_percent = 0

    psutil_success = False
    try:
        disk_parts = psutil.disk_partitions()
        for part in disk_parts:
            usage = psutil.disk_usage(part.mountpoint)
            disk_info = {
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            }
            all_disks.append(disk_info)
            part_drive = os.path.splitdrive(part.mountpoint)[0].upper()
            if part_drive == current_drive_letter:
                summary_disk = disk_info
        psutil_success = True
    except:
        pass

    if not psutil_success or not summary_disk:
        # Fallback to WMI on Windows
        if platform.system() == 'Windows':
            try:
                import wmi
                import pythoncom
                pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
                c = wmi.WMI()
                # Get all fixed disks
                logical_disks = c.Win32_LogicalDisk(DriveType=3)  # 3 = fixed disk
                for disk in logical_disks:
                    device = disk.DeviceID
                    total = int(disk.Size) if disk.Size else 0
                    free = int(disk.FreeSpace) if disk.FreeSpace else 0
                    used = total - free
                    percent = (used / total * 100) if total > 0 else 0
                    fstype = disk.FileSystem or 'unknown'
                    disk_info = {
                        'device': device,
                        'mountpoint': device,
                        'fstype': fstype,
                        'total': total,
                        'used': used,
                        'free': free,
                        'percent': round(percent, 2)
                    }
                    all_disks.append(disk_info)
                    if device == current_drive_letter:
                        summary_disk = disk_info
                pythoncom.CoUninitialize()
            except ImportError:
                pass  # Silent
            except Exception as e:
                # Silent fail for WMI
                pass

    # Use summary_disk if found, else first disk or fallback
    if summary_disk:
        disk_used = summary_disk['used']
        disk_total = summary_disk['total']
        disk_percent = summary_disk['percent']
    elif all_disks:
        disk_used = all_disks[0]['used']
        disk_total = all_disks[0]['total']
        disk_percent = all_disks[0]['percent']
    else:
        disk_used = 0
        disk_total = 0
        disk_percent = 0

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

    # Processes (optimized: ad_value=0, limit to top 20)
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'], ad_value=0):
        try:
            info = proc.info
            name = info.get('name', '')
            if name == 'System Idle Process' or not name:
                continue
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by CPU and limit to top 20
    processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    processes = processes[:20]

    # Normalize CPU % if needed
    total_cpu = sum(p.get('cpu_percent', 0) for p in processes)
    if total_cpu > 100:
        for proc in processes:
            cpu_val = proc.get('cpu_percent', 0)
            proc['cpu_percent'] = (cpu_val / total_cpu) * 100 if total_cpu > 0 else 0

    total_cpu_processes = sum(p.get('cpu_percent', 0) for p in processes)

    # Temperatures (optimized with try-except)
    temps = {}
    if hasattr(psutil, "sensors_temperatures"):
        try:
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
        except:
            pass

    # Windows-specific WMI fallback for temperatures (with init)
    if platform.system() == 'Windows' and not temps:
        try:
            import wmi
            import pythoncom
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            c = wmi.WMI()
            # Try Win32_TemperatureProbe
            for probe in c.Win32_TemperatureProbe():
                if probe.CurrentReading:
                    current = (int(probe.CurrentReading) / 10.0) - 273.15
                    if 'TemperatureProbe' not in temps:
                        temps['TemperatureProbe'] = []
                    temps['TemperatureProbe'].append({
                        'label': probe.Name or 'Probe',
                        'current': round(current, 1),
                        'high': probe.MaxReadable or None,
                        'critical': probe.MinReadable or None
                    })
            # Try MSAcpi_ThermalZoneTemperature
            for tz in c.MSAcpi_ThermalZoneTemperature():
                if tz.CurrentTemperature:
                    current = (int(tz.CurrentTemperature) / 10.0) - 273.15
                    if 'ThermalZone' not in temps:
                        temps['ThermalZone'] = []
                    temps['ThermalZone'].append({
                        'label': 'System Zone',
                        'current': round(current, 1),
                        'high': None,
                        'critical': None
                    })
            pythoncom.CoUninitialize()
        except:
            pass  # Silent fail

    result = {
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
        'processes': processes,  # Already limited to 20
        'temperatures': temps,
        'os': platform.system(),
        'hostname': platform.node(),
        'machine': platform.machine(),
        'version': platform.version(),
        'total_cpu_processes': total_cpu_processes
    }

    # Cache the result
    with _cache_lock:
        _metrics_cache = result
        _cache_timestamp = current_time

    return result
