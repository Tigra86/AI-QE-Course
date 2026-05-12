/* global Chart, OK_COUNT, WARN_COUNT, FAIL_COUNT, IDS, SIMS */

document.addEventListener("DOMContentLoaded", () => {
  const statusSel = document.getElementById("statusFilter");
  const reasonSel = document.getElementById("reasonFilter");
  const searchBox = document.getElementById("searchInput");
  const visibleEl = document.getElementById("visibleCount");
  const clearBtn  = document.getElementById("clearBtn");

  const results = Array.from(document.querySelectorAll("details.result"));

  // Build reason options from data-reason values in the report
  const reasons = new Set();
  results.forEach(el => {
    const r = (el.dataset.reason || "").trim();
    if (r && r !== "OK") reasons.add(r);
    const rs = (el.dataset.reasons || "").split(",").map(s => s.trim()).filter(Boolean);
    rs.forEach(x => { if (x && x !== "OK") reasons.add(x); });
  });

  const orderedReasons = Array.from(reasons).sort((a, b) => a.localeCompare(b));
  orderedReasons.forEach(r => {
    const opt = document.createElement("option");
    opt.value = r;
    opt.textContent = r;
    reasonSel.appendChild(opt);
  });

  function applyFilters() {
    const wantStatus = (statusSel.value || "ALL").toUpperCase();
    const wantReason = reasonSel.value || "ALL";
    const q = (searchBox.value || "").trim().toLowerCase();

    let visible = 0;

    results.forEach(el => {
      const status = (el.dataset.status || "").toUpperCase();
      const reasons = (el.dataset.reasons || "")
        .split(",")
        .map(r => r.trim())
        .filter(Boolean);

      const id = (el.dataset.id || "").toLowerCase();
      const question = (el.dataset.question || "").toLowerCase();

      let show = true;

      if (wantStatus !== "ALL" && status !== wantStatus) show = false;
      if (wantReason !== "ALL" && !reasons.includes(wantReason)) {
        show = false;
      }
      if (q) {
        const hay = `${id} ${question}`;
        if (!hay.includes(q)) show = false;
      }

      el.style.display = show ? "" : "none";
      if (show) visible++;
    });

    if (visibleEl) visibleEl.textContent = String(visible);
  }

  statusSel?.addEventListener("change", applyFilters);
  reasonSel?.addEventListener("change", applyFilters);
  searchBox?.addEventListener("input", applyFilters);
  clearBtn?.addEventListener("click", () => {
    statusSel.value = "ALL";
    reasonSel.value = "ALL";
    searchBox.value = "";
    applyFilters();
  });

  applyFilters();

  // Charts
  const pf = document.getElementById("pfChart");
  if (pf && typeof Chart !== "undefined") {
    new Chart(pf, {
      type: "doughnut",
      data: {
        labels: ["OK", "WARN", "FAIL"],
        datasets: [{
          data: [OK_COUNT, WARN_COUNT, FAIL_COUNT],
          // Keep default colors? If you prefer explicit, you can set them here.
        }]
      },
      options: {
        responsive: false,
        plugins: {
          legend: { position: "bottom" }
        },
        cutout: "65%"
      }
    });
  }

  const sim = document.getElementById("simChart");
  if (sim && typeof Chart !== "undefined") {
    new Chart(sim, {
      type: "bar",
      data: {
        labels: IDS,
        datasets: [{
          label: "Similarity %",
          data: SIMS,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100 }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
});
