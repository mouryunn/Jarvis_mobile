/**
 * JARVIS Mobile // Mark-LIV Web HUD Client
 */

let ws = null;
let isRecording = false;
let recognition = null;
let audioContext = null;
let analyser = null;
let microphone = null;
let visualizerAnimId = null;

// DOM Elements
const connBadge = document.getElementById("connBadge");
const batteryPct = document.getElementById("batteryPct");
const clockDisplay = document.getElementById("clockDisplay");
const reactorWrapper = document.getElementById("reactorWrapper");
const statusLabel = document.getElementById("statusLabel");
const transcriptBox = document.getElementById("transcriptBox");
const terminalBody = document.getElementById("terminalBody");
const textInput = document.getElementById("textInput");
const micBtn = document.getElementById("micBtn");
const micLabel = document.getElementById("micLabel");
const canvas = document.getElementById("visualizerCanvas");
const ctx = canvas.getContext("2d");

// ── CLOCK & STATUS ────────────────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, "0");
    const m = String(now.getMinutes()).padStart(2, "0");
    clockDisplay.textContent = `${h}:${m}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── LOGGING ───────────────────────────────────────────────────────────────
function log(msg, type = "system") {
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    entry.textContent = `[${time}] ${msg}`;
    terminalBody.appendChild(entry);
    terminalBody.scrollTop = terminalBody.scrollHeight;
}

function clearTerminal() {
    terminalBody.innerHTML = "";
    log("Terminal cleared.", "system");
}

// ── STATE MANAGEMENT ──────────────────────────────────────────────────────
function setHUDState(state, labelText) {
    reactorWrapper.className = "reactor-wrapper " + state;
    statusLabel.textContent = labelText;
}

// ── WEBSOCKET CONNECTION ──────────────────────────────────────────────────
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/jarvis`;

    log(`Connecting to neural core at ${wsUrl}...`);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        connBadge.textContent = "ONLINE";
        connBadge.className = "connection-badge connected";
        setHUDState("ready", "SYSTEM ONLINE");
        log("WebSocket neural link established.", "system");
        // Request initial battery status
        sendPayload({ type: "command", text: "Check battery status" });
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleIncomingMessage(data);
        } catch (e) {
            console.error("Failed to parse incoming message:", e);
        }
    };

    ws.onclose = () => {
        connBadge.textContent = "OFFLINE";
        connBadge.className = "connection-badge";
        setHUDState("offline", "LINK SEVERED");
        log("WebSocket link disconnected. Reconnecting in 3s...", "error");
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error("WS error:", err);
    };
}

function sendPayload(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
    } else {
        log("Cannot send: neural link offline.", "error");
    }
}

// ── INCOMING MESSAGE HANDLER ──────────────────────────────────────────────
function handleIncomingMessage(data) {
    if (data.type === "thinking") {
        setHUDState("thinking", "PROCESSING QUERY...");
    } else if (data.type === "response") {
        setHUDState("speaking", "JARVIS RESPONDING");
        transcriptBox.innerHTML = `<strong>JARVIS:</strong> ${data.text}`;
        log(`JARVIS: ${data.text}`, "jarvis");

        // Speak aloud
        speakAloud(data.text);

        // Update actions log
        if (data.actions && data.actions.length > 0) {
            data.actions.forEach(act => {
                log(`⚡ Executed: ${act.tool} (${JSON.stringify(act.args || {})})`, "action");
                if (act.tool === "get_battery_status" && act.result && act.result.percentage) {
                    batteryPct.textContent = `${act.result.percentage}%`;
                }
            });
        }
    } else if (data.type === "battery") {
        batteryPct.textContent = `${data.percentage}%`;
    } else if (data.type === "error") {
        setHUDState("ready", "SYSTEM READY");
        log(`Error: ${data.message}`, "error");
    }
}

// ── SPEECH SYNTHESIS (VOICE FEEDBACK) ──────────────────────────────────────
function speakAloud(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 0.95;

    // Pick best English voice if available
    const voices = window.speechSynthesis.getVoices();
    const jarvisVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Male") || v.name.includes("UK") || v.name.includes("English")));
    if (jarvisVoice) utterance.voice = jarvisVoice;

    utterance.onstart = () => {
        setHUDState("speaking", "SPEAKING");
        startSimulatedVoiceVisualizer();
    };

    utterance.onend = () => {
        setHUDState("ready", "SYSTEM READY");
        stopVisualizer();
    };

    window.speechSynthesis.speak(utterance);
}

// ── SPEECH RECOGNITION (VOICE INPUT) ───────────────────────────────────────
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        log("SpeechRecognition API not available in this browser. Please use Chrome on Android.", "error");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isRecording = true;
        micBtn.className = "mic-btn active";
        micLabel.textContent = "LISTENING...";
        setHUDState("listening", "LISTENING TO COMMAND...");
        transcriptBox.innerHTML = `<span class="subtext">Listening...</span>`;
        startAudioVisualizer();
    };

    recognition.onresult = (event) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                final += event.results[i][0].transcript;
            } else {
                interim += event.results[i][0].transcript;
            }
        }
        if (interim) {
            transcriptBox.innerHTML = `<strong>You:</strong> <em>${interim}</em>`;
        }
        if (final) {
            transcriptBox.innerHTML = `<strong>You:</strong> ${final}`;
            log(`User: ${final}`, "user");
            sendPayload({ type: "command", text: final });
        }
    };

    recognition.onerror = (e) => {
        console.warn("Speech error:", e.error);
        stopVoiceRecording();
    };

    recognition.onend = () => {
        stopVoiceRecording();
    };
}

function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        if (!recognition) initSpeechRecognition();
        try {
            recognition.start();
        } catch (e) {
            console.error("Start error:", e);
        }
    }
}

function stopVoiceRecording() {
    isRecording = false;
    micBtn.className = "mic-btn";
    micLabel.textContent = "PUSH TO SPEAK";
    if (reactorWrapper.className.includes("listening")) {
        setHUDState("ready", "SYSTEM READY");
    }
    stopVisualizer();
    try {
        if (recognition) recognition.stop();
    } catch (_) {}
}

// ── AUDIO VISUALIZER ───────────────────────────────────────────────────────
async function startAudioVisualizer() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);

        drawVisualizer();
    } catch (e) {
        console.log("Mic stream fallback to simulated visualizer:", e);
        startSimulatedVoiceVisualizer();
    }
}

function startSimulatedVoiceVisualizer() {
    let phase = 0;
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;
        const numBars = 32;

        for (let i = 0; i < numBars; i++) {
            const angle = (i / numBars) * Math.PI * 2;
            const barHeight = 8 + Math.sin(phase + i * 0.5) * 16 + Math.random() * 6;

            const x1 = centerX + Math.cos(angle) * radius;
            const y1 = centerY + Math.sin(angle) * radius;
            const x2 = centerX + Math.cos(angle) * (radius + barHeight);
            const y2 = centerY + Math.sin(angle) * (radius + barHeight);

            ctx.strokeStyle = `rgba(0, 240, 255, ${0.4 + (barHeight / 30)})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        phase += 0.2;
        visualizerAnimId = requestAnimationFrame(animate);
    }
    animate();
}

function drawVisualizer() {
    if (!analyser) return;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function render() {
        analyser.getByteFrequencyData(dataArray);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;
        const numBars = 32;

        for (let i = 0; i < numBars; i++) {
            const val = dataArray[i % bufferLength] || 0;
            const barHeight = (val / 255) * 35 + 4;
            const angle = (i / numBars) * Math.PI * 2;

            const x1 = centerX + Math.cos(angle) * radius;
            const y1 = centerY + Math.sin(angle) * radius;
            const x2 = centerX + Math.cos(angle) * (radius + barHeight);
            const y2 = centerY + Math.sin(angle) * (radius + barHeight);

            ctx.strokeStyle = `rgba(0, 240, 255, ${Math.max(0.3, val / 255)})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        visualizerAnimId = requestAnimationFrame(render);
    }
    render();
}

function stopVisualizer() {
    if (visualizerAnimId) {
        cancelAnimationFrame(visualizerAnimId);
        visualizerAnimId = null;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (audioContext && audioContext.state !== "closed") {
        try { audioContext.close(); } catch (_) {}
    }
}

// ── SEND COMMANDS ──────────────────────────────────────────────────────────
function sendTextCommand() {
    const text = textInput.value.trim();
    if (!text) return;
    textInput.value = "";
    transcriptBox.innerHTML = `<strong>You:</strong> ${text}`;
    log(`User: ${text}`, "user");
    sendPayload({ type: "command", text });
}

function sendQuickCommand(cmd) {
    transcriptBox.innerHTML = `<strong>You:</strong> ${cmd}`;
    log(`Quick Command: ${cmd}`, "user");
    sendPayload({ type: "command", text: cmd });
}

textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendTextCommand();
});

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
    connectWebSocket();
    initSpeechRecognition();
});
