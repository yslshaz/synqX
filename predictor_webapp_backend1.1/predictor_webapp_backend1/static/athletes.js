// Athletes page JS

let athletesData = [];
let mlSchema = null;

const HIDDEN_DEFAULTS = { "Unnamed: 3": 1 };
const HIDDEN_UI = new Set(["Unnamed: 3", "Heart_Rate_Body_Temp", "Oxygen_Heart_Rate_Ratio"]);

let currentFilter = new URLSearchParams(window.location.search).get('filter') || null;

function clearFilter() {
  window.location.href = '/dashboard';
}

function computeDerivedIndex(heartRate, bodyTemp, bloodOxygen) {
  let heartRateBodyTemp = null;
  let oxygenHeartRateRatio = null;
  if (heartRate != null && bodyTemp != null) heartRateBodyTemp = heartRate * bodyTemp;
  if (bloodOxygen != null && heartRate != null && heartRate !== 0) oxygenHeartRateRatio = bloodOxygen / heartRate;
  return {
    Heart_Rate_Body_Temp: heartRateBodyTemp,
    Oxygen_Heart_Rate_Ratio: oxygenHeartRateRatio
  };
}

function getPayload() {
  const payload = {};
  for (const [k, v] of Object.entries(HIDDEN_DEFAULTS)) payload[k] = v;
  if (!mlSchema || !mlSchema.features) return payload;
  const featureToInputId = {
    "Heart_Rate": "heart-rate",
    "Body_Temperature": "body-temp",
    "Blood_Oxygen": "blood-oxygen"
  };
  for (const f of mlSchema.features) {
    if (HIDDEN_UI.has(f)) continue;
    const inputId = featureToInputId[f] || f;
    const el = document.getElementById(inputId);
    payload[f] = el ? el.value : "";
  }
  const d = computeDerivedIndex(
    parseFloat(document.getElementById('heart-rate')?.value),
    parseFloat(document.getElementById('body-temp')?.value),
    parseFloat(document.getElementById('blood-oxygen')?.value)
  );
  payload["Heart_Rate_Body_Temp"] = d.Heart_Rate_Body_Temp ?? "";
  payload["Oxygen_Heart_Rate_Ratio"] = d.Oxygen_Heart_Rate_Ratio ?? "";
  return payload;
}

async function loadMLSchema() {
  if (mlSchema) return mlSchema;
  const res = await fetch("/schema");
  mlSchema = await res.json();
  return mlSchema;
}

function calculateFatiguePercentage(heartRate, bodyTemp, bloodOxygen) {
  let score = 0;
  const maxScore = 6;
  if (heartRate > 160) score += 2;
  else if (heartRate > 120) score += 1;
  if (bodyTemp >= 37.6) score += 2;
  else if (bodyTemp >= 37.3) score += 1;
  if (bloodOxygen <= 95) score += 2;
  else if (bloodOxygen <= 97) score += 1;
  return Math.round((score / maxScore) * 100);
}

function calculateEnergyPercentage(fatiguePercent) {
  return Math.max(0, 100 - fatiguePercent);
}

function getAthleteInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(' ');
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

function openAddAthleteModal() {
  document.getElementById('modal-title').textContent = 'Add Athlete';
  document.getElementById('submit-button').textContent = 'Add Athlete';
  document.getElementById('athlete-form').reset();
  document.getElementById('heart-rate-value').textContent = '120';
  document.getElementById('body-temp-value').textContent = '37.0';
  document.getElementById('blood-oxygen-value').textContent = '95';
  document.getElementById('athlete-modal').classList.add('active');
}

function closeAthleteModal() {
  document.getElementById('athlete-modal').classList.remove('active');
  document.getElementById('athlete-form').reset();
}

async function fetchAthletes() {
  try {
    const response = await fetch('/api/athletes');
    if (!response.ok) throw new Error('Failed to fetch athletes');
    const data = await response.json();
    athletesData = data;
    window.athletesData = athletesData;
    renderAthleteList(athletesData);
  } catch (error) {
    console.error('Error fetching athletes:', error);
    athletesData = [];
    window.athletesData = [];
    renderAthleteList(athletesData);
  }
}

async function initializeApp() {
  await fetchAthletes();
}

async function handleAthleteSubmit(event) {
  event.preventDefault();
  await loadMLSchema();
  if (athletesData.length >= 999) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'color:#EF4444;margin-top:12px;font-size:13px;';
    errorDiv.textContent = 'Maximum limit of 999 athletes reached. Please delete some athletes first.';
    event.target.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
    return;
  }

  const submitButton = document.getElementById('submit-button');
  const originalText = submitButton.textContent;
  submitButton.textContent = 'Saving...';
  submitButton.disabled = true;

  let fatigueStatus = 'Unknown';
  try {
    const predictRes = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getPayload())
    });
    if (predictRes.ok) {
      const predictData = await predictRes.json();
      fatigueStatus = predictData.prediction || 'Unknown';
    }
  } catch (err) {
    // fallback: keep as 'Unknown'
  }

  const athleteName = document.getElementById('athlete-name').value;
  const heartRate = parseFloat(document.getElementById('heart-rate').value);
  const bodyTemp = parseFloat(document.getElementById('body-temp').value);
  const bloodOxygen = parseFloat(document.getElementById('blood-oxygen').value);
  const notes = document.getElementById('notes').value;

  const athleteData = {
    athlete_name: athleteName,
    heart_rate: heartRate,
    body_temperature: bodyTemp,
    blood_oxygen: bloodOxygen,
    fatigue_status: fatigueStatus,
    notes: notes || ''
  };

  try {
    const response = await fetch('/api/athletes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(athleteData)
    });
    if (!response.ok) throw new Error('Failed to add athlete');
    await fetchAthletes();
    closeAthleteModal();
  } catch (error) {
    submitButton.disabled = false;
    submitButton.textContent = originalText;
    console.error('Error creating athlete:', error);
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'color:#EF4444;margin-top:12px;font-size:13px;';
    errorDiv.textContent = 'An error occurred. Please try again.';
    event.target.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
    return;
  }

  submitButton.disabled = false;
  submitButton.textContent = originalText;
}

function renderAthleteList(data) {
  const container = document.getElementById('athlete-list-container');
  const filterContainer = document.getElementById('filter-indicator-container');
  if (!container || !filterContainer) return;

  let filteredData = data || [];
  if (currentFilter) {
    filteredData = filteredData.filter(a => a.fatigue_status === currentFilter);
  }

  if (currentFilter) {
    const badgeClass = currentFilter === 'Not Fatigued' ? 'optimal' :
                      currentFilter === 'Moderate' ? 'moderate' : 'fatigued';
    filterContainer.innerHTML = `
      <div class="filter-indicator">
        <span>Showing:</span>
        <span class="filter-badge ${badgeClass}">${currentFilter}</span>
        <button class="clear-filter-btn" onclick="clearFilter()">×</button>
      </div>
    `;
  } else {
    filterContainer.innerHTML = '';
  }

  if (filteredData.length === 0) {
    const emptyMessage = currentFilter ?
      `<h3>No ${currentFilter} Athletes</h3><p>No athletes found with ${currentFilter} status</p>` :
      `<h3>No Athletes Yet</h3><p>Add your first athlete to start monitoring vitals</p>`;
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        ${emptyMessage}
      </div>
    `;
    return;
  }

  const athleteCards = filteredData.map(athlete => {
    const fatiguePercent = calculateFatiguePercentage(athlete.heart_rate, athlete.body_temperature, athlete.blood_oxygen);
    const energyPercent = calculateEnergyPercentage(fatiguePercent);
    const status = (athlete.fatigue_status === 'Not Fatigued') ? 'Normal' : athlete.fatigue_status;
    const energyClass = status === 'Normal' ? 'optimal' :
                        status === 'Moderate' ? 'moderate' : 'fatigued';
    let sphereColor1, sphereColor2;
    if (status === 'Normal') {
      sphereColor1 = '#34D399';
      sphereColor2 = '#10B981';
    } else if (status === 'Moderate') {
      sphereColor1 = '#FBBF24';
      sphereColor2 = '#F59E0B';
    } else {
      sphereColor1 = '#F87171';
      sphereColor2 = '#EF4444';
    }
    const initials = getAthleteInitials(athlete.name);
    const statusClass = status === 'Normal' ? 'status-normal' :
            status === 'Moderate' ? 'status-elevated' : 'status-fatigued';

    return `
      <div class="athlete-card" data-athlete-id="${athlete.id}" data-athlete-name="${athlete.name}">
        <div class="athlete-header">
          <div class="athlete-info-section">
            <div class="athlete-sphere">
              <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <filter id="ring-glow-${athlete.id}">
                    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                  <filter id="text-glow-${athlete.id}">
                    <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                  <linearGradient id="energy-grad-${athlete.id}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:${sphereColor1};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:${sphereColor2};stop-opacity:0.8" />
                  </linearGradient>
                </defs>
                <circle cx="50" cy="50" r="38" fill="#000000" opacity="0.9"/>
                <circle cx="50" cy="50" r="34" fill="none" stroke="${sphereColor2}" stroke-width="0.5" opacity="0.3"/>
                <circle cx="50" cy="50" r="30" fill="none" stroke="${sphereColor1}" stroke-width="0.5" opacity="0.4"/>
                <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="4.5" opacity="0.3"/>
                <circle cx="50" cy="50" r="45" fill="none" stroke="url(#energy-grad-${athlete.id})" stroke-width="4.5" opacity="1" filter="url(#ring-glow-${athlete.id})" stroke-linecap="round" stroke-dasharray="${(energyPercent / 100) * 283} 283" transform="rotate(-90 50 50)">
                  <animate attributeName="stroke-dasharray" from="0 283" to="${(energyPercent / 100) * 283} 283" dur="1.5s" fill="freeze"/>
                </circle>
                <circle cx="50" cy="5" r="2" fill="${sphereColor1}" opacity="${energyPercent > 90 ? '1' : '0.3'}"/>
                <circle cx="95" cy="50" r="2" fill="${sphereColor1}" opacity="${energyPercent > 70 ? '1' : '0.3'}"/>
                <circle cx="50" cy="95" r="2" fill="${sphereColor1}" opacity="${energyPercent > 50 ? '1' : '0.3'}"/>
                <circle cx="5" cy="50" r="2" fill="${sphereColor1}" opacity="${energyPercent > 30 ? '1' : '0.3'}"/>
                <text x="50" y="50" text-anchor="middle" dominant-baseline="central" font-family="'Orbitron', 'Montserrat', sans-serif" font-size="24" font-weight="900" fill="#FFFFFF" filter="url(#text-glow-${athlete.id})" letter-spacing="1">
                  ${initials}
                </text>
              </svg>
            </div>
            <div class="athlete-info">
              <div class="athlete-name">${athlete.name}</div>
              <div class="athlete-role">${athlete.position || 'N/A'}</div>
            </div>
          </div>
          <div class="status-badge ${statusClass}">${athlete.fatigue_status}</div>
        </div>
        <div class="energy-bar-section">
          <div class="energy-label">
            <span>Energy Level</span>
            <span class="energy-percentage">${energyPercent}%</span>
          </div>
          <div class="energy-bar">
            <div class="energy-bar-fill ${energyClass}" style="width: ${energyPercent}%;"></div>
          </div>
        </div>
        <div class="athlete-vitals">
          <div class="vital-row">
            <span class="vital-row-label">Heart Rate</span>
            <span class="vital-row-value">${athlete.heart_rate} bpm</span>
          </div>
          <div class="vital-row">
            <span class="vital-row-label">Temperature</span>
            <span class="vital-row-value">${Number(athlete.body_temperature).toFixed(1)}°C</span>
          </div>
          <div class="vital-row">
            <span class="vital-row-label">Blood Oxygen</span>
            <span class="vital-row-value">${athlete.blood_oxygen} %</span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `<div class="athlete-grid">${athleteCards}</div>`;

  setTimeout(() => {
    document.querySelectorAll('.energy-bar-fill').forEach(bar => {
      const width = bar.style.width;
      bar.style.width = '0%';
      void bar.offsetWidth;
      bar.style.transition = 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
      bar.style.width = width;
    });
  }, 100);

  setTimeout(() => {
    document.querySelectorAll('.athlete-sphere svg circle[stroke-dasharray]').forEach(ring => {
      const dash = ring.getAttribute('stroke-dasharray');
      ring.setAttribute('stroke-dasharray', '0 283');
      void ring.offsetWidth;
      ring.setAttribute('stroke-dasharray', dash);
    });
  }, 120);
}

document.addEventListener('DOMContentLoaded', () => {
  const addButton = document.querySelector('.add-athlete-button');
  if (addButton) addButton.addEventListener('click', openAddAthleteModal);

  const heartRateSlider = document.getElementById('heart-rate');
  const heartRateValue = document.getElementById('heart-rate-value');
  const bodyTempSlider = document.getElementById('body-temp');
  const bodyTempValue = document.getElementById('body-temp-value');
  const bloodOxygenSlider = document.getElementById('blood-oxygen');
  const bloodOxygenValue = document.getElementById('blood-oxygen-value');

  if (heartRateSlider && heartRateValue) {
    heartRateSlider.addEventListener('input', (e) => {
      heartRateValue.textContent = e.target.value;
    });
  }
  if (bodyTempSlider && bodyTempValue) {
    bodyTempSlider.addEventListener('input', (e) => {
      bodyTempValue.textContent = parseFloat(e.target.value).toFixed(1);
    });
  }
  if (bloodOxygenSlider && bloodOxygenValue) {
    bloodOxygenSlider.addEventListener('input', (e) => {
      bloodOxygenValue.textContent = e.target.value;
    });
  }

  initializeApp();
});
