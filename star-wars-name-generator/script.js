"use strict";

/**
 * Star Wars Name Generator (deterministic, based on user's name)
 * - No network calls, runs entirely in-browser
 * - Uses the user's input as a seed to generate consistent names
 * - Categories: Jedi, Sith, Bounty Hunter, Clone Trooper, Droid
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("nameForm");
  const input = document.getElementById("realName");
  const results = document.getElementById("results");

  const outJedi = document.getElementById("jediName");
  const outSith = document.getElementById("sithName");
  const outHunter = document.getElementById("hunterName");
  const outClone = document.getElementById("cloneName");
  const outDroid = document.getElementById("droidName");

  // Initialize subtle pointer parallax (skips if reduced motion)
  setupParallax();
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const raw = (input.value || "").trim();
    if (!raw) {
      results.classList.add("hidden");
      return;
    }

    const { first, last, seedStr } = parseName(raw);
    const seed = hashString(seedStr);
    const rng = makeLCG(seed);

    const jedi = generateJediName(first, last, rng);
    const sith = generateSithName(first, last, rng);
    const hunter = generateBountyHunterName(first, last, rng);
    const clone = generateCloneDesignation(first, last, rng);
    const droid = generateDroidName(first, last, rng);

    outJedi.textContent = jedi;
    outSith.textContent = sith;
    outHunter.textContent = hunter;
    outClone.textContent = clone;
    outDroid.textContent = droid;

    results.classList.remove("hidden");

    // Brief hyperspace burst feedback
    triggerHyperspaceBurst();
  });
});

/* ------------------------ Utilities ------------------------ */

function normalize(str) {
  return (str || "")
    .toLowerCase()
    .replace(/[^a-z\s'-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseName(input) {
  const n = normalize(input);
  const parts = n.split(" ").filter(Boolean);
  const first = (parts[0] || "").replace(/[^a-z]/g, "");
  const last = (parts.length > 1 ? parts[parts.length - 1] : "").replace(/[^a-z]/g, "");

  // Fallbacks to keep algorithms stable even with a single name
  const f = first || "anon";
  const l = last || rotateString(f, 2);

  return { first: f, last: l, seedStr: `${f}|${l}` };
}

function rotateString(s, k) {
  if (!s) return s;
  const n = s.length;
  const r = ((k % n) + n) % n;
  return s.slice(r) + s.slice(0, r);
}

function cap(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

// Simple, deterministic 32-bit hash (djb2 variant)
function hashString(str) {
  let h = 5381 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) + h + str.charCodeAt(i)) >>> 0; // h * 33 + c
  }
  return h >>> 0;
}

// Linear Congruential Generator (LCG) returning [0,1)
function makeLCG(seed) {
  let state = seed >>> 0;
  return function rand() {
    // Numerical Recipes LCG constants
    state = (1664525 * state + 1013904223) >>> 0;
    // scale to [0,1)
    return state / 4294967296;
  };
}

function pick(arr, rng) {
  return arr[Math.floor(rng() * arr.length)];
}

function sampleDistinct(arr, k, rng) {
  const copy = arr.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, k);
}

function safeSlice(s, start, len) {
  // Supports negative start; wraps if needed
  if (!s) return "";
  const n = s.length;
  let st = start;
  if (st < 0) {
    st = n + st;
    if (st < 0) st = 0;
  }
  let en = st + len;
  if (st >= n) st = n - 1;
  if (en > n) en = n;
  if (st < 0) st = 0;
  if (en < 0) en = 0;
  return s.slice(st, en);
}

function reverse(s) {
  return s.split("").reverse().join("");
}

function ensureVowelBalance(base, rng) {
  // If base ends up vowel-starved, inject a vowel syllable
  const vowels = ["a", "e", "i", "o", "u"];
  const hasVowel = /[aeiou]/.test(base);
  if (!hasVowel) {
    const v = pick(vowels, rng);
    const pos = Math.max(1, Math.min(base.length - 1, Math.floor(rng() * base.length)));
    return base.slice(0, pos) + v + base.slice(pos);
  }
  return base;
}

/* --------------------- Syllable banks ---------------------- */

// Light-side/Jedi-friendly syllables
const JEDI_A = [
  "ka", "ra", "lo", "an", "shi", "zi", "va", "ori", "elu", "ari", "jen", "qu",
  "zor", "tal", "dra", "rin", "vek", "nari", "sora", "ty", "ila", "sai", "tera", "kae"
];
const JEDI_B = [
  "la", "dor", "ven", "ith", "ora", "wyn", "een", "mar", "os", "en", "oth", "ara",
  "esh", "ion", "ar", "is", "eon", "al", "ek", "or", "une", "iel", "ari", "othi"
];

// Sith-heavy, harsh endings
const SITH_END = [
  "us", "or", "ith", "ax", "ar", "eus", "an", "is", "os", "ren", "mal", "rax", "tor", "vex", "drax"
];

// Gritty bounty-hunter components
const BH_FIRST_SEEDS = [
  "Jax", "Kara", "Vex", "Rook", "Zed", "Nova", "Talon", "Kirr", "Sable", "Rek",
  "Nix", "Cade", "Ryn", "Bex", "Juno", "Aris", "Kade", "Lex", "Nyx", "Vora", "Zerin", "Sev"
];
const BH_LAST_SEEDS = [
  "Voss", "Drax", "Krynn", "Fenn", "Rendar", "Vossk", "Morne", "Skarn", "Vect",
  "Kordo", "Varro", "Kest", "Varren", "Vos", "Kane", "Marek", "Ordo", "Kass", "Vor", "Tane"
];

// Clone nicknames
const CLONE_NICKS = [
  "Echo", "Fives", "Blaze", "Havoc", "Scope", "Boomer", "Fixer", "Seeker", "Razor",
  "Spike", "Charger", "Rebel", "Vector", "Knockout", "Switch", "Torch", "Ghost", "Striker", "Watch"
];

// Droid letter candidates (weighted toward familiar letters)
const DROID_LETTERS = "RCKIGABSTPQLMNXZ";

/* ---------------------- Generators ------------------------ */

function generateJediName(first, last, rng) {
  // Classic mashup: first 3 of last + first 2 of first
  const baseRaw = (safeSlice(last, 0, 3) + safeSlice(first, 0, 2)).toLowerCase();
  const base = ensureVowelBalance(baseRaw, rng);

  // Construct a soft, mystic surname from syllables
  const syl1 = pick(JEDI_A, rng);
  const syl2 = pick(JEDI_B, rng);
  const surname = cap(syl1 + syl2);

  return `${cap(base)} ${surname}`;
}

function generateSithName(first, last, rng) {
  // Harsh core: last 2 of first + first 3 of reversed last
  const coreRaw = (safeSlice(first, -2, 2) + safeSlice(reverse(last), 0, 3)).toLowerCase();
  let core = coreRaw;

  // Harden up the consonant feel
  core = core.replace(/h/g, "kh").replace(/f/g, "ph");
  core = ensureVowelBalance(core, rng);

  // Trim/pad to look snappy
  if (core.length < 4) core += pick(["ar", "or", "an"], rng);
  const ending = pick(SITH_END, rng);

  return `Darth ${cap(core)}${ending}`;
}

function generateBountyHunterName(first, last, rng) {
  // Build a gritty first part using user's letters + optional apostrophe
  let chunkA = safeSlice(first, 0, 2) + safeSlice(last, -2, 2);
  chunkA = chunkA.toLowerCase();
  chunkA = ensureVowelBalance(chunkA, rng);

  // Occasionally inject an apostrophe for that Outer Rim flair
  if (rng() < 0.35 && chunkA.length > 2) {
    const pos = Math.floor(rng() * (chunkA.length - 1)) + 1;
    chunkA = chunkA.slice(0, pos) + "'" + chunkA.slice(pos);
  }

  // Second part: user's letters fused with a gritty suffix seed
  let chunkB = safeSlice(last, 0, 2);
  const suffixSeed = pick(BH_LAST_SEEDS, rng);
  // Blend: ensure at least one shared vowel or add connecting vowel
  const connecting = /[aeiou]$/.test(chunkB) || /^[aeiou]/.test(suffixSeed) ? "" : pick(["a", "e", "i", "o", "u"], rng);
  chunkB = (chunkB + connecting + suffixSeed).toLowerCase();

  // Title-case with some deterministic seed choice for the first token
  const maybeSeedFirst = rng() < 0.45 ? pick(BH_FIRST_SEEDS, rng) : cap(chunkA);

  return `${cap(maybeSeedFirst)} ${cap(chunkB)}`;
}

function generateCloneDesignation(first, last, rng) {
  const prefixes = ["CT", "CC", "RC", "ARC"];
  const prefix = pick(prefixes, rng);

  // 4-digit code derived from hash with zero padding
  const code = String(Math.floor(rng() * 10000)).padStart(4, "0");

  // Optional squad letter
  const squadLetter = String.fromCharCode(65 + Math.floor(rng() * 26)); // A-Z
  const includeSquad = rng() < 0.5;

  // Deterministic nickname chosen with a slight bias from user's initials
  const initials = (first[0] || "x") + (last[0] || "x");
  const nickBase = pick(CLONE_NICKS, rng);
  const nick =
    rng() < 0.5
      ? nickBase
      : cap(ensureVowelBalance(initials, rng)) + pick(["-One", "-Two", "-Zero"], rng);

  return includeSquad
    ? `${prefix}-${squadLetter}${code} "${nick}"`
    : `${prefix}-${code} "${nick}"`;
}

function generateDroidName(first, last, rng) {
  // Choose a pattern:
  // 1) L#-L#  (R2-D2 style)
  // 2) LL-##  (IG-88 style)
  // 3) L#L-## (K2-SO-esque)
  const pattern = Math.floor(rng() * 3);

  const L = () => DROID_LETTERS[Math.floor(rng() * DROID_LETTERS.length)];
  const D = () => String(Math.floor(rng() * 10));

  if (pattern === 0) {
    return `${L()}${D()}-${L()}${D()}`;
  } else if (pattern === 1) {
    return `${L()}${L()}-${D()}${D()}`;
  } else {
    return `${L()}${D()}${L()}-${D()}${D()}`;
  }
}

/* -------------------- End of generator -------------------- */

// Motion preferences helper
function isReducedMotion() {
  return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// Pointer-based parallax for starfield layers
function setupParallax() {
  if (isReducedMotion()) return;
  const layers = Array.from(document.querySelectorAll('.starfield .star-layer'));
  if (!layers.length) return;

  const strength = [0.25, 0.5, 0.9, 1.3, 1.8];

  let targetX = 0, targetY = 0;
  let curX = 0, curY = 0;
  let rafId = null;

  function onMove(e) {
    const ww = window.innerWidth;
    const wh = window.innerHeight;
    const p = ('touches' in e && e.touches && e.touches[0]) ? e.touches[0] : e;
    const dx = ((p.clientX ?? ww / 2) - ww / 2) / (ww / 2);
    const dy = ((p.clientY ?? wh / 2) - wh / 2) / (wh / 2);
    targetX = dx;
    targetY = dy;
    if (!rafId) rafStep();
  }

  function rafStep() {
    rafId = requestAnimationFrame(() => {
      curX += (targetX - curX) * 0.08;
      curY += (targetY - curY) * 0.08;

      layers.forEach((el, i) => {
        const s = strength[i] ?? strength[strength.length - 1];
        el.style.transform = `translate3d(${(-curX * s * 10).toFixed(2)}px, ${(-curY * s * 10).toFixed(2)}px, 0)`;
      });

      if (Math.abs(targetX - curX) > 0.001 || Math.abs(targetY - curY) > 0.001) {
        rafStep();
      } else {
        rafId = null;
      }
    });
  }

  window.addEventListener('mousemove', onMove, { passive: true });
  window.addEventListener('touchmove', onMove, { passive: true });

  window.addEventListener('blur', () => {
    layers.forEach(el => (el.style.transform = 'translate3d(0,0,0)'));
    targetX = targetY = curX = curY = 0;
  });
}

// Hyperspace burst overlay
function triggerHyperspaceBurst() {
  if (isReducedMotion()) return;
  const el = document.getElementById('hyperspace');
  if (!el) return;

  // Retrigger animation by toggling class
  el.classList.remove('active');
  // Force reflow to restart CSS animation
  void el.offsetWidth;
  el.classList.add('active');

  // Safety removal in case animationend doesn't fire
  const cleanup = () => {
    el.classList.remove('active');
    el.removeEventListener('animationend', cleanup);
  };
  el.addEventListener('animationend', cleanup);
}
