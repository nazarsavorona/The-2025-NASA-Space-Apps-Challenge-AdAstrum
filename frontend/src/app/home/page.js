export default function ExoplanetHero() {
    return (
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
    );
}