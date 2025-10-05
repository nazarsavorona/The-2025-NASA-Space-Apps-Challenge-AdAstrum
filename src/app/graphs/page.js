'use client';


import FeatureImportance from "@/app/graphs/FeatureImportance";

export default function Graphs() {
    const features = {
        feature_a: 0.75,
        feature_b: 0.15,
        feacture_c: 0.1,
    };

    return (
        <div>
            <div style={{ width: '100vw', height: '100vh' }}>
                <FeatureImportance features={features} />
            </div>
        </div>
    );
}