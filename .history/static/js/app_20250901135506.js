// Theme toggle with localStorage
(function(){
  const storageKey = 'vv-theme';
  const apply = (mode)=>{ document.documentElement.classList.toggle('dark', mode === 'dark'); };
  const stored = localStorage.getItem(storageKey);
  const initial = stored || 'dark';
  apply(initial);
  const btn = document.getElementById('themeToggle');
  if(btn){
    btn.addEventListener('click', ()=>{
      const next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
      localStorage.setItem(storageKey, next);
      apply(next);
      btn.textContent = next === 'dark' ? '🌙' : '☀️';
    });
    btn.textContent = document.documentElement.classList.contains('dark') ? '🌙' : '☀️';
  }
})();

// Simple reveal-on-scroll for cards
(function(){
  const els = document.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window)){
    els.forEach(e=>e.classList.add('show')); return;
  }
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(en=>{ if(en.isIntersecting){ en.target.classList.add('show'); io.unobserve(en.target); } });
  }, { threshold: .15 });
  els.forEach(e=>io.observe(e));
})();


