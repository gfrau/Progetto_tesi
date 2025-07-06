
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
    .then(res => {
      if (!res.ok) throw new Error("Errore HTTP " + res.status);
      return res.json();
    })
    .then(data => {
      const count = Number(data.broken_count);
      if (!isNaN(count) && count === 0) {
        showToast("✓ Tutte le Observation sono collegate a pazienti.", "linear-gradient(to right, #00c851, #007e33)");
      } else if (!isNaN(count)) {
        showToast(`✖ ${count} Observation scollegate da pazienti.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Observation scollegate:", data.broken_links);
      } else {
        showToast("⚠ Dato 'broken_count' non valido o mancante.", "linear-gradient(to right, #ff9966, #ff5e62)");
      }
    })
    .catch(error => {
      showToast(`✖ Errore: ${error.message}`, "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error("Errore osservazioni:", error);
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

function checkObservationValues() {
  fetch('/api/test/observation-values')
    .then(res => res.json())
    .then(data => {
      if (data.invalid_count === 0) {
        showToast("✓ Tutte le Observation hanno valori validi.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ ${data.invalid_count} Observation con valori non validi.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Observation non valide:", data.invalid_entries);
      }
    })
    .catch(err => {
      showToast("Errore durante il test dei valori Observation", "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error(err);
    });
}

function checkObservationDuplicates() {
  fetch('/api/test/observation-duplicates')
    .then(res => res.json())
    .then(data => {
      if (data.count === 0) {
        showToast("✓ Nessuna Observation duplicata.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ Trovate ${data.count} Observation duplicate.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Observation duplicate:", data.duplicates);
      }
    })
    .catch(err => {
      showToast("Errore durante il test Observation duplicati", "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error(err);
    });
}