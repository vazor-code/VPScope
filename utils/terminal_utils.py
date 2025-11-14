import subprocess
import eventlet

def run_command(cmd, emit):
    def runner(command):
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        for line in proc.stdout:
            emit('cmd_output', {'output': line})
        proc.wait()
        emit('cmd_output', {'exit': proc.returncode})

    eventlet.spawn(runner, cmd)
