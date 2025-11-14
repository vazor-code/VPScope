document.addEventListener('DOMContentLoaded', function() {
    const output = document.getElementById('terminal-output');
    const input = document.getElementById('terminal-input');
    const socket = io('http://' + document.domain + ':' + location.port + '/terminal');

    socket.on('connect', function() {
        output.innerHTML += '$ Connected to server\n';
    });

    socket.on('cmd_output', function(data) {
        if (data.output) output.innerHTML += data.output + '\n';
        if (data.exit !== undefined) output.innerHTML += `[Process finished with code ${data.exit}]\n`;
        output.scrollTop = output.scrollHeight;
    });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const command = input.value;
            output.innerHTML += '$ ' + command + '\n';
            socket.emit('run_command', {command: command});
            input.value = '';
        }
    });

    // Фокус на ввод при клике по выводу
    output.addEventListener('click', () => input.focus());
});