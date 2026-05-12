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
      const reason = el.dataset.reason;
      const hay = `${el.dataset.id} ${el.dataset.question}`;

      let show = true;

      if (wantStatus !== "ALL" && status !== wantStatus) show = false;
      if (wantReason !== "ALL" && reason !== wantReason) show = false;
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

  new Chart(document.getElementById("pfChart"), {
    type: "doughnut",
    data: {
      labels: ["PASS", "FAIL"],
      datasets: [{
        data: [PASS_COUNT, FAIL_COUNT],
        backgroundColor: ["#198754", "#dc3545"]
      }]
    }
  });

  new Chart(document.getElementById("simChart"), {
    type: "bar",
    data: {
      labels: IDS,
      datasets: [{
        data: SIMS,
        backgroundColor: "#0d6efd"
      }]
    },
    options: {
      scales: { y: { min: 0, max: 100 } },
      plugins: { legend: { display: false } }
    }
  });
});
