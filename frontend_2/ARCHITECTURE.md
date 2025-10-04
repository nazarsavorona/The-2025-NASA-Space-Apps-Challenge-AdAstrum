# 🏗️ Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│                    http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Requests
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Vite Dev)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    index.html                          │  │
│  │  - Header (Title, Subtitle)                           │  │
│  │  - Controls (Planet Select, View Mode, Buttons)       │  │
│  │  - Canvas (3D Visualization)                          │  │
│  │  - Info Panel (Planet Details)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    src/main.js                         │  │
│  │  - Initialize Spacekit                                │  │
│  │  - Fetch planets from API                             │  │
│  │  - Handle user interactions                           │  │
│  │  - Calculate orbital mechanics                        │  │
│  │  - Render 3D scenes                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    src/style.css                       │  │
│  │  - Space-themed styling                               │  │
│  │  - Responsive layouts                                 │  │
│  │  - Animations and effects                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              node_modules/spacekit.js                  │  │
│  │  - WebGL rendering engine                             │  │
│  │  - 3D scene management                                │  │
│  │  - Camera controls                                    │  │
│  │  - Physics simulation                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI Python)                    │
│                    http://localhost:8000                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    main.py                             │  │
│  │                                                        │  │
│  │  GET /planets                                          │  │
│  │  └─> Returns JSON array of all planets                │  │
│  │                                                        │  │
│  │  GET /textures/{filename}                             │  │
│  │  └─> Serves planet texture images                     │  │
│  │                                                        │  │
│  │  GET /health                                           │  │
│  │  └─> Health check endpoint                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              data/planets.json                         │  │
│  │  - Array of 5 exoplanets                              │  │
│  │  - Physical properties                                │  │
│  │  - Orbital parameters                                 │  │
│  │  - Discovery information                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Action (Select Planet)
    ↓
JavaScript Event Handler
    ↓
Fetch Planet Data (if needed)
    ↓
Calculate Orbital Parameters
    ↓
Clear Existing 3D Objects
    ↓
Create New 3D Scene
    ├─> Create Star (if system view)
    ├─> Create Planet
    ├─> Create Orbital Path
    └─> Setup Lighting
    ↓
Position Camera
    ↓
Update Info Panel
    ↓
Start/Continue Animation Loop
```

## Component Interaction

```
┌──────────────────┐
│  Planet Selector │
└────────┬─────────┘
         │ onchange
         ▼
┌──────────────────┐      ┌─────────────────┐
│   loadPlanet()   │─────>│  Spacekit API   │
└────────┬─────────┘      └────────┬────────┘
         │                         │
         │ calls                   │ renders
         ▼                         ▼
┌──────────────────┐      ┌─────────────────┐
│ createSphere()   │      │  WebGL Canvas   │
│ createOrbit()    │      │                 │
│ createLight()    │      │  (3D Scene)     │
└──────────────────┘      └─────────────────┘
         │
         │ updates
         ▼
┌──────────────────┐
│  Info Panel DOM  │
└──────────────────┘
```

## File Dependencies

```
index.html
    │
    ├─> src/style.css (styling)
    │
    └─> src/main.js (logic)
            │
            ├─> spacekit.js (npm package)
            │       │
            │       └─> WebGL APIs
            │
            ├─> Fetch API
            │       │
            │       └─> Backend /planets endpoint
            │
            └─> DOM APIs
                    └─> User interactions
```

## View Modes

### Single Planet View
```
┌────────────────────────┐
│                        │
│                        │
│         🪐            │  <- Close-up planet
│                        │     with rotation
│                        │
│      (rotating)        │
│                        │
└────────────────────────┘
     Camera: [0, 0, 2]
     Light: [5, 5, 5]
```

### Star System View
```
┌────────────────────────┐
│                        │
│        ⭕             │  <- Orbital path
│       /  \             │
│      /    \            │
│     /  ☀️  🪐        │  <- Star and planet
│    /        \          │
│   ──────────-          │
│                        │
└────────────────────────┘
     Camera: [2a, 1.5a, 2a]
     Light: at star
     where a = semi-major axis
```

## Physics Calculations

```
Orbital Period (days)
    ↓
Convert to Years
    ↓
Apply Kepler's Third Law: P² = a³
    ↓
Calculate Semi-Major Axis (AU)
    ↓
Scale for Visualization
    ↓
Position Planet in 3D Space
```

## Event Flow

```
Page Load
    ↓
init()
    ├─> fetch('/planets')
    ├─> populatePlanetSelector()
    ├─> initializeSimulation()
    │       ├─> new Spacekit.Simulation()
    │       ├─> createStars()
    │       └─> createAmbientLight()
    ├─> setupEventListeners()
    │       ├─> planet-select.onchange
    │       ├─> view-mode.onchange
    │       ├─> animate-btn.onclick
    │       └─> reset-btn.onclick
    └─> loadPlanet(firstPlanet)
            ├─> createSphere()
            ├─> createOrbit()
            ├─> setupCamera()
            └─> updateInfoPanel()
```

## Technology Stack Layers

```
┌─────────────────────────────────────┐
│         User Interface              │
│  (HTML5, CSS3, Responsive Design)   │
└─────────────────────────────────────┘
                 │
┌─────────────────────────────────────┐
│      Application Logic              │
│     (Vanilla JavaScript ES6+)       │
└─────────────────────────────────────┘
                 │
┌─────────────────────────────────────┐
│    3D Visualization Library         │
│        (Spacekit.js v0.1.1)         │
└─────────────────────────────────────┘
                 │
┌─────────────────────────────────────┐
│       Graphics API                  │
│          (WebGL)                    │
└─────────────────────────────────────┘
                 │
┌─────────────────────────────────────┐
│      Browser Engine                 │
│   (Chrome, Firefox, Safari)         │
└─────────────────────────────────────┘
```

## State Management

```
Application State
├─ simulation: Spacekit.Simulation
├─ planetsData: Array<Planet>
├─ currentViewMode: 'planet' | 'system'
├─ isAnimating: boolean
└─ selectedPlanetId: string

Planet State
├─ id: string
├─ name: string
├─ hostStar: string
├─ physical properties
│   ├─ massEarth: number
│   ├─ radiusEarth: number
│   └─ equilibriumTemperatureK: number
├─ orbital properties
│   └─ orbitalPeriodDays: number
└─ visualization
    └─ texture: string
```

## Performance Optimization

```
Render Loop (60fps)
    ├─> Only update when animating
    ├─> Batch DOM updates
    ├─> Reuse 3D objects when possible
    └─> Lazy load textures

Memory Management
    ├─> Remove old 3D objects before creating new
    ├─> Dispose of unused geometries
    └─> Clean up event listeners

Network Optimization
    ├─> Single API call for all planets
    ├─> Cache planet data in memory
    └─> Lazy load textures on demand
```

---

**This architecture provides a scalable, maintainable, and performant web application! 🚀**
