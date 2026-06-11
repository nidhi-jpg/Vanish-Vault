// Corner 3D: small animated glTF in bottom-right corner (non-intrusive)
(function(){
  const container = document.getElementById('corner3d');
  if(!container) return;

  // Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  const DPR = Math.min(window.devicePixelRatio || 1, 1.5);
  renderer.setPixelRatio(DPR);
  renderer.setClearColor(0x000000, 0);
  container.appendChild(renderer.domElement);
  // Ensure canvas fills container
  renderer.domElement.style.width = '100%';
  renderer.domElement.style.height = '100%';
  console.log('[corner3d] renderer initialized');

  // Scene & Camera
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(0, 0.6, 3.5);

  // Lights (soft)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x222233, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.6);
  dir.position.set(2, 3, 4);
  scene.add(dir);

  // Resize handler
  function resize(){
    const w = container.clientWidth;
    const h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix();
    console.log('[corner3d] resize', w, h);
  }
  resize();
  window.addEventListener('resize', resize);

  // Primitive-only mode (no GLTF). State holds just the torus.
  const STATE = { torus: null };

  // Animate
  const clock = new THREE.Clock();
  // Always-visible primitive (subtle)
  (function(){
    const geo = new THREE.TorusKnotGeometry(0.35, 0.12, 80, 12);
    const mat = new THREE.MeshStandardMaterial({ color: 0x22c55e, metalness: 0.1, roughness: 0.6, transparent: true, opacity: 0.45 });
    const tk = new THREE.Mesh(geo, mat);
    tk.position.set(0.6, 0.1, -0.2);
    scene.add(tk);
    STATE.torus = tk;
  })();
  function animate(){
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.05);
    if(STATE.torus){
      STATE.torus.rotation.x += 0.005;
      STATE.torus.rotation.y += 0.007;
    }
    renderer.render(scene, camera);
  }
  animate();
})();
