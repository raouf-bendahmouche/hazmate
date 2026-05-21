/**
 * What it does: Fetches analytics data and renders Chart.js visualizations.
 * Why it exists: Provides dynamic, interactive charts for decision-making without reloading the page.
 * What data it uses: Consumes the JSON payload from StatisticsService.
 */

let activityChartInstance = null;
let activityDataCache = null; // Client-side cache for instant timeframe toggling

async function loadStatistics() {
    try {
        const response = await fetch('http://127.0.0.1:5757/api/statistics/dashboard');
        const responseJson = await response.json();
        
        // Handle both standard JSON and _ok() wrapped payloads gracefully
        const data = responseJson.data ? responseJson.data : responseJson;

        renderKPICards(data.kpis);
        renderDistributionCharts(data.kpis, data.municipalities);
        
        activityDataCache = data.activity;
        renderActivityLineChart('daily'); // Default to daily
        renderMunicipalityStackedChart(data.municipalities);

        // Bind timeline dropdown
        document.getElementById('timeframe-select').addEventListener('change', (e) => {
            renderActivityLineChart(e.target.value);
        });

    } catch (error) {
        console.error("Failed to load dashboard statistics:", error);
    }
}

function renderKPICards(kpis) {
    document.getElementById('kpi-total').textContent = kpis.total;
    document.getElementById('kpi-active').textContent = kpis.active;
    document.getElementById('kpi-inactive').textContent = kpis.inactive;
    document.getElementById('kpi-public').textContent = kpis.public;
    document.getElementById('kpi-private').textContent = kpis.private;
}

function renderDistributionCharts(kpis, municipalities) {
    const labels = Object.keys(municipalities);
    const values = labels.map(l => municipalities[l].total);

    // Middle Left: Carriers per Municipality
    new Chart(document.getElementById('municipalityBarChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{ label: 'Total Carriers', data: values, backgroundColor: '#3b82f6' }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Middle Right: Public vs Private Pie Chart
    new Chart(document.getElementById('publicPrivatePieChart'), {
        type: 'pie',
        data: {
            labels: ['Public Carriers', 'Private Carriers'],
            datasets: [{
                data: [kpis.public, kpis.private],
                backgroundColor: ['#10b981', '#f59e0b']
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderActivityLineChart(timeframe) {
    const dataset = activityDataCache[timeframe];
    
    if (activityChartInstance) {
        activityChartInstance.destroy(); // Destroy old chart to prevent ghosting
    }

    activityChartInstance = new Chart(document.getElementById('activityLineChart'), {
        type: 'line',
        data: {
            labels: dataset.map(d => d.date || d.week || d.month),
            datasets: [{
                label: `Transports (${timeframe})`,
                data: dataset.map(d => d.count),
                borderColor: '#6366f1',
                tension: 0.3,
                fill: true,
                backgroundColor: 'rgba(99, 102, 241, 0.1)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderMunicipalityStackedChart(municipalities) {
    const labels = Object.keys(municipalities);
    const active = labels.map(l => municipalities[l].active);
    const inactive = labels.map(l => municipalities[l].inactive);

    new Chart(document.getElementById('municipalityStackedChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Active', data: active, backgroundColor: '#10b981' },
                { label: 'Inactive', data: inactive, backgroundColor: '#ef4444' }
            ]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false,
            scales: { x: { stacked: true }, y: { stacked: true } }
        }
    });
}

document.addEventListener('DOMContentLoaded', loadStatistics);