// Dashboard page JS

function filterAthletesByStatus(status) {
  window.location.href = '/athletes?filter=' + encodeURIComponent(status);
}

async function fetchAthletes() {
  try {
    const response = await fetch('/api/athletes');
    if (!response.ok) throw new Error('Failed to fetch athletes');
    const data = await response.json();
    updateDashboardStats(data);
  } catch (error) {
    console.error('Error fetching athletes:', error);
    updateDashboardStats([]);
  }
}

function updateDashboardStats(data) {
  const totalElement = document.getElementById('total-athletes');
  const normalElement = document.getElementById('normal-count');
  const elevatedElement = document.getElementById('elevated-count');
  const fatiguedElement = document.getElementById('fatigued-count');

  const safeData = data || [];

  if (totalElement) totalElement.textContent = safeData.length;

  const normalCount = safeData.filter(a => a.fatigue_status === 'Not Fatigued').length;
  const elevatedCount = safeData.filter(a => a.fatigue_status === 'Moderate').length;
  const fatiguedCount = safeData.filter(a => a.fatigue_status === 'Fatigued').length;

  if (normalElement) normalElement.textContent = normalCount;
  if (elevatedElement) elevatedElement.textContent = elevatedCount;
  if (fatiguedElement) fatiguedElement.textContent = fatiguedCount;
}

document.addEventListener('DOMContentLoaded', () => {
  fetchAthletes();
});
