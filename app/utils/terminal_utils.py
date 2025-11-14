import subprocess
import threading

def run_command(cmd, emit):
    def runner(command):
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        for line in proc.stdout:
            emit('cmd_output', {'output': line.rstrip()})
        proc.wait()
        emit('cmd_output', {'exit': proc.returncode})

    # Запускаем в отдельном потоке
    thread = threading.Thread(target=runner, args=(cmd,))
    thread.daemon = True
    thread.start()
