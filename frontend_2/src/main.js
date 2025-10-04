import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Configuration
const BACKEND_URL = 'http://localhost:8000';
const AU_TO_KM = 149597870.7; // 1 AU in kilometers

// State
let scene, camera, renderer, controls;
let planetsData = [];
let currentViewMode = 'planet';
let isAnimating = true;
let animationId = null;
let currentPlanetMesh = null;
let currentStarMesh = null;
let currentOrbitLine = null;
let dynamicLight = null; // Dynamic light that changes based on view mode

// Initialize the application
async function init() {
    try {
        // Fetch planets data from backend
        const response = await fetch(`${BACKEND_URL}/planets`);
        planetsData = await response.json();
        
        // Populate planet selector
        populatePlanetSelector();
        
        // Initialize Three.js scene
        initializeScene();
        
        // Setup event listeners
        setupEventListeners();
        
        // Start animation loop
        animate();
        
        // Load first planet
        if (planetsData.length > 0) {
            loadPlanet(planetsData[0]);
        }
    } catch (error) {
        console.error('Failed to initialize:', error);
        alert('Failed to load planet data. Make sure the backend server is running on port 8000.');
    }
}

// Populate the planet selector dropdown
function populatePlanetSelector() {
    const select = document.getElementById('planet-select');
    select.innerHTML = planetsData.map(planet => 
        `<option value="${planet.id}">${planet.name}</option>`
    ).join('');
}

// Initialize Three.js scene
function initializeScene() {
    const container = document.getElementById('main-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    
    // Camera
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 3);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ canvas: container, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.5;
    controls.maxDistance = 50;
    
    // Lights - add strong ambient light for better visibility
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    // Create dynamic light (will be repositioned based on view mode)
    dynamicLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dynamicLight.position.set(5, 5, 5);
    scene.add(dynamicLight);
    
    // Stars background
    createStarfield();
    
    // Handle window resize
    window.addEventListener('resize', onWindowResize);
}

// Create starfield background
function createStarfield() {
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.1,
        transparent: true,
        opacity: 0.8
    });
    
    const starsVertices = [];
    for (let i = 0; i < 10000; i++) {
        const x = (Math.random() - 0.5) * 200;
        const y = (Math.random() - 0.5) * 200;
        const z = (Math.random() - 0.5) * 200;
        starsVertices.push(x, y, z);
    }
    
    starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
    const starField = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(starField);
}

// Calculate semi-major axis from orbital period using Kepler's third law
function calculateSemiMajorAxis(orbitalPeriodDays) {
    const periodYears = orbitalPeriodDays / 365.25;
    const semiMajorAxisAU = Math.pow(periodYears, 2/3);
    return semiMajorAxisAU;
}

// Calculate star size based on typical star types
function getStarRadius(starName) {
    if (starName.includes('TRAPPIST')) return 0.12;
    if (starName.includes('GJ')) return 0.21;
    if (starName.includes('Kepler')) return 0.95;
    return 1.0;
}

// Get star color based on temperature or type
function getStarColor(starName) {
    if (starName.includes('TRAPPIST') || starName.includes('GJ')) {
        return 0xff6b4a;
    }
    if (starName.includes('Kepler')) {
        return 0xffdd88;
    }
    return 0xffffdd;
}

// Clear existing planet objects
function clearScene() {
    if (currentPlanetMesh) {
        scene.remove(currentPlanetMesh);
        currentPlanetMesh.geometry.dispose();
        if (currentPlanetMesh.material.map) currentPlanetMesh.material.map.dispose();
        currentPlanetMesh.material.dispose();
        currentPlanetMesh = null;
    }
    
    if (currentStarMesh) {
        scene.remove(currentStarMesh);
        currentStarMesh.geometry.dispose();
        currentStarMesh.material.dispose();
        currentStarMesh = null;
        
        // Remove any additional star lights
        const starLights = scene.children.filter(child => 
            child.isPointLight && child.userData.isStar
        );
        starLights.forEach(light => scene.remove(light));
    }
    
    if (currentOrbitLine) {
        scene.remove(currentOrbitLine);
        currentOrbitLine.geometry.dispose();
        currentOrbitLine.material.dispose();
        currentOrbitLine = null;
    }
}

// Load and display a planet
function loadPlanet(planetData) {
    clearScene();
    
    const semiMajorAxisAU = calculateSemiMajorAxis(planetData.orbitalPeriodDays);
    const planetRadiusAU = (planetData.radiusEarth * 6371) / AU_TO_KM;
    
    if (currentViewMode === 'system') {
        // Star system view
        const starRadius = getStarRadius(planetData.hostStar);
        const starColor = getStarColor(planetData.hostStar);
        
        // Create star
        const starGeometry = new THREE.SphereGeometry(starRadius * 0.1, 32, 32);
        const starMaterial = new THREE.MeshBasicMaterial({ 
            color: starColor,
            emissive: starColor,
            emissiveIntensity: 1.0
        });
        currentStarMesh = new THREE.Mesh(starGeometry, starMaterial);
        scene.add(currentStarMesh);
        
        // Add star light at the center
        const starLight = new THREE.PointLight(starColor, 3, 100);
        starLight.position.set(0, 0, 0);
        starLight.userData.isStar = true;
        scene.add(starLight);
        
        // Position dynamic light to illuminate from the star
        dynamicLight.position.set(0, 2, 0);
        dynamicLight.color.setHex(starColor);
        dynamicLight.intensity = 2;
        
        // Create planet
        const planetRadius = Math.max(planetRadiusAU * 10, 0.05);
        const planetGeometry = new THREE.SphereGeometry(planetRadius, 32, 32);
        
        // Load texture if available
        let planetMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4488ff,
            roughness: 0.7,
            metalness: 0.1
        });
        
        if (planetData.texture) {
            const textureLoader = new THREE.TextureLoader();
            textureLoader.load(
                `${BACKEND_URL}${planetData.texture}`,
                (texture) => {
                    planetMaterial.map = texture;
                    planetMaterial.needsUpdate = true;
                },
                undefined,
                (error) => {
                    console.warn('Failed to load texture:', error);
                }
            );
        }
        
        currentPlanetMesh = new THREE.Mesh(planetGeometry, planetMaterial);
        currentPlanetMesh.position.set(semiMajorAxisAU, 0, 0);
        currentPlanetMesh.userData = { 
            angle: 0, 
            radius: semiMajorAxisAU,
            speed: 0.001 / Math.sqrt(semiMajorAxisAU) // Orbital speed
        };
        scene.add(currentPlanetMesh);
        
        // Create orbital path
        const orbitPoints = [];
        const segments = 128;
        for (let i = 0; i <= segments; i++) {
            const angle = (i / segments) * Math.PI * 2;
            orbitPoints.push(new THREE.Vector3(
                Math.cos(angle) * semiMajorAxisAU,
                0,
                Math.sin(angle) * semiMajorAxisAU
            ));
        }
        const orbitGeometry = new THREE.BufferGeometry().setFromPoints(orbitPoints);
        const orbitMaterial = new THREE.LineBasicMaterial({ color: 0x888888 });
        currentOrbitLine = new THREE.Line(orbitGeometry, orbitMaterial);
        scene.add(currentOrbitLine);
        
        // Set camera position
        camera.position.set(
            semiMajorAxisAU * 2,
            semiMajorAxisAU * 1.5,
            semiMajorAxisAU * 2
        );
        controls.target.set(0, 0, 0);
        
    } else {
        // Single planet view
        const planetRadius = Math.max(planetRadiusAU * 50, 0.2);
        const planetGeometry = new THREE.SphereGeometry(planetRadius, 64, 64);
        
        // Load texture if available
        let planetMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4488ff,
            roughness: 0.7,
            metalness: 0.1
        });
        
        if (planetData.texture) {
            const textureLoader = new THREE.TextureLoader();
            textureLoader.load(
                `${BACKEND_URL}${planetData.texture}`,
                (texture) => {
                    planetMaterial.map = texture;
                    planetMaterial.needsUpdate = true;
                },
                undefined,
                (error) => {
                    console.warn('Failed to load texture:', error);
                }
            );
        }
        
        currentPlanetMesh = new THREE.Mesh(planetGeometry, planetMaterial);
        currentPlanetMesh.userData = { rotationSpeed: 0.005 };
        scene.add(currentPlanetMesh);
        
        // Position dynamic light to illuminate the planet from front-side
        dynamicLight.position.set(3, 3, 5);
        dynamicLight.color.setHex(0xffffff);
        dynamicLight.intensity = 2;
        
        // Set camera position
        camera.position.set(0, 0, 2);
        controls.target.set(0, 0, 0);
    }
    
    controls.update();
    updateInfoPanel(planetData);
}

// Update the information panel
function updateInfoPanel(planetData) {
    const infoDiv = document.getElementById('planet-info');
    
    infoDiv.innerHTML = `
        <div class="info-item">
            <strong>Name:</strong>
            <span>${planetData.name}</span>
        </div>
        <div class="info-item">
            <strong>Host Star:</strong>
            <span>${planetData.hostStar}</span>
        </div>
        <div class="info-item">
            <strong>Discovery Year:</strong>
            <span>${planetData.discoveryYear}</span>
        </div>
        <div class="info-item">
            <strong>Distance:</strong>
            <span>${planetData.distance.toFixed(1)} light-years</span>
        </div>
        <div class="info-item">
            <strong>Mass:</strong>
            <span>${planetData.massEarth.toFixed(2)} Earth masses</span>
        </div>
        <div class="info-item">
            <strong>Radius:</strong>
            <span>${planetData.radiusEarth.toFixed(2)} Earth radii</span>
        </div>
        <div class="info-item">
            <strong>Orbital Period:</strong>
            <span>${planetData.orbitalPeriodDays.toFixed(1)} days</span>
        </div>
        <div class="info-item">
            <strong>Temperature:</strong>
            <span>${planetData.equilibriumTemperatureK}K (${(planetData.equilibriumTemperatureK - 273.15).toFixed(1)}°C)</span>
        </div>
        <div class="info-item description">
            <strong>Description:</strong>
            <span>${planetData.description}</span>
        </div>
    `;
}

// Setup event listeners
function setupEventListeners() {
    // Planet selector
    document.getElementById('planet-select').addEventListener('change', (e) => {
        const planetId = e.target.value;
        const planet = planetsData.find(p => p.id === planetId);
        if (planet) {
            loadPlanet(planet);
        }
    });
    
    // View mode selector
    document.getElementById('view-mode').addEventListener('change', (e) => {
        currentViewMode = e.target.value;
        const selectedPlanetId = document.getElementById('planet-select').value;
        const planet = planetsData.find(p => p.id === selectedPlanetId);
        if (planet) {
            loadPlanet(planet);
        }
    });
    
    // Animate button
    document.getElementById('animate-btn').addEventListener('click', () => {
        isAnimating = !isAnimating;
        const btn = document.getElementById('animate-btn');
        
        if (isAnimating) {
            btn.textContent = '⏸️ Pause Animation';
        } else {
            btn.textContent = '▶️ Play Animation';
        }
    });
    
    // Reset button
    document.getElementById('reset-btn').addEventListener('click', () => {
        const selectedPlanetId = document.getElementById('planet-select').value;
        const planet = planetsData.find(p => p.id === selectedPlanetId);
        if (planet) {
            loadPlanet(planet);
        }
    });
}

// Animation loop
function animate() {
    animationId = requestAnimationFrame(animate);
    
    if (isAnimating) {
        // Rotate planet
        if (currentPlanetMesh && currentPlanetMesh.userData.rotationSpeed) {
            currentPlanetMesh.rotation.y += currentPlanetMesh.userData.rotationSpeed;
        }
        
        // Orbit planet around star
        if (currentPlanetMesh && currentPlanetMesh.userData.angle !== undefined) {
            const userData = currentPlanetMesh.userData;
            userData.angle += userData.speed;
            currentPlanetMesh.position.x = Math.cos(userData.angle) * userData.radius;
            currentPlanetMesh.position.z = Math.sin(userData.angle) * userData.radius;
            currentPlanetMesh.rotation.y += 0.01;
        }
    }
    
    controls.update();
    renderer.render(scene, camera);
}

// Handle window resize
function onWindowResize() {
    const container = document.getElementById('main-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// Start the application
init();
