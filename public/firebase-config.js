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
/* Exam Darpan UI helpers — loaded once */
(function(){
  function load(src){
    if(document.querySelector('script[src="'+src+'"]')) return;

    const s=document.createElement('script');
    s.src=src;
    s.async=true;
    document.head.appendChild(s);
  }

  const path=location.pathname;

  if(
    path==='/admin/dashboard.html' ||
    path==='/admin/'
  ){
    load('/admin/quiz-controls.js');
  }

  if(
    path==='/' ||
    path==='/index.html' ||
    path===''
  ){
    load('/home-layout.js');
  }
})();
