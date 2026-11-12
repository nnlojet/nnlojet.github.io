// Copy buttons for the code blocks of the HTML manual.
// For shell examples only the commands are copied, without "$ " prompts and output.
function codeToCopy(text) {
    const lines = text.replace(/^\n/, '').replace(/\n$/, '').split('\n');
    if (!lines.some(line => /^\s*\$ /.test(line))) {
        return lines.join('\n');
    }
    const commands = [];
    let continued = false;
    for (const line of lines) {
        const prompt = line.match(/^\s*\$ (.*)$/);
        if (prompt || continued) {
            const command = prompt ? prompt[1] : line;
            commands.push(command);
            continued = /\\$/.test(command);
        }
    }
    return commands.join('\n');
}

document.querySelectorAll('pre.programlisting').forEach(pre => {
    const block = document.createElement('div');
    block.className = 'codeblock';
    pre.parentNode.insertBefore(block, pre);
    block.appendChild(pre);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy';
    button.textContent = 'Copy';
    button.addEventListener('click', () => {
        navigator.clipboard.writeText(codeToCopy(pre.textContent)).then(
            () => { button.textContent = 'Copied'; },
            () => { button.textContent = 'Copy failed'; });
        setTimeout(() => { button.textContent = 'Copy'; }, 1500);
    });
    block.appendChild(button);
});
