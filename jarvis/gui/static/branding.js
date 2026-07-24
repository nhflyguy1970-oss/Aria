/** Assistant branding — extracted from app.js. */
(function () {
  let assistantDisplayName = "ARIA";

  function ariaName() {
    return assistantDisplayName || "ARIA";
  }

  function applyBranding(data = {}) {
    assistantDisplayName = data.assistant_name || "ARIA";
    const name = assistantDisplayName;
    const full = data.assistant_full_name || "Adaptive Reasoning Intelligence Assistant";
    document.title = name;
    const appTitle = document.getElementById("appTitle");
    const appTagline = document.getElementById("appTagline");
    const hudEnv = document.getElementById("hudEnv");
    if (appTitle) appTitle.textContent = name;
    if (appTagline) appTagline.textContent = full;
    if (hudEnv) hudEnv.textContent = name;
    const svcName = document.getElementById("serviceAssistantName");
    if (svcName) svcName.textContent = name;
    const welcomeName = document.getElementById("welcomeAssistantName");
    if (welcomeName) welcomeName.textContent = name;
    const startupTitle = document.getElementById("startupOverlayTitle");
    if (startupTitle) startupTitle.textContent = `Starting ${name}…`;
    const upgradeBtn = document.getElementById("upgradeWizardBtn");
    if (upgradeBtn) upgradeBtn.textContent = `Upgrade ${name}`;
    const upgradeTitle = document.getElementById("upgradeWizardTitle");
    if (upgradeTitle) upgradeTitle.textContent = `Upgrade ${name}`;
    const upgradeRestart = document.getElementById("upgradeRestartBtn");
    if (upgradeRestart) upgradeRestart.textContent = `Restart ${name}`;
    const apiKeyTitle = document.getElementById("apiKeyModalTitle");
    if (apiKeyTitle) apiKeyTitle.textContent = `${name} API key`;
    const profileTitle = document.getElementById("profileModalTitle");
    if (profileTitle) profileTitle.textContent = `Help ${name} learn about you`;
  }

  window.ariaName = ariaName;
  window.applyBranding = applyBranding;
})();
