// ===================================
// Digital Wellbeing - Dashboard App
// ===================================

let currentPeriod = '7days';
let charts = {};

// ===================================
// Utility Functions
// ===================================

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('no-data').style.display = 'none';
    document.getElementById('stats-section').style.display = 'none';
    document.getElementById('top-apps-section').style.display = 'none';
    document.getElementById('charts-section').style.display = 'none';
    document.getElementById('browser-section').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showNoData() {
    hideLoading();
    document.getElementById('no-data').style.display = 'block';
    document.getElementById('stats-section').style.display = 'none';
    document.getElementById('top-apps-section').style.display = 'none';
    document.getElementById('charts-section').style.display = 'none';
    document.getElementById('browser-section').style.display = 'none';
}

function showContent() {
    hideLoading();
    document.getElementById('no-data').style.display = 'none'; // Ensure no-data is hidden
    document.getElementById('stats-section').style.display = 'grid';
    document.getElementById('top-apps-section').style.display = 'block';
    document.getElementById('charts-section').style.display = 'block';
    document.getElementById('browser-section').style.display = 'block';
}

// ===================================
// API Calls
// ===================================

async function fetchStats(period) {
    const response = await fetch(`/api/stats?period=${period}`);
    return await response.json();
}

async function fetchTopApps(period, limit = 10) {
    const response = await fetch(`/api/top-apps?period=${period}&limit=${limit}`);
    return await response.json();
}

async function fetchDailyTrend(period) {
    const response = await fetch(`/api/daily-trend?period=${period}`);
    return await response.json();
}

async function fetchBrowserActivity(period, limit = 10) {
    const response = await fetch(`/api/browser-activity?period=${period}&limit=${limit}`);
    return await response.json();
}

// ===================================
// UI Updates
// ===================================

function updateStats(stats) {
    document.getElementById('total-time').textContent = formatDuration(stats.total_time);
    document.getElementById('apps-count').textContent = stats.apps_count;

    // Update trend
    const trendIcon = document.getElementById('trend-icon');
    const trendValue = document.getElementById('trend-value');

    if (stats.change_direction === 'up') {
        trendIcon.textContent = '📈';
        trendValue.textContent = `+${stats.change_percent}%`;
    } else if (stats.change_direction === 'down') {
        trendIcon.textContent = '📉';
        trendValue.textContent = `-${stats.change_percent}%`;
    } else {
        trendIcon.textContent = '➖';
        trendValue.textContent = `${stats.change_percent}%`;
    }
}

function updateTopAppsCards(apps) {
    const container = document.getElementById('top-apps-grid');
    container.innerHTML = '';

    const topFive = apps.slice(0, 5);

    topFive.forEach((app, index) => {
        const card = document.createElement('div');
        card.className = 'app-card';
        card.style.animationDelay = `${index * 0.1}s`;

        // Check if icon is a base64 image or emoji
        const iconHtml = app.icon.startsWith('data:image')
            ? `<img src="${app.icon}" class="app-icon-img" alt="${app.display_name}">`
            : `<span class="app-icon">${app.icon}</span>`;

        card.innerHTML = `
            ${iconHtml}
            <div class="app-name">${app.display_name}</div>
            <div class="app-time">${formatDuration(app.duration)}</div>
        `;
        container.appendChild(card);
    });
}

function updateTopAppsChart(apps) {
    const ctx = document.getElementById('top-apps-chart');

    // Destroy existing chart
    if (charts.topApps) {
        charts.topApps.destroy();
    }

    const labels = apps.map(app => {
        // If icon is an image data URL, just use the name
        // If it's an emoji, include it in the label
        return app.icon.startsWith('data:') ? app.display_name : `${app.icon} ${app.display_name}`;
    });
    const data = apps.map(app => app.duration / 3600); // Convert to hours

    charts.topApps = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Hours',
                data: data,
                backgroundColor: 'rgba(0, 245, 255, 0.6)',
                borderColor: 'rgba(0, 245, 255, 1)',
                borderWidth: 2,
                borderRadius: 12,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const hours = context.parsed.x;
                            const seconds = apps[context.dataIndex].duration;
                            return formatDuration(seconds);
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateUsageDistributionChart(apps) {
    const ctx = document.getElementById('usage-distribution-chart');

    // Destroy existing chart
    if (charts.usageDistribution) {
        charts.usageDistribution.destroy();
    }

    const topSix = apps.slice(0, 6);
    const labels = topSix.map(app => {
        return app.icon.startsWith('data:') ? app.display_name : `${app.icon} ${app.display_name}`;
    });
    const data = topSix.map(app => app.duration);

    const colors = [
        'rgba(0, 245, 255, 0.9)',
        'rgba(181, 55, 242, 0.9)',
        'rgba(255, 0, 110, 0.9)',
        'rgba(59, 130, 246, 0.9)',
        'rgba(16, 185, 129, 0.9)',
        'rgba(249, 115, 22, 0.9)',
    ];

    charts.usageDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(10, 14, 39, 0.8)',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${formatDuration(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateDailyTrendChart(trendData) {
    const ctx = document.getElementById('daily-trend-chart');

    // Destroy existing chart
    if (charts.dailyTrend) {
        charts.dailyTrend.destroy();
    }

    if (!trendData || trendData.length === 0) {
        // If no trend data, maybe clear chart or return
        return;
    }

    const labels = trendData.map(item => {
        try {
            const date = new Date(item.date);
            // Check if date is valid
            if (isNaN(date.getTime())) return item.date;
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch (e) {
            return item.date;
        }
    });
    const data = trendData.map(item => item.duration / 3600); // Convert to hours

    charts.dailyTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Hours',
                data: data,
                fill: true,
                backgroundColor: 'rgba(0, 245, 255, 0.15)',
                borderColor: 'rgba(0, 245, 255, 1)',
                borderWidth: 3,
                tension: 0.4,
                pointBackgroundColor: 'rgba(0, 245, 255, 1)',
                pointBorderColor: 'rgba(181, 55, 242, 0.8)',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const hours = context.parsed.y.toFixed(1);
                            const seconds = trendData[context.dataIndex].duration;
                            return formatDuration(seconds);
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

function updateBrowserTable(browserData) {
    const container = document.getElementById('browser-table-container');

    if (browserData.length === 0) {
        container.innerHTML = '<p style="color: rgba(255, 255, 255, 0.7); text-align: center; padding: 2rem;">No browser activity recorded in this period.</p>';
        return;
    }

    let tableHTML = `
        <table class="browser-table">
            <thead>
                <tr>
                    <th>Icon</th>
                    <th>Browser</th>
                    <th>Website/Page</th>
                    <th>Time Spent</th>
                </tr>
            </thead>
            <tbody>
    `;

    browserData.forEach(item => {
        // Check if icon is a base64 image or emoji
        const iconHtml = item.icon.startsWith('data:image')
            ? `<img src="${item.icon}" class="browser-icon-img" alt="${item.browser}">`
            : `<span class="browser-icon">${item.icon}</span>`;

        tableHTML += `
            <tr>
                <td>${iconHtml}</td>
                <td>${item.browser}</td>
                <td>${item.site}</td>
                <td>${formatDuration(item.duration)}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// ===================================
// Main Data Load
// ===================================

async function loadDashboard(period) {
    showLoading();

    try {
        // Fetch all data in parallel
        const [stats, topApps, dailyTrend, browserActivity] = await Promise.all([
            fetchStats(period),
            fetchTopApps(period, 10),
            fetchDailyTrend(period),
            fetchBrowserActivity(period, 10)
        ]);

        // Check if we have data
        if (stats.total_time === 0 || topApps.length === 0) {
            showNoData();
            return;
        }

        // Update all UI elements
        showContent();

        try { updateStats(stats); } catch (e) { console.error('Stats error:', e); }
        try { updateTopAppsCards(topApps); } catch (e) { console.error('Cards error:', e); }
        try { updateTopAppsChart(topApps); } catch (e) { console.error('Top Apps Chart error:', e); }
        try { updateUsageDistributionChart(topApps); } catch (e) { console.error('Pie Chart error:', e); }
        try { updateDailyTrendChart(dailyTrend); } catch (e) { console.error('Trend Chart error:', e); }
        try { updateBrowserTable(browserActivity); } catch (e) { console.error('Browser Table error:', e); }

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNoData();
    }
}

// ===================================
// Event Handlers
// ===================================

function changePeriod(period) {
    currentPeriod = period;

    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.period === period) {
            btn.classList.add('active');
        }
    });

    // Reload dashboard
    loadDashboard(period);
}

function refreshData() {
    const btn = document.querySelector('.refresh-btn');
    btn.style.transform = 'rotate(360deg)';
    setTimeout(() => {
        btn.style.transform = '';
    }, 600);

    loadDashboard(currentPeriod);
}

// ===================================
// Initialize
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard(currentPeriod);
});
