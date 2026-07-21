document.addEventListener('DOMContentLoaded', () => {

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
});
