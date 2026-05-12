const chatWindow = document.getElementById("chat-window");
const userInput  = document.getElementById("user-input");
const drawer     = document.getElementById("debug-drawer");

let probChartInstance = null;
let lastProbabilitiesCache = null;

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  userInput.value = "";
  userInput.focus();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();

    if (data.error) {
      appendMessage("Error: " + data.error, "bot");
      return;
    }

    appendMessage(
      data.answer,
      "bot"
    );

    if (data.probabilities) {
      renderProbChart(data.probabilities);
    }
    updateExplanation(data);

  } catch (err) {
    appendMessage("Error: " + err.message, "bot");
  }
}

function appendMessage(text, who="bot") {
  const div = document.createElement("div");
  div.className = "message " + who;
  div.textContent = (who === "user" ? "You: " : "Bot: ") + text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function clearChat() {
  chatWindow.innerHTML = "";
}

function toggleDebugDrawer() {
  drawer.classList.toggle("open");
  localStorage.setItem("debugOpen", drawer.classList.contains("open") ? "1" : "0");
}

// F12 toggles drawer
document.addEventListener("keydown", (e) => {
  if (e.key === "F12") {
    e.preventDefault();
    toggleDebugDrawer();
  }
});

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);

  if (lastProbabilitiesCache && Object.keys(lastProbabilitiesCache).length) {
    renderProbChart(lastProbabilitiesCache);
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
}

window.addEventListener("load", () => {
  userInput.focus();

  // Register Chart plugins
  if (window.Chart && window["chartjs-plugin-annotation"]) {
    Chart.register(window["chartjs-plugin-annotation"]);
  }
  if (window.ChartDataLabels) {
    Chart.register(ChartDataLabels);
  }

  // debug open state
  if (localStorage.getItem("debugOpen") === "1") {
    drawer.classList.add("open");
  }

  // theme state
  const storedTheme = localStorage.getItem("theme") || "light";
  applyTheme(storedTheme);
});

function renderProbChart(probabilities) {
    const ctx = document.getElementById("probChart").getContext("2d");
    lastProbabilitiesCache = probabilities;

    if (probChartInstance) {
        probChartInstance.destroy();
    }

    const labels = Object.keys(probabilities);
    const values = Object.values(probabilities);

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";

    let gradient = ctx.createLinearGradient(0, 0, 0, 220);
    if (isDark) {
        gradient.addColorStop(0, "#ffdd66");
        gradient.addColorStop(1, "#d4a017");
    } else {
        gradient.addColorStop(0, "#4A90E2");
        gradient.addColorStop(1, "#357ABD");
    }

    probChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Probability",
                data: values,
                backgroundColor: gradient,
                borderColor: isDark ? "#ffaa00" : "#1E5BBE",
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            animation: {
                duration: 700,
                easing: "easeOutQuart",
            },

            plugins: {
                legend: { display: false },

                tooltip: {
                    callbacks: {
                        label: (ctx) => (ctx.raw * 100).toFixed(2) + "%"
                    }
                },

                annotation: {
                    annotations: {
                        threshold: {
                            type: "line",
                            yMin: 0.45,
                            yMax: 0.45,
                            borderColor: isDark ? "#ffcc00" : "#ff4444",
                            borderWidth: 2,
                            borderDash: [6, 4],
                            label: {
                                enabled: true,
                                content: "0.45 Threshold",
                                position: "start",
                                backgroundColor: isDark ? "#333" : "#fff",
                                color: isDark ? "#ffcc00" : "#ff4444",
                                padding: 4,
                            }
                        }
                    }
                },

                datalabels: {
                    anchor: "end",
                    align: "end",
                    color: isDark ? "#ffffff" : "#333333",
                    formatter: (v) => (v * 100).toFixed(1) + "%",
                    font: {
                        weight: "bold",
                        size: 12,
                    }
                }
            },

            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: isDark ? "#ddd" : "#333",
                        callback: (v) => (v * 100) + "%"
                    },
                    grid: {
                        color: isDark ? "#444" : "#ccc"
                    }
                },
                x: {
                    ticks: {
                        color: isDark ? "#ddd" : "#333",
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

function updateExplanation(result) {
    const div = document.getElementById("explanation-block");

    div.innerHTML = `
        <b>Final Intent:</b> ${result.final_intent}<br>
        <b>ML Intent:</b> ${result.ml_intent}<br>
        <b>Reason:</b> <span style="color:#0a84ff">${result.reason}</span><br>
        <b>Confidence:</b> ${(result.max_probability * 100).toFixed(2)}%
    `;
}

async function searchLogs() {
  const q = document.getElementById("log-query").value.trim();
  const out = document.getElementById("logs-results");

  if (!q) {
    out.innerHTML = "<i>Enter search term</i>";
    return;
  }

  try {
    const res = await fetch("/api/search_logs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, limit: 20 })
    });
    const data = await res.json();

    const logs = data.results || [];
    if (!logs.length) {
      out.innerHTML = "<i>No matches</i>";
      return;
    }

    let html = "";
    for (const item of logs) {
      html += `
        <div class="log-entry">
          <div><b>Q:</b> ${item.question}</div>
          <div><b>A:</b> ${item.answer}</div>
          <div style="font-size:11px;color:#777;">
            intent=${item.final_intent} | ML=${item.ml_intent} | p=${item.max_probability.toFixed(3)}
          </div>
        </div>`;
    }
    out.innerHTML = html;
  } catch (err) {
    out.innerHTML = "<span style='color:red;'>Error: " + err.message + "</span>";
  }
}

async function uploadRules() {
  const fileInput = document.getElementById("rules-file");
  const file = fileInput.files[0];
  const status = document.getElementById("upload-status");

  if (!file) {
    status.innerHTML = "<span style='color:red;'>No file selected.</span>";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  status.textContent = "Uploading...";

  try {
    const res = await fetch("/api/upload_rules", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      status.innerHTML = "<span style='color:green;'>" + data.message + "</span>";
    } else {
      status.innerHTML = "<span style='color:red;'>" + (data.error || "Upload failed") + "</span>";
    }
  } catch (err) {
    status.innerHTML = "<span style='color:red;'>Error: " + err.message + "</span>";
  }
}
