const DEFAULT_PADDING = { top: 24, right: 32, bottom: 48, left: 60 };

function buildTransitPoints({
    baseline,
    depth,
    preTransitDuration,
    ingressDuration,
    flatDuration,
    egressDuration,
    postTransitDuration
}) {
    const sanitize = (value, fallback = 0) => {
        if (typeof value !== 'number' || Number.isNaN(value) || !Number.isFinite(value)) {
            return fallback;
        }
        return Math.max(0, value);
    };

    const baseLineSafe = baseline <= 0 ? 1 : baseline;
    const depthSafe = Math.min(Math.max(depth, 0), baseLineSafe * 0.95);

    const pre = sanitize(preTransitDuration, 0.25);
    const ingress = sanitize(ingressDuration, 0.1);
    const flat = sanitize(flatDuration, 0.2);
    const egress = sanitize(egressDuration, ingress);
    const post = sanitize(postTransitDuration, 0.25);

    const totalDuration = pre + ingress + flat + egress + post;
    if (totalDuration === 0) {
        return [
            [0, baseLineSafe],
            [1, baseLineSafe]
        ];
    }

    const points = [];
    let timeCursor = 0;

    const pushPoint = (time, value) => {
        points.push([time, value]);
    };

    pushPoint(0, baseLineSafe);

    if (pre > 0) {
        timeCursor += pre;
        pushPoint(timeCursor, baseLineSafe);
    }

    if (ingress > 0) {
        const startTime = timeCursor;
        pushPoint(startTime, baseLineSafe);
        timeCursor += ingress;
        pushPoint(timeCursor, baseLineSafe - depthSafe);
    } else {
        pushPoint(timeCursor, baseLineSafe - depthSafe);
    }

    if (flat > 0) {
        const startTime = timeCursor;
        pushPoint(startTime, baseLineSafe - depthSafe);
        timeCursor += flat;
        pushPoint(timeCursor, baseLineSafe - depthSafe);
    }

    if (egress > 0) {
        const startTime = timeCursor;
        pushPoint(startTime, baseLineSafe - depthSafe);
        timeCursor += egress;
        pushPoint(timeCursor, baseLineSafe);
    } else {
        pushPoint(timeCursor, baseLineSafe);
    }

    if (post > 0) {
        const startTime = timeCursor;
        pushPoint(startTime, baseLineSafe);
        timeCursor += post;
        pushPoint(timeCursor, baseLineSafe);
    }

    if (points[points.length - 1][0] !== timeCursor || points[points.length - 1][1] !== baseLineSafe) {
        pushPoint(timeCursor, baseLineSafe);
    }

    const deduped = points.filter((point, index) => {
        if (index === 0) {
            return true;
        }
        const [prevTime, prevValue] = points[index - 1];
        const [currTime, currValue] = point;
        return Math.abs(prevTime - currTime) > 1e-6 || Math.abs(prevValue - currValue) > 1e-6;
    });

    return deduped.map(([time, value], index, arr) => {
        const normalizedTime = time / totalDuration;
        if (index === arr.length - 1) {
            return [1, value];
        }
        return [normalizedTime, value];
    });
}

export default function TransitLightCurve({
    width = 560,
    height = 240,
    baseline = 1,
    depth = 0.35,
    preTransitDuration = 0.35,
    ingressDuration = 0.12,
    flatDuration = 0.18,
    egressDuration = ingressDuration,
    postTransitDuration = 0.35,
    strokeColor = '#f6a23a',
    backgroundColor = '#040307',
    axisColor = 'rgba(255, 196, 120, 0.75)',
    gridColor = 'rgba(255, 196, 120, 0.18)',
    labelColor = '#f6b867',
    padding = DEFAULT_PADDING,
    tickCount = 4,
    className = '',
    style
}) {
    const pad = { ...DEFAULT_PADDING, ...padding };
    const innerWidth = width - pad.left - pad.right;
    const innerHeight = height - pad.top - pad.bottom;

    if (innerWidth <= 0 || innerHeight <= 0) {
        return null;
    }
    const baseLineSafe = baseline <= 0 ? 1 : baseline;
    const depthSafe = Math.min(Math.max(depth, 0), baseLineSafe * 0.95);

    const points = buildTransitPoints({
        baseline: baseLineSafe,
        depth: depthSafe,
        preTransitDuration,
        ingressDuration,
        flatDuration,
        egressDuration,
        postTransitDuration
    });

    const lowestValue = Math.min(...points.map(([, value]) => value));
    const highestValue = Math.max(...points.map(([, value]) => value));
    const yPadding = baseLineSafe * 0.1;
    const minValue = Math.min(lowestValue, baseLineSafe - depthSafe) - yPadding;
    const maxValue = Math.max(highestValue, baseLineSafe) + yPadding;
    const effectiveRange = maxValue - minValue || 1;

    const xScale = (time) => pad.left + time * innerWidth;
    const yScale = (value) => pad.top + (maxValue - value) * (innerHeight / effectiveRange);

    const pathD = points
        .map(([time, value], index) => {
            const command = index === 0 ? 'M' : 'L';
            return `${command}${xScale(time)} ${yScale(value)}`;
        })
        .join(' ');

    const ticks = Math.max(1, Math.round(tickCount));
    const tickValues = Array.from({ length: ticks + 1 }, (_, index) => index / ticks);

    return (
        <div
            className={`rounded-xl border border-[#f6a23a]/30 bg-black/60 p-4 backdrop-blur-sm ${className}`.trim()}
            style={{
                ...style,
                background:
                    'radial-gradient(circle at top, rgba(255, 193, 120, 0.15), rgba(0, 0, 0, 0.6) 55%)'
            }}
        >
            <svg width={width} height={height} role="img" aria-label="Transit light curve visualization">
                <rect x={0} y={0} width={width} height={height} fill={backgroundColor} rx={18} />
                <g>
                    <line
                        x1={pad.left}
                        y1={pad.top}
                        x2={pad.left}
                        y2={pad.top + innerHeight}
                        stroke={axisColor}
                        strokeWidth={2}
                    />
                    <line
                        x1={pad.left}
                        y1={pad.top + innerHeight}
                        x2={pad.left + innerWidth}
                        y2={pad.top + innerHeight}
                        stroke={axisColor}
                        strokeWidth={2}
                    />
                </g>
                <g>
                    {tickValues.map((tick, index) => {
                        const x = xScale(tick);
                        return (
                            <g key={`time-${tick}`}>
                                <line
                                    x1={x}
                                    y1={pad.top + innerHeight}
                                    x2={x}
                                    y2={pad.top + innerHeight + 6}
                                    stroke={axisColor}
                                    strokeWidth={1.5}
                                />
                                <text
                                    x={x}
                                    y={pad.top + innerHeight + 22}
                                    textAnchor="middle"
                                    fill={labelColor}
                                    fontSize={12}
                                    fontFamily="monospace"
                                >
                                    {index === 0 ? '0' : index}
                                </text>
                            </g>
                        );
                    })}
                </g>
                <g>
                    {tickValues.slice(1, -1).map((tick) => {
                        const y = pad.top + innerHeight - tick * innerHeight;
                        return (
                            <g key={`grid-${tick}`}>
                                <line
                                    x1={pad.left}
                                    y1={y}
                                    x2={pad.left + innerWidth}
                                    y2={y}
                                    stroke={gridColor}
                                    strokeDasharray="4 6"
                                />
                            </g>
                        );
                    })}
                </g>
                <path d={pathD} fill="none" stroke={strokeColor} strokeWidth={3} strokeLinecap="round" />
                <polygon
                    points={`${xScale(points[0][0])},${yScale(points[0][1])} ${points
                        .slice(1)
                        .map(([time, value]) => `${xScale(time)},${yScale(value)}`)
                        .join(' ')} ${pad.left + innerWidth},${pad.top + innerHeight} ${pad.left},${pad.top + innerHeight}`}
                    fill="rgba(246, 162, 58, 0.12)"
                />
                <text
                    x={pad.left / 2}
                    y={pad.top + innerHeight / 2}
                    fill={labelColor}
                    fontSize={12}
                    fontFamily="monospace"
                    transform={`rotate(-90 ${pad.left / 2} ${pad.top + innerHeight / 2})`}
                    textAnchor="middle"
                >
                    LIGHT
                </text>
                <text
                    x={pad.left + innerWidth / 2}
                    y={pad.top + innerHeight + 38}
                    fill={labelColor}
                    fontSize={12}
                    fontFamily="monospace"
                    textAnchor="middle"
                >
                    TIME
                </text>
            </svg>
        </div>
    );
}
