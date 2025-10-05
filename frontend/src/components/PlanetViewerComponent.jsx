"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// ---- Mocked exoplanet data ----
const MOCK_PLANETS = [
    { name: "TRAPPIST-1e", radiusEarth: 0.92, temperature: 300, type: "terrestrial" },
    { name: "Kepler-22b", radiusEarth: 2.4, temperature: 295, type: "super-Earth" },
    { name: "HD 209458 b", radiusEarth: 13, temperature: 1400, type: "hot Jupiter" },
    { name: "GJ 1214 b", radiusEarth: 2.7, temperature: 550, type: "mini-Neptune" },
    { name: "55 Cancri e", radiusEarth: 1.9, temperature: 2400, type: "lava world" },
    { name: "Kepler-62f", radiusEarth: 1.4, temperature: 270, type: "potentially habitable" },
];

const createProceduralTexture = (temperature = 300) => {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
        return new THREE.CanvasTexture(canvas);
    }

    const hue = THREE.MathUtils.clamp((temperature - 200) / 1000, 0, 1) * 0.7;
    const color = new THREE.Color().setHSL(hue, 0.6, 0.5);
    const grad = ctx.createRadialGradient(256, 256, 30, 256, 256, 256);
    grad.addColorStop(0, color.clone().offsetHSL(0, 0, 0.2).getStyle());
    grad.addColorStop(1, color.offsetHSL(0.05, 0, -0.3).getStyle());
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 512);

    const texture = new THREE.CanvasTexture(canvas);
    if (texture && "colorSpace" in texture) {
        texture.colorSpace = THREE.SRGBColorSpace;
    }
    texture.needsUpdate = true;
    return texture;
};

export default function PlanetViewerComponent({ planetData, options }) {
    const mountRef = useRef(null);
    const isCustomPlanet = Boolean(planetData);
    const [selectedPlanet, setSelectedPlanet] = useState(
        () => planetData?.name ?? MOCK_PLANETS[0].name
    );

    useEffect(() => {
        if (isCustomPlanet && planetData?.name) {
            setSelectedPlanet(planetData.name);
        }
    }, [isCustomPlanet, planetData?.name]);

    const planetConfig = useMemo(() => {
        if (planetData) {
            return {
                name: planetData.name ?? "Custom Planet",
                radius: planetData.radius ?? 1,
                radiusEarth: planetData.radiusEarth ?? planetData.radius ?? 1,
                temperature: planetData.temperature ?? 300,
                textureUrl: planetData.textureUrl ?? null,
                hasAtmosphere: planetData.hasAtmosphere ?? false,
                rotationSpeed: planetData.rotationSpeed ?? 0.002,
            };
        }

        const preset =
            MOCK_PLANETS.find((p) => p.name === selectedPlanet) ?? MOCK_PLANETS[0];

        return {
            ...preset,
            radius: preset.radiusEarth ?? 1,
            textureUrl: null,
            hasAtmosphere: true,
            rotationSpeed: 0.002,
        };
    }, [planetData, selectedPlanet]);

    const { autoRotate = false } = options ?? {};

    useEffect(() => {
        const container = mountRef.current;
        if (!container) {
            return undefined;
        }

        const width = container.clientWidth || 600;
        const height = container.clientHeight || 600;

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        if (renderer.outputColorSpace !== THREE.SRGBColorSpace) {
            renderer.outputColorSpace = THREE.SRGBColorSpace;
        }
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = "";
        container.appendChild(renderer.domElement);

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x000000);

        const radius = THREE.MathUtils.clamp(
            planetConfig.radius ?? planetConfig.radiusEarth ?? 1,
            0.1,
            50
        );

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        camera.position.z = Math.max(radius * 2.5, 3);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.autoRotate = autoRotate;
        controls.autoRotateSpeed = 0.5;
        controls.minDistance = 0.5;
        controls.maxDistance = 50;

        const ambient = new THREE.AmbientLight(0xffffff, 0.3);
        const dir = new THREE.DirectionalLight(0xffffff, 1);
        dir.position.set(5, 3, 5);
        scene.add(ambient, dir);

        let starField;
        let starGeometry;
        let starMaterial;
        const starCount = 1200;
        starGeometry = new THREE.BufferGeometry();
        const positions = new Float32Array(starCount * 3);
        for (let i = 0; i < starCount; i += 1) {
            const index = i * 3;
            positions[index] = (Math.random() - 0.5) * 400;
            positions[index + 1] = (Math.random() - 0.5) * 400;
            positions[index + 2] = (Math.random() - 0.5) * 400;
        }
        starGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        starMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.7, sizeAttenuation: true });
        starField = new THREE.Points(starGeometry, starMaterial);
        scene.add(starField);

        const geometry = new THREE.SphereGeometry(radius, 64, 64);

        let fallbackTexture = createProceduralTexture(planetConfig.temperature);
        let externalTexture = null;

        const material = new THREE.MeshStandardMaterial({
            map: fallbackTexture,
            bumpMap: fallbackTexture,
            bumpScale: 0.04,
            roughness: 1,
            metalness: 0,
        });

        const planetMesh = new THREE.Mesh(geometry, material);
        scene.add(planetMesh);

        let atmosphere;
        if (planetConfig.hasAtmosphere) {
            atmosphere = new THREE.Mesh(
                new THREE.SphereGeometry(radius * 1.05, 64, 64),
                new THREE.ShaderMaterial({
                    vertexShader: `
          varying vec3 vNormal;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
                    fragmentShader: `
          varying vec3 vNormal;
          void main() {
            float intensity = pow(0.6 - dot(vNormal, vec3(0,0,1.0)), 2.0);
            gl_FragColor = vec4(0.2, 0.5, 1.0, 1.0) * intensity;
          }
        `,
                    blending: THREE.AdditiveBlending,
                    side: THREE.BackSide,
                    transparent: true,
                })
            );
            planetMesh.add(atmosphere);
        }

        if (planetConfig.textureUrl) {
            const loader = new THREE.TextureLoader();
            const texturePath = planetConfig.textureUrl.startsWith("http")
                ? planetConfig.textureUrl
                : new URL(planetConfig.textureUrl, window.location.origin).href;

            loader.load(
                texturePath,
                (loadedTexture) => {
                    loadedTexture.colorSpace = THREE.SRGBColorSpace;
                    loadedTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
                    loadedTexture.needsUpdate = true;
                    planetMesh.material.map = loadedTexture;
                    planetMesh.material.bumpMap = null;
                    planetMesh.material.needsUpdate = true;
                    externalTexture = loadedTexture;
                    if (fallbackTexture) {
                        fallbackTexture.dispose();
                        fallbackTexture = null;
                    }
                },
                undefined,
                (error) => {
                    console.warn(
                        `Could not load texture "${texturePath}". Using procedural fallback instead.`,
                        error
                    );
                }
            );
        }

        const rotationSpeed = planetConfig.rotationSpeed ?? 0.002;
        let animationFrameId;

        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            planetMesh.rotation.y += rotationSpeed;
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        const handleResize = () => {
            const nextWidth = container.clientWidth || width;
            const nextHeight = container.clientHeight || height;
            renderer.setSize(nextWidth, nextHeight);
            camera.aspect = nextWidth / nextHeight;
            camera.updateProjectionMatrix();
        };
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            cancelAnimationFrame(animationFrameId);
            controls.dispose();
            renderer.dispose();
            geometry.dispose();
            material.dispose();
            if (fallbackTexture) {
                fallbackTexture.dispose();
            }
            if (externalTexture) {
                externalTexture.dispose();
            }
            if (atmosphere) {
                atmosphere.geometry.dispose();
                atmosphere.material.dispose();
            }
            if (starField) {
                scene.remove(starField);
            }
            if (starGeometry) {
                starGeometry.dispose();
            }
            if (starMaterial) {
                starMaterial.dispose();
            }
        };
    }, [planetConfig, autoRotate]);

    return (
        <div className="w-full flex flex-col items-center text-white">
            {!isCustomPlanet && (
                <select
                    className="text-black p-2 rounded mb-3"
                    value={selectedPlanet}
                    onChange={(e) => setSelectedPlanet(e.target.value)}
                >
                    {MOCK_PLANETS.map((p) => (
                        <option key={p.name} value={p.name}>
                            {p.name}
                        </option>
                    ))}
                </select>
            )}
            <div
                ref={mountRef}
                style={{
                    width: "100%",
                    height: isCustomPlanet ? "100%" : "600px",
                    maxHeight: "100%",
                }}
            ></div>
        </div>
    );
}
