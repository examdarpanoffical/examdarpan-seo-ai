const firebaseConfig = {
  apiKey: "AIzaSyAykRe0aekjneXG9DGzGxH6pnhh4RDKCVA",
  authDomain: "examdarpan-dd963.firebaseapp.com",
  projectId: "examdarpan-dd963",
  storageBucket: "examdarpan-dd963.firebasestorage.app",
  messagingSenderId: "1005840565643",
  appId: "1:1005840565643:web:8afd0a764d681e447c9b8e",
  measurementId: "G-98V5L1JSTX"
};
window.FIREBASE_CONFIG = firebaseConfig;

// Paste the reCAPTCHA Enterprise site key from Firebase App Check here.
window.FIREBASE_APPCHECK_SITE_KEY = "6LfY_pstAAAAADRIMq_NIwp6eYU_ss9hDOIqSgeG";

/* Exam Darpan Daily Test — live topper leaderboard loader */
(function(){
  if(location.pathname !== '/quiz') return;
  const load=()=>{
    if(document.querySelector('script[data-ed-leaderboard]')) return;
    const s=document.createElement('script');
    s.src='/quiz-leaderboard.js';
    s.async=true;
    s.dataset.edLeaderboard='1';
    document.head.appendChild(s);
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',load,{once:true});
  else load();
})();
