
document.addEventListener("DOMContentLoaded", async () => {
    const kpiPatients = document.getElementById("kpiPatients");
    const kpiIncontri = document.getElementById("kpiIncontri");
    const kpiParametri = document.getElementById("kpiParametri");
    const kpiCondizioni = document.getElementById("kpiCondizioni");

    async function updateKPIs() {
        try {
            const res = await fetch("/api/stats");
            const stats = await res.json();
            kpiPatients.textContent = stats.patients;
            kpiIncontri.textContent = stats.encounters;
            kpiParametri.textContent = stats.observations;
            kpiCondizioni.textContent = stats.conditions;

        } catch (error) {
            console.error("Errore caricamento KPI:", error);
        }
    }

    function getChartType(field) {
        if (field === "age_group") return "bar";
        return "pie";
    }

    function getColorPalette(size) {
        const palette = [
            "#60A5FA", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6",
            "#EC4899", "#3B82F6", "#F43F5E", "#22C55E", "#EAB308"
        ];
        return Array.from({ length: size }, (_, i) => palette[i % palette.length]);
    }

    async function fetchAndRenderChart(canvasId, field) {
        const url = `/api/stats/aggregate/${field}`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (!res.ok || !data || Object.keys(data).length === 0) {
                console.warn("Nessun dato per", field);
                return;
            }

            const canvas = document.getElementById(canvasId);
            if (canvas.chartInstance) {
                canvas.chartInstance.destroy();
            }

            const labels = Object.keys(data);
            const values = Object.values(data);
            const backgroundColors = getColorPalette(labels.length);

            canvas.chartInstance = new Chart(canvas, {
                type: getChartType(field),
                data: {
                    labels: labels,
                    datasets: [{
                        label: field,
                        data: values,
                        backgroundColor: backgroundColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true },
                        title: {
                            display: true,
                            text: `Distribuzione per ${field}`
                        }
                    },
                    scales: getChartType(field) === "bar" ? {
                        y: {
                            beginAtZero: true
                        }
                    } : {}
                }
            });

        } catch (error) {
            console.error("Errore nel caricamento del grafico:", error);
        }
    }

    document.getElementById("aggregationField1").addEventListener("change", e => {
        fetchAndRenderChart("chart1", e.target.value);
    });

    document.getElementById("aggregationField2").addEventListener("change", e => {
        fetchAndRenderChart("chart2", e.target.value);
    });

    await updateKPIs();
    fetchAndRenderChart("chart1", document.getElementById("aggregationField1").value);
    fetchAndRenderChart("chart2", document.getElementById("aggregationField2").value);
});
