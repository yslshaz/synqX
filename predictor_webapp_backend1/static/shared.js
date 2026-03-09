// Shared JS functions for all pages

// --- ML Integration (mlpage.html style) ---
let mlSchema = null;
const HIDDEN_DEFAULTS = { "Unnamed: 3": 1 };
const HIDDEN_UI = new Set(["Unnamed: 3", "Heart_Rate_Body_Temp", "Oxygen_Heart_Rate_Ratio"]);

async function loadMLSchema() {
  if (mlSchema) return mlSchema;
  const res = await fetch("/schema");
  mlSchema = await res.json();
  return mlSchema;
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

// Haptic Feedback Functions


// Navigation
function navigateToPage(pageName) {
  document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
  const pageElement = document.getElementById(pageName);
  if (pageElement) pageElement.classList.add('active');
  const navLink = document.querySelector(`[data-page="${pageName}"]`);
  if (navLink) navLink.classList.add('active');
}
// Haptic Feedback Functions
    function triggerHapticPulse(element) {
      if (!element) return;
      
      element.classList.remove('haptic-active');
      void element.offsetWidth; // Trigger reflow
      element.classList.add('haptic-active');
      
      setTimeout(() => {
        element.classList.remove('haptic-active');
      }, 400);
    }

    function triggerHapticRipple(element, event) {
      if (!element) return;
      
      // Create ripple container if it doesn't exist
      let rippleContainer = element.querySelector('.haptic-ripple-container');
      if (!rippleContainer) {
        rippleContainer = document.createElement('div');
        rippleContainer.className = 'haptic-ripple-container';
        element.style.position = 'relative';
        element.appendChild(rippleContainer);
      }
      
      // Create ripple element
      const ripple = document.createElement('div');
      ripple.className = 'haptic-ripple';
      
      // Get click position relative to element
      const rect = element.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      // Size and position ripple
      const size = Math.max(rect.width, rect.height) * 2;
      ripple.style.width = `${size}px`;
      ripple.style.height = `${size}px`;
      ripple.style.left = `${x - size / 2}px`;
      ripple.style.top = `${y - size / 2}px`;
      
      // Set color based on element's current color
      const computedStyle = window.getComputedStyle(element);
      ripple.style.color = computedStyle.color || '#FFFFFF';
      
      rippleContainer.appendChild(ripple);
      
      // Remove ripple after animation
      setTimeout(() => {
        ripple.remove();
      }, 600);
    }

    function triggerHapticGlow(element) {
      if (!element) return;
      
      element.classList.remove('haptic-glow');
      void element.offsetWidth; // Trigger reflow
      element.classList.add('haptic-glow');
      
      setTimeout(() => {
        element.classList.remove('haptic-glow');
      }, 500);
    }
// Navigation
    function navigateToPage(pageName) {
      // Only onboarding (features) page redirects to mlpage.html now
      document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
      document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
      
      const pageElement = document.getElementById(pageName);
      if (pageElement) pageElement.classList.add('active');
      
      const navLink = document.querySelector(`[data-page="${pageName}"]`);
      if (navLink) navLink.classList.add('active');
    }

    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        const pageName = link.getAttribute('data-page');
        // SPA navigation for all pages
        navigateToPage(pageName);
      });
    });


     
    // Data SDK Handler
    // Fetch athletes from backend
    async function fetchAthletes() {
      try {
        const response = await fetch('/api/athletes');
        if (!response.ok) throw new Error('Failed to fetch athletes');
        const data = await response.json();
        athletesData = data;
        renderAthleteList(athletesData);
        updateDashboardStats(athletesData);
      } catch (error) {
        console.error('Error fetching athletes:', error);
        athletesData = [];
        renderAthleteList(athletesData);
        updateDashboardStats(athletesData);
      }
    }

    // Initialize Data SDK
    async function initializeApp() {
      await fetchAthletes();
    }

    initializeApp();

// Export any other shared functions as needed
