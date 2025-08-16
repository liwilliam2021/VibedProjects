/**
 * sprites.js
 * Canvas sprite system with:
 *  - Atlas support (PNG/data URL) for frame-based animation
 *  - Procedural fallback for enemies and towers (unique, seeded variations)
 *  - Tower portraits generator for HUD and buttons
 *
 * Enemy builtin atlases (demo): conscript, rifleman (generated at runtime as PNG data URLs)
 * Towers use procedural states: idle, attack
 */
(function () {
  const Sprites = {};
  window.Sprites = Sprites;

  // --- Utilities ---
  function mulberry32(a) {
    return function () {
      let t = (a += 0x6D2B79F5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function seededRandom(seed) {
    return mulberry32(seed >>> 0);
  }
  function clamp(v, a, b) {
    return Math.max(a, Math.min(b, v));
  }
  function hsl(h, s, l, a = 1) {
    return `hsla(${((h % 360) + 360) % 360},${clamp(s,0,100)}%,${clamp(l,0,100)}%,${a})`;
  }
  // Simple string hash for stable variant seeds (wiki portraits)
  function strHash(s) {
    let h = 0 >>> 0;
    for (let i = 0; i < s.length; i++) {
      h = (Math.imul(h, 31) + s.charCodeAt(i)) >>> 0;
    }
    return h >>> 0;
  }

  // --- Registry for external atlases (future-proof) ---
  const atlasRegistry = new Map();
  Sprites.registerAtlas = function registerAtlas(kind, imageUrl, meta) {
    // meta: { frameW, frameH, fps, originX, originY, states: { move: [{x,y}, ...], ... } }
    atlasRegistry.set(kind, { imageUrl, meta, image: null, loading: false, error: null });
  };

  // Load image helper
  function loadImage(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = url;
    });
  }

  async function ensureAtlasLoaded(kind) {
    const entry = atlasRegistry.get(kind);
    if (!entry) return null;
    if (entry.image) return entry;
    if (entry.loading) {
      while (entry.loading && !entry.image && !entry.error) {
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, 10));
      }
      return entry.image ? entry : null;
    }
    entry.loading = true;
    try {
      entry.image = await loadImage(entry.imageUrl);
    } catch (e) {
      entry.error = e;
    } finally {
      entry.loading = false;
    }
    return entry.image ? entry : null;
  }

  // --- Procedural Enemy Walk Cycle Generator ---
  const procFramesCache = new Map(); // key: kind|variantSeed|size|category

  const ENEMY_BASE_STYLES = {
    conscript:  { bodyH: 18, hue: 45,  sat: 30, light: 50, gearHue: 20,  accentHue: 15 },
    rifleman:   { bodyH: 18, hue: 210, sat: 35, light: 52, gearHue: 200, accentHue: 180 },
    overseer:   { bodyH: 18, hue: 15,  sat: 5,  light: 88, gearHue: 0,   accentHue: 45 },
    mercenary:  { bodyH: 18, hue: 15,  sat: 30, light: 35, gearHue: 25,  accentHue: 350 },
    officer:    { bodyH: 18, hue: 15,  sat: 12, light: 75, gearHue: 35,  accentHue: 45 },
    steamExo:   { bodyH: 20, hue: 30,  sat: 25, light: 40, gearHue: 25,  accentHue: 15 },
    clockworkBehemoth: { bodyH: 22, hue: 30, sat: 24, light: 38, gearHue: 35, accentHue: 15 },
    steamTank:  { bodyH: 22, hue: 30,  sat: 35, light: 35, gearHue: 25,  accentHue: 10 },
  };

  function generateEnemyFrames(kind, variantSeed, size = 32) {
    const cacheKey = `enemy|${kind}|${variantSeed}|${size}`;
    if (procFramesCache.has(cacheKey)) return procFramesCache.get(cacheKey);

    const style = ENEMY_BASE_STYLES[kind] || ENEMY_BASE_STYLES.conscript;
    const rng = seededRandom(variantSeed);

    const frames = [];
    const frameCount = 6;
    const fps = 8;
    const w = size;
    const h = size;
    const originX = Math.floor(w * 0.5);
    const originY = Math.floor(h * 0.75);

    // Palette variation
    const bodyHue = clamp(style.hue + Math.floor(rng() * 20 - 10), 0, 360);
    const bodyCol = hsl(bodyHue, style.sat, style.light);
    const gearCol = hsl(style.gearHue, 35, 40);
    const accentCol = hsl(style.accentHue, 65, 55);

    // Accessory selection
    const hat = rng() < 0.55;
    const sash = rng() < 0.35;
    const backpack = rng() < 0.25;
    const plume = rng() < 0.18 && (kind === 'officer' || kind === 'rifleman');

    for (let i = 0; i < frameCount; i++) {
      const walkPhase = (i / frameCount) * Math.PI * 2;
      const bob = Math.sin(walkPhase) * 1.0;
      const legSwing = Math.sin(walkPhase) * 3;
      const armSwing = -Math.sin(walkPhase) * 3;

      const cv = document.createElement('canvas');
      cv.width = w;
      cv.height = h;
      const c = cv.getContext('2d');

      c.save();
      c.translate(Math.floor(w * 0.5), Math.floor(h * 0.5) + bob);

      if (kind === 'steamTank') {
        // Simple tank silhouette with wheels and puff
        c.save();
        c.fillStyle = gearCol;
        c.fillRect(-10, -4, 20, 10);
        c.fillStyle = bodyCol;
        c.fillRect(-12, -8, 24, 8);
        // Wheels
        c.fillStyle = hsl(0, 0, 15);
        c.beginPath(); c.arc(-7, 6, 4, 0, Math.PI * 2); c.fill();
        c.beginPath(); c.arc(7, 6, 4, 0, Math.PI * 2); c.fill();
        // Smoke puff
        if (i % 2 === 0) {
          c.fillStyle = 'rgba(200,200,200,0.6)';
          c.beginPath(); c.arc(8, -12, 3, 0, Math.PI * 2); c.fill();
        }
        c.restore();
      } else if (kind === 'clockworkBehemoth') {
        // Big automaton with saw arms
        c.save();
        c.fillStyle = bodyCol;
        c.fillRect(-8, -10, 16, 18);
        c.fillStyle = gearCol;
        c.fillRect(-6, -16, 12, 6);
        // Saw arms
        c.strokeStyle = accentCol; c.lineWidth = 3;
        c.beginPath(); c.moveTo(-8, -2); c.lineTo(-14, -2 + armSwing * 0.1); c.stroke();
        c.beginPath(); c.moveTo(8, -2); c.lineTo(14, -2 - armSwing * 0.1); c.stroke();
        c.restore();
      } else if (kind === 'steamExo') {
        // Exo-suit bulky shape
        c.save();
        c.fillStyle = gearCol;
        c.fillRect(-7, -10, 14, 16);
        c.fillStyle = bodyCol;
        c.fillRect(-5, -14, 10, 6);
        // Pistons (animated)
        c.strokeStyle = accentCol; c.lineWidth = 2;
        c.beginPath(); c.moveTo(-6, 2); c.lineTo(-10, 4 + legSwing * 0.1); c.stroke();
        c.beginPath(); c.moveTo(6, 2); c.lineTo(10, 4 - legSwing * 0.1); c.stroke();
        c.restore();
      } else {
        // Humanoid basic body
        c.save();
        // legs
        c.strokeStyle = hsl(bodyHue, 25, 15); c.lineWidth = 3;
        c.beginPath(); c.moveTo(-3, 8); c.lineTo(-3, 8 + legSwing); c.stroke();
        c.beginPath(); c.moveTo(3, 8); c.lineTo(3, 8 - legSwing); c.stroke();
        // torso
        c.fillStyle = bodyCol;
        c.fillRect(-5, -8, 10, 12);
        // arms
        c.strokeStyle = hsl(bodyHue, 30, 25); c.lineWidth = 2;
        c.beginPath(); c.moveTo(-6, -6); c.lineTo(-10, -6 + armSwing); c.stroke();
        c.beginPath(); c.moveTo(6, -6); c.lineTo(10, -6 - armSwing); c.stroke();

        // accessory layers
        if (sash) {
          c.fillStyle = accentCol;
          c.save();
          c.rotate(-0.5);
          c.fillRect(-6, -2, 12, 3);
          c.restore();
        }
        if (backpack) {
          c.fillStyle = gearCol;
          c.fillRect(-6, -10, 4, 6);
        }
        if (hat) {
          c.fillStyle = gearCol;
          c.fillRect(-6, -12, 12, 3);
          c.fillRect(-4, -15, 8, 4);
        }
        if (plume) {
          c.strokeStyle = hsl((bodyHue + 140) % 360, 70, 60);
          c.lineWidth = 2;
          c.beginPath(); c.moveTo(0, -15); c.lineTo(0, -20); c.stroke();
        }
        c.restore();
      }
      c.restore();
      frames.push(cv);
    }

    const packet = { frames, fps, originX, originY, w, h };
    procFramesCache.set(cacheKey, packet);
    return packet;
  }

  // --- Procedural Tower Sprite Generator (idle + attack) ---
  function getTowerBaseColor(towerType) {
    const map = {
      RaptorNest:  [135, 50, 55],
      Protoceratops: [110, 40, 50],
      Triceratops: [95, 35, 50],
      Brachiosaurus: [130, 35, 48],
      Dilophosaurus: [230, 45, 60],
      Stegosaurus: [25, 45, 55],
      Iguanodon: [100, 40, 48],
      Maiasaura: [95, 45, 58],
      Stonklodon: [45, 80, 55],
      TRex: [10, 55, 55],
      Spinosaurus: [180, 55, 50],
      Pteranodon: [35, 30, 65],
      Ankylosaurus: [25, 25, 50],
      Dreadnoughtus: [120, 30, 45],
      Quetzalcoatlus: [200, 25, 70]
    };
    return map[towerType] || [140, 20, 60];
  }

  function drawTowerSilhouette(c, size, towerType, phase = 0, mode = 'idle') {
    // Performance constants
    const MAX_SHAPES_PER_TYPE = 9;
    const USE_INTEGER_COORDS = true;
    
    const [hue, sat, light] = getTowerBaseColor(towerType);
    const body = hsl(hue, sat, light);
    const accent = hsl((hue + 40) % 360, sat + 10, clamp(light + 10, 0, 100));
    const detail = hsl((hue + 20) % 360, sat - 10, clamp(light - 10, 0, 100));
    const bob = mode === 'idle' ? Math.sin(phase) * 1.0 : Math.sin(phase * 2) * 0.5;

    c.save();
    c.translate(Math.floor(size / 2), Math.floor(size / 2 + bob));

    c.fillStyle = body;

    switch (towerType) {
      case 'RaptorNest':
        // Enhanced RaptorNest with nest twigs, egg crack, peeking eyes
        // Nest base
        c.beginPath(); c.arc(0, 8, 14, 0, Math.PI * 2); c.fill();
        
        // Three nest twigs (thin rectangles around base)
        c.fillStyle = detail;
        c.save();
        c.translate(0, 8);
        c.rotate(-0.3);
        c.fillRect(-12, -1, 24, 2);
        c.restore();
        c.save();
        c.translate(0, 8);
        c.rotate(0.3);
        c.fillRect(-12, -1, 24, 2);
        c.restore();
        c.fillRect(-10, 6, 20, 2);
        
        // Egg
        c.fillStyle = accent;
        c.beginPath();
        c.ellipse(0, -2, 8, 10 + (mode==='attack'?1:0), 0, 0, Math.PI * 2);
        c.fill();
        
        // Egg crack hint (zigzag line)
        c.strokeStyle = detail;
        c.lineWidth = 1;
        c.beginPath();
        c.moveTo(-3, -2);
        c.lineTo(-1, 0);
        c.lineTo(1, -2);
        c.lineTo(3, 0);
        c.stroke();
        
        // Two peeking eyes in the egg
        c.fillStyle = 'black';
        c.beginPath(); c.arc(-2, -4, 1, 0, Math.PI * 2); c.fill();
        c.beginPath(); c.arc(2, -4, 1, 0, Math.PI * 2); c.fill();
        break;
      case 'Triceratops':
        // Enhanced Triceratops with triangular horns, frill arc, and eye
        // Main body
        c.beginPath(); c.ellipse(0, 4, 12, 10, 0, 0, Math.PI * 2); c.fill();
        
        // Frill arc (behind head)
        c.fillStyle = accent;
        c.beginPath();
        c.arc(0, -4, 14, Math.PI * 1.2, Math.PI * 1.8);
        c.arc(0, -4, 10, Math.PI * 1.8, Math.PI * 1.2, true);
        c.closePath();
        c.fill();
        
        // Head
        c.fillStyle = body;
        c.beginPath(); c.arc(0, -2, 8, 0, Math.PI * 2); c.fill();
        
        // Three triangular horns
        c.fillStyle = detail;
        // Center horn (nasal)
        c.beginPath();
        c.moveTo(0, -4);
        c.lineTo(-2, 0);
        c.lineTo(2, 0);
        c.closePath();
        c.fill();
        // Left brow horn
        c.beginPath();
        c.moveTo(-5, -6 + (mode==='attack' ? -1 : 0));
        c.lineTo(-7, -2);
        c.lineTo(-3, -2);
        c.closePath();
        c.fill();
        // Right brow horn
        c.beginPath();
        c.moveTo(5, -6 + (mode==='attack' ? -1 : 0));
        c.lineTo(3, -2);
        c.lineTo(7, -2);
        c.closePath();
        c.fill();
        
        // Eye
        c.fillStyle = 'rgba(255,255,255,0.8)';
        c.beginPath(); c.arc(-3, -2, 2, 0, Math.PI * 2); c.fill();
        c.fillStyle = 'black';
        c.beginPath(); c.arc(-3, -2, 1, 0, Math.PI * 2); c.fill();
        break;
      case 'Brachiosaurus':
        // Enhanced Brachiosaurus with columnar legs, tail, nasal crest
        // Body
        c.beginPath(); c.ellipse(0, 6, 14, 10, 0, 0, Math.PI * 2); c.fill();
        
        // Two columnar legs (visible)
        c.fillStyle = detail;
        c.fillRect(-8, 10, 5, 6);
        c.fillRect(3, 10, 5, 6);
        
        // Long neck
        c.fillStyle = body;
        c.fillRect(-3, -8, 6, 14);
        
        // Head with nasal crest bump
        c.beginPath();
        c.arc(4, -10 + (mode==='attack'? -1:0), 6, 0, Math.PI * 2);
        c.fill();
        
        // Nasal crest bump
        c.fillStyle = accent;
        c.beginPath();
        c.arc(6, -12 + (mode==='attack'? -1:0), 3, Math.PI * 1.2, Math.PI * 0.2);
        c.fill();
        
        // Tail
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-10, 4);
        c.lineTo(-14, 8);
        c.lineTo(-12, 10);
        c.lineTo(-8, 6);
        c.closePath();
        c.fill();
        break;
      case 'Dilophosaurus':
        // Enhanced Dilophosaurus with dual head crests, beak-like snout, tail
        // Body
        c.fillRect(-10, 0, 20, 10);
        
        // Head with beak-like snout
        c.fillStyle = body;
        c.beginPath();
        c.arc(8, -4, 6, 0, Math.PI * 2);
        c.fill();
        
        // Beak-like snout
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(12, -4);
        c.lineTo(15 + (mode==='attack'?2:0), -3);
        c.lineTo(15 + (mode==='attack'?2:0), -2);
        c.lineTo(12, -3);
        c.closePath();
        c.fill();
        
        // Dual head crests (2 arcs/triangles)
        c.fillStyle = accent;
        // Left crest
        c.beginPath();
        c.moveTo(6, -8);
        c.lineTo(4, -12);
        c.lineTo(8, -10);
        c.closePath();
        c.fill();
        // Right crest
        c.beginPath();
        c.moveTo(10, -8);
        c.lineTo(8, -12);
        c.lineTo(12, -10);
        c.closePath();
        c.fill();
        
        // Tail
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-10, 4);
        c.lineTo(-14, 6);
        c.lineTo(-12, 8);
        c.lineTo(-8, 6);
        c.closePath();
        c.fill();
        break;
      case 'Stegosaurus':
        // Enhanced Stegosaurus with head nub, tail spikes, alternate plate heights
        // Body
        c.fillRect(-12, 2, 24, 10);
        
        // Head nub
        c.fillStyle = body;
        c.beginPath();
        c.arc(12, 4, 4, 0, Math.PI * 2);
        c.fill();
        
        // Alternating plate heights
        c.fillStyle = accent;
        const plateHeights = [8, 12, 10, 12, 8];
        for (let i = 0; i < 5; i++) {
          const x = -8 + i * 4;
          const h = plateHeights[i] + (mode==='attack'?1:0);
          c.beginPath();
          c.moveTo(x, 2);
          c.lineTo(x + 1, -h);
          c.lineTo(x + 3, -h);
          c.lineTo(x + 4, 2);
          c.closePath();
          c.fill();
        }
        
        // Tail with thagomizer (4 spikes)
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-12, 6);
        c.lineTo(-16, 8);
        c.lineTo(-14, 10);
        c.lineTo(-10, 8);
        c.closePath();
        c.fill();
        
        // Tail spikes
        c.fillStyle = detail;
        c.beginPath(); c.moveTo(-14, 8); c.lineTo(-16, 4); c.lineTo(-13, 7); c.closePath(); c.fill();
        c.beginPath(); c.moveTo(-14, 9); c.lineTo(-16, 12); c.lineTo(-13, 9); c.closePath(); c.fill();
        break;
      case 'Iguanodon':
        // Enhanced Iguanodon with split thumb spike, head beak, tail
        // Body
        c.fillRect(-12, -4, 24, 12);
        
        // Head with beak
        c.fillStyle = accent;
        c.beginPath();
        c.arc(10, -2, 5, 0, Math.PI * 2);
        c.fill();
        
        // Beak
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(13, -2);
        c.lineTo(16 + (mode==='attack'?2:0), -1);
        c.lineTo(16 + (mode==='attack'?2:0), 0);
        c.lineTo(13, -1);
        c.closePath();
        c.fill();
        
        // Split thumb spike (2 triangles for taper)
        c.fillStyle = detail;
        // Upper spike
        c.beginPath();
        c.moveTo(6, 2);
        c.lineTo(4, -2);
        c.lineTo(8, 0);
        c.closePath();
        c.fill();
        // Lower spike
        c.beginPath();
        c.moveTo(6, 4);
        c.lineTo(4, 0);
        c.lineTo(8, 2);
        c.closePath();
        c.fill();
        
        // Tail
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-12, 0);
        c.lineTo(-16, 2);
        c.lineTo(-14, 4);
        c.lineTo(-10, 2);
        c.closePath();
        c.fill();
        break;
      case 'Stonklodon':
        // Enhanced Stonklodon (economy coin) with embossed dino relief, edge rim
        // Coin base with edge rim effect
        c.fillStyle = detail;
        c.beginPath(); c.arc(0, 0, 15, 0, Math.PI * 2); c.fill();
        c.fillStyle = body;
        c.beginPath(); c.arc(0, 0, 13, 0, Math.PI * 2); c.fill();
        
        // Inner coin face
        c.fillStyle = accent;
        c.beginPath(); c.arc(-4, -4, 6 + (mode==='attack'?0.5:0), 0, Math.PI * 2); c.fill();
        
        // Embossed dino relief (small triangle head + tiny tail inside coin)
        c.fillStyle = detail;
        // Dino head triangle
        c.beginPath();
        c.moveTo(-2, -2);
        c.lineTo(2, -1);
        c.lineTo(0, 1);
        c.closePath();
        c.fill();
        // Tiny tail
        c.beginPath();
        c.moveTo(0, 1);
        c.lineTo(-3, 3);
        c.lineTo(-2, 4);
        c.lineTo(0, 2);
        c.closePath();
        c.fill();
        break;
      case 'TRex':
        // Enhanced T-Rex with jaw separation, teeth, eye, arm stubs, tail
        // Main body
        c.beginPath(); c.ellipse(0, 4, 10, 12, 0, 0, Math.PI * 2); c.fill();
        
        // Tail
        c.beginPath();
        c.moveTo(-8, 2);
        c.lineTo(-14, 6);
        c.lineTo(-12, 10);
        c.lineTo(-6, 6);
        c.closePath();
        c.fill();
        
        // Head with separated jaws
        const jawOffset = mode === 'attack' ? 2 : 0;
        // Upper jaw
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(4, -8);
        c.lineTo(12 + jawOffset, -4);
        c.lineTo(12 + jawOffset, -2);
        c.lineTo(4, -4);
        c.closePath();
        c.fill();
        
        // Lower jaw
        c.beginPath();
        c.moveTo(4, -4);
        c.lineTo(12 + jawOffset, -2);
        c.lineTo(12 + jawOffset, 2 + jawOffset);
        c.lineTo(4, 0);
        c.closePath();
        c.fill();
        
        // Teeth (2-3 visible) - using detail color
        c.fillStyle = detail;
        c.beginPath(); c.moveTo(10 + jawOffset, -3); c.lineTo(11 + jawOffset, -1); c.lineTo(9 + jawOffset, -2); c.closePath(); c.fill();
        c.beginPath(); c.moveTo(8 + jawOffset, -3); c.lineTo(9 + jawOffset, -1); c.lineTo(7 + jawOffset, -2); c.closePath(); c.fill();
        c.beginPath(); c.moveTo(10 + jawOffset, 0); c.lineTo(11 + jawOffset, -2); c.lineTo(9 + jawOffset, -1); c.closePath(); c.fill();
        
        // Eye
        c.fillStyle = accent;
        c.beginPath(); c.arc(2, -6, 2, 0, Math.PI * 2); c.fill();
        c.fillStyle = 'black';
        c.beginPath(); c.arc(2, -6, 1, 0, Math.PI * 2); c.fill();
        
        // Two arm stubs
        c.fillStyle = detail;
        c.fillRect(4, 2, 3, 2);
        c.fillRect(4, 5, 3, 2);
        break;
      case 'Spinosaurus':
        // Enhanced Spinosaurus with elongated snout, sail spines, tail paddle
        // Body
        c.fillRect(-12, 4, 24, 8);
        
        // Sail with spines
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-10, 4);
        c.lineTo(-6, -10 - (mode==='attack'?1:0));
        c.lineTo(0, 4);
        c.closePath();
        c.fill();
        
        // 2 sail spines along the sail
        c.fillStyle = detail;
        c.fillRect(-7, -4, 2, 8);
        c.fillRect(-3, -6, 2, 10);
        
        // Elongated snout
        c.fillStyle = accent;
        c.beginPath();
        c.moveTo(10, 6);
        c.lineTo(16, 5);
        c.lineTo(16, 7);
        c.lineTo(10, 8);
        c.closePath();
        c.fill();
        
        // Tail with paddle hint
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-12, 6);
        c.lineTo(-16, 7);
        c.lineTo(-15, 9);
        c.lineTo(-11, 8);
        c.closePath();
        c.fill();
        break;
      case 'Pteranodon':
        // Enhanced Pteranodon with proper beak, head crest backward, tail vane
        // Wings
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-14 - (mode==='attack'?2:0), 4);
        c.lineTo(0, -8);
        c.lineTo(14 + (mode==='attack'?2:0), 4);
        c.lineTo(0, 2);
        c.closePath();
        c.fill();
        
        // Body
        c.beginPath(); c.ellipse(0, 0, 4, 6, 0, 0, Math.PI * 2); c.fill();
        
        // Head with beak
        c.fillStyle = accent;
        c.beginPath(); c.arc(0, -8, 4, 0, Math.PI * 2); c.fill();
        
        // Proper beak
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(2, -8);
        c.lineTo(6, -7);
        c.lineTo(6, -6);
        c.lineTo(2, -7);
        c.closePath();
        c.fill();
        
        // Head crest pointing backward
        c.fillStyle = accent;
        c.beginPath();
        c.moveTo(-2, -9);
        c.lineTo(-6, -10);
        c.lineTo(-5, -8);
        c.lineTo(-1, -8);
        c.closePath();
        c.fill();
        
        // Tail vane
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(0, 4);
        c.lineTo(-2, 8);
        c.lineTo(0, 7);
        c.lineTo(2, 8);
        c.closePath();
        c.fill();
        break;
      case 'Quetzalcoatlus':
        // Enhanced Quetzalcoatlus with backward head crest, tucked hind legs, tail vane
        // Wings
        c.beginPath();
        c.moveTo(-12 - (mode==='attack'?2:0), 4);
        c.lineTo(0, -16);
        c.lineTo(12 + (mode==='attack'?2:0), 4);
        c.closePath();
        c.fill();
        
        // Head/neck
        c.fillStyle = accent;
        c.fillRect(-3, -16, 6, 6);
        
        // Backward head crest
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(-2, -15);
        c.lineTo(-6, -14);
        c.lineTo(-5, -12);
        c.lineTo(-1, -13);
        c.closePath();
        c.fill();
        
        // Two tiny triangles for tucked hind legs
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(-2, 2);
        c.lineTo(-4, 4);
        c.lineTo(-1, 4);
        c.closePath();
        c.fill();
        c.beginPath();
        c.moveTo(2, 2);
        c.lineTo(1, 4);
        c.lineTo(4, 4);
        c.closePath();
        c.fill();
        
        // Tail vane
        c.fillStyle = accent;
        c.beginPath();
        c.moveTo(0, 4);
        c.lineTo(-2, 8);
        c.lineTo(0, 7);
        c.lineTo(2, 8);
        c.closePath();
        c.fill();
        break;
      case 'Ankylosaurus':
        // Enhanced Ankylosaurus with tail club, shell scutes, head wedge, side spikes
        // Body
        c.fillRect(-14, -2, 28, 10);
        
        // Shell with scutes
        c.fillStyle = accent;
        c.fillRect(-10, -8, 20, 8 + (mode==='attack'?1:0));
        
        // 3 shell scutes (small rectangles)
        c.fillStyle = detail;
        c.fillRect(-6, -6, 3, 3);
        c.fillRect(-1, -7, 3, 3);
        c.fillRect(4, -6, 3, 3);
        
        // Head wedge
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(14, 0);
        c.lineTo(10, -4);
        c.lineTo(10, 4);
        c.closePath();
        c.fill();
        
        // Side spikes (optional, small)
        c.fillStyle = detail;
        c.beginPath(); c.moveTo(-10, -4); c.lineTo(-12, -6); c.lineTo(-9, -5); c.closePath(); c.fill();
        c.beginPath(); c.moveTo(10, -4); c.lineTo(12, -6); c.lineTo(9, -5); c.closePath(); c.fill();
        
        // Tail with club (circle)
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-14, 2);
        c.lineTo(-18, 3);
        c.lineTo(-16, 5);
        c.lineTo(-12, 4);
        c.closePath();
        c.fill();
        
        // Tail club
        c.fillStyle = detail;
        c.beginPath();
        c.arc(-18, 4, 3, 0, Math.PI * 2);
        c.fill();
        break;
      case 'Dreadnoughtus':
        // Enhanced Dreadnoughtus with tail, forelimb columns, head ellipse
        // Main body
        c.fillRect(-12, -2, 24, 12);
        
        // Neck
        c.fillStyle = accent;
        c.fillRect(-2, -10, 8, 10);
        
        // Head ellipse at neck end
        c.fillStyle = body;
        c.beginPath();
        c.ellipse(4, -12 - (mode==='attack'?1:0), 5, 4, 0, 0, Math.PI * 2);
        c.fill();
        
        // Two forelimb columns
        c.fillStyle = detail;
        c.fillRect(-8, 8, 4, 8);
        c.fillRect(4, 8, 4, 8);
        
        // Long slender tail triangle
        c.fillStyle = body;
        c.beginPath();
        c.moveTo(-12, 2);
        c.lineTo(-18, 4);
        c.lineTo(-16, 8);
        c.lineTo(-10, 4);
        c.closePath();
        c.fill();
        break;
      case 'Protoceratops':
        // Enhanced Protoceratops with frill scallops, beak, eye, tail nub
        // Body
        c.beginPath();
        c.ellipse(0, 4, 10, 8, 0, 0, Math.PI * 2);
        c.fill();
        
        // Frill shield
        c.fillStyle = accent;
        c.beginPath();
        c.moveTo(-8, -2);
        c.lineTo(-6, -10 + (mode==='attack'?-1:0));
        c.lineTo(0, -12 + (mode==='attack'?-1:0));
        c.lineTo(6, -10 + (mode==='attack'?-1:0));
        c.lineTo(8, -2);
        c.lineTo(0, 0);
        c.closePath();
        c.fill();
        
        // 2 frill scallops on shield edge
        c.fillStyle = detail;
        c.beginPath();
        c.arc(-4, -9 + (mode==='attack'?-1:0), 2, 0, Math.PI * 2);
        c.fill();
        c.beginPath();
        c.arc(4, -9 + (mode==='attack'?-1:0), 2, 0, Math.PI * 2);
        c.fill();
        
        // Head
        c.fillStyle = body;
        c.beginPath();
        c.arc(6, 0, 5, 0, Math.PI * 2);
        c.fill();
        
        // Beak
        c.fillStyle = detail;
        c.beginPath();
        c.moveTo(9, 0);
        c.lineTo(12 + (mode==='attack'?1:0), 1);
        c.lineTo(12 + (mode==='attack'?1:0), 2);
        c.lineTo(9, 1);
        c.closePath();
        c.fill();
        
        // Eye
        c.fillStyle = 'rgba(255,255,255,0.8)';
        c.beginPath(); c.arc(5, -1, 2, 0, Math.PI * 2); c.fill();
        c.fillStyle = 'black';
        c.beginPath(); c.arc(5, -1, 1, 0, Math.PI * 2); c.fill();
        
        // Tail nub
        c.fillStyle = body;
        c.beginPath();
        c.arc(-10, 4, 3, 0, Math.PI * 2);
        c.fill();
        break;
      default:
        // Default fallback shape
        c.beginPath(); c.moveTo(0, -10); c.lineTo(12 + (mode==='attack'?1:0), 8); c.lineTo(-12 - (mode==='attack'?1:0), 8); c.closePath(); c.fill();
        c.fillStyle = accent; c.fillRect(-5, -6 + (mode==='attack'?-1:0), 10, 6);
        break;
    }

    c.restore();
  }

  function generateTowerFrames(towerType, variantSeed, size = 32) {
    const cacheKey = `tower|${towerType}|${variantSeed}|${size}`;
    if (procFramesCache.has(cacheKey)) return procFramesCache.get(cacheKey);

    const idleFrames = 6;
    const attackFrames = 6;
    const w = size;
    const h = size;
    const originX = Math.floor(w * 0.5);
    const originY = Math.floor(h * 0.75);
    const states = { idle: [], attack: [] };
    const fps = { idle: 6, attack: 10 };

    for (let i = 0; i < idleFrames; i++) {
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const c = cv.getContext('2d');
      drawTowerSilhouette(c, size, towerType, (i / idleFrames) * Math.PI * 2, 'idle');
      states.idle.push(cv);
    }
    for (let i = 0; i < attackFrames; i++) {
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const c = cv.getContext('2d');
      drawTowerSilhouette(c, size, towerType, (i / attackFrames) * Math.PI * 2, 'attack');
      // brief muzzle flash/glint overlay
      c.fillStyle = 'rgba(255,255,200,0.15)';
      c.beginPath(); c.arc(w/2, h/2-8, (i%3===0)? 4:3, 0, Math.PI*2); c.fill();
      states.attack.push(cv);
    }

    const packet = { states, fps, originX, originY, w, h };
    procFramesCache.set(cacheKey, packet);
    return packet;
  }

  class SpriteInstance {
    constructor(kind, opts = {}) {
      this.kind = kind;
      this.variantSeed = opts.variantSeed || 1;
      this.state = opts.state || 'move'; // enemies: move, towers: idle/attack
      this.time = 0;
      this.scale = opts.scale || 1;
      this.flipX = false;

      this._atlasEntry = atlasRegistry.get(kind) || null;
      if (this.kind.startsWith('tower:')) {
        const t = this.kind.split(':')[1];
        this._proc = generateTowerFrames(t, this.variantSeed, 32);
      } else {
        this._proc = generateEnemyFrames(kind, this.variantSeed, 32);
      }
    }
    async ensureLoaded() {
      if (!this._atlasEntry) return false;
      const loaded = await ensureAtlasLoaded(this.kind);
      return !!(loaded && loaded.image);
    }
    update(dt) {
      this.time += dt;
    }
    draw(ctx, x, y, angle = 0, scale = this.scale) {
      // Prefer real atlas if available
      const entry = this._atlasEntry;
      if (entry && entry.image) {
        const meta = entry.meta;
        const stateKey = meta.states[this.state] ? this.state : (meta.states.move ? 'move' : Object.keys(meta.states)[0]);
        const state = meta.states[stateKey] || [];
        const localFps = meta.fps || 8;
        const idx = Math.floor(this.time * localFps) % Math.max(1, state.length);
        const frame = state[idx] || { x: 0, y: 0 };
        const sx = frame.x * meta.frameW;
        const sy = frame.y * meta.frameH;
        const sw = meta.frameW;
        const sh = meta.frameH;
        const ox = meta.originX ?? Math.floor(sw / 2);
        const oy = meta.originY ?? Math.floor(sh * 0.75);

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        if (this.flipX) ctx.scale(-1, 1);
        ctx.scale(scale, scale);
        ctx.drawImage(entry.image, sx, sy, sw, sh, -ox, -oy, sw, sh);
        ctx.restore();
        return;
      }

      // Procedural fallback frames
      const pf = this._proc;
      let frames = null;
      let localFps = 8;
      if (pf.states) {
        const stateKey = pf.states[this.state] ? this.state : (pf.states.idle ? 'idle' : Object.keys(pf.states)[0]);
        frames = pf.states[stateKey];
        localFps = (pf.fps && (pf.fps[stateKey] || pf.fps)) || 8;
      } else {
        frames = pf.frames;
        localFps = pf.fps || 8;
      }
      const idx = Math.floor(this.time * localFps) % frames.length;
      const frame = frames[idx];
      const ox = pf.originX;
      const oy = pf.originY;

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      if (this.flipX) ctx.scale(-1, 1);
      ctx.scale(scale, scale);
      ctx.drawImage(frame, -ox, -oy);
      ctx.restore();
    }
  }

  Sprites.createInstance = function createInstance(kind, opts) {
    return new SpriteInstance(kind, opts);
  };

  // --- Tower portraits (procedural) ---
  const portraitCache = new Map(); // key: towerType|size
  Sprites.getTowerPortrait = function getTowerPortrait(towerType, size = 72) {
    const key = `${towerType}|${size}`;
    if (portraitCache.has(key)) return portraitCache.get(key);
    const cv = document.createElement('canvas');
    cv.width = cv.height = size;
    const c = cv.getContext('2d');
    // bg
    c.fillStyle = 'rgba(20,40,30,0.9)';
    c.fillRect(0, 0, size, size);
    drawTowerSilhouette(c, size, towerType, 0, 'idle');

    const url = cv.toDataURL('image/png');
    portraitCache.set(key, url);
    return url;
  };

  // --- Enemy portraits (atlas if available, otherwise procedural first frame) ---
  const enemyPortraitCache = new Map(); // key: enemyKind|size
  Sprites.getEnemyPortrait = function getEnemyPortrait(enemyKind, size = 48) {
    const key = `${enemyKind}|${size}`;
    if (enemyPortraitCache.has(key)) return enemyPortraitCache.get(key);

    const cv = document.createElement('canvas');
    cv.width = cv.height = size;
    const c = cv.getContext('2d');
    c.clearRect(0, 0, size, size);

    const entry = atlasRegistry.get(enemyKind);
    if (entry && entry.image) {
      const meta = entry.meta || {};
      const state = (meta.states && (meta.states.move || meta.states.idle)) || [{ x: 0, y: 0 }];
      const frame = state[0] || { x: 0, y: 0 };
      const sx = (frame.x || 0) * (meta.frameW || 32);
      const sy = (frame.y || 0) * (meta.frameH || 32);
      const sw = meta.frameW || 32;
      const sh = meta.frameH || 32;
      const ox = meta.originX ?? Math.floor(sw / 2);
      const oy = meta.originY ?? Math.floor(sh * 0.75);
      const scale = size / Math.max(sw, sh);

      c.save();
      c.translate(size / 2, size / 2);
      c.scale(scale, scale);
      // draw centered using origin
      c.drawImage(entry.image, sx, sy, sw, sh, -ox, -oy, sw, sh);
      c.restore();

      const url = cv.toDataURL('image/png');
      enemyPortraitCache.set(key, url);
      return url;
    }

    // Fallback: procedural frame (stable seed per kind)
    const seed = strHash(enemyKind) || 1;
    const proc = (function () {
      // generate frames at a base resolution near desired size for crisp scaling
      const base = Math.min(size, 48);
      return generateEnemyFrames(enemyKind, seed, base);
    })();
    const frame = proc.frames[0];
    const sw = frame.width, sh = frame.height;
    const ox = proc.originX, oy = proc.originY;
    const scale = size / Math.max(sw, sh);

    c.save();
    c.translate(size / 2, size / 2);
    c.scale(scale, scale);
    c.drawImage(frame, -ox, -oy);
    c.restore();

    const url = cv.toDataURL('image/png');
    enemyPortraitCache.set(key, url);
    return url;
  };

  // --- Built-in demo atlases: conscript, rifleman (generated as sprite sheets) ---
  function buildAtlasFromProcedural(kind, seed, frameW = 24, frameH = 24, framesCount = 6) {
    // Use procedural enemy frames to bake a single-row sprite sheet
    const proc = generateEnemyFrames(kind, seed, Math.min(frameW, frameH));
    const frames = proc.frames.slice(0, framesCount);
    const sheet = document.createElement('canvas');
    sheet.width = frameW * frames.length;
    sheet.height = frameH;
    const c = sheet.getContext('2d');
    for (let i = 0; i < frames.length; i++) {
      // center draw
      const fx = i * frameW;
      const dx = fx + Math.floor((frameW - frames[i].width) / 2);
      const dy = Math.floor((frameH - frames[i].height) / 2);
      c.drawImage(frames[i], dx, dy);
    }
    const dataUrl = sheet.toDataURL('image/png');
    const meta = {
      frameW, frameH,
      fps: proc.fps || 8,
      originX: proc.originX ?? Math.floor(frameW / 2),
      originY: proc.originY ?? Math.floor(frameH * 0.75),
      states: { move: [] }
    };
    for (let i = 0; i < frames.length; i++) meta.states.move.push({ x: i, y: 0 });
    Sprites.registerAtlas(kind, dataUrl, meta);
  }

  function registerBuiltInAtlases() {
    try {
      buildAtlasFromProcedural('conscript', 1234, 24, 24, 6);
      buildAtlasFromProcedural('rifleman', 2345, 24, 24, 6);
    } catch (e) {
      // no-op; fallback procedural will still work
      // console.warn('Atlas build failed', e);
    }
  }

  registerBuiltInAtlases();

})();