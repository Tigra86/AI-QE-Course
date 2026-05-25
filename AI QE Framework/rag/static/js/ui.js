const chatWindow = document.getElementById("chat-window");
const userInput  = document.getElementById("user-input");
const drawer     = document.getElementById("debug-drawer");

let probChartInstance = null;
let lastProbabilitiesCache = null;

// -------------------------------------------------------------------
// VOICE STATE
// -------------------------------------------------------------------

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition = null;
let isListening = false;
let suppressRecognitionAutoSend = false;
let lastBotAnswer = "";
let autoSpeakEnabled = true;

const voiceStatusEl   = document.getElementById("voice-status");
const micBtn          = document.getElementById("mic-btn");
const stopMicBtn      = document.getElementById("stop-mic-btn");
const stopSpeakBtn    = document.getElementById("stop-speak-btn");
const speakLastBtn    = document.getElementById("speak-last-btn");
const autoSpeakToggle = document.getElementById("auto-speak-toggle");
const langSelect      = document.getElementById("voice-lang");

// -------------------------------------------------------------------
// CHAT
// -------------------------------------------------------------------

async function sendMessage(textOverride = null) {
  const text = (textOverride ?? userInput.value).trim();
  if (!text) return;

  stopListening(true);
  stopSpeaking();

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

    if (!res.ok || data.error) {
      appendMessage("Error: " + (data.error || "Request failed"), "bot");
      setVoiceStatus("Error");
      return;
    }

    const answer = data.answer || "No answer returned.";
    appendMessage(answer, "bot");
    lastBotAnswer = answer;

    if (data.probabilities && typeof data.probabilities === "object") {
      renderProbChart(data.probabilities);
    }

    updateExplanation(data);

    if (autoSpeakEnabled && lastBotAnswer) {
      speakText(lastBotAnswer);
    }
  } catch (err) {
    appendMessage("Error: " + err.message, "bot");
    setVoiceStatus("Error");
  }
}

function appendMessage(text, who = "bot") {
  const div = document.createElement("div");
  div.className = "message " + who;
  div.textContent = (who === "user" ? "You: " : "Bot: ") + text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function clearChat() {
  chatWindow.innerHTML = "";
}

// -------------------------------------------------------------------
// DEBUG DRAWER
// -------------------------------------------------------------------

function toggleDebugDrawer() {
  drawer.classList.toggle("open");
  localStorage.setItem("debugOpen", drawer.classList.contains("open") ? "1" : "0");
}

document.addEventListener("keydown", (e) => {
  if (e.key === "F12") {
    e.preventDefault();
    toggleDebugDrawer();
  }
});

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// -------------------------------------------------------------------
// THEME
// -------------------------------------------------------------------

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

// -------------------------------------------------------------------
// VOICE HELPERS
// -------------------------------------------------------------------

function setVoiceStatus(text) {
  if (voiceStatusEl) {
    voiceStatusEl.textContent = text;
  }
}

function getSelectedLang() {
  return langSelect?.value || "en-US";
}

function browserSupportsSpeechInput() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function initSpeechRecognition() {
  if (!SpeechRecognition) {
    setVoiceStatus("Speech recognition not supported");
    if (micBtn) micBtn.disabled = true;
    if (stopMicBtn) stopMicBtn.disabled = true;
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = getSelectedLang();
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  let finalTranscript = "";

  recognition.onstart = () => {
    isListening = true;
    finalTranscript = "";
    setVoiceStatus("Listening...");
    if (micBtn) micBtn.disabled = true;
    if (stopMicBtn) stopMicBtn.disabled = false;
  };

  recognition.onresult = (event) => {
    let interimTranscript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + " ";
      } else {
        interimTranscript += transcript;
      }
    }

    userInput.value = normalizeVoiceText(finalTranscript + interimTranscript);
};

  recognition.onerror = (event) => {
    isListening = false;
    if (micBtn) micBtn.disabled = false;
    if (stopMicBtn) stopMicBtn.disabled = true;
    setVoiceStatus("Recognition error: " + event.error);
  };

  recognition.onend = async () => {
    isListening = false;
    if (micBtn) micBtn.disabled = false;
    if (stopMicBtn) stopMicBtn.disabled = true;

    if (suppressRecognitionAutoSend) {
      suppressRecognitionAutoSend = false;
      setVoiceStatus("Idle");
      return;
    }

    const finalText = normalizeVoiceText(userInput.value);

    if (finalText) {
      setVoiceStatus("Sending...");
      await sendMessage(finalText);
    } else {
      setVoiceStatus("Idle");
    }
  };
}

function startListening() {
  if (!recognition) {
    initSpeechRecognition();
  }
  if (!recognition || isListening) return;

  stopSpeaking();

  try {
    recognition.lang = getSelectedLang();
    userInput.value = "";
    recognition.start();
  } catch (err) {
    setVoiceStatus("Unable to start microphone");
  }
}

function stopListening(silent = false) {
  if (recognition && isListening) {
    suppressRecognitionAutoSend = silent;
    recognition.stop();
  }
}

function speakText(text) {
  if (!text || !("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();

  const textToSpeak = text.length > 1000 ? text.slice(0, 1000) + " ..." : text;

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = getSelectedLang();
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const preferred =
    voices.find(v => v.lang === utterance.lang && /Google|Samantha|Alex|Microsoft/i.test(v.name)) ||
    voices.find(v => v.lang === utterance.lang) ||
    null;

  if (preferred) {
    utterance.voice = preferred;
  }

  utterance.onstart = () => setVoiceStatus("Speaking...");
  utterance.onend = () => setVoiceStatus("Idle");
  utterance.onerror = () => setVoiceStatus("Speech error");

  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    setVoiceStatus("Idle");
  }
}

function speakLastAnswer() {
  if (lastBotAnswer) {
    speakText(lastBotAnswer);
  }
}

function normalizeVoiceText(text) {
  if (!text) return text;

  text = text.trim();
  text = text.charAt(0).toUpperCase() + text.slice(1);

  if (!/[?.!]$/.test(text)) {
    if (/^(what|why|how|when|where|who|which|is|are|do|does|did|can|could|should|would|что|почему|как|когда|где|кто|какой|какая|какое|какие|можно|нужно|это|есть|будет)\b/i.test(text)) {
      text += "?";
    }
  }

  return text;
}

// -------------------------------------------------------------------
// INIT
// -------------------------------------------------------------------

window.addEventListener("load", () => {
  userInput.focus();

  if (window.Chart && window["chartjs-plugin-annotation"]) {
    Chart.register(window["chartjs-plugin-annotation"]);
  }
  if (window.ChartDataLabels) {
    Chart.register(ChartDataLabels);
  }

  if (localStorage.getItem("debugOpen") === "1") {
    drawer.classList.add("open");
  }

  const storedTheme = localStorage.getItem("theme") || "light";
  applyTheme(storedTheme);

  const storedAutoSpeak = localStorage.getItem("autoSpeakEnabled");
  autoSpeakEnabled = storedAutoSpeak === null ? true : storedAutoSpeak === "1";

  if (autoSpeakToggle) {
    autoSpeakToggle.checked = autoSpeakEnabled;
    autoSpeakToggle.addEventListener("change", () => {
      autoSpeakEnabled = autoSpeakToggle.checked;
      localStorage.setItem("autoSpeakEnabled", autoSpeakEnabled ? "1" : "0");
    });
  }

  if (micBtn) {
    micBtn.addEventListener("click", startListening);
  }

  if (stopMicBtn) {
    stopMicBtn.addEventListener("click", () => stopListening(false));
    stopMicBtn.disabled = true;
  }

  if (stopSpeakBtn) {
    stopSpeakBtn.addEventListener("click", stopSpeaking);
  }

  if (speakLastBtn) {
    speakLastBtn.addEventListener("click", speakLastAnswer);
  }

  if ("speechSynthesis" in window) {
    window.speechSynthesis.onvoiceschanged = () => {};
  }

  if (!browserSupportsSpeechInput()) {
    if (micBtn) {
      micBtn.disabled = true;
      micBtn.title = "Voice input is not supported in this browser";
    }

    if (stopMicBtn) {
      stopMicBtn.disabled = true;
    }

    setVoiceStatus("Voice input not supported in this browser");
  }

  initSpeechRecognition();

  if (browserSupportsSpeechInput()) {
    setVoiceStatus("Idle");
  }
});

// -------------------------------------------------------------------
// CHART
// -------------------------------------------------------------------

function renderProbChart(probabilities) {
  const canvas = document.getElementById("probChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  lastProbabilitiesCache = probabilities;

  if (probChartInstance) {
    probChartInstance.destroy();
  }

  const labels = Object.keys(probabilities);
  const values = Object.values(probabilities);

  const isDark = document.documentElement.getAttribute("data-theme") === "dark";

  const gradient = ctx.createLinearGradient(0, 0, 0, 220);
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
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 700,
        easing: "easeOutQuart"
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
                padding: 4
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
            size: 12
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

// -------------------------------------------------------------------
// EXPLANATION
// -------------------------------------------------------------------

function updateExplanation(result) {
  const div = document.getElementById("explanation-block");
  if (!div) return;

  div.innerHTML = `
    <b>Final Intent:</b> ${escapeHtml(result.final_intent)}<br>
    <b>ML Intent:</b> ${escapeHtml(result.ml_intent)}<br>
    <b>Reason:</b> <span style="color:#0a84ff">${escapeHtml(result.reason)}</span><br>
    <b>Confidence:</b> ${((result.max_probability || 0) * 100).toFixed(2)}%
  `;
}

// -------------------------------------------------------------------
// LOG SEARCH
// -------------------------------------------------------------------

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
          <div><b>Q:</b> ${escapeHtml(item.question)}</div>
          <div><b>A:</b> ${escapeHtml(item.answer)}</div>
          <div style="font-size:11px;color:#777;">
            intent=${escapeHtml(item.final_intent)} | ML=${escapeHtml(item.ml_intent)} | p=${Number(item.max_probability || 0).toFixed(3)}
          </div>
        </div>`;
    }

    out.innerHTML = html;
  } catch (err) {
    out.innerHTML = "<span style='color:red;'>Error: " + escapeHtml(err.message) + "</span>";
  }
}

// -------------------------------------------------------------------
// RULE UPLOAD
// -------------------------------------------------------------------

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
      let message = data.message || "Upload succeeded.";
      if (Array.isArray(data.validation_errors) && data.validation_errors.length) {
        message += " Validation warnings: " + data.validation_errors.join(" | ");
      }
      status.innerHTML = "<span style='color:green;'>" + escapeHtml(message) + "</span>";
    } else {
      const message = data.error || data.message || "Upload failed";
      status.innerHTML = "<span style='color:red;'>" + escapeHtml(message) + "</span>";
    }
  } catch (err) {
    status.innerHTML = "<span style='color:red;'>Error: " + escapeHtml(err.message) + "</span>";
  }
}

// -------------------------------------------------------------------
// UTILS
// -------------------------------------------------------------------

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
