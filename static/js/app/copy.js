// Copy-to-clipboard for any <button data-copy="text">. Static file because the CSP forbids inline scripts.
document.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-copy]');
    if (!button) return;

    let copied = true;
    try {
        await navigator.clipboard.writeText(button.dataset.copy);
    } catch {
        // Clipboard API needs HTTPS (or localhost): fall back to the legacy copy command.
        const field = Object.assign(document.createElement('textarea'), {value: button.dataset.copy});
        document.body.append(field);
        field.select();
        copied = document.execCommand('copy');
        field.remove();
    }

    button.dataset.label ??= button.textContent;
    button.textContent = copied ? 'Copied!' : 'Copy failed';
    document.getElementById('copy-status').textContent = copied ? 'Link copied to clipboard' : 'Could not copy the link';
    setTimeout(() => { button.textContent = button.dataset.label; }, 2000);
});
