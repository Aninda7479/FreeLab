const API_BASE = 'http://localhost:8080/api';

// Navigation State
let weekOffset = 0;
let selectedDate = null; // YYYY-MM-DD string

document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    initDashboard();
});

function setupNavigation() {
    const prevBtn = document.getElementById('prevWeekBtn');
    const nextBtn = document.getElementById('nextWeekBtn');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            weekOffset--;
            selectedDate = null; // Reset selection on weak change
            renderAll();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (weekOffset < 0) {
                weekOffset++;
                selectedDate = null;
                renderAll();
            }
        });
    }
}

async function initDashboard() {
    // On Init, default to Today if available
    const today = new Date();
    selectedDate = getLocalDateStr(today);

    renderAll();
}

async function renderAll() {
    renderWeekHeader();
    updateNavState();
    await loadData();
}

function updateNavState() {
    const nextBtn = document.getElementById('nextWeekBtn');
    if (nextBtn) {
        const isTodayOrFuture = (weekOffset >= 0);
        nextBtn.disabled = isTodayOrFuture;
    }
}

function getLocalDateStr(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Helper to get array of Dates for current view (Fixed Sunday to Saturday)
function getDaysForView() {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 = Sunday

    // Calculate the Sunday of the *current* week
    const currentWeekSunday = new Date(today);
    currentWeekSunday.setDate(today.getDate() - dayOfWeek);

    // Apply offset to shift by weeks
    const targetSunday = new Date(currentWeekSunday);
    targetSunday.setDate(currentWeekSunday.getDate() + (weekOffset * 7));

    const days = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(targetSunday);
        d.setDate(targetSunday.getDate() + i);
        days.push(d);
    }
    return days;
}

function renderWeekHeader() {
    const dateRow = document.getElementById('dateRow');
    if (!dateRow) return;

    dateRow.innerHTML = '';

    const days = getDaysForView();
    const today = new Date();
    const actualTodayStr = getLocalDateStr(today);

    days.forEach((date, i) => {
        const dateStr = getLocalDateStr(date);
        const isToday = (dateStr === actualTodayStr);
        // Future check: strictly greater than current Date
        const isFuture = (getLocalDateStr(date) > actualTodayStr);
        const isSelected = (selectedDate === dateStr);

        const el = document.createElement('div');
        el.className = `date-num ${isToday ? 'active' : ''} ${isFuture ? 'disabled' : ''} ${isSelected ? 'selected-for-filter' : ''}`;
        el.textContent = date.getDate();

        if (!isFuture) {
            el.style.cursor = 'pointer';
            el.onclick = () => onDateClick(dateStr);
        } else {
            el.style.cursor = 'default';
        }

        dateRow.appendChild(el);
    });
}

function onDateClick(dateStr) {
    if (selectedDate === dateStr) {
        selectedDate = null; // Toggle off
    } else {
        selectedDate = dateStr;
    }
    // Re-render to update UI selection and fetch filtered apps
    renderWeekHeader(); // update selection styles
    // We also need to re-render chart to highlight selection, not just apps
    loadData();
}

async function loadData() {
    try {
        const days = getDaysForView();
        const startStr = getLocalDateStr(days[0]); // Sunday
        const endStr = getLocalDateStr(days[6]);   // Saturday

        // Fetch Trend for this specific fixed week
        const trendPromise = fetch(`${API_BASE}/daily-trend?from_date=${startStr}&to_date=${endStr}`).catch(() => null);

        // Fetch Apps
        let appsUrl = '';

        // Auto-select today if selectedDate is null AND 'today' is in this view (and not future)
        // Note: we can't easily auto-set selectedDate here because it causes recursion/side-effects if we aren't careful.
        // But renderWeekHeader handles the visual class.
        // If we are in initDashboard, we set selectedDate=Today.
        // If user navigates to PREVIOUS week, selectedDate becomes null.

        if (selectedDate) {
            // Specific day selected
            appsUrl = `${API_BASE}/top-apps?target_date=${selectedDate}`;
        } else {
            // No specific day (e.g. browsing past weeks without clicking)
            // Default to whole week?
            appsUrl = `${API_BASE}/top-apps?from_date=${startStr}&to_date=${endStr}`;
        }

        const appsPromise = fetch(appsUrl).catch(() => null);

        const [trendRes, appsRes] = await Promise.all([trendPromise, appsPromise]);

        // Disable Mock Data - Return empty array if fetch fails or returns null
        const trendData = trendRes ? await trendRes.json() : [];
        const appsData = appsRes ? await appsRes.json() : [];

        renderChart(trendData);
        renderAppList(appsData);

        // Update list header
        const titleEl = document.getElementById('listTitleName');
        if (titleEl) {
            if (selectedDate) {
                // If today is selected, say "Name (Today)" or "Name (Date)"
                const today = new Date();
                if (selectedDate === getLocalDateStr(today)) {
                    titleEl.textContent = 'Name (Today)';
                } else {
                    titleEl.textContent = `Name (${selectedDate})`;
                }
                titleEl.style.color = 'var(--text-primary)'; // Or accent color
            } else {
                if (appsUrl.includes('target_date')) {
                    titleEl.textContent = 'Name (Today)';
                } else {
                    titleEl.textContent = 'Name (Weekly)';
                }
                titleEl.style.color = '';
            }
        }

    } catch (e) {
        console.error("Data load failed", e);
        renderChart([]);
        renderAppList([]);
    }
}

function renderChart(data) {
    const container = document.getElementById('barsContainer');
    if (!container) return;

    container.innerHTML = '';

    // --- Dynamic Y-Axis Scale Improvement (Strict) ---
    // 1. Calculate Max in seconds (minimum 1 second to avoid div by zero)
    const maxVal = Math.max(...data.map(d => d.duration), 1);

    // Scale Top is exactly the max value
    const scaleTop = maxVal;

    // --- Render Grid Lines (Top and Center) ---
    const gridContainer = document.getElementById('gridLines');
    if (gridContainer) {
        gridContainer.innerHTML = '';

        // Helper to create a line
        const createLine = (valueSeconds, labelText, bottomPct) => {
            const line = document.createElement('div');
            line.className = 'grid-line';
            line.style.bottom = `${bottomPct}%`;
            // Remove top style if it was set before
            line.style.top = 'auto';
            line.innerHTML = `<span class="grid-label">${labelText}</span>`;
            gridContainer.appendChild(line);
        };

        // 1. Top Line (at 100%)
        createLine(scaleTop, formatDuration(scaleTop), 100);

        // 2. Center Line (at ~50%) - rounded to integer
        // Calculate mid value in appropriate unit for "clean" integer look if possible
        let midSeconds = scaleTop / 2;

        // Use formatDuration but maybe we can just use the exact 50% point
        // User asked "around the center(integer)". 
        // If 7h -> 3.5h. Integer might mean 3h or 4h.
        // Let's force it to be the exact middle visually (50%) but formatted nicely.
        // Or if we want an integer *scale line*, we find the nearest integer hour/minute.
        // Let's try finding a nice integer middle value close to 50%.

        let midLabel = formatDuration(midSeconds);
        // If huge hours, e.g. 5h max -> 2.5h. 
        // Let's stick to strict 50% line for visual symmetry, labeled accurately.
        createLine(midSeconds, midLabel, 50);

        // 3. Baseline (0) - Optional but good for context
        // createLine(0, '0m', 0); // Usually implied by bottom of graph
    }


    // --- Render Bars ---
    const daysLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    const today = new Date();
    const actualTodayStr = getLocalDateStr(today);

    const viewDays = getDaysForView();
    const dataMap = {};
    data.forEach(d => dataMap[d.date] = d.duration);

    viewDays.forEach((dateObj, index) => {
        const dateStr = getLocalDateStr(dateObj);
        const duration = dataMap[dateStr] || 0;

        // Height is simple percentage of max
        const heightPct = (duration / scaleTop) * 100;
        // Clamp mostly for safety, though math shouldn't exceed 100
        const clampedHeight = Math.min(heightPct, 100);

        const dayLetter = daysLabels[dateObj.getDay()];
        const isItemToday = (dateStr === actualTodayStr);
        const isSelected = (selectedDate === dateStr);

        const col = document.createElement('div');
        col.className = 'chart-col';
        col.onclick = () => onDateClick(dateStr);
        // Tooltip using standard title attribute
        col.title = `${dateStr}: ${formatDuration(duration)}`;

        let barClass = 'bar';
        if (duration > 0) barClass += ' filled';
        if (isItemToday) barClass += ' today-highlight';
        if (isSelected) barClass += ' bar-selected';

        col.innerHTML = `
            <div class="bar-wrapper">
                <div class="${barClass}" style="height: ${clampedHeight}%"></div>
            </div>
            <div class="day-label ${isItemToday ? 'current-day-circle' : ''} ${isSelected ? 'selected-day-text' : ''}">
                ${dayLetter}
            </div>
        `;
        container.appendChild(col);
    });
}

function renderAppList(apps) {
    const container = document.getElementById('appList');
    if (!container) return;

    container.innerHTML = '';

    // Filter out apps with duration < 60 seconds (1 minute)
    const filteredApps = apps.filter(app => app.duration >= 60);

    if (filteredApps.length === 0) {
        container.innerHTML = '<div style="color:var(--text-secondary); text-align:center; padding:20px;">No activity > 1 min</div>';
        return;
    }

    // Sort by duration desc just in case
    filteredApps.sort((a, b) => b.duration - a.duration);

    filteredApps.forEach(app => {
        const row = document.createElement('div');
        row.className = 'app-item';

        const timeStr = formatDuration(app.duration);

        // Handle Icon: check if it looks like a URL or use initials
        let iconHtml = '';
        if (app.icon && (app.icon.startsWith('http') || app.icon.startsWith('data:image'))) {
            iconHtml = `<img src="${app.icon}" alt="icon" onerror="this.style.display='none'">`;
        } else {
            // Fallback to initial
            iconHtml = app.display_name[0].toUpperCase();
        }

        row.innerHTML = `
            <div class="app-info">
                 <div class="app-icon-placeholder" style="background-color: ${stringToColor(app.display_name)}">
                    ${iconHtml}
                 </div>
                <div class="app-name" title="${app.display_name}">${app.display_name}</div>
            </div>
            <div class="app-time">${timeStr}</div>
        `;
        container.appendChild(row);
    });
}

function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hrs > 0) return `${hrs}h ${mins}m`;
    return `${mins}m`;
}

// Compact formatter for grid lines (e.g., "8h" instead of "8h 0m")
function formatDurationSimple(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hrs > 0) {
        if (mins === 0) return `${hrs}h`;
        return `${hrs}h ${mins}m`;
    }
    return `${mins}m`;
}

function stringToColor(str) {
    if (!str) return '#1A1A1A';
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
    return '#' + '00000'.substring(0, 6 - c.length) + c;
}
