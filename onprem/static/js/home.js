(function() {
    // Admin dropdown toggle (inside sidebar)
    var toggle = document.querySelector('.admin-toggle');
    if (toggle) {
        var menu = toggle.parentElement.querySelector('.admin-menu');
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            menu.classList.toggle('open');
        });
    }
})();
