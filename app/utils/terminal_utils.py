import subprocess
import threading
import shlex

def run_command(cmd, emit_func):
    def runner(command):
        try:
            # Enhanced validation to block shell injection and dangerous commands
            if any(char in command for char in [';', '&', '|', '(', ')', '[', ']', '{', '}', '<', '>', '^', '"', "'", '`']):
                emit_func('cmd_output', {'output': 'Command blocked: shell metacharacters not allowed.'})
                return
            if any(dangerous in command.lower() for dangerous in ['rm -rf', 'del /f /q /s', 'format', 'fdisk', 'mkfs', 'dd if=']):
                emit_func('cmd_output', {'output': 'Command blocked for security reasons.'})
                return

            # Use shell=True for Windows compatibility with built-ins, but validated
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, bufsize=1, text=True, universal_newlines=True)
            for line in proc.stdout:
                emit_func('cmd_output', {'output': line.rstrip()})
            proc.wait()
            emit_func('cmd_output', {'exit': proc.returncode})
        except Exception as e:
            emit_func('cmd_output', {'output': f'Error: {str(e)}', 'exit': -1})

    # Run in separate thread
    thread = threading.Thread(target=runner, args=(cmd,))
    thread.daemon = True
    thread.start()
