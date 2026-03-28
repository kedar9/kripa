// This script is placed at the end of <body>, so all DOM elements already
// exist when it runs. No DOMContentLoaded/load wrappers are needed.
(function () {
  var SIZE_KEY = "kripa_test_font_size";
  var WEIGHT_KEY = "kripa_test_font_weight";
  var DEFAULT_SIZE = 30;
  var DEFAULT_WEIGHT = 400;

  var sizeSlider = document.getElementById("font-size-slider");
  var weightSlider = document.getElementById("font-weight-slider");
  var resetButton = document.getElementById("font-reset-button");
  var sizeLabel = document.getElementById("font-size-value");
  var weightLabel = document.getElementById("font-weight-value");

  if (!sizeSlider || !weightSlider) {
    return;
  }

  function safeGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }
  function safeSet(key, val) {
    try {
      window.localStorage.setItem(key, val);
    } catch (e) {}
  }
  function safeRemove(key) {
    try {
      window.localStorage.removeItem(key);
    } catch (e) {}
  }
  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  function apply() {
    var size = Number(sizeSlider.value);
    var weight = Number(weightSlider.value);
    document.body.style.setProperty("--sample-font-size", size + "px");
    document.body.style.setProperty("--sample-font-weight", String(weight));
    if (sizeLabel) {
      sizeLabel.textContent = size + "px";
    }
    if (weightLabel) {
      weightLabel.textContent = String(weight);
    }
    safeSet(SIZE_KEY, String(size));
    safeSet(WEIGHT_KEY, String(weight));
  }

  function reset() {
    sizeSlider.value = String(DEFAULT_SIZE);
    weightSlider.value = String(DEFAULT_WEIGHT);
    safeRemove(SIZE_KEY);
    safeRemove(WEIGHT_KEY);
    apply();
  }

  // Restore saved values only when there is an actual stored string (not null).
  // Note: Number(null) === 0 which is finite, so we must check for null first.
  var rawSize = safeGet(SIZE_KEY);
  if (rawSize !== null) {
    var n = Number(rawSize);
    if (isFinite(n) && n > 0) {
      sizeSlider.value = String(
        clamp(n, Number(sizeSlider.min), Number(sizeSlider.max)),
      );
    }
  }

  var rawWeight = safeGet(WEIGHT_KEY);
  if (rawWeight !== null) {
    var m = Number(rawWeight);
    if (isFinite(m) && m > 0) {
      weightSlider.value = String(
        clamp(m, Number(weightSlider.min), Number(weightSlider.max)),
      );
    }
  }

  sizeSlider.addEventListener("input", apply);
  sizeSlider.addEventListener("change", apply);
  weightSlider.addEventListener("input", apply);
  weightSlider.addEventListener("change", apply);
  if (resetButton) {
    resetButton.addEventListener("click", reset);
  }

  apply();
})();
