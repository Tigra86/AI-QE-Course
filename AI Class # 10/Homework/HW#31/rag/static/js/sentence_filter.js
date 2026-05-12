/* global Chart, OK_COUNT, WARN_COUNT, FAIL_COUNT, IDS_JSON, SIMS_JSON */

document.addEventListener("DOMContentLoaded", () => {

  const statusSel = document.getElementById("statusFilter");
  const reasonSel = document.getElementById("reasonFilter");
  const searchBox = document.getElementById("searchInput");
  const visibleEl = document.getElementById("visibleCount");
  const clearBtn  = document.getElementById("clearBtn");

  function applyFilters() {
    let visible = 0;
    const wantStatus = statusSel.value;
    const wantReason = reasonSel.value;
    const q = searchBox.value.trim().toLowerCase();

    document.querySelectorAll("details.result").forEach(el => {
      const status = el.dataset.status;
      const reasonsCsv = el.dataset.reasons || "";
      const reasons = reasonsCsv.split(",").map(s => s.trim()).filter(Boolean);
      const hay = `${el.dataset.id} ${el.dataset.question}`;

      let show = true;

      if (wantStatus !== "ALL" && status !== wantStatus) show = false;
      if (wantReason !== "ALL" && !reasons.includes(wantReason)) show = false;
      if (q && !hay.includes(q)) show = false;

      el.style.display = show ? "" : "none";
      if (show) visible++;
    });

    document.querySelectorAll(".file-section").forEach(section => {
      const anyVisible = [...section.querySelectorAll("details.result")]
        .some(el => el.style.display !== "none");
      section.style.display = anyVisible ? "" : "none";
    });

    visibleEl.textContent = visible;
  }

  const reasonsSet = new Set();
  document.querySelectorAll("details.result").forEach(el => {
    (el.dataset.reasons || "")
      .split(",")
      .map(s => s.trim())
      .filter(Boolean)
      .forEach(r => {
        if (r !== "OK") reasonsSet.add(r);
      });
  });

  [...reasonsSet].sort().forEach(r => {
    const opt = document.createElement("option");
    opt.value = r;
    opt.textContent = r;
    reasonSel.appendChild(opt);
  });

  statusSel.addEventListener("change", applyFilters);
  reasonSel.addEventListener("change", applyFilters);
  searchBox.addEventListener("input", applyFilters);

  clearBtn.addEventListener("click", () => {
    statusSel.value = "ALL";
    reasonSel.value = "ALL";
    searchBox.value = "";
    applyFilters();
  });

  applyFilters();

  const ok   = window.OK_COUNT || 0;
  const warn = window.WARN_COUNT || 0;
  const fail = window.FAIL_COUNT || 0;

  const ids  = Array.isArray(window.IDS_JSON) ? window.IDS_JSON : [];
  const sims = Array.isArray(window.SIMS_JSON) ? window.SIMS_JSON : [];

  new Chart(document.getElementById("pfChart"), {
    type: "doughnut",
    data: {
      labels: ["OK", "WARN", "FAIL"],
      datasets: [{
        data: [ok, warn, fail],
        backgroundColor: ["#198754", "#ffc107", "#dc3545"]
      }]
    }
  });

new Chart(document.getElementById("simChart"), {
  type: "bar",
  data: {
    labels: ids,
    datasets: [{
      data: sims,
      backgroundColor: "#0d6efd"
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: {
          autoSkip: true,
          maxTicksLimit: 20
        }
      },
      y: {
        min: 0,
        max: 100
      }
    },
    plugins: {
      legend: { display: false }
    }
  }
});

});
