# 🚀 Exoplanet Visualizer - Setup Guide

Welcome to the Exoplanet Visualizer project! This guide will help you get the application running.

## 📋 Prerequisites

- **Node.js** v16 or higher ([Download](https://nodejs.org/))
- **Python** 3.8 or higher
- **Modern web browser** (Chrome, Firefox, Edge, or Safari)

## 🎯 Quick Start

### Step 1: Install Frontend Dependencies

```bash
cd frontend_2
npm install
```

### Step 2: Install Backend Dependencies

```bash
cd ../backend
pip install -r requirements.txt
```

### Step 3: Start the Backend Server

From the `backend` directory:

```bash
python main.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal running!

### Step 4: Start the Frontend Development Server

Open a **new terminal** and navigate to `frontend_2`:

```bash
cd frontend_2
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Step 5: Open the Application

The application should automatically open in your browser at `http://localhost:3000`

If it doesn't, manually navigate to that URL.

## 🎮 Using the Application

### Controls

1. **Select Planet/System**: Use the dropdown to choose which exoplanet to visualize
2. **View Mode**: 
   - **Single Planet**: See a close-up view of the planet with rotation
   - **Star System**: See the planet orbiting its host star
3. **Play/Pause**: Control the animation
4. **Reset View**: Reset the camera to default position

### Available Planets

- **Kepler-186 f** - First Earth-size planet in the habitable zone
- **Kepler-22 b** - Ocean candidate planet
- **TRAPPIST-1 e** - One of seven Earth-size worlds
- **HD 209458 b** - Famous hot Jupiter with evaporating atmosphere
- **GJ 1214 b** - Water-rich sub-Neptune

## 🏗️ Project Structure

```
The-2025-NASA-Space-Apps-Challenge-AdAstrum/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── requirements.txt     # Python dependencies
│   └── data/
│       └── planets.json     # Planet dataset
├── frontend/
│   └── public/
│       └── textures/        # Planet textures (used by backend)
│           ├── rocky.png
│           ├── earth.jpg
│           ├── blueGasGiant.png
│           ├── tanGasGiant.png
│           └── sun.jpg
└── frontend_2/              # Spacekit visualization app
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── main.js         # Main application logic
    │   └── style.css       # Styling
    └── README.md
```

## 🔧 Troubleshooting

### Backend Issues

**Problem**: "Failed to load planet data"
- **Solution**: Make sure the backend server is running on port 8000
- Check: `curl http://localhost:8000/planets`

**Problem**: Port 8000 already in use
- **Solution**: Kill the process using port 8000 or change the port in `main.js`

### Frontend Issues

**Problem**: "npm install" fails
- **Solution**: Make sure you have Node.js v16+ installed
- Try: `rm -rf node_modules package-lock.json && npm install`

**Problem**: Planet textures not loading
- **Solution**: Verify texture files exist in `frontend/public/textures/`
- Check browser console for 404 errors

### Performance Issues

**Problem**: Animation is laggy
- **Solution**: 
  - Reduce `jdPerSecond` in `main.js` (line 20)
  - Close other browser tabs
  - Use a more powerful GPU

## 🚀 Building for Production

To create a production build:

```bash
cd frontend_2
npm run build
```

The optimized files will be in the `dist/` directory.

To preview the production build:

```bash
npm run preview
```

## 📝 API Endpoints

### GET /planets
Returns all planets from the dataset.

**Example Response:**
```json
[
  {
    "id": "kepler-186f",
    "name": "Kepler-186 f",
    "hostStar": "Kepler-186",
    "status": "Confirmed",
    "discoveryYear": 2014,
    "distance": 492.0,
    "massEarth": 1.1,
    "radiusEarth": 1.11,
    "orbitalPeriodDays": 129.9,
    "equilibriumTemperatureK": 188,
    "texture": "/textures/rocky.png",
    "description": "..."
  }
]
```

### GET /textures/{filename}
Serves planet texture images.

### GET /health
Health check endpoint.

## 🎨 Customization

### Adding New Planets

1. Add planet data to `backend/data/planets.json`
2. (Optional) Add texture to `frontend/public/textures/`
3. Restart the backend server

### Changing Colors

Edit `frontend_2/src/style.css`:
- Primary color: `#6c5ce7`
- Background gradient: `linear-gradient(135deg, #0f0c29, #302b63, #24243e)`

### Adjusting Simulation Speed

Edit `frontend_2/src/main.js`, line 20:
```javascript
jdPerSecond: 0.1,  // Increase for faster, decrease for slower
```

## 🐛 Known Issues

1. **First load may be slow**: Spacekit downloads assets on first use
2. **Mobile performance**: May be slow on older mobile devices
3. **Safari compatibility**: Some WebGL features may not work on older Safari versions

## 📚 Technologies Used

- **[Spacekit.js](https://github.com/typpo/spacekit)**: WebGL space visualization
- **[Vite](https://vitejs.dev/)**: Fast build tool
- **[FastAPI](https://fastapi.tiangolo.com/)**: Python web framework
- **Vanilla JavaScript**: No framework overhead

## 🤝 Contributing

Found a bug or want to add a feature? Feel free to submit a pull request!

## 📄 License

This project is part of the NASA Space Apps Challenge 2025.

## 🙏 Credits

- **Spacekit.js** by Ian Webster
- **Exoplanet data** from NASA Exoplanet Archive
- **Textures** from NASA and public domain sources

---

**Happy Exploring! 🌌**
