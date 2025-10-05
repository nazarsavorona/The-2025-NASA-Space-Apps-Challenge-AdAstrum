'use client';


import FeatureImportance from "@/app/graphs/FeatureImportance";

export default function Graphs() {
    return (
        <div>
            <div style={{ width: '100vw', height: '100vh' }}>
                <FeatureImportance />
            </div>
        </div>
    );
}