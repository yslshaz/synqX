// Onboarding page JS

document.addEventListener('DOMContentLoaded', function() {
  // Haptic feedback on feature cards
  document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('click', function(event) {
      triggerHapticRipple(this, event);
      const icon = this.querySelector('.feature-icon');
      if (icon) {
        triggerHapticGlow(icon);
      }
    });
  });

  if (typeof initializeApp === 'function') {
    initializeApp();
  }
});
