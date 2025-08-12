// Wiki system for Dinosaur Tower Defense
(function() {
  let gameData = null;
  let enemiesData = null;
  let tipsData = null;
  let currentPage = 'dinosaurs';
  let currentTipIndex = 0;
  
  // Load JSON data
  async function loadWikiData() {
    try {
      const [gameResponse, enemiesResponse, tipsResponse] = await Promise.all([
        fetch('game-data.json'),
        fetch('enemies-data.json'),
        fetch('tips.json')
      ]);
      
      gameData = await gameResponse.json();
      enemiesData = await enemiesResponse.json();
      tipsData = await tipsResponse.json();
      
      // Initialize wiki when data is loaded
      initializeWiki();
    } catch (error) {
      console.error('Failed to load wiki data:', error);
      document.getElementById('wikiContent').innerHTML = `
        <div class="wiki-error">
          <p>Failed to load wiki data. Please refresh the page.</p>
        </div>
      `;
    }
  }
  
  function initializeWiki() {
    // Add click handlers to navigation buttons
    const navButtons = document.querySelectorAll('.wiki-nav-btn');
    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.getAttribute('data-page');
        switchPage(page);
      });
    });
    
    // Load initial page
    switchPage('dinosaurs');
  }
  
  function switchPage(page) {
    currentPage = page;
    
    // Update active nav button
    document.querySelectorAll('.wiki-nav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-page') === page);
    });
    
    // Load page content
    const contentEl = document.getElementById('wikiContent');
    
    switch(page) {
      case 'dinosaurs':
        contentEl.innerHTML = renderDinosaursPage();
        break;
      case 'enemies':
        contentEl.innerHTML = renderEnemiesPage();
        break;
      case 'overview':
        contentEl.innerHTML = renderOverviewPage();
        break;
      default:
        contentEl.innerHTML = '<p>Page not found</p>';
    }
    
    // Add click handlers for expandable entries
    addEntryClickHandlers();
  }
  
  // Helper: render "Coming Soon" Mythic previews (not in game data)
  function renderMythicPreview(name, tease) {
    return `
      <div class="wiki-entry tower-entry mythic" data-tower="${name.replace(/\\s+/g,'')}">
        <div class="entry-header">
          <span class="entry-emoji">✨</span>
          <div class="entry-title">
            <h4>${name}</h4>
            <span class="entry-type">Mythic — Coming Soon</span>
          </div>
          <span class="expand-icon">▼</span>
        </div>
        <div class="entry-content" style="display: none;">
          <div class="entry-section">
            <h5>Preview</h5>
            <p>${tease}</p>
          </div>
        </div>
      </div>
    `;
  }
  function renderDinosaursPage() {
    if (!gameData || !gameData.towers) {
      return '<p>Loading dinosaur data...</p>';
    }
    
    let html = `
      <div class="wiki-page dinosaurs-page">
        <h3 class="wiki-title">🦖 Dinosaur Defense Forces</h3>
        <p class="wiki-intro">
          These prehistoric warriors have been awakened and trained to defend against the colonial invasion. 
          Each species brings unique abilities honed over millions of years of evolution.
        </p>
        <div class="wiki-entries">
    `;
    
    // Group towers by rarity
    const rarityOrder = ['Common', 'Uncommon', 'Rare', 'Legendary', 'Mythic'];
    const towersByRarity = {};
    
    for (const [key, tower] of Object.entries(gameData.towers)) {
      const rarity = tower.rarity || 'Common';
      if (!towersByRarity[rarity]) {
        towersByRarity[rarity] = [];
      }
      towersByRarity[rarity].push({ key, ...tower });
    }
    
    // Render towers by rarity group
    for (const rarity of rarityOrder) {
      if (!towersByRarity[rarity]) continue;
      
      html += `<div class="rarity-group">`;
      html += `<h4 class="rarity-header ${rarity.toLowerCase()}">${rarity} Towers</h4>`;
      
      for (const tower of towersByRarity[rarity]) {
        const rarityClass = tower.rarity ? tower.rarity.toLowerCase() : 'common';
        html += `
          <div class="wiki-entry tower-entry ${rarityClass}" data-tower="${tower.key}">
            <div class="entry-header">
              <span class="entry-emoji">${tower.emoji}</span>
              <div class="entry-title">
                <h4>${tower.name}</h4>
                <span class="entry-cost">Cost: ${tower.cost}</span>
                <span class="entry-type">${tower.type}</span>
              </div>
              <span class="expand-icon">▼</span>
            </div>
            <div class="entry-content" style="display: none;">
              <div class="stats-grid">
                <div class="stat-item damage">
                  <span class="stat-label">⚔️ Damage</span>
                  <span class="stat-value">${tower.damage}</span>
                </div>
                <div class="stat-item range">
                  <span class="stat-label">🎯 Range</span>
                  <span class="stat-value">${tower.range}</span>
                </div>
                <div class="stat-item speed">
                  <span class="stat-label">⚡ Attack Speed</span>
                  <span class="stat-value">${tower.attackSpeed}</span>
                </div>
                <div class="stat-item special">
                  <span class="stat-label">✨ Special Ability</span>
                  <span class="stat-value">${tower.special}</span>
                </div>
              </div>
              
              <div class="entry-section">
                <h5>📋 Strategy</h5>
                <p>${tower.strategy}</p>
              </div>
              
              <div class="entry-section">
                <h5>📖 Lore</h5>
                <p class="lore-text">${tower.lore}</p>
              </div>
              
              <div class="entry-section fun-fact">
                <h5>🎲 Fun Fact</h5>
                <p>${tower.funFact}</p>
              </div>
            </div>
          </div>
        `;
      }
      
      html += `</div>`;
    }
    
    html += `
        </div>

        <div class="rarity-group">
          <h4 class="rarity-header mythic">Mythic Beasts — Coming Soon</h4>
          ${renderMythicPreview('King Kong', 'Titanic simian with skyscraper-scale throws and fear roars.')}
          ${renderMythicPreview('Kraken', 'Abyssal horror that lashes paths with inky tentacles and tidal surges.')}
          ${renderMythicPreview('Sky Whale', 'Drifting colossus that creates gravity wells and wind bursts.')}
          ${renderMythicPreview('Supersaur', 'Primeval apex whose footsteps rewrite the path itself.')}
          ${renderMythicPreview('Fungal King', 'Spore monarch that spreads parasitic mycelium, enthralling foes.')}
        </div>
      </div>
    `;
    
    return html;
  }
  
  function renderEnemiesPage() {
    if (!enemiesData || !enemiesData.enemies) {
      return '<p>Loading enemy data...</p>';
    }
    
    let html = `
      <div class="wiki-page enemies-page">
        <h3 class="wiki-title">⚔️ Belgian Free State Colonial Forces</h3>
    `;
    
    // Add the new lore section if it exists
    if (enemiesData.lore) {
      html += `
        <div class="wiki-lore-box">
          <h4>${enemiesData.lore.title}</h4>
          <p>${enemiesData.lore.story}</p>
        </div>
      `;
    }
    
    html += `
        <div class="wiki-disclaimer">
          <strong>Historical Context:</strong> The enemies in this game are based on the real atrocities
          committed in the Congo Free State (1885-1908) under Leopold II of Belgium, where millions died
          under brutal colonial exploitation.
        </div>
        <div class="wiki-entries">
    `;
    
    // Group enemies by type
    const typeOrder = ['Basic', 'Fast', 'Ranged', 'Heavy', 'Elite', 'Support', 'Special', 'Commander', 'Elite Heavy', 'Boss'];
    const enemiesByType = {};
    
    for (const [key, enemy] of Object.entries(enemiesData.enemies)) {
      const type = enemy.type || 'Basic';
      if (!enemiesByType[type]) {
        enemiesByType[type] = [];
      }
      enemiesByType[type].push({ key, ...enemy });
    }
    
    // Render enemies by type
    for (const type of typeOrder) {
      if (!enemiesByType[type]) continue;
      
      html += `<div class="enemy-type-group">`;
      html += `<h4 class="type-header">${type} Units</h4>`;
      
      for (const enemy of enemiesByType[type]) {
        html += `
          <div class="wiki-entry enemy-entry" data-enemy="${enemy.key}">
            <div class="entry-header">
              <span class="entry-emoji">👤</span>
              <div class="entry-title">
                <h4>${enemy.name}</h4>
                <span class="entry-stats">HP: ${enemy.hp} | Speed: ${enemy.speed} | Reward: ${enemy.reward}</span>
              </div>
              <span class="expand-icon">▼</span>
            </div>
            <div class="entry-content" style="display: none;">
              <div class="entry-section">
                <h5>Appearance</h5>
                <p>${enemy.appearance}</p>
              </div>
              
              <div class="entry-section">
                <h5>Combat Strategy</h5>
                <p>${enemy.strategy}</p>
              </div>
              
              <div class="entry-section">
                <h5>Historical Lore</h5>
                <p class="lore-text">${enemy.lore}</p>
              </div>
              
              <div class="entry-section historical-note">
                <h5>📚 Historical Note</h5>
                <p>${enemy.historicalNote}</p>
              </div>
              
              <div class="entry-section fun-fact">
                <h5>🎲 Fun Fact</h5>
                <p>${enemy.funFact}</p>
              </div>
            </div>
          </div>
        `;
      }
      
      html += `</div>`;
    }
    
    html += `
        </div>
      </div>
    `;
    
    return html;
  }
  
  function renderOverviewPage() {
    // Get a random tip if tips are loaded
    let tipHtml = '';
    if (tipsData && tipsData.tips && tipsData.tips.length > 0) {
      const tip = tipsData.tips[currentTipIndex];
      tipHtml = `
        <div class="wiki-tip-box">
          <div class="tip-header">
            <span class="tip-icon">💡</span>
            <span class="tip-category">${tip.category} Tip</span>
            <button class="tip-refresh" onclick="window.nextTip()">↻ Next Tip</button>
          </div>
          <p class="tip-text">${tip.text}</p>
        </div>
      `;
    }
    
    return `
      <div class="wiki-page overview-page">
        <h3 class="wiki-title">📜 Game Overview</h3>
        
        ${tipHtml}
        
        <div class="overview-section">
          <h4>The Lost Expedition</h4>
          <p>
            In 1897, Leopold II's forces discovered the hidden Mkuyu Gorge - a volcanic valley where dinosaurs
            survived and evolved for millions of years. The colonial expedition, driven by greed, saw only
            resources to exploit. But these weren't mere beasts - they were intelligent beings who had formed
            bonds with local tribes over generations.
          </p>
          <p>
            Now, mechanized colonial forces clash with prehistoric defenders in a battle that will determine
            the fate of both species. Command the dinosaur resistance and repel the invaders before they can
            establish their brutal regime in this lost world.
          </p>
        </div>
        
        <div class="overview-section">
          <h4>Game Mechanics</h4>
          <ul>
            <li><strong>Tower Defense:</strong> Place dinosaur towers along paths to stop waves of colonial forces</li>
            <li><strong>Economy:</strong> Earn gold by defeating enemies and use Stonklodons for passive income</li>
            <li><strong>Synergies:</strong> Combine different dinosaur abilities for maximum effectiveness</li>
            <li><strong>Wave System:</strong> Face increasingly difficult waves with boss enemies every 7 waves</li>
            <li><strong>Multiple Paths:</strong> Later maps feature multiple routes that enemies can take</li>
          </ul>
        </div>
        
        <div class="overview-section">
          <h4>Tower Synergies</h4>
          <ul>
            <li><strong>Slow + Damage:</strong> Brachiosaurus slows enemies for other towers to maximize damage</li>
            <li><strong>Knockback Chains:</strong> Triceratops and Ankylosaurus can juggle enemies</li>
            <li><strong>Area Denial:</strong> Dilophosaurus and Spinosaurus create no-go zones</li>
            <li><strong>Pierce Lines:</strong> Stegosaurus excels when enemies are funneled into lines</li>
            <li><strong>Economy First:</strong> Early Stonklodons compound into late-game legendary towers</li>
          </ul>
        </div>
        
        <div class="overview-section">
          <h4>Historical Context</h4>
          <p>
            The Congo Free State (1885-1908) was the personal property of King Leopold II of Belgium. 
            Under the guise of humanitarian work, Leopold's regime killed an estimated 10 million Congolese 
            through forced labor, starvation, and outright murder. The rubber quota system led to widespread 
            mutilation, with hands severed as proof that bullets hadn't been "wasted."
          </p>
          <p>
            This game uses fantasy elements (dinosaurs) to create a scenario where these historical villains 
            can be defeated, offering a form of cathartic alternative history where the oppressed have 
            powerful defenders.
          </p>
        </div>
        
        <div class="overview-section">
          <h4>Tips for New Players</h4>
          <ul>
            <li>Start with Raptor Nests - they're cheap and effective against early waves</li>
            <li>Place Brachiosaurus towers at chokepoints to maximize their slowing aura</li>
            <li>Save for at least one Stonklodon early - the economy boost is crucial</li>
            <li>Don't neglect area damage - later waves feature dense enemy clusters</li>
            <li>Learn enemy types - fast units need slows, heavy units need sustained damage</li>
            <li>Experiment with tower combinations - synergy is key to victory</li>
          </ul>
        </div>
      </div>
    `;
  }
  
  function addEntryClickHandlers() {
    const entries = document.querySelectorAll('.wiki-entry');
    entries.forEach(entry => {
      const header = entry.querySelector('.entry-header');
      const content = entry.querySelector('.entry-content');
      const expandIcon = entry.querySelector('.expand-icon');
      
      if (header && content) {
        header.addEventListener('click', () => {
          const isExpanded = content.style.display !== 'none';
          
          // Close all other entries in the same page
          const pageEntries = entry.closest('.wiki-page').querySelectorAll('.wiki-entry');
          pageEntries.forEach(e => {
            const c = e.querySelector('.entry-content');
            const i = e.querySelector('.expand-icon');
            if (c) c.style.display = 'none';
            if (i) i.textContent = '▼';
            e.classList.remove('expanded');
          });
          
          // Toggle this entry
          if (!isExpanded) {
            content.style.display = 'block';
            if (expandIcon) expandIcon.textContent = '▲';
            entry.classList.add('expanded');
          }
        });
      }
    });
  }
  
  // Function to cycle through tips
  window.nextTip = function() {
    if (tipsData && tipsData.tips && tipsData.tips.length > 0) {
      currentTipIndex = (currentTipIndex + 1) % tipsData.tips.length;
      switchPage('overview'); // Refresh the overview page to show new tip
    }
  };
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    // Load wiki data when modal is opened
    const wikiBtn = document.getElementById('menuWiki');
    if (wikiBtn) {
      wikiBtn.addEventListener('click', () => {
        if (!gameData || !enemiesData || !tipsData) {
          loadWikiData();
        }
      });
    }
  });
})();