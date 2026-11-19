(() => {
  const buttons = 'button, input:is([type="button"], [type="submit"], [type="reset"])';
  const feedbackTime = 155;
  let currentPress;

  function clearPress() {
    if (!currentPress) return;
    window.clearTimeout(currentPress.timer);
    currentPress.control.removeAttribute('data-fyf-pressed');
    currentPress = null;
  }

  function showPress(event, pointerId) {
    const control = event.target.closest?.(buttons);
    if (!control || control.matches(':disabled, .option-card') || control.closest('[aria-disabled="true"]')) return;

    clearPress();
    control.setAttribute('data-fyf-pressed', '');
    currentPress = {control, pointerId, timer:window.setTimeout(clearPress, feedbackTime)};
  }

  document.addEventListener('pointerdown', event => {
    if (event.isPrimary && event.button === 0) showPress(event, event.pointerId);
  }, {capture:true, passive:true});

  document.addEventListener('pointercancel', event => {
    if (event.pointerId === currentPress?.pointerId) clearPress();
  }, {capture:true, passive:true});

  document.addEventListener('click', event => {
    if (event.isTrusted && event.detail === 0) showPress(event, null);
  }, {capture:true, passive:true});
  window.addEventListener('blur', clearPress);
})();
