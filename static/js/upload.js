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
            text: `✅ Inseriti: ${result.inserted} | ⛔ Scartati: ${result.skipped}`,
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
          const errorText = result.errors.slice(0, 5).join('\n');
          Toastify({
            text: `⚠️ Errori:\n${errorText}`,
            duration: 7000,
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
          duration: 8000,
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

  handleCsvUpload("patientCsvForm", "/api/upload/patient/csv");
  handleCsvUpload("encounterCsvForm", "/api/upload/encounter/csv");
  handleCsvUpload("observationCsvForm", "/api/upload/observation/csv");
});