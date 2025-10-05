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
            const response = await fetch(`http://localhost:8000/get-result/${planet.id}`, {
                method: 'GET',
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
        <>
            <div className="relative min-h-screen bg-black text-white overflow-hidden">
                {/* Background starfield effect */}
                <div className="absolute inset-0 bg-gradient-to-b from-black via-gray-900 to-black">
                    <div className="absolute inset-0" style={{
                        backgroundImage: `radial-gradient(2px 2px at 20% 30%, white, transparent),
                         radial-gradient(2px 2px at 60% 70%, white, transparent),
                         radial-gradient(1px 1px at 50% 50%, white, transparent),
                         radial-gradient(1px 1px at 80% 10%, white, transparent),
                         radial-gradient(2px 2px at 90% 60%, white, transparent),
                         radial-gradient(1px 1px at 33% 80%, white, transparent)`,
                        backgroundSize: '200% 200%',
                        backgroundPosition: '50% 50%'
                    }}></div>
                </div>

                {/* Content */}
                <div className="relative z-10 flex items-center justify-between min-h-screen px-8 md:px-16 lg:px-24">
                    {/* Left side - Text content */}
                    <div className="w-full md:w-1/2 space-y-8">
                        {/* Logo */}
                        <div className="text-sm tracking-widest font-light">AdAstrum</div>

                        {/* Main heading */}
                        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight">
                            EXPLORE<br />
                            EXOPLANETS...
                        </h1>

                        {/* Description */}
                        <p className="text-base md:text-lg text-gray-300 max-w-md font-light leading-relaxed">
                            Dive into NASA's real space<br />
                            data and let AI uncover<br />
                            distant worlds.
                        </p>

                        {/* CTA Buttons */}
                        <div className="space-y-6 pt-4">
                            <button className="border border-white px-8 py-3 hover:bg-white hover:text-black transition-all duration-300 text-sm tracking-wider">
                                Explore Exoplanets
                            </button>

                            <div className="flex items-center space-x-2 text-sm text-gray-400 cursor-pointer hover:text-white transition-colors">
                                <span>See how it works</span>
                                <span className="text-xs">∨</span>
                            </div>
                        </div>
                    </div>

                    {/* Right side - Planet image */}
                    <div className="hidden md:block md:w-1/2 relative">
                        <div className="relative w-full h-full flex items-center justify-center">
                            {/* Planet sphere */}
                            <div className="relative w-96 h-96 lg:w-[500px] lg:h-[500px]">
                                {/* Glow effect */}
                                <div className="absolute inset-0 rounded-full bg-gradient-radial from-orange-200/20 via-orange-300/10 to-transparent blur-3xl"></div>

                                {/* Planet surface */}
                                <div className="absolute inset-0 rounded-full overflow-hidden shadow-2xl">
                                    <div className="w-full h-full bg-gradient-to-br from-orange-200 via-amber-300 to-orange-400 relative">
                                        {/* Surface texture overlay */}
                                        <div className="absolute inset-0 opacity-40" style={{
                                            backgroundImage: `radial-gradient(circle at 30% 40%, rgba(139, 69, 19, 0.3) 0%, transparent 50%),
                                   radial-gradient(circle at 70% 60%, rgba(160, 82, 45, 0.2) 0%, transparent 40%),
                                   radial-gradient(circle at 50% 80%, rgba(210, 105, 30, 0.3) 0%, transparent 35%)`
                                        }}></div>

                                        {/* Darker spots/features */}
                                        <div className="absolute top-20 right-32 w-24 h-32 bg-orange-600/30 rounded-full blur-xl"></div>
                                        <div className="absolute top-40 left-24 w-32 h-24 bg-red-800/20 rounded-full blur-lg"></div>
                                        <div className="absolute bottom-32 right-40 w-28 h-28 bg-amber-700/25 rounded-full blur-xl"></div>

                                        {/* Shadow effect for sphere */}
                                        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-black/40 rounded-full"></div>
                                    </div>
                                </div>

                                {/* Atmospheric glow */}
                                <div className="absolute inset-0 rounded-full ring-1 ring-orange-300/20"></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Mobile planet background */}
                <div className="md:hidden absolute bottom-0 right-0 w-64 h-64 opacity-30">
                    <div className="relative w-full h-full">
                        <div className="absolute inset-0 rounded-full bg-gradient-radial from-orange-200/30 via-orange-300/20 to-transparent blur-2xl"></div>
                        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-orange-200 via-amber-300 to-orange-400"></div>
                    </div>
                </div>
            </div>
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
        </>
    )
};
