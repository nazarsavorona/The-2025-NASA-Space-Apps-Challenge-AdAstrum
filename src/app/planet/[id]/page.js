'use client';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import TransitLightCurve from '../../../components/TransitLightCurve';
import TransitCurveControls from '../../../components/TransitCurveControls';

const planetImages = {
    'Super Earth': 'https://images.unsplash.com/photo-1614732414444-096e5f1122d5?w=800',
    'Terrestrial': 'https://images.unsplash.com/photo-1614313913007-2b4ae8ce32ec?w=800',
    'Hot Jupiter': 'https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=800',
    'Sub-Neptune': 'https://images.unsplash.com/photo-1614728263952-84ea256f9679?w=800'
};

const planetDetails = {
    'Kepler-452b': {
        mass: '5 Earth masses',
        radius: '1.63 Earth radii',
        orbitalPeriod: '385 days',
        temperature: '265 K',
        star: 'Kepler-452',
        discovered: '2015',
        description: 'Often called Earth 2.0, this exoplanet orbits within the habitable zone of a Sun-like star.'
    },
    'Proxima Centauri b': {
        mass: '1.17 Earth masses',
        radius: '1.1 Earth radii',
        orbitalPeriod: '11.2 days',
        temperature: '234 K',
        star: 'Proxima Centauri',
        discovered: '2016',
        description: 'The closest known exoplanet to Earth, orbiting our nearest stellar neighbor.'
    },
    'TRAPPIST-1e': {
        mass: '0.62 Earth masses',
        radius: '0.92 Earth radii',
        orbitalPeriod: '6.1 days',
        temperature: '251 K',
        star: 'TRAPPIST-1',
        discovered: '2017',
        description: 'One of seven Earth-sized planets in the TRAPPIST-1 system, potentially habitable.'
    },
    'HD 209458 b': {
        mass: '0.69 Jupiter masses',
        radius: '1.38 Jupiter radii',
        orbitalPeriod: '3.5 days',
        temperature: '1130 K',
        star: 'HD 209458',
        discovered: '1999',
        description: 'One of the first transiting exoplanets discovered, nicknamed "Osiris".'
    },
    'Gliese 667Cc': {
        mass: '3.8 Earth masses',
        radius: '1.5 Earth radii',
        orbitalPeriod: '28.1 days',
        temperature: '277 K',
        star: 'Gliese 667C',
        discovered: '2011',
        description: 'A super-Earth located in the habitable zone of a red dwarf star.'
    },
    'K2-18b': {
        mass: '8.6 Earth masses',
        radius: '2.6 Earth radii',
        orbitalPeriod: '33 days',
        temperature: '265 K',
        star: 'K2-18',
        discovered: '2015',
        description: 'A sub-Neptune with potential water vapor in its atmosphere, possibly habitable.'
    }
};

const planetTransitMetrics = {
    'Kepler-1 b': {
        depthPpm: 14230.9,
        durationHours: 1.74319,
        snr: 4304.3,
        orbitalPeriodDays: 2.470613377,
        epochBkjd: 122.763305
    },
    'Kepler-452b': {
        depthPpm: 450,
        durationHours: 8.5,
        snr: 95,
        orbitalPeriodDays: 385,
        epochBkjd: 711.2
    },
    'Proxima Centauri b': {
        depthPpm: 1300,
        durationHours: 2.4,
        snr: 250,
        orbitalPeriodDays: 11.186,
        epochBkjd: 135.4
    },
    'TRAPPIST-1e': {
        depthPpm: 5400,
        durationHours: 1.1,
        snr: 810,
        orbitalPeriodDays: 6.099,
        epochBkjd: 131.4
    },
    'HD 209458 b': {
        depthPpm: 15200,
        durationHours: 3.1,
        snr: 6000,
        orbitalPeriodDays: 3.52474859,
        epochBkjd: 140.6
    },
    'Gliese 667Cc': {
        depthPpm: 900,
        durationHours: 4.8,
        snr: 120,
        orbitalPeriodDays: 28.155,
        epochBkjd: 310.8
    },
    'K2-18b': {
        depthPpm: 2500,
        durationHours: 2.6,
        snr: 430,
        orbitalPeriodDays: 33,
        epochBkjd: 200.1
    }
};

export default function PlanetDetail({ params }) {
    const [planet, setPlanet] = useState(null);
    const [curveConfig, setCurveConfig] = useState({
        baseline: 1,
        depth: 0.012,
        preTransitDuration: 0.8,
        ingressDuration: 0.35,
        flatDuration: 1.1,
        egressDuration: 0.35,
        postTransitDuration: 0.8,
        slope: 2.2
    });
    const [observation, setObservation] = useState({
        depthPpm: Number((0.012 * 1_000_000).toFixed(0)),
        durationHours: Number((0.35 + 1.1 + 0.35).toFixed(2)),
        snr: 400,
        orbitalPeriodDays: 10,
        epochBkjd: 120
    });
    const router = useRouter();

    const applyDurationTemplate = (durationHours) => {
        if (!Number.isFinite(durationHours) || durationHours <= 0) {
            return;
        }
        const ingress = Math.max(0.02, Math.min(durationHours / 2 - 0.05, durationHours * 0.18));
        const roundedIngress = Number(ingress.toFixed(2));
        const flat = Math.max(0.02, durationHours - roundedIngress * 2);
        const roundedFlat = Number(flat.toFixed(2));
        const baselineWindow = Number(Math.max(durationHours * 0.6, 0.5).toFixed(2));

        setCurveConfig((prev) => ({
            ...prev,
            ingressDuration: roundedIngress,
            egressDuration: roundedIngress,
            flatDuration: roundedFlat,
            preTransitDuration: baselineWindow,
            postTransitDuration: baselineWindow
        }));
    };

    useEffect(() => {
        const storedPlanet = sessionStorage.getItem('selectedPlanet');
        if (!storedPlanet) {
            router.push('/results');
            return;
        }
        setPlanet(JSON.parse(storedPlanet));
    }, [router]);

    useEffect(() => {
        if (!planet) {
            return;
        }

        const metrics = planetTransitMetrics[planet.name] || {
            depthPpm: 9000,
            durationHours: 2.4,
            snr: 350,
            orbitalPeriodDays: 12,
            epochBkjd: 120
        };

        setObservation({
            depthPpm: Number(metrics.depthPpm.toFixed(1)),
            durationHours: Number(metrics.durationHours.toFixed(2)),
            snr: metrics.snr,
            orbitalPeriodDays: metrics.orbitalPeriodDays,
            epochBkjd: metrics.epochBkjd
        });

        setCurveConfig((prev) => ({
            ...prev,
            depth: metrics.depthPpm / 1_000_000,
            ingressDuration: Number(Math.max(0.02, Math.min(metrics.durationHours * 0.2, metrics.durationHours / 2 - 0.05)).toFixed(2)),
            egressDuration: Number(Math.max(0.02, Math.min(metrics.durationHours * 0.2, metrics.durationHours / 2 - 0.05)).toFixed(2)),
            flatDuration: Number(Math.max(0.02, metrics.durationHours - Math.max(0.02, Math.min(metrics.durationHours * 0.2, metrics.durationHours / 2 - 0.05)) * 2).toFixed(2)),
            preTransitDuration: Number(Math.max(metrics.durationHours * 0.6, 0.5).toFixed(2)),
            postTransitDuration: Number(Math.max(metrics.durationHours * 0.6, 0.5).toFixed(2))
        }));
    }, [planet]);

    useEffect(() => {
        const derivedDepth = Number((curveConfig.depth * 1_000_000).toFixed(1));
        if (Number.isFinite(derivedDepth) && Math.abs((observation?.depthPpm ?? 0) - derivedDepth) > 0.5) {
            setObservation((prev) => ({
                ...prev,
                depthPpm: derivedDepth
            }));
        }
    }, [curveConfig.depth]);

    useEffect(() => {
        const transitDuration = Number(
            (curveConfig.ingressDuration + curveConfig.flatDuration + curveConfig.egressDuration).toFixed(2)
        );
        if (Number.isFinite(transitDuration) && Math.abs((observation?.durationHours ?? 0) - transitDuration) > 0.01) {
            setObservation((prev) => ({
                ...prev,
                durationHours: transitDuration
            }));
        }
    }, [curveConfig.ingressDuration, curveConfig.flatDuration, curveConfig.egressDuration]);

    const updateValue = (key, value, boundaries = {}) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const { min = 0, max } = boundaries;
        const clamped = Math.max(min, max !== undefined ? Math.min(value, max) : value);
        setCurveConfig((prev) => ({ ...prev, [key]: clamped }));
        if (key === 'depth') {
            setObservation((prev) => ({ ...prev, depthPpm: Number((clamped * 1_000_000).toFixed(1)) }));
        }
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

    const handleObservationChange = (key, rawValue) => {
        if (!Number.isFinite(rawValue)) {
            return;
        }

        if (key === 'depthPpm') {
            const clampedDepth = Math.max(1, rawValue);
            setObservation((prev) => ({ ...prev, depthPpm: Number(clampedDepth.toFixed(1)) }));
            setCurveConfig((prev) => ({ ...prev, depth: Number((clampedDepth / 1_000_000).toFixed(6)) }));
            return;
        }

        if (key === 'durationHours') {
            const clampedDuration = Math.max(0.2, rawValue);
            setObservation((prev) => ({ ...prev, durationHours: Number(clampedDuration.toFixed(2)) }));
            applyDurationTemplate(clampedDuration);
            return;
        }

        if (key === 'snr') {
            const clampedSnr = Math.max(1, rawValue);
            setObservation((prev) => ({ ...prev, snr: Number(clampedSnr.toFixed(1)) }));
            return;
        }

        if (key === 'orbitalPeriodDays') {
            const clampedPeriod = Math.max(0.1, rawValue);
            setObservation((prev) => ({ ...prev, orbitalPeriodDays: Number(clampedPeriod.toFixed(4)) }));
            return;
        }

        if (key === 'epochBkjd') {
            setObservation((prev) => ({ ...prev, epochBkjd: Number(rawValue.toFixed(4)) }));
        }
    };

    if (!planet) {
        return <div>Loading...</div>;
    }

    const details = planetDetails[planet.name] || {
        mass: 'Unknown',
        radius: 'Unknown',
        orbitalPeriod: 'Unknown',
        temperature: 'Unknown',
        star: 'Unknown',
        discovered: 'Unknown',
        description: 'Details for this exoplanet are currently being researched.'
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-blue-900 text-white p-8">
            <div className="max-w-6xl mx-auto">
                <button
                    onClick={() => router.push('/results')}
                    className="mb-6 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                    ← Back to Results
                </button>

                <div className="grid md:grid-cols-2 gap-8">
                    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-2xl">
                        <img
                            src={planetImages[planet.type] || planetImages['Terrestrial']}
                            alt={planet.name}
                            className="w-full h-96 object-cover"
                        />
                    </div>

                    <div className="bg-gray-800 rounded-lg p-8 shadow-2xl">
                        <h1 className="text-4xl font-bold mb-4">{planet.name}</h1>
                        <div className="mb-6">
                            <span className="inline-block px-3 py-1 bg-blue-600 rounded-full text-sm">
                                {planet.type}
                            </span>
                            <span className="ml-2 text-gray-400">
                                Classification: {(planet.probability * 100).toFixed(0)}% confidence
                            </span>
                        </div>

                        <p className="text-gray-300 mb-6">{details.description}</p>

                        <div className="space-y-3">
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Mass:</span>
                                <span>{details.mass}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Radius:</span>
                                <span>{details.radius}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Orbital Period:</span>
                                <span>{details.orbitalPeriod}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Temperature:</span>
                                <span>{details.temperature}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Host Star:</span>
                                <span>{details.star}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-700 pb-2">
                                <span className="text-gray-400">Distance from Earth:</span>
                                <span>{planet.distance}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Year Discovered:</span>
                                <span>{details.discovered}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="mt-12 bg-gray-900/80 border border-blue-400/20 rounded-2xl p-8 shadow-2xl">
                    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                        <div>
                            <h2 className="text-2xl font-semibold">Transit Light Curve</h2>
                            <p className="text-sm text-gray-400 mt-1">
                                Adjust the parameters to simulate how this planet dims its host star during transit.
                            </p>
                        </div>
                        <div className="text-sm text-gray-400 bg-gray-800/70 border border-blue-300/20 rounded-lg px-4 py-2">
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

                    <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
                        <label className="flex flex-col gap-1 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Transit depth (ppm)</span>
                            <input
                                type="number"
                                min="1"
                                value={observation.depthPpm}
                                onChange={(event) => handleObservationChange('depthPpm', parseFloat(event.target.value))}
                                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Transit duration (hrs)</span>
                            <input
                                type="number"
                                min="0.2"
                                step="0.05"
                                value={observation.durationHours}
                                onChange={(event) => handleObservationChange('durationHours', parseFloat(event.target.value))}
                                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">SNR</span>
                            <input
                                type="number"
                                min="1"
                                step="1"
                                value={observation.snr}
                                onChange={(event) => handleObservationChange('snr', parseFloat(event.target.value))}
                                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Orbital period (days)</span>
                            <input
                                type="number"
                                min="0.1"
                                step="0.01"
                                value={observation.orbitalPeriodDays}
                                onChange={(event) => handleObservationChange('orbitalPeriodDays', parseFloat(event.target.value))}
                                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Transit epoch (BKJD)</span>
                            <input
                                type="number"
                                step="0.0001"
                                value={observation.epochBkjd}
                                onChange={(event) => handleObservationChange('epochBkjd', parseFloat(event.target.value))}
                                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2"
                            />
                        </label>
                    </div>

                    <div className="mt-4 text-xs text-gray-500">
                        <span>Transit span (ingress + flat + egress): {(curveConfig.ingressDuration + curveConfig.flatDuration + curveConfig.egressDuration).toFixed(2)} hrs · </span>
                        <span>Observation window: {(curveConfig.preTransitDuration + curveConfig.ingressDuration + curveConfig.flatDuration + curveConfig.egressDuration + curveConfig.postTransitDuration).toFixed(2)} hrs</span>
                    </div>

                    <div className="mt-8">
                        <TransitLightCurve
                            className="bg-gradient-to-br from-gray-950 to-gray-900"
                            width={640}
                            height={320}
                            baseline={curveConfig.baseline}
                            depth={curveConfig.depth}
                            preTransitDuration={curveConfig.preTransitDuration}
                            ingressDuration={curveConfig.ingressDuration}
                            flatDuration={curveConfig.flatDuration}
                            egressDuration={curveConfig.egressDuration}
                            postTransitDuration={curveConfig.postTransitDuration}
                            slope={curveConfig.slope}
                            tickCount={6}
                            fluxTickCount={5}
                            fluxScale={1_000_000}
                            fluxUnit="ppm relative drop"
                            timeUnit="hours"
                            showNoise
                            snr={observation.snr}
                            timeAxisLabel="Time (hours relative to mid-transit)"
                            fluxAxisLabel="Flux (ppm relative drop)"
                        />
                    </div>
                </div>

            </div>
        </div>
    );
}
