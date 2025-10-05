'use client';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { storage } from '../../utils/storage';

export default function Results() {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    const columnMappings = {
        kepoi_name: 'KOI Name',
        toi: 'TESS Object of Interest',
        pl_name: 'Planet Name',
        kepler_name: 'Kepler Name',
        tid: 'TESS Input Catalog ID',
        hostname: 'Host Name',
        predicted_class: 'Predicted Class',
        predicted_confidence: 'Confidence'
    };

    useEffect(() => {
        loadResults();
    }, []);

    const loadResults = async () => {
        try {
            const storedData = await storage.getData('results', 'predictionResults');
            if (!storedData || !storedData.predictions) {
                console.warn('No prediction results found');
                router.push('/');
                return;
            }
            setResults(storedData.predictions);
            setLoading(false);
        } catch (error) {
            console.error('Error loading results:', error);
            router.push('/');
        }
    };

    const handleRowClick = async (planet) => {
        try {
            // Make GET request to fetch detailed data
            const existingSessionId = typeof window !== 'undefined' ? window.localStorage.getItem('adastrumSessionId') : null;
            const headers = {};

            if (existingSessionId) {
                headers['X-Session-Id'] = existingSessionId;
            }

            const response = await fetch(`http://localhost:8000/get-result/${planet.id}`, {
                method: 'GET',
                headers,
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const detailedData = await response.json();
            console.log('Detailed planet data:', detailedData);

            // Save the detailed data to storage
            await storage.saveData('results', 'selectedPlanet', detailedData);
            router.push(`/planet/${planet.id}`);
        } catch (error) {
            console.error('Error fetching planet details:', error);
            alert('Failed to load planet details');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-950 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto"></div>
                    <p className="mt-4 text-purple-300">Loading results...</p>
                </div>
            </div>
        );
    }

    const getAvailableColumns = () => {
        if (results.length === 0) return [];
        const firstResult = results[0];
        const columns = [];
        const orderedKeys = ['kepoi_name', 'pl_name', 'kepler_name', 'toi', 'tid', 'hostname', 'predicted_class', 'predicted_confidence'];
        orderedKeys.forEach(key => {
            if (key in firstResult) columns.push(key);
        });
        Object.keys(firstResult).forEach(key => {
            if (!columns.includes(key) && key !== 'id') {
                columns.push(key);
            }
        });
        return columns;
    };

    const formatColumnName = (key) => {
        return columnMappings[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const formatCellValue = (key, value) => {
        if (value === null || value === undefined) return 'N/A';

        if (key === 'predicted_confidence') {
            return (
                <div className="flex items-center">
                    <div className="w-28 bg-purple-900/40 rounded-full h-2.5 mr-2">
                        <div
                            className="bg-gradient-to-r from-purple-400 to-pink-500 h-2.5 rounded-full"
                            style={{ width: `${value * 100}%` }}
                        ></div>
                    </div>
                    <span className="text-purple-200 text-xs">{(value * 100).toFixed(0)}%</span>
                </div>
            );
        }

        if (key === 'predicted_class') {
            const classLabels = ['False Positive', 'Candidate', 'Confirmed'];
            return <span className="text-purple-100">{classLabels[value] || value}</span>;
        }

        if (typeof value === 'number') {
            return <span className="text-purple-100">{value.toFixed(4)}</span>;
        }

        return <span className="text-purple-100">{value}</span>;
    };

    const availableColumns = getAvailableColumns();

    return (

        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-950 to-black p-10 text-purple-100">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-10">
                    <button onClick={() => router.push('/')} className="text-sm text-purple-300 hover:text-white">
                        &lt; Back
                    </button>
                    <button
                        onClick={async () => {
                            await storage.clearStore('results');
                            router.push('/');
                        }}
                        className="border border-purple-400 px-5 py-2 text-sm hover:bg-purple-600/20 transition"
                    >
                        New Classification
                    </button>
                </div>

                <h1 className="text-2xl font-mono tracking-widest text-purple-100 mb-2">
                    CLASSIFICATION RESULTS
                </h1>
                <p className="text-sm text-purple-400 mb-8">File: exoplanets.csv | {results.length} Exoplanets found</p>

                <div className="bg-gradient-to-br from-gray-900/60 to-purple-950/60 border border-purple-800/40 rounded-xl shadow-2xl overflow-x-auto">
                    <table className="min-w-full font-mono text-sm">
                        <thead className="border-b border-purple-700/50 text-purple-400">
                            <tr>
                                {availableColumns.map((key) => (
                                    <th key={key} className="px-6 py-3 text-left font-normal uppercase tracking-wider">
                                        {formatColumnName(key)}
                                    </th>
                                ))}
                                <th className="px-6 py-3 text-left font-normal uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {results.map((row, idx) => (
                                <tr
                                    key={row.id || idx}
                                    className="hover:bg-purple-900/30 transition"
                                >
                                    {availableColumns.map((key) => (
                                        <td key={key} className="px-6 py-4 whitespace-nowrap">
                                            {formatCellValue(key, row[key])}
                                        </td>
                                    ))}
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <button
                                            onClick={() => handleRowClick(row)}
                                            className="bg-purple-600 cursor-pointer hover:bg-purple-700 text-white px-4 py-2 rounded-md text-xs transition-colors"
                                        >
                                            View Details
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
};
