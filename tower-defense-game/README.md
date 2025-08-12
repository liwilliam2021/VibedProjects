# Tower Defense Game

A lightweight, vanilla HTML5 Canvas tower defense game. No build step or dependencies required.

How to Run
- Open `index.html` in any modern web browser (Chrome, Edge, Firefox, Safari).
- Optional: Serve via a simple HTTP server if your browser restricts local file access.

Files
- index.html — Main page with canvas and HUD
- styles.css — Styling for layout and HUD
- main.js — Game logic, rendering, input handling

Gameplay
- You start with Money: 100 and Lives: 10.
- Click on the map (not on the path) to place a tower (50 money).
- Press the “Start Wave” button to spawn enemies.
- Press the “x2 Speed” button to toggle fast-forward.
- Towers automatically target and shoot enemies in range.
- Enemies that reach the end subtract Lives. When Lives reach 0, the game ends.
- Killing enemies grants additional Money.

Controls
- Mouse Move: Preview tower placement position.
- Mouse Click: Place a tower (if you have enough money and it’s not on the path).
- Keyboard: R to rotate the placement preview (cosmetic).

Waves
- Each wave increases enemy count, HP, and speed.
- Start waves manually using the Start Wave button.

Notes
- Basic visuals are intentionally simple for readability.
- Collision and path checks prevent placing towers on the path.
- You can tweak constants like range, damage, prices in `main.js` to change difficulty.

Changelog
- Added multiple paths for advanced maps (Coastal Cliffs has 2 paths, Volcanic Pass has 3 paths)
- Lengthened the path for Jungle Ridge (easy map) to make it more forgiving for beginners
- Enemies now randomly choose between available paths based on configurable weights
- Visual distinction between primary and secondary paths (secondary paths appear with reduced opacity)

Future Enhancements
- Add multiple tower types (e.g., slow, splash, sniper).
- Add sell/upgrade mechanics.
- Add path editor / multiple maps.
- Add sounds and improved art.

---

Running Locally (step-by-step)

Option A — Open the file directly
- Finder: double‑click index.html
- Or from Terminal:
  - macOS:
    open index.html
Notes: This usually works since the game is pure HTML/CSS/JS with no network calls. If your browser blocks local file access, use Option B.

Option B — Serve with Python (recommended)
- From the repo root:
  - cd tower-defense-game
  - python3 -m http.server 8000
- Open your browser to:
  - http://localhost:8000
- Alternatively, if you start the server from the root of this workspace instead of the folder:
  - python3 -m http.server 8000
  - Then open: http://localhost:8000/tower-defense-game/

Option C — Serve with Node (npx http-server)
- cd tower-defense-game
- npx http-server -p 8000
- Open http://localhost:8000

Option D — VS Code Live Server
- Install the “Live Server” extension
- Right‑click index.html → “Open with Live Server”
- Your browser will open on a local address (e.g., http://127.0.0.1:5500)

Troubleshooting
- Port already in use: pick another port (e.g., 8080) in the commands above.
- Blank screen or nothing happens: open the browser devtools console and check for errors; ensure you served the folder (not just the parent) or adjusted the URL path correctly.
- file:// CORS/security warnings: run a local server (Options B–D) instead of opening the file directly.

Quick Start Recap
- Easiest cross‑platform:
  - cd tower-defense-game
  - python3 -m http.server 8000
  - Visit http://localhost:8000
