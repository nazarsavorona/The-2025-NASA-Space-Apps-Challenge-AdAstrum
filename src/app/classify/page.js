'use client';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { storage } from '../../utils/storage';

export default function Classify() {
    const [formData, setFormData] = useState({
        algorithm: 'random-forest',
        features: '',
        targetColumn: '',
        trainTestSplit: '80'
    });
    const [columns, setColumns] = useState([]);
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    useEffect(() => {
        loadColumns();
    }, []);

    const loadColumns = async () => {
        try {
            const storedColumns = await storage.getData('processedData', 'columns');
            if (!storedColumns) {
                router.push('/');
                return;
            }
            setColumns(storedColumns);
        } catch (error) {
            console.error('Error loading columns:', error);
            router.push('/');
        }
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleClassify = async () => {
        setLoading(true);

        try {
            // Get the processed data
            const processedData = await storage.getData('processedData', 'data');

            // Here you would normally send to your backend
            // const response = await fetch('YOUR_BACKEND_URL/classify', {
            //   method: 'POST',
            //   headers: { 'Content-Type': 'application/json' },
            //   body: JSON.stringify({ data: processedData, settings: formData })
            // });

            // Mock results for demonstration
            await new Promise(resolve => setTimeout(resolve, 1500));

            const mockResults = [
                { id: 1, name: 'Kepler-452b', type: 'Super Earth', probability: 0.89, distance: '1400 light-years' },
                { id: 2, name: 'Proxima Centauri b', type: 'Terrestrial', probability: 0.76, distance: '4.24 light-years' },
                { id: 3, name: 'TRAPPIST-1e', type: 'Terrestrial', probability: 0.82, distance: '39 light-years' },
                { id: 4, name: 'HD 209458 b', type: 'Hot Jupiter', probability: 0.94, distance: '150 light-years' },
                { id: 5, name: 'Gliese 667Cc', type: 'Super Earth', probability: 0.71, distance: '23.62 light-years' },
                { id: 6, name: 'K2-18b', type: 'Sub-Neptune', probability: 0.88, distance: '124 light-years' }
            ];

            await storage.saveData('results', 'classification', mockResults);

            // Clear processed data to free space
            await storage.clearStore('processedData');

            router.push('/results');
        } catch (error) {
            console.error('Error during classification:', error);
            alert('Error during classification');
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 p-8">
            <div className="max-w-3xl mx-auto">
                <h1 className="text-4xl font-bold text-gray-800 mb-8 text-center">
                    Classification Settings
                </h1>

                <div className="bg-white rounded-lg shadow-lg p-8">
                    <form className="space-y-6">
                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Classification Algorithm
                            </label>
                            <select
                                name="algorithm"
                                value={formData.algorithm}
                                onChange={handleChange}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            >
                                <option value="random-forest">Random Forest</option>
                                <option value="svm">Support Vector Machine</option>
                                <option value="neural-network">Neural Network</option>
                                <option value="knn">K-Nearest Neighbors</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Select Features (comma-separated)
                            </label>
                            <input
                                type="text"
                                name="features"
                                value={formData.features}
                                onChange={handleChange}
                                placeholder="e.g., mass, radius, temperature"
                                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                Available columns: {columns.join(', ')}
                            </p>
                        </div>

                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Target Column
                            </label>
                            <select
                                name="targetColumn"
                                value={formData.targetColumn}
                                onChange={handleChange}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            >
                                <option value="">Select target column</option>
                                {columns.map(col => (
                                    <option key={col} value={col}>{col}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Train/Test Split (%)
                            </label>
                            <input
                                type="number"
                                name="trainTestSplit"
                                value={formData.trainTestSplit}
                                onChange={handleChange}
                                min="50"
                                max="90"
                                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            />
                        </div>

                        <button
                            type="button"
                            onClick={handleClassify}
                            disabled={loading}
                            className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${!loading
                                ? 'bg-purple-500 text-white hover:bg-purple-600'
                                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                }`}
                        >
                            {loading ? 'Classifying...' : 'Classify'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}