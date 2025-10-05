'use client';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function ClassifyModal({ onClose }) {
    const [formData, setFormData] = useState({
        candidate_threshold: 0.5,
        confirmed_threshold: 0.8,
    });
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: parseFloat(e.target.value),
        });
    };

    const handleClassify = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    candidate_threshold: formData.candidate_threshold,
                    confirmed_threshold: formData.confirmed_threshold,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Prediction result:', data);

            router.push('/results'); // go to results after prediction
        } catch (error) {
            console.error('Error during prediction:', error);
            alert('Error during prediction');
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-lg">
                <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
                    Classification Settings
                </h1>

                {/* Candidate threshold */}
                <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-bold mb-2">
                        Candidate Threshold: {formData.candidate_threshold}
                    </label>
                    <input
                        type="range"
                        name="candidate_threshold"
                        value={formData.candidate_threshold}
                        onChange={handleChange}
                        min="0"
                        max="1"
                        step="0.01"
                        className="w-full"
                    />
                </div>

                {/* Confirmed threshold */}
                <div className="mb-6">
                    <label className="block text-gray-700 text-sm font-bold mb-2">
                        Confirmed Threshold: {formData.confirmed_threshold}
                    </label>
                    <input
                        type="range"
                        name="confirmed_threshold"
                        value={formData.confirmed_threshold}
                        onChange={handleChange}
                        min="0"
                        max="1"
                        step="0.01"
                        className="w-full"
                    />
                </div>

                {/* Buttons */}
                <div className="flex justify-end gap-4">
                    <button
                        onClick={() => (onClose ? onClose() : router.back())}
                        className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleClassify}
                        disabled={loading}
                        className={`px-6 py-2 rounded-lg font-semibold transition-colors ${!loading
                            ? 'bg-purple-500 text-white hover:bg-purple-600'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                    >
                        {loading ? 'Processing...' : 'Submit'}
                    </button>
                </div>
            </div>
        </div>
    );
}
