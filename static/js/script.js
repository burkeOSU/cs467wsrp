document.addEventListener('DOMContentLoaded', () => {
    // For security toggle buttons
    const buttons = document.querySelectorAll('.toggleBtn');
    const securitySelection = document.getElementById('securityChoice');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            // 1. Remove the 'selected' class from all buttons 
            buttons.forEach(btn => {
                btn.classList.remove('selected');
                btn.disabled = false;
            });
            
            // 2. Add the 'selected' class to clicked button and disable it
            button.classList.add('selected');
            button.disabled = true;

            // 3. Update hidden input value to match selected button
            securitySelection.value = button.getAttribute('data-value');
        });
    });

    // For hint/explanation buttons
    const hintButtons = document.querySelectorAll('.hintBtn');
    const contents = document.querySelectorAll('.content');

    hintButtons.forEach(hintBtn => {
        hintBtn.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const contentTarget = document.getElementById(target);
            // If content is already displayed, hide it
            if (contentTarget.classList.contains('show')) {
                contentTarget.classList.remove('show');
                return;
            }
            // Otherwise hide all contents
            contents.forEach(content => content.classList.remove('show'));
            // Show only the targeted panel
            contentTarget.classList.add('show');
        });
    });
});
