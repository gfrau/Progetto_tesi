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

   function handleJsonUpload() {
    const form = document.getElementById("genericJsonForm");
    const loader = document.getElementById("csvLoader");

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(form);
      loader.style.display = "inline";

      fetch("/api/upload/fhir/json", {
        method: "POST",
        body: formData,
      })
        .then(response => response.json())
        .then(data => {
          loader.style.display = "none";
          showToast(`✔️ Upload completato. Inseriti: ${data.inserted}, Scartati: ${data.skipped}`, "linear-gradient(to right, #00b09b, #96c93d)");
        })
        .catch(error => {
          loader.style.display = "none";
          showToast("Errore durante l'upload JSON", "#dc2626", 6000);
        });
    });
  }

  handleCsvUpload("patientCsvForm", "/api/upload/patient/csv");
  handleCsvUpload("encounterCsvForm", "/api/upload/encounter/csv");
  handleCsvUpload("observationCsvForm", "/api/upload/observation/csv");
  handleJsonUpload();
});