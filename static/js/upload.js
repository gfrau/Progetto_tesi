document.addEventListener("DOMContentLoaded", function () {
  function handleCsvUpload(formId, endpoint) {
    const form = document.getElementById(formId);

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fileInput = form.querySelector("input[type='file']");
      const file = fileInput.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          body: formData,
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.detail || "Errore durante l'upload");
        }

        // Messaggio success
        if (result.inserted > 0 || result.skipped > 0) {
          Toastify({
            text: `Inseriti: ${result.inserted} | Scartati: ${result.skipped}`,
            duration: 3500,
            gravity: "top",
            position: "center",
          //  offset: { y: 100 },
            style: {
              background: "#1d4ed8",
              color: "white",
              fontWeight: "bold",
            },
            close: true
          }).showToast();
        }

        // Mostra eventuali errori dettagliati
        if (result.errors && result.errors.length > 0) {
          const errorText = result.errors.slice(0, 15).join('\n');
          Toastify({
            text: ` Errori:\n${errorText}`,
            duration: -1,
            gravity: "top",
            position: "center",
            offset: { y: 250 },
            style: {
              background: "#f97316",
              whiteSpace: "pre-line",
              fontSize: "0.85rem"
            },
            close: true
          }).showToast();
        }

      } catch (err) {
        Toastify({
          text: `Errore: ${err.message || "Errore durante l'upload"}`,
          duration: -1,
          gravity: "top",
          position: "center",
          offset: { y: 150 },
          style: {
            background: "#dc2626",
            fontWeight: "bold"
          },
          close: true
        }).showToast();
      }
    });
  }

    // --- JSON bulk upload
  function handleJsonUpload() {
    const form = document.getElementById("genericJsonForm");
    if (!form) {
      console.warn("Form genericJsonForm non trovato");
      return;
    }
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(form);

      try {
        const resp = await fetch("/api/upload/json/bulk", { method: "POST", body: fd });
        const res = await resp.json();
        if (!resp.ok) throw new Error(res.detail || "Errore JSON");

        Toastify({
          text: `JSON: Inseriti ${res.inserted}, Scartati ${res.skipped}`,
          duration: 5000,
          gravity: "top",
          position: "center",
          style: { background: "linear-gradient(to right, #00b09b, #96c93d)" },
          close: true
        }).showToast();

        if (res.errors?.length) {
          Toastify({
            text: `JSON Errori:\n${res.errors.slice(0,15).join("\\n")}`,
            duration: -1,
            gravity: "top",
            position: "center",
            style: { background: "#f97316", whiteSpace: "pre-line", fontSize: "0.85rem" },
            close: true
          }).showToast();
        }
      } catch (err) {
        Toastify({
          text: `JSON Errore: ${err.message}`,
          duration: -1,
          gravity: "top",
          position: "center",
          style: { background: "#dc2626", color: "white", fontWeight: "bold" },
          close: true
        }).showToast();
      }
    });
  }


  handleCsvUpload("patientCsvForm", "/api/upload/patient/csv");
  handleCsvUpload("encounterCsvForm", "/api/upload/encounter/csv");
  handleCsvUpload("observationCsvForm", "/api/upload/observation/csv");
  handleCsvUpload("conditionCsvForm", "/api/upload/condition/csv");

  handleJsonUpload();
});