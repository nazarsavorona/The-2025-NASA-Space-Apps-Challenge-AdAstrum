'use client';
import { useRouter, useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import PlanetViewerComponent from '../../../components/PlanetViewerComponent';
import TransitCurveControls from '../../../components/TransitCurveControls';
import TransitLightCurve from '../../../components/TransitLightCurve';
import { storage } from '../../../utils/storage';
import FeatureImportance from "@/app/graphs/FeatureImportance";

export default function PlanetDetail() {
    const [planet, setPlanet] = useState(null);
    const [loading, setLoading] = useState(true);
    const [texture, setTexture] = useState(null);
    const [curveConfig, setCurveConfig] = useState({
        baseline: 1,
        depth: 0.35,
        preTransitDuration: 0.35,
        ingressDuration: 0.12,
        flatDuration: 0.18,
        egressDuration: 0.12,
        postTransitDuration: 0.35,
        slope: 2.2
    });
    const router = useRouter();
    const chartContainerRef = useRef(null);
    const [chartWidth, setChartWidth] = useState(680);
    const [periodHours, setPeriodHours] = useState(undefined);
    const [usePhase, setUsePhase] = useState(false);
    const [snr, setSnr] = useState(0);

    const routeParams = useParams();
    const routeIdStr = routeParams?.id;
    const routeId = Number.parseInt(Array.isArray(routeIdStr) ? routeIdStr[0] : routeIdStr, 10);

    useEffect(() => {
        const loadPlanetData = async () => {
            try {
                // 1) Try restore from local storage (set by Results page)
                const storedPlanet = await storage.getData('results', 'selectedPlanet');

                if (storedPlanet && Number.isFinite(routeId) && Number(storedPlanet?.id) === routeId) {
                    setPlanet(storedPlanet);
                    setLoading(false);
                    return;
                }

                // 2) Fallback: fetch detailed planet from backend by id (preserves session via cookie)
                if (Number.isFinite(routeId)) {
                    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                    const response = await fetch(`${API_URL}/get-result/${routeId}`, {
                        method: 'GET',
                        credentials: 'include'
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const detailedData = await response.json();
                    setPlanet(detailedData);
                    // Save for quick back/forward navigation
                    await storage.saveData('results', 'selectedPlanet', detailedData);
                    setLoading(false);
                    return;
                }

                console.warn('No planet data found');
                router.push('/results');
            } catch (error) {
                console.error('Error loading planet data:', error);
                router.push('/results');
            }
        };

        loadPlanetData();
    }, [router, routeId]);

    useEffect(() => {
        if (!planet) return;

        const selectedTexture = select_texture(planet.predicted_category) ?? '/textures/Terrestrial/Terrestrial1.png';
        setTexture(selectedTexture);

        const pickNumber = (...keys) => {
            for (const key of keys) {
                const raw = planet?.[key];
                const num = typeof raw === 'number' ? raw : parseFloat(raw);
                if (Number.isFinite(num)) return num;
            }
            return undefined;
        };

        const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

        // Depth from planet data: koi_depth or pl_trandep (ppm)
        const depthPpm = pickNumber('koi_depth', 'pl_trandep');
        if (Number.isFinite(depthPpm)) {
            const depthFrac = clamp(depthPpm / 1_000_000, 0.0001, 0.08);
            setCurveConfig((prev) => ({ ...prev, depth: Number(depthFrac.toFixed(6)) }));
        } else {
            // Fallback: derive from predicted_confidence
            const probabilityRaw = typeof planet.predicted_confidence === 'number'
                ? planet.predicted_confidence
                : parseFloat(planet.predicted_confidence);
            const boundedProbability = Number.isFinite(probabilityRaw)
                ? clamp(probabilityRaw, 0, 1)
                : 0.7;
            const minDepth = 0.005;
            const maxDepth = 0.08;
            const derivedDepthRaw = minDepth + (1 - boundedProbability) * (maxDepth - minDepth);
            const derivedDepth = Number(clamp(derivedDepthRaw, minDepth, maxDepth).toFixed(4));
            setCurveConfig((prev) => ({ ...prev, depth: derivedDepth }));
        }

        // Duration from planet data: koi_duration or pl_trandur (hours), split 20/60/20
        const durationHrs = pickNumber('koi_duration', 'pl_trandur');
        if (Number.isFinite(durationHrs) && durationHrs > 0) {
            const ingress = clamp(durationHrs * 0.2, 0.02, 3);
            const flat = clamp(durationHrs * 0.6, 0.05, 8);
            const envelope = clamp(Math.max(durationHrs * 0.6, 0.5), 0.2, 12);
            setCurveConfig((prev) => ({
                ...prev,
                ingressDuration: Number(ingress.toFixed(2)),
                egressDuration: Number(ingress.toFixed(2)),
                flatDuration: Number(flat.toFixed(2)),
                preTransitDuration: Number(envelope.toFixed(2)),
                postTransitDuration: Number(envelope.toFixed(2))
            }));
        }

        // Period to hours and show phase when available
        const periodDays = pickNumber('koi_period', 'pl_orbper');
        if (Number.isFinite(periodDays) && periodDays > 0) {
            setUsePhase(true);
            setPeriodHours(Number((periodDays * 24).toFixed(4)));
        } else {
            setUsePhase(false);
            setPeriodHours(undefined);
        }

        // Baseline flux heuristic from stellar magnitude (if available).
        const magnitude = pickNumber(
            'koi_kepmag', 'kepmag', 'st_kepmag', 'st_vmag', 'Tmag', 'Vmag', 'phot_g_mean_mag'
        );
        if (Number.isFinite(magnitude)) {
            // Map magnitude to a small baseline offset around 1.0 and clamp to control bounds.
            const baselineGuess = clamp(1 + (12 - magnitude) * 0.05, 0.6, 1.4);
            setCurveConfig((prev) => ({ ...prev, baseline: Number(baselineGuess.toFixed(2)) }));
        }

        // SNR from common fields if present.
        const snrCandidate = pickNumber('koi_model_snr', 'koi_snr', 'pl_trandsnr', 'tran_snr', 'SNR', 'snr');
        if (Number.isFinite(snrCandidate)) {
            setSnr(clamp(snrCandidate, 1, 5000));
        } else {
            setSnr(0);
        }
    }, [planet]);

    const updateValue = (key, value, boundaries = {}) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const { min = 0, max } = boundaries;
        const clamped = Math.max(min, max !== undefined ? Math.min(value, max) : value);
        setCurveConfig((prev) => ({ ...prev, [key]: clamped }));
    };

    const updateSymmetricEnvelope = (value) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const clamped = Math.max(0.2, Math.min(value, 12));
        setCurveConfig((prev) => ({
            ...prev,
            preTransitDuration: clamped,
            postTransitDuration: clamped
        }));
    };

    const updateIngress = (value) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const clamped = Math.max(0.02, Math.min(value, 3));
        setCurveConfig((prev) => ({ ...prev, ingressDuration: clamped, egressDuration: clamped }));
    };

    // Responsive chart width (stretches horizontally)
    useEffect(() => {
        const update = () => {
            if (chartContainerRef.current) {
                const w = chartContainerRef.current.clientWidth || 680;
                setChartWidth(Math.min(1200, Math.max(360, w)));
            }
        };
        update();
        window.addEventListener('resize', update);
        return () => window.removeEventListener('resize', update);
    }, []);

    if (loading || !planet) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-950 to-black flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto"></div>
                    <p className="mt-4 text-purple-300">Loading planet details...</p>
                </div>
            </div>
        );
    }

    // Get classification label
    const getClassLabel = (classValue) => {
        const classLabels = ['False Positive', 'Candidate', 'Confirmed'];
        return classLabels[classValue] || 'Unknown';
    };

    // Format field names
    const formatFieldName = (key) => {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    // Format field values
    const formatValue = (value) => {
        if (value === null || value === undefined) return 'N/A';
        if (typeof value === 'number') {
            return value.toFixed(4);
        }
        return String(value);
    };

    const planetName = planet.pl_name || planet.kepoi_name || planet.kepler_name || planet.hostname || `Planet ${planet.id}`;
    const classLabel = getClassLabel(planet.predicted_class);
    const confidence = planet.predicted_confidence || 0;

    const excludeFields = ['id', 'predicted_class', 'predicted_confidence', 'pl_name', 'kepoi_name', 'kepler_name'];

    const detailFields = Object.keys(planet).filter(key => !excludeFields.includes(key));

    function select_texture(category)  {
        const textures = {
            "Gas Giant": [
                "/textures/Gas Giant/Gaseous1.png",
                "/textures/Gas Giant/Gaseous2.png",
                "/textures/Gas Giant/Gaseous3.png",
                "/textures/Gas Giant/Gaseous4.png",
            ],
            "Neptune-like": [
                "/textures/Neptune-like/2k_uranus.png",
                "/textures/Neptune-like/Giant.png",
                "/textures/Neptune-like/Neptune.png",
                "/textures/Neptune-like/Pink.png",
            ],
            "Super-Earth": [
                "/textures/Super-Earth/Alpine.png",
                "/textures/Super-Earth/Icy.png",
                "/textures/Super-Earth/Savannah.png",
                "/textures/Super-Earth/Swamp.png",
                "/textures/Super-Earth/Tropical.png",
                "/textures/Super-Earth/Volcanic.png",
            ],
            "Terrestrial": [
                "/textures/Terrestrial/Martian.png",
                "/textures/Terrestrial/Terrestrial1.png",
                "/textures/Terrestrial/Terrestrial2.png",
                "/textures/Terrestrial/Terrestrial3.png",
                "/textures/Terrestrial/Terrestrial4.png",
                "/textures/Terrestrial/Venusian.png",
            ],
        };
        const tList = textures[category];
        if (!tList) return null;
        const randomIndex = Math.floor(Math.random() * tList.length);
        return tList[randomIndex];
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-950 to-black text-purple-100 p-8">
            <div className="max-w-6xl mx-auto">
                <button
                    onClick={() => router.push('/results')}
                    className="mb-6 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
                >
                    ← Back to Results
                </button>

                <div className="grid md:grid-cols-2 gap-8">
                    <div className="bg-gray-800/60 border border-purple-800/40 rounded-lg overflow-hidden shadow-2xl">
                        <PlanetViewerComponent
                            planetData={{
                                name: 'Earth',
                                radius: 5,
                                textureUrl: texture,
                                hasAtmosphere: true,
                                hasRings: false,
                            }}
                            options={{
                                autoRotate: true,
                            }}
                        />
                    </div>

                    <div className="bg-gray-800/60 border border-purple-800/40 rounded-lg p-8 shadow-2xl">
                        <h1 className="text-4xl font-bold mb-4 text-purple-100">{planetName}</h1>
                        <div className="mb-6">
                            <span className={`inline-block px-3 py-1 rounded-full text-sm ${planet.predicted_class === 2 ? 'bg-green-600' :
                                planet.predicted_class === 1 ? 'bg-yellow-600' :
                                    'bg-red-600'
                                }`}>
                                {classLabel}
                            </span>
                            <span className="ml-2 text-purple-400">
                                Confidence: {(confidence * 100).toFixed(1)}%
                            </span>
                        </div>

                        <div className="mb-4">
                            <div className="w-full bg-purple-900/40 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-purple-400 to-pink-500 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${confidence * 100}%` }}
                                ></div>
                            </div>
                        </div>

                        <div className="space-y-2 max-h-96 overflow-y-auto">
                            {detailFields.map((key) => (
                                <div key={key} className="flex justify-between border-b border-purple-700/30 pb-2">
                                    <span className="text-purple-400 font-mono text-sm">{formatFieldName(key)}:</span>
                                    <span className="text-purple-100 text-sm">{formatValue(planet[key])}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="mt-12 bg-gray-900/80 border border-purple-400/20 rounded-2xl p-8 shadow-2xl">
                    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                        <div>
                            <h2 className="text-2xl font-semibold text-purple-100">Transit Light Curve</h2>
                            <p className="text-sm text-purple-400 mt-1">
                                Adjust the parameters to simulate how this planet dims its host star during transit.
                            </p>
                        </div>
                        <div className="text-sm text-purple-400 bg-gray-800/70 border border-purple-300/20 rounded-lg px-4 py-2">
                            Current depth: {(curveConfig.depth * 100).toFixed(1)}% flux drop
                        </div>
                    </div>

                    <details className="mt-6 group">
                        <summary className="cursor-pointer select-none inline-flex items-center gap-2 text-purple-200/90 bg-gray-800/70 border border-purple-300/20 rounded-md px-3 py-2">
                            <span className="font-medium">Curve settings</span>
                            <span className="text-xs text-purple-300 group-open:hidden">(expand)</span>
                            <span className="text-xs text-purple-300 hidden group-open:inline">(collapse)</span>
                        </summary>
                        <div className="mt-4">
                            <TransitCurveControls
                                config={curveConfig}
                                onValueChange={updateValue}
                                onIngressChange={updateIngress}
                                onEnvelopeChange={updateSymmetricEnvelope}
                            />
                        </div>
                    </details>

                    <div className="mt-8">
                        <div ref={chartContainerRef} className="w-full">
                            <TransitLightCurve
                                className="mx-auto bg-gradient-to-br from-gray-950 to-gray-900 border border-purple-400/20"
                                /* App theme-aligned colours */
                                backgroundColor="transparent"
                                axisColor="rgba(167, 139, 250, 0.8)"
                                gridColor="rgba(167, 139, 250, 0.15)"
                                labelColor="#E9D5FF"
                                strokeColor="#C084FC"
                                noiseColor="#60A5FA"
                                width={chartWidth}
                                height={360}
                                baseline={curveConfig.baseline}
                                depth={curveConfig.depth}
                                preTransitDuration={curveConfig.preTransitDuration}
                                ingressDuration={curveConfig.ingressDuration}
                                flatDuration={curveConfig.flatDuration}
                                egressDuration={curveConfig.egressDuration}
                                postTransitDuration={curveConfig.postTransitDuration}
                                slope={curveConfig.slope}
                                displayAsPhase={usePhase}
                                orbitalPeriodHours={periodHours}
                                showNoise={Boolean(snr && snr > 0)}
                                snr={snr}
                            />
                        </div>
                    </div>

                    <div className="mt-8">
                        <FeatureImportance />
                    </div>
                </div>
            </div>
        </div>
    );
}
