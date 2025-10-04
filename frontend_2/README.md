# Exoplanet Visualizer

A beautiful web application for visualizing exoplanets and star systems using [Spacekit.js](https://github.com/typpo/spacekit).

## Features

- 🪐 **3D Planet Visualization** - View individual exoplanets with real textures
- 🌟 **Star System View** - Explore complete planetary systems with orbital paths
- 📊 **Real NASA Data** - All planet data sourced from confirmed exoplanet discoveries
- 🎮 **Interactive Controls** - Switch between planets, view modes, and control animations
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Prerequisites

- Node.js (v16 or higher)
- Running backend server on port 8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Make sure your backend server is running:
```bash
cd ../backend
python main.py
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser to `http://localhost:3000`

## Usage

### View Modes

- **Single Planet**: Close-up view of an individual planet with rotation
- **Star System**: Wide view showing the planet orbiting its host star

### Controls

- **Select Planet/System**: Choose which exoplanet to visualize
- **View Mode**: Switch between single planet and star system views
- **Play/Pause**: Control the animation
- **Reset View**: Reset the camera to default position

### Supported Planets

The application includes data for several confirmed exoplanets:
- Kepler-186 f
- Kepler-22 b
- TRAPPIST-1 e
- HD 209458 b
- GJ 1214 b

## Technical Details

### Technologies Used

- **Spacekit.js**: WebGL-based 3D space visualization library
- **Vite**: Fast build tool and development server
- **Vanilla JavaScript**: No framework overhead for better performance

### Data Structure

Each planet includes:
- Name and host star information
- Physical properties (mass, radius, temperature)
- Orbital characteristics
- Texture mapping for realistic rendering
- Discovery details and description

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend_2/
├── index.html          # Main HTML file
├── package.json        # Dependencies and scripts
├── vite.config.js      # Vite configuration
├── src/
│   ├── main.js        # Main application logic
│   └── style.css      # Styling
└── README.md          # This file
```

## Troubleshooting

### Backend Connection Issues

If you see "Failed to load planet data" error:
1. Make sure the backend server is running on port 8000
2. Check that CORS is enabled in the backend
3. Verify the planets.json file exists in backend/data/

### Texture Loading Issues

If planet textures don't appear:
1. Check that texture files exist in `backend/public/textures/`
2. Verify the paths in planets.json are correct
3. Check browser console for CORS or 404 errors

## Future Enhancements

- [ ] Add more exoplanets from the NASA Exoplanet Archive
- [ ] Implement search and filter functionality
- [ ] Add comparison view for multiple planets
- [ ] Include habitability zone visualization
- [ ] Add export/screenshot functionality

## License

MIT License - See LICENSE file for details

## Credits

- Spacekit.js by Ian Webster
- Exoplanet data from NASA Exoplanet Archive
- Textures from NASA and public domain sources
