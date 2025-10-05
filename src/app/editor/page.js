'use client';
import { useRouter } from 'next/navigation';
import Papa from 'papaparse';
import { useEffect, useState } from 'react';
import { storage } from '../../utils/storage';

export default function Editor() {
    const [data, setData] = useState([]);
    const [columns, setColumns] = useState([]);
    const [fileName, setFileName] = useState('');
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalRows, setTotalRows] = useState(0);
    const rowsPerPage = 50;
    const router = useRouter();

    useEffect(() => {
        loadCSVData();
    }, []);

    const loadCSVData = async () => {
        try {
            setLoading(true);

            // Get metadata
            const metadata = await storage.getData('csvData', 'metadata');
            if (!metadata) {
                router.push('/');
                return;
            }

            setFileName(metadata.fileName);

            // Reconstruct CSV from chunks
            let csvContent = '';
            for (let i = 0; i < metadata.chunksCount; i++) {
                const chunk = await storage.getData('csvData', `chunk_${i}`);
                csvContent += chunk;
            }

            // Pre-process CSV to remove comment lines
            const lines = csvContent.split('\n');
            const cleanedLines = lines.filter(line => {
                // Remove lines that start with # (comments)
                const trimmedLine = line.trim();
                return trimmedLine && !trimmedLine.startsWith('#');
            });
            const cleanedCsv = cleanedLines.join('\n');


            Papa.parse(cleanedCsv, {
                header: true,
                skipEmptyLines: false, // let us handle "empty rows" ourselves
                delimiter: ",",
                dynamicTyping: true,
                complete: (result) => {
                    // Remove rows that are *completely empty* (all values are null/undefined/"")
                    const filteredData = result.data.filter(row =>
                        Object.values(row).some(value => {
                            // keep if there is any non-empty cell
                            if (typeof value === "number") return true; // includes 0
                            if (typeof value === "boolean") return true; // true/false
                            if (typeof value === "string" && value.trim() !== "") return true;
                            return false;
                        })
                    );

                    setData(filteredData);
                    setTotalRows(filteredData.length);

                    if (filteredData.length > 0) {
                        // Keep column names exactly as they are (no trimming/cleaning)
                        setColumns(Object.keys(filteredData[0]));
                    }

                    setLoading(false);
                },
                error: (err) => {
                    console.error("Parse error:", err);
                    alert("Error parsing CSV file");
                    setLoading(false);
                },
            });

        } catch (error) {
            console.error('Error loading data:', error);
            alert('Error loading data');
            router.push('/');
        }
    };

    const handleColumnNameChange = (oldName, newName) => {
        if (!newName.trim() || oldName === newName) return;

        const newData = data.map(row => {
            const newRow = { ...row };
            newRow[newName] = row[oldName];
            delete newRow[oldName];
            return newRow;
        });

        const newColumns = columns.map(col => col === oldName ? newName : col);
        setColumns(newColumns);
        setData(newData);
    };

    const handleDeleteColumn = (columnName) => {
        if (columns.length === 1) {
            alert('Cannot delete the last column');
            return;
        }

        const newData = data.map(row => {
            const newRow = { ...row };
            delete newRow[columnName];
            return newRow;
        });

        const newColumns = columns.filter(col => col !== columnName);
        setColumns(newColumns);
        setData(newData);
    };

    const handleCellEdit = (rowIndex, columnName, value) => {
        const newData = [...data];
        newData[rowIndex][columnName] = value;
        setData(newData);
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            // Save processed data to IndexedDB
            await storage.saveData('processedData', 'data', data);
            await storage.saveData('processedData', 'columns', columns);

            // Get the original file from IndexedDB
            const originalFile = await storage.getData('csvData', 'originalFile');

            if (!originalFile) {
                alert('Original file not found. Please re-upload your CSV.');
                setLoading(false);
                return;
            }

            // Create FormData and append the file
            const formData = new FormData();
            formData.append('file', originalFile);

            try {
                const response = await fetch("http://0.0.0.0:8001/upload/", {
                    method: "POST",
                    body: formData,
                    credentials: "include"
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log('Upload successful:', result);

                // Clear original CSV data to free up space
                await storage.clearStore('csvData');

                router.push('/classify');
            } catch (error) {
                console.error('Error uploading file:', error);
                alert('Error uploading file: ' + error.message);
                setLoading(false);
                return;
            }

        } catch (error) {
            console.error('Error saving data:', error);
            alert('Error saving data: ' + error.message);
            setLoading(false);
        }
    };

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const currentData = data.slice(startIndex, endIndex);
    const totalPages = Math.ceil(totalRows / rowsPerPage);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading CSV data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-full mx-auto">
                <div className="bg-white rounded-lg shadow-lg p-6 mb-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 mb-2">CSV Editor</h1>
                            <p className="text-gray-600">File: {fileName}</p>
                            <p className="text-sm text-gray-500">
                                Total rows: {totalRows} | Total columns: {columns.length}
                            </p>
                        </div>
                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400 font-semibold"
                        >
                            Submit & Continue to Classification
                        </button>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                    <div className="mb-4 flex justify-between items-center">
                        <div className="text-sm text-gray-600">
                            Showing rows {startIndex + 1} to {Math.min(endIndex, totalRows)} of {totalRows}
                        </div>

                        <div className="flex gap-2 items-center">
                            <button
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1}
                                className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
                            >
                                ← Previous
                            </button>
                            <span className="px-4 py-2 bg-gray-100 rounded">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
                            >
                                Next →
                            </button>
                        </div>
                    </div>

                    <div className="overflow-x-auto border border-gray-200 rounded-lg">
                        <div className="min-w-full inline-block align-middle">
                            <div className="overflow-hidden">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50 sticky top-0 z-10">
                                        <tr>
                                            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 bg-gray-100">
                                                #
                                            </th>
                                            {columns.map((col, idx) => (
                                                <th key={idx} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[150px]">
                                                    <div className="flex flex-col gap-1">
                                                        <input
                                                            type="text"
                                                            value={col}
                                                            onChange={(e) => handleColumnNameChange(col, e.target.value)}
                                                            className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                            title={col}
                                                        />
                                                        <button
                                                            onClick={() => handleDeleteColumn(col)}
                                                            className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {currentData.map((row, rowIdx) => (
                                            <tr key={startIndex + rowIdx} className="hover:bg-gray-50">
                                                <td className="px-3 py-2 text-sm text-gray-500 border-r border-gray-200 bg-gray-50 font-medium">
                                                    {startIndex + rowIdx + 1}
                                                </td>
                                                {columns.map((col, colIdx) => (
                                                    <td key={colIdx} className="px-3 py-2 text-sm text-gray-900 border-r border-gray-200 min-w-[150px]">
                                                        <input
                                                            type="text"
                                                            value={row[col] || ''}
                                                            onChange={(e) => handleCellEdit(startIndex + rowIdx, col, e.target.value)}
                                                            className="w-full px-2 py-1 border-0 bg-transparent focus:outline-none focus:bg-white focus:border focus:border-blue-500 focus:rounded"
                                                            title={row[col] || ''}
                                                        />
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div className="mt-4 flex justify-between items-center">
                        <div className="text-sm text-gray-500">
                            <strong>Tip:</strong> Use horizontal scroll to see all columns. Click on any cell to edit.
                        </div>
                        <div className="flex gap-2">
                            <select
                                value={rowsPerPage}
                                onChange={(e) => {
                                    const newRowsPerPage = parseInt(e.target.value);
                                    setCurrentPage(1);
                                    // You would need to add state for rowsPerPage if you want this to work
                                }}
                                className="px-3 py-1 border rounded text-sm"
                                disabled
                            >
                                <option value="25">25 rows</option>
                                <option value="50">50 rows</option>
                                <option value="100">100 rows</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}