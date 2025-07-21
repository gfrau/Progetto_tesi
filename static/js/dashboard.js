// dashboard.js – versione completa
// -----------------------------------------------------------------------------
//  KPI, grafici dinamici (Demografia + Clinica), Incidenza giornaliera Covid-19
//  e Confronto incidenza Covid-19 tra due periodi. Card alte fisse e canvas
//  che non crescono. Ultimo update: Lug 2025
// -----------------------------------------------------------------------------

/***************** Registrazione plugin DataLabels *****************************/
if (window.ChartDataLabels && typeof Chart !== "undefined") {
  Chart.register(window.ChartDataLabels);
}
Chart.defaults.set("plugins.datalabels", { display: false });
/***************** Helper AJAX *************************************************/
async function fetchJSON(url) {
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return r.json();
}

/***************** Helper date (ISO) *******************************************/
function todayISO() { return new Date().toISOString().split("T")[0]; }
function daysAgoISO(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

/***************** KPI *********************************************************/
async function updateKPIs() {
  try {
    const s = await fetchJSON("/api/dashboard/stats");
    kpiPatients .textContent = s.patients   .toLocaleString("it-IT");
    kpiIncontri .textContent = s.encounters .toLocaleString("it-IT");
    kpiParametri.textContent = s.observations.toLocaleString("it-IT");
    kpiCondizioni.textContent= s.conditions .toLocaleString("it-IT");
  } catch (e) { console.error("KPI", e); }
}

/***************** Palette + tipo grafico **************************************/
const okabeIto = ["#E69F00","#56B4E9","#009E73","#F0E442","#0072B2","#D55E00","#CC79A7","#999999"];
const palette  = n => Array.from({ length: n }, (_, i) => okabeIto[i % okabeIto.length]);
function chartType({ field, nLabels, forceDoughnut }) {
  if (forceDoughnut) return "doughnut";           // grafico 2 fisso
  if (field === "gender")    return "polarArea"; // genere polar area
  if (field === "age_group") return "bar";       // fasce età bar
  return nLabels > 12 ? "bar" : "doughnut";      // fallback
}

/***************** Mapping LOINC **********************************************/
async function fetchLoincNames(codes) {
  if (!codes.length) return {};
  try { return await fetchJSON(`/api/loinc/names?codes=${codes.join(",")}`); }
  catch { return {}; }
}

/***************** Grafici dinamici (card 1 e 2) ******************************/
async function fetchAndRenderChart(canvasId, field) {
  try {
    const raw = await fetchJSON(`/api/dashboard/stats/aggregate/${field}`);
    if (!raw || !Object.keys(raw).length) return console.warn("Nessun dato", field);

    const codes  = Object.keys(raw);
    const values = codes.map(c => raw[c]);
    const total  = values.reduce((a,b)=>a+b,0);

    let labels   = [...codes];
    if (field === "code") {
      const map = await fetchLoincNames(codes);
      labels = codes.map(c => map[c] || c);
    }

    const dataPairs = labels.map((l,i)=>[l,values[i]]).sort((a,b)=>b[1]-a[1]);
    labels        = dataPairs.map(p=>p[0]);
    const series  = dataPairs.map(p=>p[1]);

    const type = chartType({ field, nLabels: labels.length, forceDoughnut: canvasId==="chart2" });
    const colors = palette(labels.length);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    canvas.chartInstance?.destroy();
    canvas.parentElement.style.minHeight = "300px";

    canvas.chartInstance = new Chart(canvas, {
      type,
      data:{ labels, datasets:[{ data: series, backgroundColor: colors, borderWidth:1, borderRadius:type==="bar"?4:0, hoverOffset:4 }] },
      options:{
        maintainAspectRatio:false,
        indexAxis:type==="bar"?"y":"x",
        scales:type==="bar"?{ x:{ beginAtZero:true } }:{},
        plugins:{
          legend:{ display:type==="doughnut"||type==="polarArea", position:"bottom" },
          datalabels:type==="polarArea"?{ color:"#222", font:{weight:"600",size:10}, anchor:"end", align:"end", offset:8, formatter:v=>`${(v/total*100).toFixed(1)} %` }:{ display:false },
          tooltip:{ callbacks:{ label: ctx=>`${ctx.label}: ${ctx.parsed.toLocaleString("it-IT")}` } }
        }
      }
    });
  } catch(e){ console.error("Grafici dinamici", e); }
}

/***************** Incidenza giornaliera Covid-19 *****************************/
const COVID_CODE   = "U07.1";
let   incidenceChart;

async function renderIncidenceChart(days = 30) {
  try {
    const qs = new URLSearchParams({
      start     : daysAgoISO(days - 1),
      end       : todayISO(),
      condition : COVID_CODE
    });

    const data = await fetchJSON(`/api/dashboard/conditions/daily-incidence?${qs}`);
    if (!Array.isArray(data) || !data.length) { incidenceChart?.destroy(); return; }

    incidenceChart?.destroy();
    incidenceChart = new Chart(chartIncidence, {
      type   : "line",
      data   : {
        datasets: [{
          label          : `Covid-19 • ultimi ${days} gg`,
          data           : data.map(d => ({ x: d.date, y: d.value })),
          borderColor    : "#0072B2",
          backgroundColor: "rgba(0,114,178,.15)",
          borderWidth    : 2,
          tension        : .3,
          pointRadius    : 2,
          fill           : true
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            type: "time",
            time: { unit: "day", displayFormats: { day: "dd/MM" } },
            title: { display: true, text: "Data" },
            ticks: { maxRotation: 0, maxTicksLimit: 7 }
          },
          y: { beginAtZero: true }
        }
      }
    });
  } catch (e) { console.error("Incidenza", e); }
}



/***************** Pazienti per provincia ************************************/
let provinceChart;
async function renderProvinceChart () {
  try {
    const data = await fetchJSON("/api/dashboard/patients/by-province");
    if (!Array.isArray(data) || !data.length) return;

    const canvas = chartProvince;
    canvas.chartInstance?.destroy();
    canvas.style.width = canvas.style.height = "";
    const card = canvas.parentElement;
    card.style.height   = "300px";
    card.style.overflow = "hidden";

    canvas.chartInstance = new Chart(canvas, {
      type  : "bar",
      data  : {
        labels   : data.map(d => d.province || "–"),
        datasets : [{
          data           : data.map(d => d.value),
          backgroundColor: "#56B4E9",
          borderRadius   : 4
        }]
      },
      options: {
        responsive         : true,
        maintainAspectRatio: false,                     // riempie la card fissa
        plugins            : { legend: { display: false } },
        scales             : { y: { beginAtZero: true } }
      }
    });
  } catch (e) {
    console.error("Provincia", e);
  }
}

/***************** Confronto incidenza Covid-19 (due periodi) *************/
let periodChart;
async function renderPeriodComparison() {
  try {
    if (
      !period1Start.value && !period1End.value &&
      !period2Start.value && !period2End.value
    ) {
      period1Start.value = daysAgoISO(14);  // 14 gg fa
      period1End.value   = daysAgoISO(7);   // 7  gg fa
      period2Start.value = daysAgoISO(7);   // 7  gg fa
      period2End.value   = todayISO();      // oggi
    }

    const [s1, e1, s2, e2] = [
      period1Start.value,
      period1End.value,
      period2Start.value,
      period2End.value
    ];
    if (!s1 || !e1 || !s2 || !e2) return;   // campi incompleti? esci.

    const qs = new URLSearchParams({
      start1: s1, end1: e1,
      start2: s2, end2: e2,
      condition: COVID_CODE
    });
    const data = await fetchJSON(`/api/dashboard/conditions/incidence-period?${qs}`);
    if (!Array.isArray(data) || data.length < 2) return;

    periodChart?.destroy();
    const canvas   = chartPeriodCompare;
    const cardBody = canvas.parentElement;
    canvas.style.width = canvas.style.height = "";
    cardBody.style.overflow = "hidden";


    periodChart = new Chart(chartPeriodCompare, {
  type: "bar",
  data: {
    labels: [`${s1} → ${e1}`, `${s2} → ${e2}`],
    datasets: [{
      data           : data.map(d => d.value),
      backgroundColor: ["#36A2EB", "#FF6384"],
      borderRadius   : 5,
      /* 👉 barre più sottili */
      categoryPercentage: 0.5,   // spazio occupato dalla categoria (default 0.8)
      barPercentage     : 0.7,   // larghezza della barra dentro la categoria
      datalabels        : {
        color : "#fff",
        anchor: "center",
        align : "center",
        font  : { weight: "600", size: 12 }
      }
    }]
  },
  options: {
    indexAxis: "y",                   // orizzontale
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales : {
      x: { beginAtZero: true, min: 0 },
      y: { ticks: { padding: 4 } }    // meno spazio attorno all’etichetta
    },
    layout: { padding: { right: 8 } } // riduce “cuscino” a destra
  }
});

/* Altezza card-body leggermente inferiore (facoltativo) */
chartPeriodCompare.parentElement.style.height = "320px";

  } catch (e) {
    console.error("Period", e);
  }
}




/***************** Bootstrapping *********************************************/
document.addEventListener("DOMContentLoaded", async () => {
  /* 1. KPI */
  await updateKPIs();

  /* 2. Grafici dinamici (Demografia & Clinica) */
  fetchAndRenderChart("chart1", aggregationField1.value);
  fetchAndRenderChart("chart2", aggregationField2.value);

  aggregationField1.addEventListener("change", e => {
    fetchAndRenderChart("chart1", e.target.value);
  });
  aggregationField2.addEventListener("change", e => {
    fetchAndRenderChart("chart2", e.target.value);
  });

  /* 3. Incidenza giornaliera Covid-19 */
  const selInc = document.getElementById("incidencePeriod");
  const defaultDays = parseInt(selInc.value, 10) || 30;
  renderIncidenceChart(defaultDays);

  selInc.addEventListener("change", e => {
    const days = parseInt(e.target.value, 10);
    if (!isNaN(days)) renderIncidenceChart(days);
  });


  /* 4. Pazienti per provincia */
  renderProvinceChart();

  /* 5. Confronto incidenza Covid-19: due periodi */
  renderPeriodComparison();                       // primo draw con default
  btnPeriodCompare.addEventListener("click", renderPeriodComparison);
});