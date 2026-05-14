const COLORS = {
  accent: '#111111',
  success: '#16a34a',
  warning: '#b45309',
  danger: '#dc2626',
  muted: '#9ca3af',
  surface2: '#f7f7f7',
};

Chart.defaults.color = '#737373';
Chart.defaults.borderColor = '#e5e5e5';
Chart.defaults.font.family = "'DM Sans', system-ui, sans-serif";

function gradeColor(avg) {
  if (avg === null || avg === undefined) return COLORS.muted;
  if (avg >= 7) return COLORS.success;
  if (avg >= 5) return COLORS.warning;
  return COLORS.danger;
}

function initTrendChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Average Grade',
        data,
        borderColor: COLORS.accent,
        backgroundColor: 'rgba(17,17,17,0.05)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: COLORS.accent,
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          min: 1, max: 10,
          grid: { color: '#e5e5e5' },
          ticks: { stepSize: 1 },
        },
        x: { grid: { color: '#1e293b' } }
      }
    }
  });
}

function initSubjectBar(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const colors = data.map(v => gradeColor(v));
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Average',
        data,
        backgroundColor: colors.map(c => c + '33'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { min: 0, max: 10, grid: { color: '#1e293b' } },
        y: { grid: { display: false } }
      }
    }
  });
}

function initSubjectDetailBar(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const colors = data.map(v => gradeColor(v));
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Average by Type',
        data,
        backgroundColor: colors.map(c => c + '44'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 10, grid: { color: '#1e293b' } },
        x: { grid: { display: false } }
      }
    }
  });
}

function initDistributionChart(canvasId, distribution) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const labels = Object.keys(distribution);
  const data = Object.values(distribution);
  const colors = labels.map(l => gradeColor(parseFloat(l)));
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.map(c => c + '55'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#1e293b' }, ticks: { stepSize: 1 } },
        x: { grid: { display: false } }
      }
    }
  });
}
