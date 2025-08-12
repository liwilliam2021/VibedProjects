// main.js — Dinosaur Tower Defense
(() => {
  // Canvas and HUD
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  const moneyEl = document.getElementById('money');
  const livesEl = document.getElementById('lives');
  const waveEl = document.getElementById('wave');
  const startBtn = document.getElementById('startWave');
  const fastBtn = document.getElementById('fastForward');
  const pauseBtn = document.getElementById('pauseGame');
  const restartBtn = document.getElementById('restartGame');
  const infoEl = document.getElementById('info');

  const selectedNameEl = document.getElementById('selectedTowerName');
  const selectedCostEl = document.getElementById('selectedCost');
  const autoNextEl = document.getElementById('autoNext');
  // Enhanced HUD elements
  const selectedEmojiEl = document.getElementById('selectedEmoji');
  const selectedTowerLabelEl = document.getElementById('selectedTowerLabel');
  const statRangeEl = document.getElementById('statRange');
  const statRangeValueEl = document.getElementById('statRangeValue');
  const statPowerEl = document.getElementById('statPower');
  const statPowerValueEl = document.getElementById('statPowerValue');

  // Main menu / map UI elements
  const mainMenuEl = document.getElementById('mainMenu');
  const mapListEl = document.getElementById('mapList');
  const menuPlayBtn = document.getElementById('menuPlay');
  const menuWikiBtn = document.getElementById('menuWiki');
  const wikiModal = document.getElementById('wikiModal');
  const closeWikiBtn = document.getElementById('closeWiki');
  const mapInfoEl = document.getElementById('mapInfo');
  const menuCloseBtn = document.getElementById('menuClose');
  const menuOptionsBtn = document.getElementById('menuOptions');
  const optionsModal = document.getElementById('optionsModal');
  const closeOptionsBtn = document.getElementById('closeOptions');

  // Map state & modifiers (set by loadMap)
  let currentMapId = 'jungle';
  let mapModifiers = { hpMult: 1, speedMult: 1, countMult: 1 };
  
  // Game settings (can be modified via options)
  let gameSettings = {
    difficulty: 'normal',
    startingMoney: 100,
    startingLives: 10,
    waveReward: 20,
    showRanges: true,
    showDamageNumbers: false,
    particleEffects: true,
    screenShake: false,
    masterVolume: 70,
    soundEffects: true,
    musicEnabled: true,
    confirmPlacement: false,
    gridSnap: false,
    keyboardShortcuts: true
  };
  
  // Tips system
  let tipsData = null;
  let currentMenuTipIndex = 0;
  
  // Load tips data
  async function loadTips() {
    try {
      const response = await fetch('tips.json');
      tipsData = await response.json();
      if (tipsData && tipsData.tips && tipsData.tips.length > 0) {
        // Start rotating tips
        showNextTip();
        setInterval(showNextTip, 8000); // Rotate every 8 seconds
      }
    } catch (error) {
      console.error('Failed to load tips:', error);
    }
  }
  
  function showNextTip() {
    const tipEl = document.getElementById('menuTip');
    if (tipEl && tipsData && tipsData.tips && tipsData.tips.length > 0) {
      const tip = tipsData.tips[currentMenuTipIndex];
      tipEl.innerHTML = `<strong>Tip:</strong> ${tip.text}`;
      tipEl.style.animation = 'fadeIn 0.5s ease';
      currentMenuTipIndex = (currentMenuTipIndex + 1) % tipsData.tips.length;
      
      // Reset animation
      setTimeout(() => {
        if (tipEl) tipEl.style.animation = '';
      }, 500);
    }
  }
  
  // Load saved settings from localStorage
  function loadSettings() {
    const saved = localStorage.getItem('td_game_settings');
    if (saved) {
      try {
        gameSettings = Object.assign(gameSettings, JSON.parse(saved));
        applySettings();
      } catch(e) {
        console.error('Failed to load settings:', e);
      }
    }
  }
  
  // Save settings to localStorage
  function saveSettings() {
    localStorage.setItem('td_game_settings', JSON.stringify(gameSettings));
  }
  
  // Apply difficulty modifiers
  function getDifficultyModifiers() {
    switch(gameSettings.difficulty) {
      case 'easy':
        return { hpMult: 0.7, speedMult: 0.8, countMult: 0.8, moneyMult: 1.3 };
      case 'hard':
        return { hpMult: 1.3, speedMult: 1.2, countMult: 1.2, moneyMult: 0.8 };
      case 'nightmare':
        return { hpMult: 1.6, speedMult: 1.4, countMult: 1.5, moneyMult: 0.6 };
      default: // normal
        return { hpMult: 1.0, speedMult: 1.0, countMult: 1.0, moneyMult: 1.0 };
    }
  }
  
  // Apply settings to game
  function applySettings() {
    // Update UI elements with current settings
    const difficultySelect = document.getElementById('difficultySelect');
    const startingMoneySlider = document.getElementById('startingMoney');
    const startingLivesSlider = document.getElementById('startingLives');
    const waveRewardSlider = document.getElementById('waveReward');
    const showRangesCheck = document.getElementById('showRanges');
    const showDamageCheck = document.getElementById('showDamageNumbers');
    const particleCheck = document.getElementById('particleEffects');
    const screenShakeCheck = document.getElementById('screenShake');
    const masterVolumeSlider = document.getElementById('masterVolume');
    const soundEffectsCheck = document.getElementById('soundEffects');
    const musicEnabledCheck = document.getElementById('musicEnabled');
    const confirmPlacementCheck = document.getElementById('confirmPlacement');
    const gridSnapCheck = document.getElementById('gridSnap');
    const keyboardShortcutsCheck = document.getElementById('keyboardShortcuts');
    
    if (difficultySelect) difficultySelect.value = gameSettings.difficulty;
    if (startingMoneySlider) {
      startingMoneySlider.value = gameSettings.startingMoney;
      const valueEl = document.getElementById('startingMoneyValue');
      if (valueEl) valueEl.textContent = gameSettings.startingMoney;
    }
    if (startingLivesSlider) {
      startingLivesSlider.value = gameSettings.startingLives;
      const valueEl = document.getElementById('startingLivesValue');
      if (valueEl) valueEl.textContent = gameSettings.startingLives;
    }
    if (waveRewardSlider) {
      waveRewardSlider.value = gameSettings.waveReward;
      const valueEl = document.getElementById('waveRewardValue');
      if (valueEl) valueEl.textContent = gameSettings.waveReward;
    }
    if (showRangesCheck) showRangesCheck.checked = gameSettings.showRanges;
    if (showDamageCheck) showDamageCheck.checked = gameSettings.showDamageNumbers;
    if (particleCheck) particleCheck.checked = gameSettings.particleEffects;
    if (screenShakeCheck) screenShakeCheck.checked = gameSettings.screenShake;
    if (masterVolumeSlider) {
      masterVolumeSlider.value = gameSettings.masterVolume;
      const valueEl = document.getElementById('masterVolumeValue');
      if (valueEl) valueEl.textContent = gameSettings.masterVolume + '%';
    }
    if (soundEffectsCheck) soundEffectsCheck.checked = gameSettings.soundEffects;
    if (musicEnabledCheck) musicEnabledCheck.checked = gameSettings.musicEnabled;
    if (confirmPlacementCheck) confirmPlacementCheck.checked = gameSettings.confirmPlacement;
    if (gridSnapCheck) gridSnapCheck.checked = gameSettings.gridSnap;
    if (keyboardShortcutsCheck) keyboardShortcutsCheck.checked = gameSettings.keyboardShortcuts;
  }
 
  let money = gameSettings.startingMoney, lives = gameSettings.startingLives, wave = 0;
  let gameSpeed = 1;
  let autoNextTimerId = null;
  let isPaused = false;
  let previousGameSpeed = 1;
 
  // Placement state
  let previewPos = null;
  let rotatePreview = 0;
  let selectedType = 'RaptorNest';

  // Make ranges slightly larger to ensure engagement even with novice placements
  const TOWER_TYPES = {
    RaptorNest:     { name: 'Raptor Nest',    cost: 60,  range: 140 },
    Protoceratops:  { name: 'Protoceratops',  cost: 55,  range: 110 },
    Triceratops:    { name: 'Triceratops',    cost: 85,  range: 130 },
    Brachiosaurus:  { name: 'Brachiosaurus',  cost: 95,  range: 160 },
    Dilophosaurus:  { name: 'Dilophosaurus',  cost: 75,  range: 180 },
    Stegosaurus:    { name: 'Stegosaurus',    cost: 80,  range: 170 },
    Iguanodon:      { name: 'Iguanodon',      cost: 70,  range: 150 },
    Stonklodon:     { name: 'Stonklodon',     cost: 90,  range: 120 }, // Economy tower — fixed payout per wave
    TRex:           { name: 'T-Rex',          cost: 150, range: 155 }, // Legendary
    Spinosaurus:    { name: 'Spinosaurus',    cost: 170, range: 190 }, // Legendary
    Pteranodon:     { name: 'Pteranodon',     cost: 130, range: 200 }, // Rare
    Ankylosaurus:   { name: 'Ankylosaurus',   cost: 110, range: 145 }, // Rare
    Dreadnoughtus:  { name: 'Dreadnoughtus',  cost: 190, range: 150 }, // Legendary
    Quetzalcoatlus: { name: 'Quetzalcoatlus', cost: 200, range: 9999 } // Legendary (global)
  };
  // Lightweight UI metadata for HUD portrait + power bar
  const TOWER_UI = {
    RaptorNest:     { emoji: '🦖', power: 4 },
    Protoceratops:  { emoji: '🦕', power: 3 },
    Triceratops:    { emoji: '🦕', power: 5 },
    Brachiosaurus:  { emoji: '🦕', power: 3 },
    Dilophosaurus:  { emoji: '🦖', power: 5 },
    Stegosaurus:    { emoji: '🦕', power: 6 },
    Iguanodon:      { emoji: '🦖', power: 5 },
    Stonklodon:     { emoji: '🪙', power: 1 },
    TRex:           { emoji: '🦖', power: 9 },
    Spinosaurus:    { emoji: '🦕', power: 8 },
    Pteranodon:     { emoji: '🦖', power: 7 },
    Ankylosaurus:   { emoji: '🦕', power: 7 },
    Dreadnoughtus:  { emoji: '🦕', power: 9 },
    Quetzalcoatlus: { emoji: '🦅', power: 8 }
  };

  // Removed legacy MAP metadata block.
  // A single MAPS object with paths + modifiers is defined below (see "Map definitions and current path").

  // persistent selected map
  let selectedMap = localStorage.getItem('td_selected_map') || 'jungle';

   // Map definitions and current path
   const MAPS = {
     jungle: {
       name: 'Jungle Ridge',
       desc: 'Dense canopy, winding paths — Easy.',
       // Single longer path for easy map
       path: [
         {x: 50, y: 300},
         {x: 120, y: 300},
         {x: 120, y: 200},
         {x: 180, y: 200},
         {x: 180, y: 140},
         {x: 280, y: 140},
         {x: 280, y: 240},
         {x: 380, y: 240},
         {x: 380, y: 140},
         {x: 480, y: 140},
         {x: 480, y: 320},
         {x: 580, y: 320},
         {x: 580, y: 380},
         {x: 680, y: 380},
         {x: 680, y: 300},
         {x: 750, y: 300}
       ],
       modifiers: { hpMult: 0.9, speedMult: 0.95, countMult: 1.0 }
     },
     coast: {
       name: 'Coastal Cliffs',
       desc: 'Narrow bridges, multiple routes — Medium.',
       // Multiple paths for medium difficulty
       paths: [
         // Path 1: Upper route
         [
           {x: 40, y: 150},
           {x: 160, y: 150},
           {x: 160, y: 80},
           {x: 320, y: 80},
           {x: 320, y: 180},
           {x: 480, y: 180},
           {x: 480, y: 120},
           {x: 600, y: 120},
           {x: 600, y: 200},
           {x: 750, y: 200}
         ],
         // Path 2: Lower route
         [
           {x: 40, y: 450},
           {x: 140, y: 450},
           {x: 140, y: 380},
           {x: 280, y: 380},
           {x: 280, y: 480},
           {x: 420, y: 480},
           {x: 420, y: 380},
           {x: 560, y: 380},
           {x: 560, y: 450},
           {x: 750, y: 450}
         ]
       ],
       pathWeights: [0.5, 0.5], // Equal probability
       modifiers: { hpMult: 1.0, speedMult: 1.05, countMult: 1.1 }
     },
     volcano: {
       name: 'Volcanic Pass',
       desc: 'Lava hazards, three dangerous paths — Hard.',
       // Multiple paths for hard difficulty
       paths: [
         // Path 1: Top route
         [
           {x: 40, y: 100},
           {x: 140, y: 100},
           {x: 140, y: 60},
           {x: 280, y: 60},
           {x: 280, y: 140},
           {x: 420, y: 140},
           {x: 420, y: 80},
           {x: 560, y: 80},
           {x: 560, y: 160},
           {x: 750, y: 160}
         ],
         // Path 2: Middle route
         [
           {x: 40, y: 300},
           {x: 120, y: 300},
           {x: 120, y: 240},
           {x: 240, y: 240},
           {x: 240, y: 340},
           {x: 380, y: 340},
           {x: 380, y: 280},
           {x: 520, y: 280},
           {x: 520, y: 360},
           {x: 750, y: 360}
         ],
         // Path 3: Bottom route
         [
           {x: 40, y: 500},
           {x: 160, y: 500},
           {x: 160, y: 440},
           {x: 300, y: 440},
           {x: 300, y: 520},
           {x: 460, y: 520},
           {x: 460, y: 460},
           {x: 600, y: 460},
           {x: 600, y: 520},
           {x: 750, y: 520}
         ]
       ],
       pathWeights: [0.3, 0.4, 0.3], // Middle path slightly more common
       modifiers: { hpMult: 1.25, speedMult: 1.15, countMult: 1.3 }
     }
   };
 
   // Current active paths (will be reset by loadMap)
   let paths = [];
   let pathWeights = [];
 
   function loadMap(id) {
     if (!MAPS[id]) return;
     currentMapId = id;
     
     // Handle both single path and multiple paths
     if (MAPS[id].paths) {
       // Multiple paths
       paths = MAPS[id].paths.map(p => p.slice());
       pathWeights = MAPS[id].pathWeights || new Array(paths.length).fill(1.0 / paths.length);
     } else if (MAPS[id].path) {
       // Single path (backwards compatible)
       paths = [MAPS[id].path.slice()];
       pathWeights = [1.0];
     }
     
     mapModifiers = Object.assign({}, MAPS[id].modifiers);
     if (mapInfoEl) mapInfoEl.innerHTML = `<strong>${MAPS[id].name}</strong><br/><small class="muted">${MAPS[id].desc}</small>`;
   }
 
   // initialize with default map
   loadMap(currentMapId);

  // Utility
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function dist(a,b){ return Math.hypot(a.x-b.x, a.y-b.y); }
  function angleBetween(ax,ay,bx,by){ return Math.atan2(by-ay,bx-ax); }
  function normalize(dx,dy){ const d=Math.hypot(dx,dy)||1; return {x:dx/d,y:dy/d}; }
  function wrapAngle(a){ while(a<=-Math.PI)a+=Math.PI*2; while(a>Math.PI)a-=Math.PI*2; return a; }
  function lerpAngle(a,b,maxStep){
    const da = wrapAngle(b - a);
    const step = clamp(da, -maxStep, maxStep);
    return a + step;
  }
  
  // Select a path index based on weights
  function selectPathByWeight() {
    if (paths.length === 1) return 0;
    
    // Normalize weights to ensure they sum to 1
    const totalWeight = pathWeights.reduce((sum, w) => sum + w, 0);
    const normalizedWeights = pathWeights.map(w => w / totalWeight);
    
    const random = Math.random();
    let cumulative = 0;
    
    for (let i = 0; i < normalizedWeights.length; i++) {
      cumulative += normalizedWeights[i];
      if (random < cumulative) {
        return i;
      }
    }
    
    return normalizedWeights.length - 1; // Fallback to last path
  }

  // Enemy with status effects
  let ENEMY_ID_SEQ = 1;

  class Enemy {
    constructor(hp, speed, pathIndex = null) { // speed in px/s
      this.id = ENEMY_ID_SEQ++;
      this.hp = hp;
      this.maxHp = hp;
      this.baseSpeed = speed;
      this.radius = 10;

      // Select a path based on weights if not specified
      if (pathIndex === null) {
        pathIndex = selectPathByWeight();
      }
      this.pathIndex = pathIndex;
      this.path = paths[pathIndex];
      
      this.waypoint = 0;
      // Start exactly at the first waypoint
      const startPoint = this.path[0];
      this.x = startPoint.x;
      this.y = startPoint.y;
      this.alive = true;
      
      // Track progress along current segment for smooth movement
      this.segmentProgress = 0; // 0 to 1 along current segment

      // Status
      this.bleedDps = 0;
      this.bleedTimer = 0;
      this.slowFactor = 1; // 1 = no slow, 0.6 = 40% slow
      this.slowTimer = 0;
      this.stunTimer = 0;
    }
    get nextTarget() {
      return this.path[this.waypoint+1] || null;
    }
    get currentWaypoint() {
      return this.path[this.waypoint] || null;
    }
    applyBleed(dps, duration) {
      // Take strongest dps, refresh duration
      this.bleedDps = Math.max(this.bleedDps, dps);
      this.bleedTimer = Math.max(this.bleedTimer, duration);
    }
    applySlow(factor, duration) {
      // Take strongest slow (min factor), refresh duration
      this.slowFactor = Math.min(this.slowFactor, factor);
      this.slowTimer = Math.max(this.slowTimer, duration);
    }
    applyStun(duration) {
      this.stunTimer = Math.max(this.stunTimer, duration);
    }
    knockback(distance) {
      if (this.waypoint <= 0) return; // Can't knockback from start
      
      const a = this.path[this.waypoint];
      const b = this.path[this.waypoint+1] || a;
      
      // Calculate knockback direction (opposite of forward)
      let dir = normalize(b.x-a.x, b.y-a.y);
      const newX = this.x - dir.x * distance;
      const newY = this.y - dir.y * distance;
      
      // Check if knockback would go past previous waypoint
      if (this.waypoint > 0) {
        const prev = this.path[this.waypoint - 1];
        const distToPrev = Math.hypot(newX - prev.x, newY - prev.y);
        const distCurrToPrev = Math.hypot(a.x - prev.x, a.y - prev.y);
        
        if (distToPrev < distCurrToPrev) {
          // Knockback crosses previous waypoint, snap to previous segment
          this.waypoint--;
          // Position on the previous segment
          const prevDir = normalize(a.x - prev.x, a.y - prev.y);
          const remainingDist = distance - Math.hypot(this.x - a.x, this.y - a.y);
          this.x = a.x - prevDir.x * Math.min(remainingDist, distCurrToPrev * 0.9);
          this.y = a.y - prevDir.y * Math.min(remainingDist, distCurrToPrev * 0.9);
        } else {
          // Normal knockback within current segment
          this.x = newX;
          this.y = newY;
        }
      } else {
        // At first waypoint, limit knockback
        const maxBack = Math.hypot(this.x - a.x, this.y - a.y) * 0.9;
        const actualDist = Math.min(distance, maxBack);
        this.x -= dir.x * actualDist;
        this.y -= dir.y * actualDist;
      }
    }
    takeDamage(d) {
      this.hp -= d;
      if (this.hp <= 0) this.die();
    }
    die() {
      if (!this.alive) return;
      this.alive = false;
      const diffMods = getDifficultyModifiers();
      money += Math.round(10 * diffMods.moneyMult);
    }
    reachEnd() {
      if (!this.alive) return;
      this.alive = false;
      lives -= 1;
    }
    update(dt) {
      if (!this.alive) return;

      // Apply bleed
      if (this.bleedTimer > 0) {
        this.hp -= this.bleedDps * dt;
        this.bleedTimer -= dt;
        if (this.bleedTimer <= 0) this.bleedDps = 0;
        if (this.hp <= 0) { this.die(); return; }
      }

      // Slow timer decay
      if (this.slowTimer > 0) {
        this.slowTimer -= dt;
        if (this.slowTimer <= 0) this.slowFactor = 1;
      }

      // Stun handling
      if (this.stunTimer > 0) {
        this.stunTimer -= dt;
        return; // no movement while stunned
      }

      const target = this.nextTarget;
      if (!target) {
        // No next target means we're at the end
        if (this.waypoint >= this.path.length - 1) {
          this.reachEnd();
        }
        return;
      }

      const dx = target.x - this.x;
      const dy = target.y - this.y;
      const distToTarget = Math.hypot(dx, dy);
      
      // Calculate movement for this frame
      const speed = this.baseSpeed * this.slowFactor * gameSpeed;
      const moveDistance = speed * dt;
      
      // Check if we'll reach or pass the waypoint this frame
      if (distToTarget <= moveDistance + 2) { // Slightly larger threshold for smoother transitions
        // Snap to waypoint to avoid overshooting
        this.x = target.x;
        this.y = target.y;
        this.waypoint++;
        
        // Check if we've reached the end
        if (this.waypoint >= this.path.length - 1) {
          this.reachEnd();
          return;
        }
        
        // If there's remaining movement, continue to next segment
        const remainingMove = moveDistance - distToTarget;
        if (remainingMove > 0 && this.nextTarget) {
          const newTarget = this.nextTarget;
          const ndx = newTarget.x - this.x;
          const ndy = newTarget.y - this.y;
          const ndist = Math.hypot(ndx, ndy);
          if (ndist > 0) {
            this.x += (ndx / ndist) * Math.min(remainingMove, ndist);
            this.y += (ndy / ndist) * Math.min(remainingMove, ndist);
          }
        }
      } else {
        // Normal movement toward waypoint
        const moveX = (dx / distToTarget) * moveDistance;
        const moveY = (dy / distToTarget) * moveDistance;
        this.x += moveX;
        this.y += moveY;
      }
      
      // Sanity check: ensure enemy stays on path
      this.validatePosition();
    }
    
    validatePosition() {
      // Ensure the enemy hasn't gone off-path due to floating point errors
      if (!this.currentWaypoint || !this.nextTarget) return;
      
      const curr = this.currentWaypoint;
      const next = this.nextTarget;
      
      // Project position onto the line segment
      const segX = next.x - curr.x;
      const segY = next.y - curr.y;
      const segLenSq = segX * segX + segY * segY;
      
      if (segLenSq > 0) {
        const t = Math.max(0, Math.min(1,
          ((this.x - curr.x) * segX + (this.y - curr.y) * segY) / segLenSq
        ));
        
        const projX = curr.x + t * segX;
        const projY = curr.y + t * segY;
        
        // If enemy is too far from the path line, snap back
        const distFromPath = Math.hypot(this.x - projX, this.y - projY);
        if (distFromPath > 5) { // 5 pixel tolerance
          this.x = projX;
          this.y = projY;
        }
      }
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      // Body
      ctx.fillStyle = '#ff6f6f';
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI*2);
      ctx.fill();
      // Status rings
      if (this.slowFactor < 1) {
        ctx.strokeStyle = 'rgba(120,200,255,0.8)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius+4, 0, Math.PI*2);
        ctx.stroke();
      }
      if (this.stunTimer > 0) {
        ctx.strokeStyle = 'rgba(255,230,120,0.9)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius+8, 0, Math.PI*2);
        ctx.stroke();
      }
      // HP bar
      const w = 24;
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(this.x-w/2, this.y-16, w, 4);
      ctx.fillStyle = '#6af';
      const pct = Math.max(0, this.hp/this.maxHp);
      ctx.fillRect(this.x-w/2, this.y-16, w*pct, 4);
      ctx.restore();
    }
  }

  // Dino Towers
  class RaptorNestTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.RaptorNest.range;
      this.fireRate = 1.0; // s
      this.cooldown = 0;
      this.bleedDps = 6;
      this.bleedDur = 3.0;
      this.impact = 8;
      this.leapSpeed = 450; // px/s
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        raptorLeaps.push(new HomingLeap(this.x, this.y, target, this.leapSpeed, this.impact, this.bleedDps, this.bleedDur));
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      // Nest base
      ctx.fillStyle = '#7a8a96';
      ctx.beginPath();
      ctx.arc(this.x, this.y, 16, 0, Math.PI*2);
      ctx.fill();
      // Egg
      ctx.fillStyle = '#dfe8ef';
      ctx.beginPath();
      ctx.ellipse(this.x, this.y-4, 8, 10, 0, 0, Math.PI*2);
      ctx.fill();
      // Range
      if (gameSettings.showRanges) {
        ctx.fillStyle = 'rgba(100,220,140,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
      }
      ctx.restore();
    }
  }

  class TriceratopsTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Triceratops.range;
      this.cooldown = 0;
      this.rushCooldown = 2.2; // s, slightly faster for responsiveness
      this.rushSpeed = 600; // px/s
      this.rushLength = 160; // px
      this.stunDur = 0.8;
      this.knockback = 60; // px
      this.damage = 12;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        rushStrikes.push(new RushStrike(this.x, this.y, angleBetween(this.x,this.y,target.x,target.y), this.rushSpeed, this.rushLength, this.stunDur, this.knockback, this.damage));
        this.cooldown = this.rushCooldown;
      }
    }
    draw(ctx) {
      ctx.save();
      // Body wedge
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#9ec071';
      ctx.beginPath();
      ctx.moveTo(0,-14);
      ctx.lineTo(16,10);
      ctx.lineTo(-16,10);
      ctx.closePath();
      ctx.fill();
      // Horns
      ctx.strokeStyle = '#e6eed8'; ctx.lineWidth=3;
      ctx.beginPath(); ctx.moveTo(-6,-4); ctx.lineTo(-12,-14); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(6,-4); ctx.lineTo(12,-14); ctx.stroke();
      ctx.restore();

      // Range
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(240,240,150,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class BrachiosaurusTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Brachiosaurus.range;
      this.slowFactor = 0.6; // 40% slow
      this.dotDps = 1.5;     // light canopy chip damage so effect is visible
    }
    update(dt, enemies) {
      // Aura applies continuously
      for (const e of enemies) {
        if (!e.alive) continue;
        if (Math.hypot(e.x-this.x, e.y-this.y) <= this.range) {
          e.applySlow(this.slowFactor, 0.3);
          // light damage-over-time so the "attack" is visible
          e.hp -= this.dotDps * dt;
          if (e.hp <= 0) e.die();
        }
      }
    }
    draw(ctx) {
      ctx.save();
      // Tall neck silhouette
      ctx.fillStyle = '#86b38a';
      ctx.beginPath();
      ctx.ellipse(this.x, this.y, 16, 12, 0, 0, Math.PI*2);
      ctx.fill();
      ctx.fillRect(this.x-4, this.y-28, 8, 20);
      ctx.beginPath(); ctx.arc(this.x+6, this.y-32, 8, Math.PI*0.7, Math.PI*1.9); ctx.fill();
      // Aura
      if (gameSettings.showRanges) {
        ctx.fillStyle = 'rgba(120,200,160,0.08)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
      }
      ctx.restore();
    }
  }

  class DilophosaurusTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Dilophosaurus.range;
      this.fireRate = 1.3;
      this.cooldown = 0;
      this.spitSpeed = 380;
      this.poolRadius = 60;
      this.poolDuration = 4;
      this.poolDps = 8;
      this.poolSlow = 0.7;
      this.impact = 6;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        spits.push(new SpitProjectile(this.x, this.y, target, this.spitSpeed, this.impact, (ix,iy)=>{
          acidPools.push(new AcidPool(ix, iy, this.poolRadius, this.poolDuration, this.poolDps, this.poolSlow));
        }));
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      // Frill head
      ctx.fillStyle = '#9fa6e8';
      ctx.beginPath();
      ctx.moveTo(0,-16); ctx.lineTo(12,0); ctx.lineTo(-12,0); ctx.closePath(); ctx.fill();
      // Body
      ctx.fillStyle='#6f85cf';
      ctx.fillRect(-8,0,16,12);
      ctx.restore();

      // Range
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(140,160,255,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class StegosaurusTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Stegosaurus.range;
      this.fireRate = 0.9;
      this.cooldown = 0;
      this.spikeSpeed = 520;
      this.damage = 18;
      this.pierce = 4;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        const ang = angleBetween(this.x, this.y, target.x, target.y);
        spikes.push(new SpikeProjectile(this.x, this.y, ang, this.spikeSpeed, this.damage, this.pierce));
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      // Plates
      ctx.fillStyle = '#c99665';
      for (let i=-2;i<=2;i++) {
        ctx.beginPath();
        ctx.moveTo(i*6, -4);
        ctx.lineTo(i*6+4, -12);
        ctx.lineTo(i*6+8, -4);
        ctx.closePath();
        ctx.fill();
      }
      // Body
      ctx.fillStyle = '#9f7b52';
      ctx.fillRect(-14, -2, 28, 12);
      ctx.restore();

      // Range
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(205,160,120,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }// Economy Tower — Stonklodon (prints fixed money per wave)
  class StonklodonTower {
    constructor(x,y) {
      this.x = x; this.y = y;
      this.range = (TOWER_TYPES.Stonklodon && TOWER_TYPES.Stonklodon.range) || 120;
    }
    update(dt) {
      // No per-second income; payout occurs at the start of each wave in startNextWave()
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      // Coin body
      ctx.fillStyle = '#d9d06b';
      ctx.beginPath();
      ctx.arc(0,0,14,0,Math.PI*2); ctx.fill();
      // Coin shine
      ctx.fillStyle = '#fff6a0';
      ctx.beginPath();
      ctx.arc(-4,-4,6,0,Math.PI*2); ctx.fill();
      ctx.restore();

      // Soft gold aura (range indicator)
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(230,210,90,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  // Legendary and Mythic Towers
  class TRexTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.TRex.range;
      this.cooldown = 0;
      this.fireRate = 2.2;
      this.biteDamage = 40;
      this.stunRadius = 80;
      this.stunDur = 0.6;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        // heavy bite on target
        target.takeDamage(this.biteDamage);
        // intimidate nearby enemies around target
        for (const e of enemies) {
          if (!e.alive) continue;
          if (Math.hypot(e.x-target.x, e.y-target.y) <= this.stunRadius) {
            e.applyStun(this.stunDur);
          }
        }
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#b25d5d';
      ctx.beginPath();
      ctx.moveTo(0,-16); ctx.lineTo(14,6); ctx.lineTo(-14,6); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#eee';
      ctx.fillRect(-3, -6, 6, 8);
      ctx.restore();

      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(255,120,120,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class SpinosaurusTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Spinosaurus.range;
      this.cooldown = 0;
      this.fireRate = 1.9;
      // Uses acid pools to simulate a sweeping water cone
      this.poolRadius = 70;
      this.poolDuration = 3.2;
      this.poolDps = 10;
      this.poolSlow = 0.65;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        const ang = Math.atan2(target.y - this.y, target.x - this.x);
        // place two pools along the direction toward the target
        const d1 = Math.min(this.range*0.45, Math.hypot(target.x-this.x, target.y-this.y)*0.6);
        const d2 = Math.min(this.range*0.85, Math.hypot(target.x-this.x, target.y-this.y)*1.0);
        const x1 = this.x + Math.cos(ang)*d1, y1 = this.y + Math.sin(ang)*d1;
        const x2 = this.x + Math.cos(ang)*d2, y2 = this.y + Math.sin(ang)*d2;
        acidPools.push(new AcidPool(x1, y1, this.poolRadius, this.poolDuration, this.poolDps, this.poolSlow));
        acidPools.push(new AcidPool(x2, y2, this.poolRadius, this.poolDuration, this.poolDps, this.poolSlow));
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#4dbbb3';
      ctx.beginPath();
      ctx.moveTo(-10,8); ctx.lineTo(-6,-10); ctx.lineTo(0,8); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#66d2cc';
      ctx.fillRect(-12, 4, 24, 8);
      ctx.restore();

      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(100,220,220,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class PteranodonTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Pteranodon.range;
      this.cooldown = 0;
      this.fireRate = 1.6;
      this.aoe = 70;
      this.damage = 26;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        // instant airstrike at target location
        for (const e of enemies) {
          if (!e.alive) continue;
          if (Math.hypot(e.x-target.x, e.y-target.y) <= this.aoe) e.takeDamage(this.damage);
        }
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#c6c1a8';
      ctx.beginPath();
      ctx.moveTo(-12, 4); ctx.lineTo(0,-16); ctx.lineTo(12,4); ctx.closePath(); ctx.fill();
      ctx.restore();

      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(220,220,180,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class AnkylosaurusTower {
    constructor(x,y) {
      this.x=x; this.y=y;
      this.range = TOWER_TYPES.Ankylosaurus.range;
      this.cooldown = 0;
      this.fireRate = 2.1;
      this.slamRadius = 85;
      this.damage = 18;
      this.knockback = 42;
      this.stunDur = 0.25;
    }
    update(dt, enemies) {
      this.cooldown -= dt*gameSpeed;
      if (this.cooldown > 0) return;
      // slam around itself if any enemy in range
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        for (const e of enemies) {
          if (!e.alive) continue;
          if (Math.hypot(e.x-this.x, e.y-this.y) <= this.slamRadius) {
            e.takeDamage(this.damage);
            e.applyStun(this.stunDur);
            e.knockback(this.knockback);
          }
        }
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#8a7d63';
      ctx.fillRect(-14, -6, 28, 12);
      ctx.fillStyle = '#b39b74';
      ctx.fillRect(-10, -10, 20, 8);
      ctx.restore();

      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(210,180,120,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  // New towers: Common, Uncommon, Legendary additions
  class ProtoceratopsTower {
    constructor(x,y) {
      this.x = x; this.y = y;
      this.range = TOWER_TYPES.Protoceratops.range;
      this.cooldown = 0;
      this.fireRate = 1.1; // s
      this.damage = 7;
      this.stagger = 0.2; // mini-stun
    }
    update(dt, enemies) {
      this.cooldown -= dt * gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        target.takeDamage(this.damage);
        target.applyStun(this.stagger);
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#6fa86b';
      ctx.beginPath();
      ctx.moveTo(0,-10); ctx.lineTo(12,8); ctx.lineTo(-12,8); ctx.closePath(); ctx.fill();
      // small head shield
      ctx.fillStyle = '#cfdacb';
      ctx.fillRect(-5, -6, 10, 6);
      ctx.restore();
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(140,200,140,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class IguanodonTower {
    constructor(x,y) {
      this.x = x; this.y = y;
      this.range = TOWER_TYPES.Iguanodon.range;
      this.cooldown = 0;
      this.fireRate = 1.2; // s
      this.spearSpeed = 560;
      this.damage = 14;
    }
    update(dt, enemies) {
      this.cooldown -= dt * gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        const ang = angleBetween(this.x, this.y, target.x, target.y);
        // Use SpikeProjectile with single pierce to simulate spear
        spikes.push(new SpikeProjectile(this.x, this.y, ang, this.spearSpeed, this.damage, 1));
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      // body
      ctx.fillStyle = '#88b06b';
      ctx.fillRect(-12, -6, 24, 12);
      // arm/spike
      ctx.fillStyle = '#dfe3cf';
      ctx.fillRect(6, -2, 8, 4);
      ctx.restore();
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(100,220,140,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class DreadnoughtusTower {
    constructor(x,y) {
      this.x = x; this.y = y;
      this.range = TOWER_TYPES.Dreadnoughtus.range;
      this.cooldown = 0;
      this.fireRate = 2.8;
      this.stompRadius = 95;
      this.damage = 28;
      this.knockback = 60;
      this.stunDur = 0.35;
    }
    update(dt, enemies) {
      this.cooldown -= dt * gameSpeed;
      if (this.cooldown > 0) return;
      const target = findNearestEnemy(this.x, this.y, this.range, enemies);
      if (target) {
        for (const e of enemies) {
          if (!e.alive) continue;
          if (Math.hypot(e.x - this.x, e.y - this.y) <= this.stompRadius) {
            e.takeDamage(this.damage);
            e.applyStun(this.stunDur);
            e.knockback(this.knockback);
          }
        }
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#6b8c63';
      ctx.fillRect(-18, -8, 36, 16);
      ctx.fillStyle = '#9fb98f';
      ctx.fillRect(-12, -14, 24, 8);
      ctx.restore();
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(150,220,160,0.06)';
        ctx.beginPath(); ctx.arc(this.x, this.y, this.range, 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }

  class QuetzalcoatlusTower {
    constructor(x,y) {
      this.x = x; this.y = y;
      this.range = TOWER_TYPES.Quetzalcoatlus.range; // effectively global
      this.cooldown = 0;
      this.fireRate = 2.0;
      this.aoe = 80;
      this.damage = 30;
    }
    update(dt, enemiesList) {
      this.cooldown -= dt * gameSpeed;
      if (this.cooldown > 0) return;
      // Prioritize highest current HP anywhere on the map
      let target = null, bestHp = -1;
      for (const e of enemiesList) {
        if (!e.alive) continue;
        if (e.hp > bestHp) { bestHp = e.hp; target = e; }
      }
      if (target) {
        for (const e of enemiesList) {
          if (!e.alive) continue;
          if (Math.hypot(e.x - target.x, e.y - target.y) <= this.aoe) {
            e.takeDamage(this.damage);
          }
        }
        this.cooldown = this.fireRate;
      }
    }
    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = '#cfc8a6';
      ctx.beginPath();
      ctx.moveTo(-14, 6); ctx.lineTo(0, -16); ctx.lineTo(14, 6); ctx.closePath(); ctx.fill();
      // beak
      ctx.fillStyle = '#f0e5b8';
      ctx.fillRect(-3, -16, 6, 6);
      ctx.restore();
      if (gameSettings.showRanges) {
        ctx.save();
        ctx.fillStyle = 'rgba(220,220,180,0.03)';
        ctx.beginPath(); ctx.arc(this.x, this.y, Math.min(220, 220), 0, Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
  }
  // Projectiles and effects
  class HomingLeap {
    constructor(x,y,target,speed,impact,bleedDps,bleedDur) {
      this.x=x; this.y=y; this.target=target; this.speed=speed;
      this.impact=impact; this.bleedDps=bleedDps; this.bleedDur=bleedDur;
      this.alive=true; this.angle=angleBetween(x,y,target.x,target.y);
    }
    update(dt) {
      if (!this.alive) return;
      if (!this.target.alive) { this.alive=false; return; }
      // Home towards target
      const desired = angleBetween(this.x,this.y,this.target.x,this.target.y);
      const turn = 8 * dt * gameSpeed;
      this.angle = wrapAngle(lerpAngle(this.angle, desired, turn));
      const move = this.speed * dt * gameSpeed;
      this.x += Math.cos(this.angle)*move;
      this.y += Math.sin(this.angle)*move;
      if (Math.hypot(this.x-this.target.x, this.y-this.target.y) < this.target.radius+8) {
        this.target.takeDamage(this.impact);
        this.target.applyBleed(this.bleedDps, this.bleedDur);
        this.alive = false;
      }
      if (this.x< -40 || this.x>W+40 || this.y< -40 || this.y>H+40) this.alive=false;
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);
      ctx.fillStyle = '#f5d08a';
      ctx.beginPath();
      ctx.moveTo(10,0); ctx.lineTo(-8,-6); ctx.lineTo(-8,6); ctx.closePath(); ctx.fill();
      ctx.restore();
    }
  }

  class RushStrike {
    constructor(x,y,angle,speed,length,stunDur,knockback,damage) {
      this.x=x; this.y=y; this.angle=angle; this.speed=speed;
      this.left = length; this.stunDur=stunDur; this.knockback=knockback; this.damage=damage;
      this.alive=true;
      this.hitSet = new Set();
    }
    update(dt) {
      if (!this.alive) return;
      const step = Math.min(this.left, this.speed*dt*gameSpeed);
      this.left -= step;
      const vx = Math.cos(this.angle)*step;
      const vy = Math.sin(this.angle)*step;
      this.x += vx; this.y += vy;

      // Hit detection around current position
      for (const e of enemies) {
        if (!e.alive) continue;
        if (this.hitSet.has(e.id)) continue;
        const d = Math.hypot(e.x-this.x, e.y-this.y);
        if (d < 18) {
          e.takeDamage(this.damage);
          e.applyStun(this.stunDur);
          e.knockback(this.knockback);
          this.hitSet.add(e.id);
        }
      }

      if (this.left <= 0) this.alive=false;
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);
      ctx.strokeStyle = 'rgba(255,230,120,0.9)';
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.moveTo(-12,0); ctx.lineTo(12,0); ctx.stroke();
      ctx.restore();
    }
  }

  class SpitProjectile {
    constructor(x,y,target,speed,impact,onExplode) {
      this.x=x; this.y=y; this.target=target; this.speed=speed; this.impact=impact;
      this.onExplode = onExplode;
      this.alive = true; this.angle = angleBetween(x,y,target.x,target.y);
    }
    update(dt) {
      if (!this.alive) return;
      if (!this.target.alive) { this.alive=false; return; }
      const desired = angleBetween(this.x,this.y,this.target.x,this.target.y);
      const turn = 5 * dt * gameSpeed;
      this.angle = wrapAngle(lerpAngle(this.angle, desired, turn));
      const step = this.speed * dt * gameSpeed;
      this.x += Math.cos(this.angle)*step;
      this.y += Math.sin(this.angle)*step;

      if (Math.hypot(this.x-this.target.x, this.y-this.target.y) < this.target.radius+6) {
        this.target.takeDamage(this.impact);
        if (this.onExplode) this.onExplode(this.x, this.y);
        this.alive=false;
      }
      if (this.x< -40 || this.x>W+40 || this.y< -40 || this.y>H+40) this.alive=false;
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);
      ctx.fillStyle = '#a0ff9a';
      ctx.beginPath();
      ctx.ellipse(0,0,8,4,0,0,Math.PI*2);
      ctx.fill();
      ctx.restore();
    }
  }

  class AcidPool {
    constructor(x,y,radius,duration,dps,slowFactor) {
      this.x=x; this.y=y; this.radius=radius; this.timer=duration;
      this.dps=dps; this.slow=slowFactor; this.alive=true;
    }
    update(dt) {
      if (!this.alive) return;
      this.timer -= dt;
      if (this.timer <= 0) { this.alive=false; return; }
      for (const e of enemies) {
        if (!e.alive) continue;
        const d = Math.hypot(e.x-this.x, e.y-this.y);
        if (d <= this.radius) {
          e.applySlow(this.slow, 0.5);
          e.hp -= this.dps * dt;
          if (e.hp <= 0) e.die();
        }
      }
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      const alpha = 0.18 + 0.1 * (this.timer % 0.4);
      ctx.fillStyle = `rgba(120,255,160,${alpha.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI*2); ctx.fill();
      ctx.restore();
    }
  }

  class SpikeProjectile {
    constructor(x,y,angle,speed,damage,pierce) {
      this.x=x; this.y=y; this.angle=angle; this.speed=speed;
      this.damage=damage; this.pierce=pierce; this.alive=true;
    }
    update(dt) {
      if (!this.alive) return;
      const step = this.speed*dt*gameSpeed;
      this.x += Math.cos(this.angle)*step;
      this.y += Math.sin(this.angle)*step;

      for (const e of enemies) {
        if (!e.alive) continue;
        if (Math.hypot(e.x-this.x, e.y-this.y) < e.radius+4) {
          e.takeDamage(this.damage);
          this.pierce -= 1;
          if (this.pierce <= 0) { this.alive=false; break; }
        }
      }
      if (this.x< -40 || this.x>W+40 || this.y< -40 || this.y>H+40) this.alive=false;
    }
    draw(ctx) {
      if (!this.alive) return;
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);
      ctx.fillStyle = '#d8c3a1';
      ctx.fillRect(-10,-2,20,4);
      ctx.restore();
    }
  }

  // Collections
  const enemies = [];
  const towers = [];
  const raptorLeaps = [];
  const rushStrikes = [];
  const spits = [];
  const acidPools = [];
  const spikes = [];

  // Wave generation (harder scaling + periodic miniboss)
  let spawning = false;
  let spawnTimerId = null;
  function startNextWave() {
    if (spawning) return;
    // Per-wave economy payout (Stonklodon)
    const stonkCount = towers.filter(t => t instanceof StonklodonTower).length;
    if (stonkCount > 0) {
      const payoutPerTower = 3; // fixed money per wave per Stonklodon
      const payout = payoutPerTower * stonkCount;
      money += payout;
      infoTemp(`Stonklodon paid +${payout}`);
      updateHUD();
    }
    
    // Wave completion bonus
    if (wave > 0) {
      money += gameSettings.waveReward;
      infoTemp(`Wave complete! +${gameSettings.waveReward} bonus`);
    }

    wave++;
    waveEl.textContent = wave;
    spawning = true;
 
    // Gentler early waves; ramps up mid/late game, modified by selected map
    const baseCount = 6 + Math.floor(wave * 1.2);
    const count = Math.max(1, Math.round(baseCount * (mapModifiers.countMult || 1)));
    let spawned = 0;
    const intervalMs = 750;

    // Clear any previous timer (safety)
    if (spawnTimerId) { clearInterval(spawnTimerId); spawnTimerId = null; }

    // Early game easier, accelerate growth after wave 10
    const diffMods = getDifficultyModifiers();
    const baseHp = (20 + (10 * wave) + Math.max(0, wave - 10) * 6) * diffMods.hpMult;
    const baseSpeed = (50 + 4 * wave) * diffMods.speedMult;

    spawnTimerId = setInterval(() => {
      if (spawned >= count) {
        clearInterval(spawnTimerId);
        spawnTimerId = null;
        // Miniboss every 7 waves (starting at 7)
        if (wave >= 7 && wave % 7 === 0) {
          const bossHp = Math.round(baseHp * 8);
          const bossSpeed = Math.max(35, Math.round(baseSpeed * 0.85));
          const tank = new Enemy(bossHp, bossSpeed);
          tank.radius = 14; // visually larger steam tank
          enemies.push(tank);
        }
        spawning = false;
        return;
      }
      // Occasional elites and steampunk exo-units (mid-bosses)
      const eliteChance = Math.min(0.05 + wave * 0.005, 0.35);
      const steamEliteChance = Math.min(0.02 + wave * 0.003, 0.20);
      const elite = Math.random() < eliteChance;
      const steamElite = !elite && (Math.random() < steamEliteChance);
      const hp = Math.round(baseHp * (steamElite ? 2.2 : (elite ? 1.4 : 1.0)));
      const speed = baseSpeed * (steamElite ? 1.05 : (elite ? 1.2 : 1.0));
      const e = new Enemy(hp, speed);
      if (steamElite) e.radius = 12; // slight visual hint
      enemies.push(e);
      spawned++;
    }, intervalMs / gameSpeed);
  }

  // Input handling
  canvas.addEventListener('mousemove', (e)=>{
    const rect=canvas.getBoundingClientRect();
    const x=(e.clientX-rect.left)*(canvas.width/rect.width);
    const y=(e.clientY-rect.top)*(canvas.height/rect.height);
    previewPos = {x,y};
  });
  canvas.addEventListener('mouseleave', ()=> previewPos = null);

  canvas.addEventListener('click', ()=>{
    if (!previewPos) return;
    if (isOnPath(previewPos.x, previewPos.y)) { infoTemp('Cannot place on path'); return; }
    const def = TOWER_TYPES[selectedType];
    if (money < def.cost) { infoTemp('Not enough money'); return; }
    placeTower(selectedType, previewPos.x, previewPos.y);
    money -= def.cost;
    updateHUD();
  });

  window.addEventListener('keydown', (e)=>{
    if (e.key === 'r' || e.key === 'R') {
      rotatePreview = (rotatePreview + Math.PI/2)%(Math.PI*2);
    }
  });

  startBtn.addEventListener('click', ()=> {
    // If the main menu is still open, close it and then start the wave
    if (mainMenuEl && !mainMenuEl.hasAttribute('hidden')) {
      mainMenuEl.setAttribute('hidden','');
      mainMenuEl.setAttribute('aria-hidden','true');
    }
    if (wikiModal && !wikiModal.hasAttribute('hidden')) {
      wikiModal.setAttribute('hidden','');
      wikiModal.setAttribute('aria-hidden','true');
    }
    document.body.classList.remove('modal-open');
    startNextWave();
  });
  fastBtn.addEventListener('click', ()=>{
    if (gameSpeed === 1) { gameSpeed = 2; fastBtn.classList.add('active'); fastBtn.textContent='x2 Speed'; }
    else { gameSpeed = 1; fastBtn.classList.remove('active'); fastBtn.textContent='x1 Speed'; }
  });
  
  // Pause button functionality
  if (pauseBtn) {
    pauseBtn.addEventListener('click', () => {
      showMainMenuAsPause();
    });
  }
  if (restartBtn) {
    restartBtn.addEventListener('click', restartGame);
  }

  // Tower selection UI
  const towerButtons = document.querySelectorAll('.towerBtn');
  towerButtons.forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const type = btn.getAttribute('data-type') || 'RaptorNest';
      selectedType = type;
      updateSelectionUI();
    });
  });
  function updateSelectionUI() {
    const def = TOWER_TYPES[selectedType];
    if (!def) return;
    if (selectedNameEl) selectedNameEl.textContent = def.name;
    if (selectedCostEl) selectedCostEl.textContent = def.cost;

    // Enhanced HUD portrait and stats
    const ui = TOWER_UI[selectedType] || {};
    if (selectedEmojiEl && ui.emoji) selectedEmojiEl.textContent = ui.emoji;
    if (selectedTowerLabelEl) selectedTowerLabelEl.textContent = def.name;

    // Range bar: normalize against ~200 as soft cap
    const maxRange = 200;
    const rangePct = clamp(def.range / maxRange, 0, 1) * 100;
    if (statRangeEl) statRangeEl.style.width = rangePct.toFixed(0) + '%';
    if (statRangeValueEl) statRangeValueEl.textContent = def.range;

    // Power bar: 1..10 scale
    const power = clamp((ui.power || 1), 1, 10);
    const powerPct = (power / 10) * 100;
    if (statPowerEl) statPowerEl.style.width = powerPct.toFixed(0) + '%';
    if (statPowerValueEl) statPowerValueEl.textContent = power;

    // Buttons: selected/locked state
    towerButtons.forEach(b=>{
      const t = b.getAttribute('data-type');
      b.classList.toggle('selected', t === selectedType);
      const c = TOWER_TYPES[t].cost;
      b.classList.toggle('locked', money < c);
    });
  }

  function placeTower(type,x,y) {
    let tower = null;
    switch(type) {
      case 'RaptorNest':     tower = new RaptorNestTower(x,y); break;
      case 'Protoceratops':  tower = new ProtoceratopsTower(x,y); break;
      case 'Triceratops':    tower = new TriceratopsTower(x,y); break;
      case 'Brachiosaurus':  tower = new BrachiosaurusTower(x,y); break;
      case 'Dilophosaurus':  tower = new DilophosaurusTower(x,y); break;
      case 'Stegosaurus':    tower = new StegosaurusTower(x,y); break;
      case 'Iguanodon':      tower = new IguanodonTower(x,y); break;
      case 'Stonklodon':     tower = new StonklodonTower(x,y); break;
      case 'TRex':           tower = new TRexTower(x,y); break;
      case 'Spinosaurus':    tower = new SpinosaurusTower(x,y); break;
      case 'Pteranodon':     tower = new PteranodonTower(x,y); break;
      case 'Ankylosaurus':   tower = new AnkylosaurusTower(x,y); break;
      case 'Dreadnoughtus':  tower = new DreadnoughtusTower(x,y); break;
      case 'Quetzalcoatlus': tower = new QuetzalcoatlusTower(x,y); break;
      default:               tower = new RaptorNestTower(x,y); break;
    }
    towers.push(tower);
  }

  let infoTimeout = null;
  function infoTemp(msg, ms=900) {
    infoEl.textContent = msg;
    clearTimeout(infoTimeout);
    infoTimeout = setTimeout(()=> infoEl.textContent = 'Select a dino tower and click to place (not on the path). Press R to rotate preview.', ms);
  }

  function isOnPath(x,y) {
    // Check all paths for collision
    const buffer = 24;
    
    for (const path of paths) {
      for (let i=0;i<path.length-1;i++) {
        const a = path[i], b = path[i+1];
        const px = b.x - a.x, py = b.y - a.y;
        const t = ((x-a.x)*px + (y-a.y)*py) / (px*px+py*py);
        const clampT = Math.max(0, Math.min(1, t));
        const projX = a.x + clampT*px;
        const projY = a.y + clampT*py;
        const d = Math.hypot(projX-x, projY-y);
        if (d < buffer) return true;
      }
    }
    return false;
  }

  function findNearestEnemy(x,y,range,enemies) {
    let best=null, bestD=Infinity;
    for (const e of enemies) {
      if (!e.alive) continue;
      const d = Math.hypot(e.x-x, e.y-y);
      if (d<=range && d<bestD) { best=e; bestD=d; }
    }
    return best;
  }

  function updateHUD() {
    moneyEl.textContent = money;
    livesEl.textContent = lives;
    waveEl.textContent = wave;
    updateSelectionUI();
  }

  // Game loop
  let last = performance.now();
  let loopRunning = true;
  function loop(ts) {
    const dt = (ts - last)/1000;
    last = ts;
    update(dt);
    draw();
    if (lives > 0 && loopRunning) requestAnimationFrame(loop);
    else if (!loopRunning) return;
    else {
      // game over overlay
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.6)';
      ctx.fillRect(0,0,W,H);
      ctx.fillStyle='#fff';
      ctx.font='36px sans-serif';
      ctx.fillText('Game Over', W/2-90, H/2);
      ctx.restore();
    }
  }

  function update(dt) {
    // Update enemies
    for (const e of enemies) e.update(dt);
    // Update towers
    for (const t of towers) t.update(dt, enemies);
    // Projectiles/effects
    for (const p of raptorLeaps) p.update(dt);
    for (const r of rushStrikes) r.update(dt);
    for (const s of spits) s.update(dt);
    for (const a of acidPools) a.update(dt);
    for (const sp of spikes) sp.update(dt);

    // Auto next wave scheduling
    if (!spawning && enemies.length === 0 && autoNextEl && autoNextEl.checked) {
      if (!autoNextTimerId) {
        autoNextTimerId = setTimeout(() => {
          autoNextTimerId = null;
          startNextWave();
        }, 1000);
      }
    } else {
      if (autoNextTimerId) { clearTimeout(autoNextTimerId); autoNextTimerId = null; }
    }

    // Cleanup
    pruneDead(enemies, e=>!e.alive);
    pruneDead(raptorLeaps, o=>!o.alive);
    pruneDead(rushStrikes, o=>!o.alive);
    pruneDead(spits, o=>!o.alive);
    pruneDead(acidPools, o=>!o.alive);
    pruneDead(spikes, o=>!o.alive);

    // HUD
    updateHUD();
  }

  function pruneDead(arr, pred) {
    for (let i=arr.length-1;i>=0;i--) if (pred(arr[i])) arr.splice(i,1);
  }

  function draw() {
    ctx.clearRect(0,0,W,H);
    // Draw path — outer and inner strokes for dino theme
    drawPath();

    // Acid pools under enemies
    for (const a of acidPools) a.draw(ctx);

    // Towers
    for (const t of towers) t.draw(ctx);
    // Enemies
    for (const e of enemies) e.draw(ctx);

    // Projectiles/effects
    for (const p of raptorLeaps) p.draw(ctx);
    for (const r of rushStrikes) r.draw(ctx);
    for (const s of spits) s.draw(ctx);
    for (const sp of spikes) sp.draw(ctx);

    // Placement preview
    if (previewPos) {
      const def = TOWER_TYPES[selectedType];
      const x=previewPos.x, y=previewPos.y;
      const valid = !isOnPath(x,y) && money >= def.cost;
      ctx.save();
      ctx.globalAlpha = 0.9;
      // body preview
      ctx.fillStyle = valid ? 'rgba(100,220,140,0.55)' : 'rgba(220,80,80,0.45)';
      ctx.translate(x,y);
      ctx.rotate(rotatePreview);
      ctx.fillRect(-14,-14,28,28);
      ctx.restore();

      // range
      ctx.save();
      ctx.fillStyle = valid ? 'rgba(120,200,160,0.08)' : 'rgba(200,100,100,0.06)';
      ctx.beginPath(); ctx.arc(x,y, def.range, 0, Math.PI*2); ctx.fill();
      ctx.restore();
    }
  }

  function drawPath() {
    ctx.save();
    
    // Draw all paths
    for (let pathIdx = 0; pathIdx < paths.length; pathIdx++) {
      const path = paths[pathIdx];
      const isSecondary = pathIdx > 0;
      
      // Adjust opacity for secondary paths
      const alpha = isSecondary ? 0.6 : 1.0;
      
      // Outer earth
      ctx.lineWidth = 20;
      ctx.lineCap = 'round';
      ctx.strokeStyle = isSecondary ? `rgba(43, 58, 45, ${alpha})` : '#2b3a2d';
      ctx.beginPath();
      ctx.moveTo(path[0].x, path[0].y);
      for (let i=1;i<path.length;i++) ctx.lineTo(path[i].x, path[i].y);
      ctx.stroke();
      
      // Inner trail
      ctx.strokeStyle = isSecondary ? `rgba(63, 105, 74, ${alpha})` : '#3f694a';
      ctx.lineWidth=12;
      ctx.beginPath();
      ctx.moveTo(path[0].x, path[0].y);
      for (let i=1;i<path.length;i++) ctx.lineTo(path[i].x, path[i].y);
      ctx.stroke();
    }
    
    ctx.restore();
  }

  // Restart logic
  function restartGame() {
    // Clear timers
    if (spawnTimerId) { clearInterval(spawnTimerId); spawnTimerId = null; }
    if (autoNextTimerId) { clearTimeout(autoNextTimerId); autoNextTimerId = null; }
    spawning = false;

    // Reset state
    enemies.length = 0;
    towers.length = 0;
    raptorLeaps.length = 0;
    rushStrikes.length = 0;
    spits.length = 0;
    acidPools.length = 0;
    spikes.length = 0;

    money = gameSettings.startingMoney;
    lives = gameSettings.startingLives;
    wave = 0;
    gameSpeed = 1;
    fastBtn.classList.remove('active');
    fastBtn.textContent = 'x2 Speed';
    infoEl.textContent = 'Select a dino tower and click to place (not on the path). Press R to rotate preview.';

    // Sync HUD
    updateHUD();

    // Restart loop if it had stopped
    loopRunning = true;
    last = performance.now();
    requestAnimationFrame(loop);
  }

  // Resize helper
  function fitCanvas() {
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', fitCanvas);

  // Initial UI sync
  updateHUD();

  // Utility to hide main menu and any open modals/tooltips
  function hideMainMenuAndModals() {
    if (mainMenuEl) {
      mainMenuEl.setAttribute('hidden','');
      mainMenuEl.setAttribute('aria-hidden','true');
      mainMenuEl.style.display = 'none';  // Force hide with CSS as well
    }
    if (wikiModal && !wikiModal.hasAttribute('hidden')) {
      wikiModal.setAttribute('hidden','');
      wikiModal.setAttribute('aria-hidden','true');
    }
    document.body.classList.remove('modal-open');
    if (typeof hideTooltip === 'function') hideTooltip();
    
    // Resume game if it was paused
    if (isPaused) {
      resumeGame();
    }
  }
  
  // Show main menu as pause menu
  function showMainMenuAsPause() {
    if (mainMenuEl) {
      // Pause the game
      pauseGame();
      
      // Update menu title to show it's paused
      const menuTitle = mainMenuEl.querySelector('.menu-header h1');
      if (menuTitle) {
        menuTitle.textContent = 'Dinosaur Defense — Paused';
      }
      
      // Show the menu
      mainMenuEl.removeAttribute('hidden');
      mainMenuEl.setAttribute('aria-hidden', 'false');
      mainMenuEl.style.display = '';
    }
  }
  
  // Pause game functionality
  function pauseGame() {
    if (!isPaused) {
      isPaused = true;
      previousGameSpeed = gameSpeed;
      gameSpeed = 0; // Stop all game updates
      if (pauseBtn) pauseBtn.textContent = 'Resume';
    }
  }
  
  // Resume game functionality
  function resumeGame() {
    if (isPaused) {
      isPaused = false;
      gameSpeed = previousGameSpeed;
      if (pauseBtn) pauseBtn.textContent = 'Pause';
      
      // Reset menu title
      const menuTitle = mainMenuEl?.querySelector('.menu-header h1');
      if (menuTitle) {
        menuTitle.textContent = 'Dinosaur Defense — Main Menu';
      }
    }
  }

  // ---- Main menu & wiki wiring ----
  // Map selection handler
  if (mapListEl) {
    mapListEl.addEventListener('click', (e) => {
      const li = e.target.closest('li[data-map]');
      if (!li) return;
      // mark selected in UI
      mapListEl.querySelectorAll('.mapItem').forEach(n => n.classList.remove('selected'));
      li.classList.add('selected');
      const id = li.getAttribute('data-map');
      loadMap(id);
    });
  }

  // Play button: hide menu and start game on chosen map
  if (menuPlayBtn) {
    menuPlayBtn.addEventListener('click', () => {
      // If game is paused, just resume
      if (isPaused) {
        hideMainMenuAndModals();
      } else {
        hideMainMenuAndModals();
        // reload map and restart game
        loadMap(currentMapId);
        restartGame();
        // start immediate first wave
        startNextWave();
      }
    });
  }

  // Allow closing the main menu without starting the game
  if (menuCloseBtn) {
    menuCloseBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      hideMainMenuAndModals();
    });
  }

  // Keyboard: ESC toggles pause/menu, P pauses
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (mainMenuEl && mainMenuEl.hasAttribute('hidden')) {
        showMainMenuAsPause();
      } else {
        hideMainMenuAndModals();
      }
    } else if (e.key === 'p' || e.key === 'P') {
      if (mainMenuEl && mainMenuEl.hasAttribute('hidden')) {
        showMainMenuAsPause();
      } else {
        hideMainMenuAndModals();
      }
    }
  });

  // Wiki modal open/close — improved accessibility and backdrop handling
  if (menuWikiBtn && wikiModal) {
    menuWikiBtn.addEventListener('click', () => {
      wikiModal.removeAttribute('hidden');
      wikiModal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      // move focus into modal for keyboard users
      if (closeWikiBtn) closeWikiBtn.focus();
    });
  }
  if (closeWikiBtn && wikiModal) {
    closeWikiBtn.addEventListener('click', () => {
      wikiModal.setAttribute('hidden', '');
      wikiModal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      if (typeof hideTooltip === 'function') hideTooltip();
    });
  }
  // Close modal when clicking the backdrop (but not when interacting with modal-card)
  if (wikiModal) {
    wikiModal.addEventListener('click', (e) => {
      if (e.target === wikiModal) {
        wikiModal.setAttribute('hidden', '');
        wikiModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        if (typeof hideTooltip === 'function') hideTooltip();
      }
    });
  }
  
  // Options modal open/close
  if (menuOptionsBtn && optionsModal) {
    menuOptionsBtn.addEventListener('click', () => {
      optionsModal.removeAttribute('hidden');
      optionsModal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      applySettings(); // Update UI with current settings
    });
  }
  
  if (closeOptionsBtn && optionsModal) {
    closeOptionsBtn.addEventListener('click', () => {
      optionsModal.setAttribute('hidden', '');
      optionsModal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
    });
  }
  
  // Close options modal when clicking backdrop
  if (optionsModal) {
    optionsModal.addEventListener('click', (e) => {
      if (e.target === optionsModal) {
        optionsModal.setAttribute('hidden', '');
        optionsModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
      }
    });
  }
  
  // Options controls event listeners
  const setupOptionsListeners = () => {
    // Sliders with value display
    const startingMoneySlider = document.getElementById('startingMoney');
    const startingLivesSlider = document.getElementById('startingLives');
    const waveRewardSlider = document.getElementById('waveReward');
    const masterVolumeSlider = document.getElementById('masterVolume');
    
    if (startingMoneySlider) {
      startingMoneySlider.addEventListener('input', (e) => {
        const value = e.target.value;
        document.getElementById('startingMoneyValue').textContent = value;
        gameSettings.startingMoney = parseInt(value);
      });
    }
    
    if (startingLivesSlider) {
      startingLivesSlider.addEventListener('input', (e) => {
        const value = e.target.value;
        document.getElementById('startingLivesValue').textContent = value;
        gameSettings.startingLives = parseInt(value);
      });
    }
    
    if (waveRewardSlider) {
      waveRewardSlider.addEventListener('input', (e) => {
        const value = e.target.value;
        document.getElementById('waveRewardValue').textContent = value;
        gameSettings.waveReward = parseInt(value);
      });
    }
    
    if (masterVolumeSlider) {
      masterVolumeSlider.addEventListener('input', (e) => {
        const value = e.target.value;
        document.getElementById('masterVolumeValue').textContent = value + '%';
        gameSettings.masterVolume = parseInt(value);
      });
    }
    
    // Save button
    const saveBtn = document.getElementById('saveOptions');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        // Collect all settings
        const difficultySelect = document.getElementById('difficultySelect');
        const showRangesCheck = document.getElementById('showRanges');
        const showDamageCheck = document.getElementById('showDamageNumbers');
        const particleCheck = document.getElementById('particleEffects');
        const screenShakeCheck = document.getElementById('screenShake');
        const soundEffectsCheck = document.getElementById('soundEffects');
        const musicEnabledCheck = document.getElementById('musicEnabled');
        const confirmPlacementCheck = document.getElementById('confirmPlacement');
        const gridSnapCheck = document.getElementById('gridSnap');
        const keyboardShortcutsCheck = document.getElementById('keyboardShortcuts');
        
        gameSettings.difficulty = difficultySelect.value;
        gameSettings.showRanges = showRangesCheck.checked;
        gameSettings.showDamageNumbers = showDamageCheck.checked;
        gameSettings.particleEffects = particleCheck.checked;
        gameSettings.screenShake = screenShakeCheck.checked;
        gameSettings.soundEffects = soundEffectsCheck.checked;
        gameSettings.musicEnabled = musicEnabledCheck.checked;
        gameSettings.confirmPlacement = confirmPlacementCheck.checked;
        gameSettings.gridSnap = gridSnapCheck.checked;
        gameSettings.keyboardShortcuts = keyboardShortcutsCheck.checked;
        
        saveSettings();
        infoTemp('Settings saved!', 1500);
        
        // Close modal
        optionsModal.setAttribute('hidden', '');
        optionsModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
      });
    }
    
    // Reset button
    const resetBtn = document.getElementById('resetOptions');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        gameSettings = {
          difficulty: 'normal',
          startingMoney: 100,
          startingLives: 10,
          waveReward: 20,
          showRanges: true,
          showDamageNumbers: false,
          particleEffects: true,
          screenShake: false,
          masterVolume: 70,
          soundEffects: true,
          musicEnabled: true,
          confirmPlacement: false,
          gridSnap: false,
          keyboardShortcuts: true
        };
        applySettings();
        infoTemp('Settings reset to defaults', 1500);
      });
    }
  };
  
  // Initialize options listeners
  setupOptionsListeners();
  
  // Load saved settings on startup
  loadSettings();
  
  // Load tips on startup
  loadTips();

  // show main menu by default (game hidden until play)
  if (mainMenuEl) {
    mainMenuEl.removeAttribute('hidden');
    mainMenuEl.setAttribute('aria-hidden', 'false');
    mainMenuEl.style.display = '';  // Ensure display is not none
  }

// Global tooltip behavior for elements with data-desc
const tooltipEl = document.getElementById('tooltip');
function positionTooltip(x, y) {
  if (!tooltipEl) return;
  const offsetX = 14, offsetY = 16;
  let left = x + offsetX;
  let top = y + offsetY;
  const rect = tooltipEl.getBoundingClientRect ? tooltipEl.getBoundingClientRect() : { width: 0, height: 0 };
  const vw = window.innerWidth || 0, vh = window.innerHeight || 0;
  if (left + rect.width + 12 > vw) left = vw - rect.width - 12;
  if (top + rect.height + 12 > vh) top = vh - rect.height - 12;
  tooltipEl.style.left = left + 'px';
  tooltipEl.style.top = top + 'px';
}
function showTooltip(text, x, y) {
  if (!tooltipEl) return;
  // Suppress tooltips when a modal is open to avoid visual clutter
  if (document.body.classList.contains('modal-open')) return;
  tooltipEl.textContent = text || '';
  tooltipEl.hidden = false;
  positionTooltip(x, y);
}
function hideTooltip() {
  if (!tooltipEl) return;
  tooltipEl.hidden = true;
}
document.addEventListener('mousemove', (e) => {
  const attrEl = e.target && e.target.closest ? e.target.closest('[data-desc]') : null;
  if (attrEl) {
    const text = attrEl.getAttribute('data-desc') || '';
    showTooltip(text, e.clientX, e.clientY);
  } else {
    hideTooltip();
  }
});
document.addEventListener('mouseleave', hideTooltip);
  // Start loop
  requestAnimationFrame(loop);

  // Wave button exposed for console
  window._TD = {
    enemies, towers, paths,
    startNextWave,
    restartGame,
    moneyRef: ()=>money
  };

})();