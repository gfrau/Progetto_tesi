function showToast(message, type = "primary") {
  const bootstrapColors = {
    primary: "#0d6efd",   // blu
    success: "#198754",   // verde
    danger: "#dc3545",    // rosso
    warning: "#ffc107",   // arancione
    info: "#0dcaf0",      // azzurro
    dark: "#212529",      // grigio scuro
    light: "#f8f9fa"      // bianco
  };

  const textColors = {
    light: "#000",  // testo scuro su sfondo chiaro
    warning: "#000",
    default: "#fff" // testo bianco su sfondo scuro
  };

  const textColor = textColors[type] || textColors.default;

  Toastify({
    text: message,
    duration: 5000,
    gravity: "top",
    position: "center",
    close: true,
    style: {
      background: bootstrapColors[type] || bootstrapColors.primary,
      color: textColor,
      fontFamily: "'Segoe UI', Roboto, sans-serif",
      fontSize: "0.95rem",
      borderRadius: "0.375rem",
      boxShadow: "0 0.5rem 1rem rgba(0,0,0,0.1)",
      padding: "10px 16px"
    }
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
  console.log("➡️ Chiamata a /api/test/observation-links");

  fetch('/api/test/observation-links')
    .then(res => {
      if (!res.ok) throw new Error("Errore HTTP " + res.status);
      return res.json();
    })
    .then(data => {
      console.log("📦 Risposta ricevuta:", data);

      if (data.status === "empty") {
        showToast("Nessuna risorsa Observation presente nel sistema.", "warning");
      return;
      }

      const count = Number(data.broken_count);

      if (count === 0) {
        showToast("Tutte le Observation sono collegate a pazienti.", "success");
      } else {
        showToast(`${count} Observation scollegate da pazienti.`, "danger");
        console.warn("Observation scollegate:", data.broken_links);
      }
    })
    .catch(error => {
      showBootstrapToast(`Errore: ${error.message}`, "Errore", "danger");
      console.error("Errore durante il controllo delle observation:", error);
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



function checkObservationLoinc() {
  fetch('/api/test/observation-loinc')
    .then(res => res.json())
    .then(data => {
      if (data.invalid_count === 0) {
        showToast("✓ Tutti i codici LOINC delle Observation sono validi.", "linear-gradient(to right, #00c851, #007e33)");
      } else {
        showToast(`✖ ${data.invalid_count} codici LOINC non validi trovati.`, "linear-gradient(to right, #ff5f6d, #ffc371)");
        console.warn("Codici LOINC invalidi:", data.invalid_codes);
      }
    })
    .catch(err => {
      showToast("Errore durante il test dei codici LOINC", "linear-gradient(to right, #ff416c, #ff4b2b)");
      console.error(err);
    });
}



function checkObservationValues() {
  fetch('/api/test/observation-values')
    .then(res => res.json())
    .then(data => {
      if (data.sinvalid_count === 0) {
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

function renderTable(data) {
  const tableHead = document.getElementById("data-table-head");
  const tableBody = document.getElementById("data-table-body");

  tableHead.innerHTML = "";
  tableBody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tableBody.innerHTML = "<tr><td colspan='6' class='text-center text-muted'>Nessun dato disponibile.</td></tr>";
    return;
  }

  const headerLabels = {
    "resourceType": "Tipo Risorsa",
    "identifier.0.value": "ID Risorsa",
    "subject.identifier.value": "ID Paziente",
    "name.0.family": "Cognome",
    "name.0.given.0": "Nome",
    "birthDate": "Data di Nascita",
    "gender": "Sesso",
    "address.0.city": "Città",
    "address.0.state": "Provincia",
    "address.0.postalCode": "CAP",
    "address.0.line.0": "Indirizzo",
    "period.start": "Data Inizio",
    "period.end": "Data Fine",
    "status": "Stato",
    "class_fhir.coding.0.code": "Classe",
    "code.coding.0.display": "Test",
    "code.coding.0.code": "Codice LOINC",
    "effectiveDateTime": "Data Osservazione",
    "valueQuantity.value": "Valore",
    "valueQuantity.unit": "Unità"
  };

  const getLabel = key => headerLabels[key] || key;

  const resourceType = data[0].resourceType;
  const headersByType = {
    "Patient": [
      "resourceType", "id", "identifier.0.value", "name.0.family", "name.0.given.0",
      "birthDate", "gender", "address.0.city", "address.0.district", "address.0.postalCode"
    ],
    "Encounter": [
      "resourceType", "id", "status", "class_fhir.coding.0.code",
      "period.start", "peraiiod.end", "subject.identifier.value"
    ],
    "Observation": [
      "resourceType", "id", "code.coding.0.display", "code.coding.0.code",
      "valueQuantity.value", "valueQuantity.unit", "effectiveDateTime", "subject.identifier.value"
    ],
    "Condition": [
      "resourceType", "id", "code.coding.0.display", "code.coding.0.code",
      "subject.identifier.value", "recordedDate", "clinicalStatus", "verificationStatus.coding.0.code"
    ]
};



  const headers = headersByType[resourceType] || Object.keys(flattenObject(data[0]));

  // Intestazioni
  tableHead.innerHTML = `<tr>${headers.map(h => `<th>${getLabel(h)}</th>`).join("")}</tr>`;

  // Corpo
  data.forEach(item => {
    const flat = flattenObject(item);
    const row = document.createElement("tr");
    headers.forEach(h => {
      let val = flat[h] ?? "—";

      // Format date
      if (h.toLowerCase().includes("date") && val !== "—") {
        try {
          val = new Date(val).toLocaleDateString("it-IT", {
            day: "2-digit", month: "long", year: "numeric"
          });
        } catch (_) {}
      }

      row.innerHTML += `<td>${val}</td>`;
    });
    tableBody.appendChild(row);
  });
}

function flattenObject(obj, prefix = "", res = {}) {
  for (const key in obj) {
    const val = obj[key];
    const newKey = prefix ? `${prefix}.${key}` : key;
    if (Array.isArray(val)) {
      if (val.length > 0 && typeof val[0] === "object") {
        flattenObject(val[0], `${newKey}.0`, res);
      } else {
        res[newKey] = val.join(", ");
      }
    } else if (typeof val === "object" && val !== null) {
      flattenObject(val, newKey, res);
    } else {
      res[newKey] = val;
    }
  }
  return res;
}

function loadTestData(resourceType) {
  fetch(`/api/${resourceType}`)
    .then(res => res.json())
    .then(data => renderTable(data))
    .catch(err => {
      console.error("Errore caricamento dati:", err);
      document.getElementById("data-table-body").innerHTML =
        `<tr><td colspan="6" class="text-danger">Errore durante il caricamento dei dati</td></tr>`;
    });
}