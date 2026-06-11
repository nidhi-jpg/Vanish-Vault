// Three.js 3D background - lightweight and subtle
(function(){
  const container = document.getElementById('bg3d');
  if(!container){ return; }

  // Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  const DPR = Math.min(window.devicePixelRatio || 1, 1.25);
  renderer.setPixelRatio(DPR);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0); // transparent
  container.appendChild(renderer.domElement);

  // Scene & Camera
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 8);

  // Lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambient);
  const point = new THREE.PointLight(0x00ffb2, 0.8);
  point.position.set(4, 6, 8);
  scene.add(point);

  // Minimal scene (no centerpiece) to reduce distraction

  // Particles (smaller, softer)
  const starCount = 600;
  const positions = new Float32Array(starCount * 3);
  for (let i = 0; i < starCount; i++) {
    const r = 18 * Math.pow(Math.random(), 0.6) + 6; // bias outward
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    positions[i*3+0] = r * Math.sin(phi) * Math.cos(theta);
    positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i*3+2] = r * Math.cos(phi);
  }
  const starsGeo = new THREE.BufferGeometry();
  starsGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const starsMat = new THREE.PointsMaterial({ size: 0.02, color: 0xffffff, transparent: true, opacity: 0.28 });
  const stars = new THREE.Points(starsGeo, starsMat);
  scene.add(stars);

  // Few small glowing orbs moving on smooth, slow paths
  const orbs = [], orbData = [];
  const orbColors = [0x00ffb2, 0xffd369, 0x38bdf8];
  for (let i = 0; i < 4; i++) {
    const baseR = 2 + Math.random() * 1.2;
    const g2 = new THREE.SphereGeometry(0.06 + Math.random() * 0.04, 20, 20);
    const c = orbColors[i % orbColors.length];
    const m2 = new THREE.MeshStandardMaterial({
      color: c,
      emissive: c,
      emissiveIntensity: 0.5,
      metalness: 0.12,
      roughness: 0.45,
      transparent: true,
      opacity: 0.6
    });
    const orb = new THREE.Mesh(g2, m2);
    scene.add(orb);
    orbs.push(orb);
    orbData.push({
      ax: 0.15 + Math.random() * 0.2,
      ay: 0.15 + Math.random() * 0.2,
      az: 0.15 + Math.random() * 0.2,
      rx: baseR * (0.9 + Math.random() * 0.3),
      ry: baseR * (0.8 + Math.random() * 0.3),
      rz: baseR * (0.9 + Math.random() * 0.3),
      phase: Math.random() * Math.PI * 2
    });
  }

  // Mouse parallax
  const mouse = { x: 0, y: 0 };
  window.addEventListener('mousemove', (e) => {
    const nx = (e.clientX / window.innerWidth) * 2 - 1;
    const ny = (e.clientY / window.innerHeight) * 2 - 1;
    mouse.x = nx; mouse.y = ny;
  }, { passive: true });

  // Resize
  function onResize(){
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', onResize);

  // Animate
  let t = 0;
  function animate(){
    requestAnimationFrame(animate);
    t += 0.003;

    // Gentle camera parallax
    camera.position.x += ((mouse.x * 0.6) - camera.position.x) * 0.02;
    camera.position.y += ((-mouse.y * 0.6) - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);

    // Subtle particle drift (slower)
    stars.rotation.y += 0.0004;
    stars.rotation.x += 0.00015;

    // Move orbs along slow lissajous-like paths with slight pulsation
    for (let i = 0; i < orbs.length; i++) {
      const d = orbData[i];
      const tt = t * 0.6 + d.phase;
      orbs[i].position.set(
        Math.sin(tt * (1.0 + d.ax)) * d.rx,
        Math.cos(tt * (1.1 + d.ay)) * d.ry,
        Math.sin(tt * (0.9 + d.az)) * d.rz
      );
      const s = 0.98 + Math.sin(tt * 1.2) * 0.02;
      orbs[i].scale.set(s, s, s);
    }

    renderer.render(scene, camera);
  }
  animate();
})();
