# ⚡ JARVIS Mobile // Mark-LIV (Android Termux Edition)

> An autonomous, voice-enabled AI assistant inspired by **FatihMakes' Mark-LIV**, redesigned from the ground up to run directly on **Android** inside **Termux**.

---

## 🌟 Key Features

* **🧠 Google Gemini Intelligence**: Powered by Google Gemini with autonomous tool-calling to control your device based on spoken or typed natural language commands.
* **📱 Native Android Hardware Control (Termux:API)**:
  * **Flashlight (Torch)**: Toggle device flashlight on/off.
  * **Battery Diagnostics**: Check percentage, charging status, health, and temperature.
  * **Camera Capture**: Snap photos with front or rear cameras for AI vision queries.
  * **Clipboard Integration**: Read and write system clipboard.
  * **Status Bar Notifications & Vibration**: Native alerts and haptic feedback.
* **🎮 Deep Screen Automation (Wireless ADB)**:
  * **App Launching**: Launch any Android app by name (`WhatsApp`, `YouTube`, `Chrome`, `Spotify`, `Settings`).
  * **Touch Screen Simulation**: Tap coordinates (`tap x y`), swipe, and scroll.
  * **Screen Inspection**: Capture screenshots directly for Gemini multimodal analysis.
* **⚛️ Mobile Web HUD (Futuristic Arc Reactor)**:
  * Runs a local FastAPI server on `http://localhost:8000`.
  * Open in Chrome/Firefox on your phone or install as a PWA on your home screen.
  * Multi-ring animated Arc Reactor pulsing with state (Standby, Listening, Thinking, Speaking).
  * Real-time audio waveform visualizer.
  * Integrated Web Speech recognition & text-to-speech voice loop.
* **💻 Rich Terminal Mode (`--cli`)**:
  * Clean, interactive CLI inside the Termux shell with formatted panels and status badges.
* **🛡️ Built-in Simulation Mode**:
  * Runs seamlessly on PC (Windows, macOS, Linux) with simulated hardware mocks for effortless testing and development.

---

## 📁 Repository Structure

```
Jarvis-Mobile/
├── actions/
│   ├── termux_api.py      # Termux:API hardware wrapper & mock fallbacks
│   ├── adb_control.py     # Wireless ADB touch & screen control
│   └── web_tools.py       # DuckDuckGo search, time/date, shell execution
├── core/
│   ├── config.py          # Environment configuration & platform detection
│   ├── brain.py           # Gemini Live & tool calling execution engine
│   └── tools_schema.py    # Function definitions & dispatcher
├── hud/
│   ├── static/
│   │   ├── css/style.css  # Cyberpunk / Arc Reactor HUD design
│   │   └── js/app.js      # WebSockets, Audio Visualizer, Speech API
│   └── templates/
│       └── index.html     # Mobile-optimized Web HUD
├── cli.py                 # Rich-based Terminal UI for Termux shell
├── server.py              # FastAPI server (WebSockets + Web HUD)
├── main.py                # Main launcher (--cli or web HUD)
├── setup_termux.sh        # Automated one-step installer for Termux
├── run.sh                 # Fast runner script
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 🚀 Quickstart on Android (Termux)

### Step 1: Install Required Android Apps
1. Install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/) (do **not** use the outdated Google Play Store version).
2. Install **Termux:API** from [F-Droid](https://f-droid.org/en/packages/com.termux.api/).

### Step 2: Clone & Run Automated Setup
Open Termux and run:

```bash
# Clone the repository
git clone https://github.com/your-username/Jarvis-Mobile.git
cd Jarvis-Mobile

# Run the automated setup script
chmod +x setup_termux.sh run.sh
./setup_termux.sh
```

### Step 3: Add Your Gemini API Key
Edit `.env` using `nano` or your favorite editor:
```bash
nano .env
```
Set your Google AI Studio key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Step 4: Launch JARVIS!

#### Option A: Mobile Web HUD (Recommended)
```bash
python main.py
```
Open your mobile browser (Chrome or Firefox) and navigate to:
```
http://localhost:8000
```
> **Tip**: Tap Chrome's menu (`⋮`) -> **Add to Home screen** to use JARVIS like a native fullscreen app!

#### Option B: Terminal CLI Mode
```bash
python main.py --cli
```

---

## 🔌 Optional: Setting Up Wireless ADB (For Screen Taps & App Automation)

On Android 11+:
1. Go to **Settings** -> **Developer Options**.
2. Enable **Wireless Debugging**.
3. Tap **Pair device with pairing code**.
4. In Termux, pair and connect:
   ```bash
   adb pair 127.0.0.1:<PORT> <PAIRING_CODE>
   adb connect 127.0.0.1:<PORT>
   ```
Now JARVIS can tap, swipe, launch third-party apps, and capture screens!

---

## 🗣️ Example Voice / Text Commands

* *"Jarvis, turn on the flashlight."*
* *"What is my battery level and temperature?"*
* *"Take a photo with the front camera."*
* *"Open YouTube on my phone."*
* *"Vibrate the device."*
* *"Search the web for the latest tech news."*
* *"Copy 'Meeting at 4 PM' to my clipboard."*
* *"What's the current time and date?"*

---

## 💻 Testing on PC (Windows / Mac / Linux)

You can run and test Jarvis-Mobile on your computer right away:
```bash
pip install -r requirements.txt
python main.py
```
Open `http://localhost:8000` in your browser. All Android-specific calls will automatically execute in **Simulation Mode** without throwing errors.
