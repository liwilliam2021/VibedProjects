# Comprehensive Technical Analysis: Dinosaur Tower Implementations

## Table of Contents
1. [Canvas and Animation System](#canvas-and-animation-system)
2. [Color System](#color-system)
3. [Portrait Generation](#portrait-generation)
4. [Individual Dinosaur Implementations](#individual-dinosaur-implementations)
5. [Animation System](#animation-system)

---

## Canvas and Animation System

### Technical Constraints

#### Canvas Dimensions
- **Primary Canvas**: 800x600 pixels (defined in index.html)
- **Sprite Size**: 32x32 pixels (default for tower sprites)
- **Portrait Size**: 72x72 pixels (for HUD display)
- **Origin Point**: 
  - X: 50% of width (16px for 32px canvas)
  - Y: 75% of height (24px for 32px canvas)

#### Animation Parameters
- **Idle State**: 6 frames at 6 FPS
- **Attack State**: 6 frames at 10 FPS
- **Phase Calculation**: `(frameIndex / totalFrames) * Math.PI * 2`
- **Vertical Bob**: `Math.sin(phase) * 1.0` for idle, `Math.sin(phase * 2) * 0.5` for attack

#### Performance Requirements
- Image smoothing disabled for pixel-art rendering
- Canvas context 2D with no antialiasing
- Sprite caching via `procFramesCache` Map
- Data URL generation for portraits to avoid repeated rendering

---

## Color System

### Base Color Mapping (getTowerBaseColor - lines 227-246)

The color system uses HSL (Hue, Saturation, Lightness) values:

```javascript
{
  RaptorNest:     [135, 50, 55],  // Green-cyan, medium saturation
  Protoceratops:  [110, 40, 50],  // Yellow-green, lower saturation
  Triceratops:    [95, 35, 50],   // Yellow-green, desaturated
  Brachiosaurus:  [130, 35, 48],  // Green, desaturated
  Dilophosaurus:  [230, 45, 60],  // Blue, medium saturation
  Stegosaurus:    [25, 45, 55],   // Orange-brown, medium saturation
  Iguanodon:      [100, 40, 48],  // Yellow-green, lower saturation
  Maiasaura:      [95, 45, 58],   // Yellow-green, medium saturation
  Stonklodon:     [45, 80, 55],   // Gold, high saturation
  TRex:           [10, 55, 55],   // Red, medium-high saturation
  Spinosaurus:    [180, 55, 50],  // Cyan, medium-high saturation
  Pteranodon:     [35, 30, 65],   // Light brown, low saturation
  Ankylosaurus:   [25, 25, 50],   // Brown, low saturation
  Dreadnoughtus:  [120, 30, 45],  // Green, low saturation
  Quetzalcoatlus: [200, 25, 70]   // Light blue, low saturation
}
```

### Accent Color Generation
- **Formula**: `hsl((baseHue + 40) % 360, baseSat + 10, clamp(baseLight + 10, 0, 100))`
- Accent colors are 40 degrees shifted in hue
- 10% increase in saturation
- 10% increase in lightness (clamped to valid range)

---

## Portrait Generation

### getTowerPortrait() System (lines 442-456)

#### Process
1. Creates 72x72 pixel canvas element
2. Fills background with `rgba(20,40,30,0.9)` (dark green-gray)
3. Calls `drawTowerSilhouette()` with idle mode
4. Converts to PNG data URL
5. Caches result in `portraitCache` Map

#### Cache Key Format
- Pattern: `${towerType}|${size}`
- Example: `"RaptorNest|72"`

---

## Individual Dinosaur Implementations

### drawTowerSilhouette() Function (lines 248-321)

All dinosaurs are drawn relative to a center point with phase-based animation.

#### 1. RaptorNest (lines 260-263)
**Shape Composition**:
- Base: Circle (radius 14px at y+8)
- Accent: Ellipse (8x10px at y-2, expands by 1px height in attack)
- **Coordinate System**: Center-based
- **Attack Animation**: Egg pulsates (height increases)

#### 2. Protoceratops (lines 314-317)
**Shape Composition**:
- Body: Triangle (apex at y-10, base points at (±12, 8))
- Shield: Rectangle (10x6px at y-6, shifts up by 1px in attack)
- **Attack Animation**: Shield raises, triangle expands by 1px

#### 3. Triceratops (lines 264-267)
**Shape Composition**:
- Body: Triangle (apex at y-12, base at (±16, 10))
- Horns: Rectangle accent (6x8px at y-6, shifts up by 1px in attack)
- **Attack Animation**: Horns raise position

#### 4. Brachiosaurus (lines 268-272)
**Shape Composition**:
- Body: Ellipse (16x10px at y+8)
- Neck: Rectangle (8x16px vertical)
- Head: Arc (radius 8px, angles π*0.7 to π*1.9, at (8, -10))
- **Attack Animation**: Head raises by 1px

#### 5. Dilophosaurus (lines 273-276)
**Shape Composition**:
- Frill: Triangle (apex at y-14, base at (±12, 0))
- Body: Rectangle accent (20x10px at y=0)
- **Attack Animation**: Frill expands by 2px width

#### 6. Stegosaurus (lines 277-283)
**Shape Composition**:
- Body: Rectangle (28x12px at y=0)
- Plates: 5 triangular spikes (6px spacing, 10px height)
  - Each spike: Triangle from (i*6, -2) to (i*6+4, -12) to (i*6+8, -2)
- **Attack Animation**: Spikes extend 1px higher

#### 7. Iguanodon (lines 284-287)
**Shape Composition**:
- Body: Rectangle (24x12px at y-4)
- Spike/Arm: Rectangle accent (8x4px at x+6, extends by 2px in attack)
- **Attack Animation**: Arm extends forward

#### 8. Maiasaura (Not in drawTowerSilhouette - uses default)
Falls through to default Protoceratops shape

#### 9. Stonklodon (lines 288-291)
**Shape Composition**:
- Body: Circle (radius 14px)
- Coin shine: Circle accent (radius 6px at (-4, -4))
- **Attack Animation**: Shine radius increases by 0.5px

#### 10. TRex (lines 292-295)
**Shape Composition**:
- Body: Triangle (apex at y-14, base at (±14, 8))
- Teeth: Rectangle accent (6x8px centered)
- **Attack Animation**: Triangle expands by 2px width

#### 11. Spinosaurus (lines 296-299)
**Shape Composition**:
- Sail: Triangle ((-10, 8) to (-6, -10) to (0, 8))
- Body: Rectangle accent (24x8px at y+4)
- **Attack Animation**: Sail peak raises by 1px

#### 12. Pteranodon (lines 300-304)
**Shape Composition**:
- Wings: Triangle ((-12, 4) to (0, -16) to (12, 4))
- Head: Rectangle accent (6x6px at y-16)
- **Attack Animation**: Wings expand by 2px width

#### 13. Ankylosaurus (lines 305-308)
**Shape Composition**:
- Body: Rectangle (28x12px at y-6)
- Shell: Rectangle accent (20x8px at y-10)
- **Attack Animation**: Shell height increases by 1px

#### 14. Dreadnoughtus (lines 309-312)
**Shape Composition**:
- Body: Rectangle (36x16px at y-8)
- Head/Neck: Rectangle accent (24x8px at y-14)
- **Attack Animation**: No specific animation modifier

#### 15. Quetzalcoatlus (lines 300-304, shares with Pteranodon)
**Shape Composition**:
- Wings: Triangle ((-12, 4) to (0, -16) to (12, 4))
- Beak: Rectangle accent (6x6px at y-16)
- **Attack Animation**: Wings expand by 2px width

---

## Animation System

### Frame Generation Process (generateTowerFrames - lines 323-355)

#### State Management
```javascript
states = {
  idle: [],   // 6 frames
  attack: []  // 6 frames
}
```

#### Animation Phases
1. **Idle Animation**:
   - 6 frames cycling through 0 to 2π phase
   - Vertical bob: `Math.sin(phase) * 1.0`
   - Frame rate: 6 FPS

2. **Attack Animation**:
   - 6 frames cycling through 0 to 2π phase
   - Vertical bob: `Math.sin(phase * 2) * 0.5` (faster, smaller)
   - Frame rate: 10 FPS
   - Muzzle flash overlay: `rgba(255,255,200,0.15)`
   - Flash radius: 4px on frame%3==0, else 3px

### Attack Overlay System (lines 346-349)
- **Muzzle Flash**: Semi-transparent yellow-white circle
- **Position**: Center of sprite, offset by -8px vertically
- **Timing**: Appears on every 3rd frame (when i%3===0)
- **Color**: `rgba(255,255,200,0.15)` (warm white, 15% opacity)

### Coordinate Transformations

#### Base Transform
```javascript
c.save();
c.translate(size / 2, size / 2 + bob);
// Draw operations relative to center
c.restore();
```

#### Attack Mode Modifiers
- Position shifts: Typically ±1-2 pixels
- Size expansions: 1-2 pixels for aggressive poses
- Conditional rendering based on `mode === 'attack'`

### Sprite Instance Integration

#### SpriteInstance Class Usage
- Manages animation state ('idle' or 'attack')
- Tracks animation time for frame selection
- Handles rotation and scaling
- Supports horizontal flipping via `flipX` property

#### Frame Selection Algorithm
```javascript
frameIndex = Math.floor(time * fps) % frameCount
```

### Performance Optimizations

1. **Caching Strategy**:
   - Cache key: `tower|${towerType}|${variantSeed}|${size}`
   - Prevents redundant canvas operations
   - Stores complete frame sets

2. **Canvas Reuse**:
   - Individual canvases per frame
   - Pre-rendered at initialization
   - Direct `drawImage()` calls during gameplay

3. **Data URL Generation**:
   - Portraits converted once to data URLs
   - Stored for repeated HUD updates
   - Reduces repeated rendering overhead

---

## Technical Summary

The dinosaur tower system implements a sophisticated procedural sprite generation system with:

- **15 unique dinosaur designs** with distinct geometric compositions
- **Dual-state animation system** (idle/attack) with different frame rates
- **HSL-based color system** with automatic accent generation
- **Phase-based movement** for organic animation
- **Efficient caching mechanisms** for performance
- **Modular coordinate system** allowing easy positioning and transformation
- **Attack state visual feedback** through shape morphing and overlay effects

Each dinosaur is composed of 2-5 primitive shapes (circles, rectangles, triangles, arcs) with specific positioning relative to a center origin, allowing for consistent scaling and rotation while maintaining visual coherence across all animation states.