/* Runs before CSS to avoid a flash of the wrong theme. No account data is stored. */
(function () {
  'use strict';
  var key = 'foodlink-theme';
  var media = window.matchMedia('(prefers-color-scheme: dark)');
  function stored() { try { var value = localStorage.getItem(key); return value === 'dark' || value === 'light' ? value : null; } catch (_) { return null; } }
  function apply(value) {
    document.documentElement.setAttribute('data-bs-theme', value);
    document.documentElement.setAttribute('data-theme', value); // Django admin compatibility.
    document.documentElement.style.colorScheme = value;
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      var next = value === 'dark' ? 'light' : 'dark';
      button.hidden = false;
      button.setAttribute('aria-label', 'Switch to ' + next + ' mode');
      button.title = 'Switch to ' + next + ' mode';
      var label = button.querySelector('.theme-label');
      if (label) label.textContent = next === 'dark' ? 'Dark' : 'Light';
    });
  }
  apply(stored() || (media.matches ? 'dark' : 'light'));
  document.addEventListener('DOMContentLoaded', function () {
    apply(stored() || (media.matches ? 'dark' : 'light'));
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        var value = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, value); localStorage.setItem('theme', value); } catch (_) {}
        apply(value);
      });
    });
  });
  media.addEventListener('change', function (event) { if (!stored()) apply(event.matches ? 'dark' : 'light'); });
  window.addEventListener('storage', function (event) {
    if (event.key === key || event.key === null) apply(stored() || (media.matches ? 'dark' : 'light'));
  });
})();
