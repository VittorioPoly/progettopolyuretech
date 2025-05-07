document.addEventListener('DOMContentLoaded', function() {
    // Toggle per il cambio tema
    const darkModeToggle = document.getElementById('darkModeToggle');
    const themeIcon = document.getElementById('theme-icon');
    
    // Gestisce il cambio tema
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            const theme = this.checked ? 'dark' : 'light';
            changeTheme(theme);
        });
    }
    
    function changeTheme(theme) {
        // Aggiorna icona
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        }
        
        // Cambia stylesheet
        const themeStyle = document.getElementById('theme-style');
        themeStyle.href = `/static/css/theme-${theme}.css`;
        
        // Salva preferenza
        fetch(`/change_theme/${theme}`);
        
        // Salva anche in localStorage come backup
        localStorage.setItem('theme', theme);
    }
    
    // Inizializza tooltip di Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Nascondi messaggi flash dopo 5 secondi
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Gestisci form di upload file per mostrare il nome del file selezionato
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0] ? e.target.files[0].name : '';
            const label = e.target.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName;
            }
        });
    });
});