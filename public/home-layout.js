(function () {
  'use strict';

  function moveDailyQuiz() {
    const quiz = document.getElementById('daily-quiz');
    const notificationGrid = document.querySelector('main.main > .grid3');

    if (!quiz || !notificationGrid) return;

    // Existing quiz UI/content untouched — only its dashboard position changes.
    notificationGrid.insertAdjacentElement('afterend', quiz);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', moveDailyQuiz, { once: true });
  } else {
    moveDailyQuiz();
  }
})();
