// Athlete Profile page JS
// window.athleteIdParam must be set by an inline <script> in the HTML before this file loads

document.addEventListener('DOMContentLoaded', async function() {
  const athleteIdParam = window.athleteIdParam || '';
  if (!athleteIdParam) return;
  try {
    const response = await fetch('/api/athletes');
    window.athletesData = await response.json();
    // Match by unique ID — handles duplicate names correctly
    const athlete = window.athletesData.find(a => String(a.id) === athleteIdParam);
    if (athlete) {
      openAthleteProfile(athlete.id);
      updateWarningIndicators(athlete.fatigue_status);
    }
    setupGestureControls();
  } catch (error) {
    console.error('Failed to load athlete:', error);
  }
});

// Baseline vitals
let baselineVitals = {
  heart_rate: 120,
  temperature: 36.8,
  blood_oxygen: 98
};
let vitalHistory = {
  heart_rate: [],
  temperature: [],
  blood_oxygen: []
};

// Gesture control variables
let doubleTapTimer = null;
let longPressTimer = null;
let longPressTarget = null;

// Particle System Functions
function createParticle(startX, startY, targetX, targetY, color, isLarge = false) {
  const container = document.getElementById('particle-container');
  if (!container) return;

  const particle = document.createElement('div');
  particle.className = isLarge ? 'particle large' : 'particle';
  particle.style.left = startX + 'px';
  particle.style.top = startY + 'px';
  particle.style.color = color;

  const deltaX = targetX - startX;
  const deltaY = targetY - startY;

  particle.style.setProperty('--tx', deltaX + 'px');
  particle.style.setProperty('--ty', deltaY + 'px');

  container.appendChild(particle);

  particle.style.animation = 'particle-flow-in 2s cubic-bezier(0.4, 0, 0.2, 1) forwards';

  setTimeout(() => {
    particle.remove();
  }, 2000);
}

function startParticleFlow(status) {
  const container = document.getElementById('particle-container');
  if (!container) return;

  const orbitalPositions = [
    { x: 340, y: 100 },
    { x: 580, y: 340 },
    { x: 100, y: 340 }
  ];

  const centerX = 340;
  const centerY = 340;

  let color, interval, largeParticleChance;
  if (status === 'Not Fatigued') {
    color = '#00FF88';
    interval = 200;
    largeParticleChance = 0.6;
  } else if (status === 'Moderate') {
    color = '#FFB800';
    interval = 500;
    largeParticleChance = 0.3;
  } else {
    color = '#FF3366';
    interval = 300;
    largeParticleChance = 0.2;
  }

  const particleInterval = setInterval(() => {
    if (document.getElementById('athlete-profile').classList.contains('active')) {
      const randomOrbital = orbitalPositions[Math.floor(Math.random() * orbitalPositions.length)];
      const isLarge = Math.random() < largeParticleChance;
      createParticle(randomOrbital.x, randomOrbital.y, centerX, centerY, color, isLarge);

      if (status === 'Normal' && Math.random() < 0.4) {
        const randomOrbital2 = orbitalPositions[Math.floor(Math.random() * orbitalPositions.length)];
        setTimeout(() => {
          createParticle(randomOrbital2.x, randomOrbital2.y, centerX, centerY, color, isLarge);
        }, 100);
      }
    } else {
      clearInterval(particleInterval);
    }
  }, interval);
}

// Warning indicators
function updateWarningIndicators(status) {
  const warningOrbit = document.getElementById('warning-orbit');
  if (!warningOrbit) return;
  warningOrbit.innerHTML = '';
}

// Reactor aura intensity
function updateReactorAura(status) {
  const aura = document.getElementById('reactor-aura');
  const reactor = document.getElementById('central-reactor');
  if (!aura || !reactor) return;

  aura.classList.remove('intense');
  reactor.classList.remove('reactor-fatigued');

  if (status === 'Fatigued') {
    aura.classList.add('intense');
    reactor.classList.add('reactor-fatigued');
  }
}

// Heat trail animation
function createHeatTrail(x, y, color) {
  const trail = document.createElement('div');
  trail.className = 'heat-trail';
  trail.style.left = x + 'px';
  trail.style.top = y + 'px';
  trail.style.color = color;
  trail.style.animation = 'trail-fade 0.8s ease-out forwards';

  const container = document.querySelector('.orbital-system');
  if (container) {
    container.appendChild(trail);
    setTimeout(() => trail.remove(), 800);
  }
}

// Energy burst celebration — fires on page load when energy = 100%
function celebrateFullEnergy() {
  const reactor = document.getElementById('central-reactor');
  if (!reactor) return;

  const color = reactor.style.color || '#00FF88';

  for (let i = 0; i < 5; i++) {
    setTimeout(() => {
      const ring = document.createElement('div');
      ring.className = 'energy-burst-ring animate';
      ring.style.color = color;
      reactor.appendChild(ring);
      setTimeout(() => ring.remove(), 1000);
    }, i * 180);
  }
}

// Sparkline chart functions
function generateVitalHistory(currentValue, type) {
  const history = [];
  const points = 20;

  let baseValue, variance;
  if (type === 'heart_rate') {
    baseValue = currentValue;
    variance = 10;
  } else if (type === 'temperature') {
    baseValue = currentValue;
    variance = 0.3;
  } else {
    baseValue = currentValue;
    variance = 2;
  }

  for (let i = 0; i < points; i++) {
    const randomOffset = (Math.random() - 0.5) * variance;
    history.push(baseValue + randomOffset);
  }

  history[points - 1] = currentValue;
  return history;
}

function drawSparkline(canvasId, data, color, minVal, maxVal) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const width = canvas.width = canvas.offsetWidth * 2;
  const height = canvas.height = canvas.offsetHeight * 2;

  ctx.clearRect(0, 0, width, height);

  if (data.length < 2) return;

  const padding = 10;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const xStep = chartWidth / (data.length - 1);
  const range = maxVal - minVal;

  const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
  gradient.addColorStop(0, color + '40');
  gradient.addColorStop(1, color + '00');

  ctx.beginPath();
  ctx.moveTo(padding, height - padding);

  data.forEach((value, index) => {
    const x = padding + index * xStep;
    const y = height - padding - ((value - minVal) / range) * chartHeight;
    ctx.lineTo(x, y);
  });

  ctx.lineTo(width - padding, height - padding);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  ctx.beginPath();
  data.forEach((value, index) => {
    const x = padding + index * xStep;
    const y = height - padding - ((value - minVal) / range) * chartHeight;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.strokeStyle = color;
  ctx.lineWidth = 4;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  const lastX = padding + (data.length - 1) * xStep;
  const lastY = height - padding - ((data[data.length - 1] - minVal) / range) * chartHeight;

  ctx.beginPath();
  ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 2;
  ctx.stroke();
}

let activeSparkline = null;
let sparklineTimer = null;

function showSparkline(type) {
  if (activeSparkline) {
    document.getElementById(activeSparkline).classList.remove('active');
  }

  clearTimeout(sparklineTimer);

  const sparklineId = `sparkline-${type}`;
  const sparkline = document.getElementById(sparklineId);
  if (!sparkline) return;

  activeSparkline = sparklineId;
  sparkline.classList.add('active');

  let canvasId, history, minVal, maxVal, color;

  if (type === 'heart-rate') {
    canvasId = 'sparkline-hr-canvas';
    history = vitalHistory.heart_rate.length ? vitalHistory.heart_rate : generateVitalHistory(window.currentAthlete.heart_rate, 'heart_rate');
    minVal = 60;
    maxVal = 180;
    color = '#A855F7';
  } else if (type === 'temperature') {
    canvasId = 'sparkline-temp-canvas';
    history = vitalHistory.temperature.length ? vitalHistory.temperature : generateVitalHistory(window.currentAthlete.body_temperature, 'temperature');
    minVal = 35;
    maxVal = 39;
    color = '#EC4899';
  } else if (type === 'blood-oxygen') {
    canvasId = 'sparkline-o2-canvas';
    history = vitalHistory.blood_oxygen.length ? vitalHistory.blood_oxygen : generateVitalHistory(window.currentAthlete.blood_oxygen, 'blood_oxygen');
    minVal = 90;
    maxVal = 100;
    color = '#3B82F6';
  }

  if (canvasId && history) {
    drawSparkline(canvasId, history, color, minVal, maxVal);
  }

  sparklineTimer = setTimeout(() => {
    sparkline.classList.remove('active');
    activeSparkline = null;
  }, 5000);
}

function hideSparkline(type) {
  const sparklineId = `sparkline-${type}`;
  const sparkline = document.getElementById(sparklineId);
  if (sparkline) {
    sparkline.classList.remove('active');
  }
  if (activeSparkline === sparklineId) {
    activeSparkline = null;
  }
  clearTimeout(sparklineTimer);
}

// Gesture Controls
function setupGestureControls() {
  const reactor = document.getElementById('central-reactor');
  if (!reactor) return;

  reactor.addEventListener('click', function(event) {
    event.stopPropagation();
    this.style.animation = 'none';
    void this.offsetWidth;
    this.style.animation = 'vibranium-vibrate 0.75s cubic-bezier(0.36, 0.07, 0.19, 0.97)';
    setTimeout(() => {
      this.style.animation = 'float-reactor 4.5s ease-in-out infinite';
    }, 750);
  });

  const orbitals = [
    { id: 'orbital-hr',   type: 'heart-rate' },
    { id: 'orbital-temp', type: 'temperature' },
    { id: 'orbital-o2',   type: 'blood-oxygen' }
  ];

  orbitals.forEach(orbital => {
    const element = document.getElementById(orbital.id);
    if (!element) return;

    let clickCount = 0;
    let clickTimer = null;

    element.addEventListener('click', function(e) {
      e.stopPropagation();
      clickCount++;

      if (clickCount === 1) {
        clickTimer = setTimeout(() => {
          const panel = document.getElementById(`comparison-panel-${orbital.type}`);
          if (panel) {
            if (panel.classList.contains('active')) {
              panel.classList.remove('active');
            } else {
              document.querySelectorAll('.comparison-panel').forEach(p => {
                p.classList.remove('active');
              });
              panel.classList.add('active');
              updateComparisonPanel(orbital.type);
            }
          }
          clickCount = 0;
        }, 300);
      } else if (clickCount === 2) {
        clearTimeout(clickTimer);
        clickCount = 0;

        const panel = document.getElementById(`comparison-panel-${orbital.type}`);
        if (panel) {
          panel.classList.remove('active');
        }

        showSparkline(orbital.type);
      }
    });
  });
}

function closeComparison(type) {
  const panel = document.getElementById(`comparison-panel-${type}`);
  if (panel) {
    panel.classList.remove('active');
  }
}

function updateComparisonPanel(type) {
  if (!window.currentAthlete) return;

  let current, baseline, unit, changeElement;

  if (type === 'heart-rate') {
    current = window.currentAthlete.heart_rate;
    baseline = baselineVitals.heart_rate;
    unit = 'bpm';
    changeElement = document.getElementById('heart-rate-change');
    document.getElementById('baseline-heart-rate').textContent = baseline;
    document.getElementById('current-heart-rate').textContent = current;
  } else if (type === 'temperature') {
    current = window.currentAthlete.body_temperature;
    baseline = baselineVitals.temperature;
    unit = '°C';
    changeElement = document.getElementById('temperature-change');
    document.getElementById('baseline-temperature').textContent = baseline.toFixed(1);
    document.getElementById('current-temperature').textContent = current.toFixed(1);
  } else if (type === 'blood-oxygen') {
    current = window.currentAthlete.blood_oxygen;
    baseline = baselineVitals.blood_oxygen;
    unit = '%';
    changeElement = document.getElementById('blood-oxygen-change');
    document.getElementById('baseline-blood-oxygen').textContent = baseline;
    document.getElementById('current-blood-oxygen').textContent = current;
  }

  if (changeElement) {
    const diff = current - baseline;
    const diffAbs = Math.abs(diff);

    changeElement.classList.remove('positive', 'negative', 'neutral');

    if (type === 'blood-oxygen') {
      if (diff > 0) {
        changeElement.classList.add('positive');
        changeElement.innerHTML = `<span class="comparison-arrow">↑</span><span>+${diffAbs}${unit} Better</span>`;
      } else if (diff < 0) {
        changeElement.classList.add('negative');
        changeElement.innerHTML = `<span class="comparison-arrow">↓</span><span>-${diffAbs}${unit} Lower</span>`;
      } else {
        changeElement.classList.add('neutral');
        changeElement.innerHTML = `<span class="comparison-arrow">   </span><span>No change</span>`;
      }
    } else {
      if (diff > 0) {
        changeElement.classList.add('negative');
        changeElement.innerHTML = `<span class="comparison-arrow">↑</span><span>+${type === 'temperature' ? diffAbs.toFixed(1) : diffAbs}${unit} Elevated</span>`;
      } else if (diff < 0) {
        changeElement.classList.add('positive');
        changeElement.innerHTML = `<span class="comparison-arrow">↓</span><span>-${type === 'temperature' ? diffAbs.toFixed(1) : diffAbs}${unit} Improved</span>`;
      } else {
        changeElement.classList.add('neutral');
        changeElement.innerHTML = `<span class="comparison-arrow">→</span><span>No change</span>`;
      }
    }
  }
}
