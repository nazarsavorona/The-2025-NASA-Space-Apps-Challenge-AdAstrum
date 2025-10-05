import { Bar } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);
export default function FeatureImportance({ features }) {
    // Sort features by importance (descending)
    const sorted = Object.entries(features).sort((a, b) => b[1] - a[1]);
    const labels = sorted.map(([name]) => name);
    const values = sorted.map(([_, importance]) => importance);

    const data = {
        labels,
        datasets: [
            {
                label: "Importance",
                data: values,
                backgroundColor: "rgba(168, 85, 247, 0.8)", // purple
                borderColor: "rgba(168, 85, 247, 1)",
                borderWidth: 1,
            },
        ],
    };

    const options = {
        indexAxis: "y", // horizontal bar chart
        responsive: true,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: "Feature importance",
                color: "#fff",
                font: { size: 18 },
            },
        },
        scales: {
            x: {
                ticks: { color: "#fff" },
                grid: { color: "rgba(255,255,255,0.1)" },
            },
            y: {
                ticks: { color: "#fff" },
                grid: { color: "rgba(255,255,255,0.1)" },
            },
        },
    };

    return (
        <div className="relative w-full max-w-2xl p-6 rounded-xl bg-gradient-to-br from-[#1a1a2e] via-[#13111c] to-[#0d0b13] shadow-xl border border-white/10">
            <Bar data={data} options={options} />
        </div>
    );
}