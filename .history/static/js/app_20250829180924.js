// Theme toggle with localStorage
(function(){
  const storageKey = 'vv-theme';
  const apply = (mode)=>{ document.documentElement.classList.toggle('dark', mode === 'dark'); };
  const current = localStorage.getItem(storageKey) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  apply(current);
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


