// Shared JS — globals and functions used across multiple pages

// Global state — assigned directly on window to avoid declaration conflicts
// with `let athletesData` in athletes.html's inline script (var/let can't coexist in the same scope).
// Any script can read/write these as plain identifiers; JS resolves them via window.
window.athletesData = window.athletesData || [];
window.currentAthlete = window.currentAthlete || null;
window.lastEnergyPercent = window.lastEnergyPercent || 0;

// Classification functions — needed by openAthleteProfile on the profile page.
// (Also defined in athletes.html for that page's own card rendering.)
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

    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
          const pageName = link.getAttribute('data-page');
          // SPA navigation for all pages
          navigateToPage(pageName);
        });
      });
    });

// Athlete card click handler - navigates to profile page (uses event delegation for dynamically rendered cards)
document.addEventListener('click', (event) => {
  const card = event.target.closest('.athlete-card');
  if (card) {
    const id = card.getAttribute('data-athlete-id');
    if (id) {
      sessionStorage.setItem('athleteListUrl', window.location.href);
      window.location.href = `/athleteprofile/${id}`;
    }
  }
});


    function openAthleteProfile(athleteId) {
      const athlete = window.athletesData.find(a => String(a.id) === String(athleteId));
      if (!athlete) return;

      window.currentAthlete = athlete;

      // Close all comparison panels and sparklines
      document.querySelectorAll('.comparison-panel').forEach(p => {
        p.classList.remove('active');
      });
      document.querySelectorAll('.sparkline-container').forEach(s => {
        s.classList.remove('active');
      });

      const fatiguePercent = calculateFatiguePercentage(athlete.heart_rate, athlete.body_temperature, athlete.blood_oxygen);
      const energyPercent = calculateEnergyPercentage(fatiguePercent);

      // Resolve fatigue colour once — used for reactor, energy label, and celebration
      const statusColor = athlete.fatigue_status === 'Not Fatigued' ? '#00FF88'
        : athlete.fatigue_status === 'Moderate' ? '#FFB800'
        : '#FF3366';

      // Fire celebration whenever athlete has full energy (fresh page load each time)
      if (energyPercent === 100) {
        celebrateFullEnergy();
      }
      window.lastEnergyPercent = energyPercent;

      document.getElementById('profile-athlete-name').textContent = athlete.name;
      document.getElementById('profile-athlete-status').textContent = `Status: ${athlete.fatigue_status}`;

      // Energy label — colour matches fatigue level
      const energyLabel = document.getElementById('energy-label');
      if (energyLabel) {
        energyLabel.textContent = `${energyPercent}%`;
        energyLabel.style.color = statusColor;
      }

      // Sphere centre text
      const spherePct = document.getElementById('sphere-pct');
      const sphereStatus = document.getElementById('sphere-status');
      if (spherePct) spherePct.textContent = `${energyPercent}%`;
      if (sphereStatus) sphereStatus.textContent = athlete.fatigue_status || '—';

      const hrElement = document.getElementById('profile-heart-rate');
      const tempElement = document.getElementById('profile-temperature');
      const bloodOxygenElement = document.getElementById('profile-blood-oxygen');

      if (hrElement) hrElement.textContent = athlete.heart_rate;
      if (tempElement) tempElement.textContent = athlete.body_temperature.toFixed(1);
      if (bloodOxygenElement) bloodOxygenElement.textContent = athlete.blood_oxygen;

      // Update reactor color — set on the container so SVG currentColor inherits correctly
      const reactor = document.getElementById('central-reactor');
      if (reactor) reactor.style.color = statusColor;

      // Start particle flow
      startParticleFlow(athlete.fatigue_status);

      // Update reactor aura intensity
      updateReactorAura(athlete.fatigue_status);

      // Update energy ring (outer ring of reactor) — fill + rotation speed
      const energyRing = document.getElementById('energy-ring');
      if (energyRing) {
        const circumference = 691;
        const fillAmount = (energyPercent / 100) * circumference;
        energyRing.setAttribute('stroke-dasharray', `${fillAmount} ${circumference}`);

        // Faster spin when energy is high, slower when tired (4s – 20s range)
        const speed = (4 + (1 - energyPercent / 100) * 16).toFixed(1);
        energyRing.style.setProperty('--ring-speed', speed + 's');
      }

      // Update orbital rings - fill based on value within range WITH ANIMATION
      const hrRing = document.getElementById('hr-ring');
      if (hrRing) {
        // Heart rate: range 60-180 bpm
        const minHR = 60;
        const maxHR = 180;
        const range = maxHR - minHR;
        
        // Calculate how much of the ring to fill based on current value
        const fillPercent = Math.min(100, Math.max(0, ((athlete.heart_rate - minHR) / range) * 100));
        
        const circumference = 440;
        const targetFillLength = (fillPercent / 100) * circumference;
        
        // Start from 0 and animate to target
        hrRing.setAttribute('stroke-dasharray', `0 ${circumference}`);
        hrRing.setAttribute('stroke-dashoffset', '0');
        
        // Animate after a brief delay
        setTimeout(() => {
          hrRing.style.transition = 'stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
          hrRing.setAttribute('stroke-dasharray', `${targetFillLength} ${circumference - targetFillLength}`);
        }, 100);
      }

      const tempRing = document.getElementById('temp-ring');
      if (tempRing) {
        // Temperature: range 35-39°C
        const minTemp = 35;
        const maxTemp = 39;
        const range = maxTemp - minTemp;
        
        const fillPercent = Math.min(100, Math.max(0, ((athlete.body_temperature - minTemp) / range) * 100));
        
        const circumference = 440;
        const targetFillLength = (fillPercent / 100) * circumference;
        
        // Start from 0 and animate to target
        tempRing.setAttribute('stroke-dasharray', `0 ${circumference}`);
        tempRing.setAttribute('stroke-dashoffset', '0');
        
        // Animate after a brief delay
        setTimeout(() => {
          tempRing.style.transition = 'stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
          tempRing.setAttribute('stroke-dasharray', `${targetFillLength} ${circumference - targetFillLength}`);
        }, 300);
      }

      const o2Ring = document.getElementById('o2-ring');
      if (o2Ring) {
        // blood_oxygen: range 90-100%
        const minO2 = 90;
        const maxO2 = 100;
        const range = maxO2 - minO2;
        
        const fillPercent = Math.min(100, Math.max(0, ((athlete.blood_oxygen - minO2) / range) * 100));
        
        const circumference = 440;
        const targetFillLength = (fillPercent / 100) * circumference;
        
        // Start from 0 and animate to target
        o2Ring.setAttribute('stroke-dasharray', `0 ${circumference}`);
        o2Ring.setAttribute('stroke-dashoffset', '0');

        setTimeout(() => {
          o2Ring.style.transition = 'stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
          o2Ring.setAttribute('stroke-dasharray', `${targetFillLength} ${circumference - targetFillLength}`);
        }, 500);
      }

   

    }



// Export any other shared functions as needed
