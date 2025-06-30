document.addEventListener("DOMContentLoaded", function () {
  fetch("/observations/chart-data")
    .then(response => response.json())
    .then(data => {
      if (!Array.isArray(data.labels) || !Array.isArray(data.values)) {
        throw new Error("Formato dati non valido.");
      }

      const ctx = document.getElementById("observationChart").getContext("2d");

      new Chart(ctx, {
        type: "line",
        data: {
          labels: data.labels,
          datasets: [{
            label: "Numero di osservazioni",
            data: data.values,
            borderWidth: 2,
            fill: false,
            tension: 0.1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top'
            },
            title: {
              display: true,
              text: 'Andamento delle Osservazioni Cliniche'
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Data'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Valore'
              },
              beginAtZero: true
            }
          }
        }
      });
    })
    .catch(error => {
      console.error("Errore durante il caricamento dei dati:", error);
      alert("Errore durante il caricamento dei dati: " + error.message);
    });
});