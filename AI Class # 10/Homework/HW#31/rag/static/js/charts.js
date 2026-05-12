document.addEventListener("DOMContentLoaded", () => {

  if (typeof Chart === "undefined") return;

  const pf = document.getElementById("pfChart");
  if (pf) {
    new Chart(pf, {
      type: "doughnut",
      data: {
        labels: ["PASS", "FAIL"],
        datasets: [{
          data: [PASS_COUNT, FAIL_COUNT],
          backgroundColor: ["#198754", "#dc3545"]
        }]
      },
      options: {
        responsive: false,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  }

  const sim = document.getElementById("simChart");
  if (sim) {
    new Chart(sim, {
      type: "bar",
      data: {
        labels: IDS,
        datasets: [{
          label: "Similarity %",
          data: SIMS,
          backgroundColor: "#0d6efd"
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
