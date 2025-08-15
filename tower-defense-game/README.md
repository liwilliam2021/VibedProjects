# Tower Defense Game (Visuals Note)

This lightweight Dinosaur Tower Defense game uses a procedural sprite system and a simple canvas renderer. Recent visual improvements were added to enhance the retro pixel-art feel:

- Particle effects (pixelated square particles) for hits, deaths, and acid splashes.
- Floating damage numbers that can optionally be shown.
- Localized hit flashes and small camera shake on heavy hits.
- Pixel-art friendly rendering with smoothing disabled.

Tuning & Debugging
- The effects module is available at `effects.js`. At runtime the API is exposed on the global `VFX` object (also accessible as `window._VFX` for console debugging).
- Configuration and runtime flags:
  - `VFX.config` — tweak particle lifetime, speeds, sizes, damage-number font and life, and flash duration.
  - `VFX.setFlags({ particles: true, showDamageNumbers: false, screenShake: false })` — enable/disable categories of effects.
- Settings in the in-game Options menu now sync to the VFX flags automatically when saved (`Particle Effects`, `Show Damage Numbers`, `Screen Shake`).

Performance
- Effects use internal pooling with conservative defaults (max particles and max damage numbers) to avoid frame drops.
- If you observe performance issues on slower devices, reduce `VFX.config.maxParticles` via the console (e.g. `window._VFX.config.maxParticles = 120`).

Where to look
- Runtime effects implementation: [`tower-defense-game/effects.js`](tower-defense-game/effects.js:1)
- Main game logic + VFX hooks: [`tower-defense-game/main.js`](tower-defense-game/main.js:1)
- Styling (pixelated canvas): [`tower-defense-game/styles.css`](tower-defense-game/styles.css:33)

How to test quickly
1. Open `index.html` in a modern browser.
2. In Options enable `Particle Effects` and `Show Damage Numbers`.
3. Start a wave and observe hits; large hits will spawn small camera shake and bursts.
4. For rapid experimentation, open the console and toggle flags:
   - `window._VFX.setFlags({ particles: true, showDamageNumbers: true, screenShake: true })`
   - Adjust parameters: `window._VFX.config.particleLifeMax = 1.0`

This README note complements the in-game Options UI and helps developers quickly tune and debug the new visual systems.