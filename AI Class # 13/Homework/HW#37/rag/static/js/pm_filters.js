document.addEventListener("DOMContentLoaded", () => {

  const statusSel  = document.getElementById("statusFilter");
  const reasonSel  = document.getElementById("reasonFilter");
  const searchBox  = document.getElementById("searchInput");
  const visibleEl  = document.getElementById("visibleCount");
  const clearBtn   = document.getElementById("clearBtn");

  function applyFilters() {
    const wantStatus = statusSel ? statusSel.value : "ALL";
    const wantReason = reasonSel ? reasonSel.value : "ALL";
    const q = searchBox ? searchBox.value.trim().toLowerCase() : "";

    let visible = 0;

    document.querySelectorAll("details.result").forEach(el => {
      const status   = el.dataset.status;
      const reason   = el.dataset.reason || "";
      const id       = (el.dataset.id || "").toLowerCase();
      const question = (el.dataset.question || "").toLowerCase();

      let show = true;

      if (wantStatus !== "ALL" && status !== wantStatus) {
        show = false;
      }

      if (reasonSel && wantReason !== "ALL") {
        if (status !== "FAIL" || reason !== wantReason) {
          show = false;
        }
      }

      if (q && !(`${id} ${question}`.includes(q))) {
        show = false;
      }

      el.classList.toggle("hidden", !show);
      if (show) visible++;
    });

    document.querySelectorAll(".file-section").forEach(section => {
      const anyVisible = [...section.querySelectorAll("details.result")]
        .some(el => !el.classList.contains("hidden"));
      section.classList.toggle("hidden", !anyVisible);
    });

    if (visibleEl) visibleEl.textContent = visible;
  }

  if (statusSel) {
    statusSel.addEventListener("change", () => {
      if (reasonSel) {
        reasonSel.disabled = (statusSel.value === "PASS");
      }
      applyFilters();
    });
  }

  if (reasonSel) {
    reasonSel.addEventListener("change", applyFilters);
  }

  if (searchBox) {
    searchBox.addEventListener("input", applyFilters);
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (statusSel) statusSel.value = "ALL";
      if (reasonSel) {
        reasonSel.value = "ALL";
        reasonSel.disabled = false;
      }
      if (searchBox) searchBox.value = "";
      applyFilters();
    });
  }

  applyFilters();
});