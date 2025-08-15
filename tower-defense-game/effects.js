/**
 * effects.js
 * Retro pixel-art friendly effects for the tower defense game.
 * - Particles (pooled, square pixels)
 * - Damage numbers (float up, fade)
 * - Hit flashes (local white flash)
 * - Screen shake proxy (main.js owns the camera; we call window._shakeCamera)
 * - Config + flags for runtime tuning
 *
 * Usage (from main.js or gameplay code):
 *   VFX.setFlags({ particles: true, showDamageNumbers: false, screenShake: false });
 *   VFX.spawnDamageNumber(x, y, amount, { crit: false });
 *   VFX.spawnBurst(x, y, 12, { hue: 120, size: 2, speed: 120 });
 *   VFX.hitSpark(x, y, dmg);
 *   VFX.deathBurst(x, y);
 *   VFX.shakeCamera(6, 0.18);
 *   VFX.update(dt);
 *   // Inside world transform:
 *   VFX.draw(ctx);
 */
(function () {
  const VFX = {};
  window.VFX = VFX;

  // --- Config and flags ---
  VFX.config = {
    maxParticles: 320,
    maxDamageNumbers: 48,
    gravityY: 360,          // px/s^2 for particles
    friction: 0.88,         // velocity damping per second (applied as pow)
    particleLifeMin: 0.25,  // s
    particleLifeMax: 0.65,  // s
    defaultSize: 2,         // in pixels (square)
    sizeJitter: 1,          // +/- pixels
    defaultSpeed: 140,      // initial speed magnitude
    speedJitter: 60,        // +/- speed
    // damage numbers
    dmgRiseSpeed: 36,       // px/s
    dmgLife: 0.8,           // seconds
    dmgFont: 'bold 12px monospace',
    dmgColor: '#ffe089',
    dmgCritColor: '#ffb2b2',
    dmgShadow: 'rgba(0,0,0,0.75)',
    // hit flash
    flashLife: 0.12,        // seconds
    flashBaseRadius: 16,    // px
  };

  // Toggle via Options (wired by main.js -> applySettings)
  VFX.flags = {
    particles: true,
    showDamageNumbers: false,
    screenShake: false,
  };

  VFX.setFlags = function setFlags(flags) {
    if (!flags) return;
    if (typeof flags.particles === 'boolean') VFX.flags.particles = flags.particles;
    if (typeof flags.showDamageNumbers === 'boolean') VFX.flags.showDamageNumbers = flags.showDamageNumbers;
    if (typeof flags.screenShake === 'boolean') VFX.flags.screenShake = flags.screenShake;
  };

  // --- Internal pools ---
  const particles = []; // {x,y,vx,vy,t,life,size,color}
  const damageNumbers = []; // {x,y,t,life,text,color}
  const flashes = []; // {x,y,t,life,radius}

  // Utility
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function randRange(a, b) { return a + Math.random() * (b - a); }
  function randSign() { return Math.random() < 0.5 ? -1 : 1; }
  function hsla(h, s, l, a = 1) {
    return `hsla(${((h % 360) + 360) % 360},${clamp(s,0,100)}%,${clamp(l,0,100)}%,${a})`;
  }

  // --- API: Particles ---
  VFX.spawnParticle = function spawnParticle(x, y, opts = {}) {
    if (!VFX.flags.particles) return;
    const cfg = VFX.config;
    if (particles.length >= cfg.maxParticles) {
      // Drop oldest to keep CPU predictable
      particles.shift();
    }
    const hue = opts.hue ?? 40;       // default amber
    const sat = opts.sat ?? 60;
    const lit = opts.lit ?? 60;
    const alpha = opts.alpha ?? 1;
    const color = opts.color || hsla(hue, sat, lit, alpha);

    const size = Math.max(1, Math.round((opts.size ?? cfg.defaultSize) + randSign() * (opts.sizeJitter ?? cfg.sizeJitter)));
    const spd = (opts.speed ?? cfg.defaultSpeed) + randSign() * (opts.speedJitter ?? cfg.speedJitter);
    const ang = (opts.angle != null) ? opts.angle : Math.random() * Math.PI * 2;
    const life = clamp(opts.life ?? randRange(cfg.particleLifeMin, cfg.particleLifeMax), 0.05, 2.0);

    particles.push({
      x, y,
      vx: Math.cos(ang) * spd,
      vy: Math.sin(ang) * spd,
      t: 0,
      life,
      size,
      color,
      g: (opts.gravity ?? cfg.gravityY),
      fric: (opts.friction ?? cfg.friction),
    });
  };

  VFX.spawnBurst = function spawnBurst(x, y, count = 12, opts = {}) {
    if (!VFX.flags.particles) return;
    for (let i = 0; i < count; i++) {
      VFX.spawnParticle(x, y, opts);
    }
  };

  // Convenience patterns
  VFX.hitSpark = function hitSpark(x, y, damage = 0) {
    if (!VFX.flags.particles) return;
    const pow = Math.min(1, damage / 40); // scale by hit power
    const count = 6 + Math.floor(8 * pow);
    VFX.spawnBurst(x, y, count, {
      hue: 45 + Math.round(20 * Math.random()),
      sat: 65,
      lit: 60,
      size: 2,
      speed: 120 + 80 * pow,
      gravity: 420,
      friction: 0.86,
    });
  };

  VFX.acidSplash = function acidSplash(x, y) {
    if (!VFX.flags.particles) return;
    VFX.spawnBurst(x, y, 10 + Math.floor(Math.random() * 6), {
      hue: 120, sat: 70, lit: 60,
      size: 2,
      speed: 140,
      gravity: 200,
    });
  };

  VFX.deathBurst = function deathBurst(x, y) {
    if (!VFX.flags.particles) return;
    VFX.spawnBurst(x, y, 14 + Math.floor(Math.random() * 10), {
      hue: 20 + Math.floor(Math.random() * 20),
      sat: 50,
      lit: 60,
      size: 2,
      speed: 160,
      gravity: 480,
    });
    // subtle flash on death
    VFX.spawnHitFlash(x, y, VFX.config.flashBaseRadius * 0.9, 0.10);
  };

  // --- API: Damage numbers ---
  VFX.spawnDamageNumber = function spawnDamageNumber(x, y, amount, opts = {}) {
    if (!VFX.flags.showDamageNumbers) return;
    const cfg = VFX.config;
    if (damageNumbers.length >= cfg.maxDamageNumbers) {
      damageNumbers.shift();
    }
    const crit = !!opts.crit;
    const txt = (opts.text != null) ? String(opts.text) : String(Math.max(1, Math.round(amount)));
    damageNumbers.push({
      x,
      y,
      t: 0,
      life: (opts.life ?? cfg.dmgLife),
      text: txt,
      color: crit ? cfg.dmgCritColor : (opts.color || cfg.dmgColor),
      vy: -(opts.riseSpeed ?? cfg.dmgRiseSpeed),
      scale: opts.scale || 1,
    });
  };

  // --- API: Hit flash ---
  VFX.spawnHitFlash = function spawnHitFlash(x, y, radius = VFX.config.flashBaseRadius, life = VFX.config.flashLife) {
    flashes.push({ x, y, t: 0, life, radius });
  };

  // --- API: Screen shake (delegated to main.js camera) ---
  VFX.shakeCamera = function shakeCamera(mag = 5, dur = 0.18) {
    if (!VFX.flags.screenShake) return;
    if (typeof window._shakeCamera === 'function') {
      window._shakeCamera(mag, dur);
    }
  };

  // --- Update/Draw ---
  VFX.update = function update(dt) {
    // Particles
    if (particles.length) {
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.t += dt;
        if (p.t >= p.life) { particles.splice(i, 1); continue; }
        // Physics
        p.vy += p.g * dt;
        // Apply friction in a time-scaled manner
        const fricPow = Math.pow(p.fric, dt);
        p.vx *= fricPow;
        p.vy *= fricPow;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
      }
    }

    // Damage numbers
    if (damageNumbers.length) {
      for (let i = damageNumbers.length - 1; i >= 0; i--) {
        const d = damageNumbers[i];
        d.t += dt;
        if (d.t >= d.life) { damageNumbers.splice(i, 1); continue; }
        d.y += d.vy * dt;
      }
    }

    // Flashes
    if (flashes.length) {
      for (let i = flashes.length - 1; i >= 0; i--) {
        const f = flashes[i];
        f.t += dt;
        if (f.t >= f.life) flashes.splice(i, 1);
      }
    }
  };

  VFX.draw = function draw(ctx) {
    // Draw order: flashes under particles, then particles, then damage numbers
    // Flashes
    if (flashes.length) {
      for (let i = 0; i < flashes.length; i++) {
        const f = flashes[i];
        const a = 1 - (f.t / f.life);
        if (a <= 0) continue;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = `rgba(255,255,255,${(0.25 * a).toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(Math.round(f.x), Math.round(f.y), Math.max(6, Math.round(f.radius * a)), 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    // Particles (pixel squares)
    if (particles.length) {
      ctx.save();
      // ensure crisp pixels
      if (ctx.imageSmoothingEnabled !== undefined) ctx.imageSmoothingEnabled = false;
      for (let i = 0; i &#60; particles.length; i++) {
        const p = particles[i];
        const a = 1 - (p.t / p.life);
        if (a <= 0) continue;
        ctx.globalAlpha = Math.max(0, Math.min(1, a));
        ctx.fillStyle = p.color;
        const s = Math.max(1, p.size | 0);
        // snap to integer pixel grid for crispness
        const rx = Math.round(p.x - s / 2);
        const ry = Math.round(p.y - s / 2);
        ctx.fillRect(rx, ry, s, s);
      }
      ctx.globalAlpha = 1;
      ctx.restore();
    }

    // Damage numbers
    if (damageNumbers.length) {
      const cfg = VFX.config;
      ctx.save();
      if (ctx.imageSmoothingEnabled !== undefined) ctx.imageSmoothingEnabled = false;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = cfg.dmgFont;
      for (let i = 0; i &#60; damageNumbers.length; i++) {
        const d = damageNumbers[i];
        const a = 1 - (d.t / d.life);
        if (a <= 0) continue;
        const x = Math.round(d.x);
        const y = Math.round(d.y);
        // shadow
        ctx.fillStyle = cfg.dmgShadow;
        ctx.globalAlpha = Math.min(1, a + 0.2);
        ctx.fillText(d.text, x + 1, y + 1);
        // main
        ctx.fillStyle = d.color;
        ctx.globalAlpha = a;
        ctx.fillText(d.text, x, y);
      }
      ctx.globalAlpha = 1;
      ctx.restore();
    }
  };

  // Small helper to expose internals for debugging
  VFX._debug = {
    particles,
    damageNumbers,
    flashes,
  };

  // Make config/flags tweakable in console
  try {
    window._VFX = VFX;
  } catch (e) {
    // no-op
  }
})();