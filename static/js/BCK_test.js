function showToast(message, color = "linear-gradient(to right, #00b09b, #96c93d)") {
  Toastify({
    text: message,
    duration: 5000,
    gravity: "top",
    position: "center",
    backgroundColor: color,
    close: true
  }).showToast();
}

function checkEncounters() {
  fetch('/api/test/encounter-links')
    .then(res => res.json())
    .then(data => {
      if (data.broken_count === 0) {
        showToast("✓ Tutti gli Encounter sono collegati a pazienti.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ ${data.broken_count} Encounter scollegati da pazienti.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Encounter scollegati:", data.broken_links);
      }
    })
    .catch(err => {
      showToast("Errore durante il test Encounter", "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error(err);
    });
}

function checkObservations() {
  fetch('/api/test/observation-links')
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        showToast(data.message, "linear-gradient(to right, #ffcc00, #ff9900)");
        return;
      }

      if (data.broken_count === 0) {
        showToast("✓ Tutte le Observation sono collegate a pazienti.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ ${data.broken_count} Observation scollegate da pazienti.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Observation scollegate:", data.broken_links);
      }
    });
}

function checkDuplicates() {
  fetch('/api/test/duplicates')
    .then(res => res.json())
    .then(data => {
      if (data.count === 0) {
        showToast("✓ Nessun paziente duplicato.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ Trovati ${data.count} pazienti duplicati.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Duplicati:", data.duplicates);
      }
    })
    .catch(err => {
      showToast("Errore durante il test Duplicati", "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error(err);
    });
}