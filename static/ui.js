/* Keep navigation usable if the Bootstrap CDN script is blocked. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    if (window.bootstrap) return;
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(function (button) {
      button.addEventListener('click', function () {
        var panel = document.querySelector(button.getAttribute('data-bs-target'));
        if (!panel) return;
        var open = panel.classList.toggle('show');
        button.setAttribute('aria-expanded', String(open));
      });
    });
    document.querySelectorAll('[data-bs-dismiss="alert"]').forEach(function (button) {
      button.addEventListener('click', function () { var alert = button.closest('.alert'); if (alert) alert.remove(); });
    });
  });
})();
