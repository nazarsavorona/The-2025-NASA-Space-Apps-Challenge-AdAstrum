'use client';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import TransitCurveControls from '../../../components/TransitCurveControls';
import TransitLightCurve from '../../../components/TransitLightCurve';
import { storage } from '../../../utils/storage';

const planetImage = 'https://images.unsplash.com/photo-1614313913007-2b4ae8ce32ec?w=800';

export default function PlanetDetail({ params }) {
    const [planet, setPlanet] = useState(null);
    const [loading, setLoading] = useState(true);
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

    useEffect(() => {
        const loadPlanetData = async () => {
            try {
                const storedPlanet = await storage.getData('results', 'selectedPlanet');
                if (!storedPlanet) {
                    console.warn('No planet data found');
                    router.push('/results');
                    return;
                }
                setPlanet(storedPlanet);
                setLoading(false);
            } catch (error) {
                console.error('Error loading planet data:', error);
                router.push('/results');
            }
        };

        loadPlanetData();
    }, [router]);

    useEffect(() => {
        if (!planet) {
            return;
        }

        // Use predicted_confidence from API response
        const probabilityRaw = typeof planet.predicted_confidence === 'number'
            ? planet.predicted_confidence
            : parseFloat(planet.predicted_confidence);
        const boundedProbability = Number.isFinite(probabilityRaw)
            ? Math.min(Math.max(probabilityRaw, 0), 1)
            : 0.7;
        const derivedDepthRaw = 0.15 + (1 - boundedProbability) * 0.45;
        const derivedDepth = Number(Math.min(0.75, Math.max(0.05, derivedDepthRaw)).toFixed(2));

        setCurveConfig((prev) => {
            if (Math.abs(prev.depth - derivedDepth) < 0.01) {
                return prev;
            }
            return { ...prev, depth: derivedDepth };
        });
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
        const clamped = Math.max(0.05, Math.min(value, 2));
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
        const clamped = Math.max(0.04, Math.min(value, 0.6));
        setCurveConfig((prev) => ({ ...prev, ingressDuration: clamped, egressDuration: clamped }));
    };

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

    // Get planet name from available fields
    const planetName = planet.pl_name || planet.kepoi_name || planet.kepler_name || planet.hostname || `Planet ${planet.id}`;
    const classLabel = getClassLabel(planet.predicted_class);
    const confidence = planet.predicted_confidence || 0;

    // Fields to exclude from the details list
    const excludeFields = ['id', 'predicted_class', 'predicted_confidence', 'pl_name', 'kepoi_name', 'kepler_name'];

    // Get all other fields dynamically
    const detailFields = Object.keys(planet).filter(key => !excludeFields.includes(key));

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
                        <img
                            src={planetImage}
                            alt={planetName}
                            className="w-full h-96 object-cover"
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
                            Current depth: {(curveConfig.depth * 100).toFixed(0)}% flux drop · Slope {curveConfig.slope.toFixed(1)}
                        </div>
                    </div>

                    <div className="mt-6">
                        <TransitCurveControls
                            config={curveConfig}
                            onValueChange={updateValue}
                            onIngressChange={updateIngress}
                            onEnvelopeChange={updateSymmetricEnvelope}
                        />
                    </div>

                    <div className="mt-8">
                        <TransitLightCurve
                            className="bg-gradient-to-br from-gray-950 to-gray-900"
                            baseline={curveConfig.baseline}
                            depth={curveConfig.depth}
                            preTransitDuration={curveConfig.preTransitDuration}
                            ingressDuration={curveConfig.ingressDuration}
                            flatDuration={curveConfig.flatDuration}
                            egressDuration={curveConfig.egressDuration}
                            postTransitDuration={curveConfig.postTransitDuration}
                            slope={curveConfig.slope}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
