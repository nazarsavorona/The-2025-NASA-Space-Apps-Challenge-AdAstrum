'use client';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { storage } from '../utils/storage';

export default function Home() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const router = useRouter();

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Only CSV files are supported.');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);

    try {
      await storage.init();
      const chunkSize = 1024 * 1024 * 10; // 10MB
      const chunks = [];
      let offset = 0;

      while (offset < file.size) {
        const chunk = file.slice(offset, offset + chunkSize);
        const text = await chunk.text();
        chunks.push(text);
        offset += chunkSize;
        setProgress(Math.min(90, (offset / file.size) * 90));
      }

      // Store the file object in IndexedDB for later use
      await storage.saveData('csvData', 'originalFile', file);

      await storage.saveData('csvData', 'metadata', {
        fileName: file.name,
        fileSize: file.size,
        chunksCount: chunks.length,
      });

      for (let i = 0; i < chunks.length; i++) {
        await storage.saveData('csvData', `chunk_${i}`, chunks[i]);
      }

      setProgress(100);
      setTimeout(() => router.push('/editor'), 700);
    } catch (err) {
      console.error(err);
      setError('Something went wrong while uploading. Try again.');
      setUploading(false);
      setProgress(0);
    }
  };

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
              <button
                onClick={() => document.getElementById('section-2')?.scrollIntoView({ behavior: 'smooth' })}
                className="border border-white px-8 py-3 hover:bg-white hover:text-black transition-all duration-300 text-sm tracking-wider"
              >
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

      <div id="section-2" className="relative min-h-screen flex items-center justify-center px-6 overflow-hidden bg-gradient-to-br from-black via-[#0b0217] to-black text-white">
        {/* background glowing blobs */}
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-purple-600/30 blur-[180px] animate-pulse" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-fuchsia-600/20 blur-[150px] animate-pulse delay-700" />

        <div className="relative w-full max-w-2xl rounded-2xl bg-gradient-to-br from-[#1a1a2e] via-[#13111c] to-[#0d0b13] p-10 shadow-2xl border border-white/10 backdrop-blur-xl">
          <h1 className="text-4xl font-bold text-center bg-gradient-to-r from-purple-400 to-fuchsia-600 bg-clip-text text-transparent">
            Upload Your CSV
          </h1>
          <p className="text-center text-gray-400 mt-3 mb-8">
            Securely upload and process large CSV files. We'll split it into chunks for smooth editing.
          </p>

          {error && (
            <div className="mb-6 p-3 rounded-lg bg-red-900/40 border border-red-500/40 text-red-300 text-sm">
              {error}
            </div>
          )}

          <div
            className={`w-full h-40 mb-6 flex flex-col items-center justify-center rounded-lg border-2 border-dashed 
    ${uploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"} 
    border-purple-500/60 bg-purple-500/10 hover:bg-purple-500/20 transition`}
            onClick={() => !uploading && document.getElementById("csv-upload").click()}
          >
            <input
              id="csv-upload"
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              disabled={uploading}
              className="hidden"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-10 w-10 text-purple-400 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 12V4m0 0L8 8m4-4l4 4" />
            </svg>
            <p className="text-gray-300 text-sm">
              {uploading ? "Uploading..." : "Click to upload or drag & drop CSV"}
            </p>
            <p className="text-xs text-gray-400">Only .csv files are supported</p>
          </div>


          {file && (
            <div className="mb-6 rounded-lg border border-purple-600/30 bg-black/40 p-4">
              <p className="text-xs text-gray-400">Selected file:</p>
              <p className="font-semibold text-purple-300">{file.name}</p>
              <p className="text-xs text-gray-500">
                Size: {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}

          {uploading && (
            <div className="mb-6">
              <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                <span>Processing...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-gray-800 overflow-hidden">
                <div
                  className="h-2 bg-gradient-to-r from-purple-500 to-fuchsia-500 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`w-full py-3 px-6 rounded-xl font-semibold transition-all duration-300 shadow-lg ${file && !uploading
              ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white hover:from-purple-500 hover:to-fuchsia-500 focus:ring-2 focus:ring-purple-500'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
          >
            {uploading ? 'Processing...' : 'Upload and Continue'}
          </button>
        </div>
      </div>
    </>

  );
}
