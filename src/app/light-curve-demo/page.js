'use client';
import { useState } from 'react';
import TransitLightCurve from '../../components/TransitLightCurve';
import TransitCurveControls from '../../components/TransitCurveControls';

const createDefaultCurve = () => ({
    baseline: 1,
    depth: 0.35,
    preTransitDuration: 0.35,
    ingressDuration: 0.12,
    flatDuration: 0.18,
    egressDuration: 0.12,
    postTransitDuration: 0.35
});

const createDefaultView = () => ({
    width: 640,
    height: 280,
    tickCount: 4,
    strokeColor: '#f6a23a',
    backgroundColor: '#040307'
});

export default function LightCurveDemo() {
    const [curveConfig, setCurveConfig] = useState(() => createDefaultCurve());
    const [viewConfig, setViewConfig] = useState(() => createDefaultView());

    const updateCurveValue = (key, value, boundaries = {}) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const { min = 0, max } = boundaries;
        const clamped = Math.max(min, max !== undefined ? Math.min(value, max) : value);
        setCurveConfig((prev) => ({ ...prev, [key]: clamped }));
    };

    const updateEnvelope = (value) => {
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

    const updateViewNumber = (key, value, boundaries = {}) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const { min = 0, max } = boundaries;
        const clamped = Math.max(min, max !== undefined ? Math.min(value, max) : value);
        setViewConfig((prev) => ({ ...prev, [key]: clamped }));
    };

    const updateTickCount = (value) => {
        if (!Number.isFinite(value)) {
            return;
        }
        const clamped = Math.max(2, Math.min(Math.round(value), 12));
        setViewConfig((prev) => ({ ...prev, tickCount: clamped }));
    };

    const handleReset = () => {
        setCurveConfig(createDefaultCurve());
        setViewConfig(createDefaultView());
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-black via-slate-950 to-indigo-950 text-white px-6 py-10">
            <div className="max-w-5xl mx-auto space-y-10">
                <header className="space-y-2 text-center">
                    <h1 className="text-4xl font-semibold">Transit Light Curve Playground</h1>
                    <p className="text-base text-gray-300">
                        Experiment with transit parameters and instantly preview the resulting light curve. Use this page to
                        validate styling changes before integrating them elsewhere.
                    </p>
                </header>

                <section className="bg-slate-900/70 border border-indigo-400/30 rounded-2xl p-6 shadow-2xl space-y-6">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <h2 className="text-xl font-medium">Curve Parameters</h2>
                        <span className="text-sm text-gray-400">
                            Flux drop: {(curveConfig.depth * 100).toFixed(1)}% • Ingress: {curveConfig.ingressDuration.toFixed(2)} • Flat: {curveConfig.flatDuration.toFixed(2)}
                        </span>
                    </div>
                    <TransitCurveControls
                        config={curveConfig}
                        onValueChange={updateCurveValue}
                        onIngressChange={updateIngress}
                        onEnvelopeChange={updateEnvelope}
                    />
                </section>

                <section className="bg-slate-900/70 border border-indigo-400/30 rounded-2xl p-6 shadow-2xl space-y-4">
                    <h2 className="text-xl font-medium">Display Options</h2>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <label className="flex flex-col gap-2 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Width</span>
                            <input
                                type="number"
                                min="360"
                                max="1024"
                                step="10"
                                value={viewConfig.width}
                                onChange={(event) => updateViewNumber('width', parseFloat(event.target.value), { min: 360, max: 1024 })}
                                className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-2 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Height</span>
                            <input
                                type="number"
                                min="220"
                                max="400"
                                step="10"
                                value={viewConfig.height}
                                onChange={(event) => updateViewNumber('height', parseFloat(event.target.value), { min: 220, max: 400 })}
                                className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-2 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Tick count</span>
                            <input
                                type="number"
                                min="2"
                                max="12"
                                value={viewConfig.tickCount}
                                onChange={(event) => updateTickCount(parseFloat(event.target.value))}
                                className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2"
                            />
                        </label>
                        <label className="flex flex-col gap-2 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Stroke colour</span>
                            <input
                                type="color"
                                value={viewConfig.strokeColor}
                                onChange={(event) => setViewConfig((prev) => ({ ...prev, strokeColor: event.target.value }))}
                                className="h-10 w-full rounded-lg border border-slate-700 bg-slate-800"
                            />
                        </label>
                        <label className="flex flex-col gap-2 text-sm">
                            <span className="text-gray-300 uppercase tracking-widest text-xs">Background colour</span>
                            <input
                                type="color"
                                value={viewConfig.backgroundColor}
                                onChange={(event) => setViewConfig((prev) => ({ ...prev, backgroundColor: event.target.value }))}
                                className="h-10 w-full rounded-lg border border-slate-700 bg-slate-800"
                            />
                        </label>
                    </div>
                    <div className="flex flex-wrap gap-3 pt-2">
                        <button
                            onClick={handleReset}
                            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 transition-colors"
                        >
                            Reset defaults
                        </button>
                        <button
                            onClick={() => {
                                const randomDepth = Number((0.05 + Math.random() * 0.6).toFixed(2));
                                const randomIngress = Number((0.05 + Math.random() * 0.25).toFixed(2));
                                const randomFlat = Number((0.12 + Math.random() * 0.38).toFixed(2));
                                const randomEnvelope = Number((0.2 + Math.random() * 0.8).toFixed(2));
                                setCurveConfig((prev) => ({
                                    ...prev,
                                    depth: randomDepth,
                                    ingressDuration: randomIngress,
                                    egressDuration: randomIngress,
                                    flatDuration: randomFlat,
                                    preTransitDuration: randomEnvelope,
                                    postTransitDuration: randomEnvelope
                                }));
                            }}
                            className="rounded-lg border border-indigo-400/40 px-4 py-2 text-sm font-medium text-indigo-200 hover:bg-indigo-500/10 transition-colors"
                        >
                            Randomise curve
                        </button>
                    </div>
                </section>

                <section className="bg-slate-900/70 border border-indigo-400/30 rounded-2xl p-6 shadow-2xl">
                    <h2 className="text-xl font-medium mb-4">Preview</h2>
                    <TransitLightCurve
                        className="bg-gradient-to-br from-slate-950 to-slate-900"
                        width={viewConfig.width}
                        height={viewConfig.height}
                        tickCount={viewConfig.tickCount}
                        strokeColor={viewConfig.strokeColor}
                        backgroundColor={viewConfig.backgroundColor}
                        baseline={curveConfig.baseline}
                        depth={curveConfig.depth}
                        preTransitDuration={curveConfig.preTransitDuration}
                        ingressDuration={curveConfig.ingressDuration}
                        flatDuration={curveConfig.flatDuration}
                        egressDuration={curveConfig.egressDuration}
                        postTransitDuration={curveConfig.postTransitDuration}
                    />
                </section>
            </div>
        </div>
    );
}
