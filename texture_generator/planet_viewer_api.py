"""
Backend API endpoints for Planet Viewer
Serves planet data and 3D models to the frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Dict
import json

app = FastAPI(title="Planet Viewer API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for 3D models
models_dir = Path("./models")
models_dir.mkdir(exist_ok=True)
app.mount("/models", StaticFiles(directory=str(models_dir)), name="models")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Planet Viewer API",
        "version": "1.0.0",
        "endpoints": {
            "/planets": "Get list of available planets",
            "/models": "Get list of available 3D models",
            "/models/{filename}": "Download specific 3D model"
        }
    }


@app.get("/planets")
async def get_planets() -> List[Dict]:
    """
    Get list of available planets with their properties.
    
    Returns:
        List of planet data dictionaries
    """
    planets = [
        {
            "id": "earth",
            "name": "Earth",
            "radiusEarth": 6.3,
            "hasAtmosphere": True,
            "atmosphereColor": "0x4169e1",
            "description": "Our home planet and the only known planet with life.",
            "diameter": "12,742 km",
            "mass": "5.972 × 10²⁴ kg",
            "orbitalPeriod": "365.25 days",
            "distanceFromSun": "149.6 million km",
            "moons": [
                {
                    "name": "Moon",
                    "size": 1.7,
                    "distance": 10,
                    "speed": 1.0,
                    "color": "0xaaaaaa"
                }
            ]
        },
        {
            "id": "mars",
            "name": "Mars",
            "radiusEarth": 3.4,
            "hasAtmosphere": False,
            "description": "The Red Planet, known for its iron oxide surface.",
            "diameter": "6,779 km",
            "mass": "6.39 × 10²³ kg",
            "orbitalPeriod": "687 days",
            "distanceFromSun": "227.9 million km",
            "moons": [
                {
                    "name": "Phobos",
                    "size": 0.5,
                    "distance": 7,
                    "speed": 2.0,
                    "color": "0x8b7355"
                },
                {
                    "name": "Deimos",
                    "size": 0.3,
                    "distance": 9,
                    "speed": 1.5,
                    "color": "0x9b8365"
                }
            ]
        },
        {
            "id": "jupiter",
            "name": "Jupiter",
            "radiusEarth": 25,
            "hasAtmosphere": False,
            "description": "The largest planet in our solar system.",
            "diameter": "139,820 km",
            "mass": "1.898 × 10²⁷ kg",
            "orbitalPeriod": "11.86 years",
            "distanceFromSun": "778.5 million km"
        },
        {
            "id": "saturn",
            "name": "Saturn",
            "radiusEarth": 21,
            "hasRings": True,
            "ringColor": "0xd4a373",
            "hasAtmosphere": False,
            "description": "Best known for its spectacular ring system.",
            "diameter": "116,460 km",
            "mass": "5.683 × 10²⁶ kg",
            "orbitalPeriod": "29.46 years",
            "distanceFromSun": "1.43 billion km"
        }
    ]
    
    return planets


@app.get("/models")
async def get_models() -> List[Dict[str, str]]:
    """
    Get list of available 3D models from DreamFusion or other sources.
    
    Returns:
        List of model metadata dictionaries
    """
    models = []
    
    # Scan models directory for supported 3D files
    supported_extensions = {'.glb', '.gltf', '.obj', '.ply'}
    
    if models_dir.exists():
        for model_file in models_dir.iterdir():
            if model_file.suffix.lower() in supported_extensions:
                models.append({
                    "name": model_file.stem.replace('_', ' ').title(),
                    "url": f"/models/{model_file.name}",
                    "description": f"3D model - {model_file.suffix[1:].upper()} format",
                    "filename": model_file.name,
                    "format": model_file.suffix[1:].upper()
                })
    
    # Add example models (for demonstration)
    if not models:
        models = [
            {
                "name": "Example Planet 1",
                "url": "/models/example1.glb",
                "description": "DreamFusion generated exoplanet model",
                "filename": "example1.glb",
                "format": "GLB"
            },
            {
                "name": "Example Planet 2",
                "url": "/models/example2.obj",
                "description": "Custom 3D planet model",
                "filename": "example2.obj",
                "format": "OBJ"
            }
        ]
    
    return models


@app.get("/planet/{planet_id}")
async def get_planet_by_id(planet_id: str) -> Dict:
    """
    Get detailed information about a specific planet.
    
    Args:
        planet_id: Planet identifier
        
    Returns:
        Planet data dictionary
        
    Raises:
        HTTPException: If planet not found
    """
    planets = await get_planets()
    
    for planet in planets:
        if planet["id"] == planet_id:
            return planet
    
    raise HTTPException(status_code=404, detail=f"Planet {planet_id} not found")


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Planet Viewer API server...")
    print("API will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("\nPlace 3D models in ./models/ directory to serve them")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
