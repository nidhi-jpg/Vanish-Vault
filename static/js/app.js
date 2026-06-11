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

// Count-up animation for statistics
(function(){
  const counters = document.querySelectorAll('.stat-number[data-count]');
  if(!counters.length) return;
  const ease = t => 1 - Math.pow(1 - t, 3);
  const animate = el => {
    const target = parseInt(el.getAttribute('data-count') || '0', 10);
    const dur = 1200; // ms
    const start = performance.now();
    const fmt = n => new Intl.NumberFormat().format(n);
    const tick = (now) => {
      const p = Math.min(1, (now - start) / dur);
      const val = Math.floor(ease(p) * target);
      el.textContent = fmt(val);
      if(p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  if('IntersectionObserver' in window){
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(en=>{
        if(en.isIntersecting){ animate(en.target); io.unobserve(en.target); }
      });
    }, { threshold: .2 });
    counters.forEach(c=>io.observe(c));
  } else {
    counters.forEach(animate);
  }
})();

// Ripple effect for buttons
(function(){
  document.addEventListener('click', function(e){
    const target = e.target.closest('.btn');
    if(!target) return;
    const rect = target.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
    ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
    target.appendChild(ripple);
    setTimeout(()=> ripple.remove(), 600);
  }, false);
})();

