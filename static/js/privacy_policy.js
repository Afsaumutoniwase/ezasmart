// Privacy policy checkbox color and blocking logic

document.addEventListener('DOMContentLoaded', function() {
    const checkbox = document.getElementById('privacy_policy');
    if (!checkbox){
        console.log('Privacy policy checkbox not found!');
    }

    // Set initial color
    updateCheckboxColor();
    checkbox.addEventListener('change', updateCheckboxColor);

    // Block form submission if not checked
    const registerForm = document.querySelector('.register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            if (!checkbox.checked) {
                e.preventDefault();
                checkbox.focus();
                updateCheckboxColor();
                alert('You must agree to the Privacy Policy to create an account.');
            }
        });
    }

    function updateCheckboxColor() {
        if (checkbox.checked) {
            checkbox.style.accentColor = '#28a745'; // green
        } else {
            checkbox.style.accentColor = '#1976d2'; // blue (default)
        }
    }
});
