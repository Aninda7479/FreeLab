// ScreenTime V2 - Dark UI Logic
let mainChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    setInterval(loadDashboardData, 60000); // refresh every minute
});

async function loadDashboardData() {
    try {
        const statsRes = await fetch('/api/stats?period=today');
        const stats = await statsRes.json();
        
        const topAppsRes = await fetch('/api/top-apps?period=today&limit=5');
        const topApps = await topAppsRes.json();
        
        const trendRes = await fetch('/api/daily-trend?period=7days');
        const trend = await trendRes.json();

        updateStats(stats);
        updateTopApps(topApps, stats.total_time);
        updateChart(trend);
        updateLocalDeviceStatus(stats);
    } catch (e) {
        console.error("Dashboard Load Error:", e);
    }
}

function formatDuration(seconds) {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds/60)}m ${Math.floor(seconds%60)}s`;
    return `${Math.floor(seconds/3600)}h ${Math.floor((seconds%3600)/60)}m`;
}

function updateStats(stats) {
    document.getElementById('total-time').innerText = formatDuration(stats.total_time);
    document.getElementById('apps-count').innerText = stats.apps_count;
}

function updateTopApps(apps, totalTime) {
    const container = document.getElementById('activity-list');
    container.innerHTML = '';
    
    if (apps.length === 0) {
        container.innerHTML = '<div class="activity-item">No activity today yet.</div>';
        return;
    }

    const colors = ['#FF6B4A', '#7CE0FF', '#3E7BFA', '#9994B6', '#FFFFFF'];

    apps.forEach((app, i) => {
        const color = colors[i % colors.length];
        const percent = totalTime > 0 ? (app.duration / totalTime) * 100 : 0;
        
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-name">
                <span class="activity-icon">${app.icon}</span>
                <span>${app.display_name}</span>
            </div>
            <div class="activity-bar-container">
                <div class="activity-bar" style="width: ${percent}%; background-color: ${color}"></div>
            </div>
            <div class="activity-time">${formatDuration(app.duration)}</div>
        `;
        container.appendChild(item);
    });
}

function updateChart(trend) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    const labels = trend.map(t => {
        const d = new Date(t.date);
        return d.toLocaleDateString('en-US', {weekday: 'short'});
    });
    const data = trend.map(t => t.duration / 3600); // in hours

    if (mainChart) {
        mainChart.destroy();
    }

    Chart.defaults.color = '#9994B6';
    Chart.defaults.font.family = 'Outfit';

    mainChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Screen Time (Hours)',
                data: data,
                backgroundColor: function(context) {
                    const ctx = context.chart.ctx;
                    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
                    gradient.addColorStop(0, '#3E7BFA');
                    gradient.addColorStop(1, '#1C1935');
                    return gradient;
                },
                borderRadius: 8,
                barThickness: 16
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    border: { display: false }
                },
                x: {
                    grid: { display: false },
                    border: { display: false }
                }
            }
        }
    });
}

function updateLocalDeviceStatus(stats) {
    document.getElementById('win-stats').innerText = `Tracked ${formatDuration(stats.total_time)} today. Listening on mDNS...`;
}

function syncData() {
    // In full V2, this will forcefully push/pull from known local IP
    alert("mDNS active. Auto-discovering Android devices on LAN...");
}
