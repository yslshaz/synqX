// Welcome page JS

document.addEventListener('DOMContentLoaded', function() {
  // Haptic feedback on vital cards
  document.querySelectorAll('.vital-card').forEach(card => {
    card.addEventListener('click', function(event) {
      triggerHapticRipple(this, event);
      const icon = this.querySelector('.vital-icon');
      if (icon) {
        triggerHapticGlow(icon);
      }
    });
  });

  if (typeof initializeApp === 'function') {
    initializeApp();
  }
});
