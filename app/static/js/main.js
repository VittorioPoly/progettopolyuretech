// Funzioni di utilità generale
document.addEventListener('DOMContentLoaded', function() {
    // Inizializza i tooltip di Bootstrap se presenti
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Gestione della conferma per le azioni di eliminazione
    document.querySelectorAll('.delete-confirm').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm('Sei sicuro di voler eliminare questo elemento?')) {
                e.preventDefault();
            }
        });
    });

    // Gestione dei messaggi flash
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}); 