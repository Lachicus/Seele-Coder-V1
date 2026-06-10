# Seele Vollerei AI Assistant (Seele-Coder-V1)

A feature-rich, autonomous personal AI assistant and developer agent modeled after the persona of **Seele Vollerei** from *Honkai Impact 3rd*. Seele-Coder-V1 combines advanced conversational AI, deep reasoning, real-time Google search grounding, local file analysis, and autonomous local terminal access with a gorgeous web UI and a desktop Spotlight-style widget.

---

## 🌟 Key Features

### 1. 🤖 Seele Vollerei Persona
*   **Immersive Roleplay:** Seele interacts with you as her **"Captain"**. Her personality is sweet, modest, kind, caring, and playful.
*   **Interactive Quirk:** If she makes a mistake or encounters a minor hiccup, she brushes it off with a silly, goofy `"hehe."` vibe.
*   **Tech Savvy:** Behind the sweet demeanor is an expert assistant fluent in programming, command-line usage, and autonomous problem-solving.

### 2. 💻 Autonomous Local Terminal Accessibility
*   **Persistent Shell Session:** Seele has a persistent local terminal connection (`/bin/bash` on macOS) initialized via pseudo-terminals (`pty`).
*   **Recursive Loop Executions:** When Seele generates commands enclosed in `$# <command> $#` tags, the Flask server intercepts, executes them in the terminal, captures the output, and feeds it back to Seele's context in real time (up to 20 rounds).
*   **Autonomous Search & Actions:** She can explore paths (e.g., checks typical user directories like `Desktop`, `Downloads`, `Documents`), run developer scripts, or use the macOS `open` utility, asking for confirmation only when modifying files.
*   **Self-Correction:** If a command fails, Seele attempts self-correction up to 5 times. She shuts down terminal loops cleanly using `!stop`.

### 3. 🧠 Advanced Gemini API Capabilities
*   **Standard Conversational Mode:** Uses `gemini-2.5-flash` configured with Seele's behavioral persona system instruction.
*   **Web Grounding Search:** Uses `gemini-2.0-flash` with Google Search grounding enabled to retrieve real-time facts and documentation.
*   **Coder Reasoner Mode:** Leverages Gemini's thinking capability (`thinking_config` enabled) to display her inner monologue/reasoning process dynamically in the UI before presenting her final answers.

### 4. 🎨 Stunning Web Chat Interface
*   **Vibrant, Premium Aesthetics:** Sleek dark-mode design with glowing color gradients, custom animations (e.g., rotating multi-color user avatar borders), and polished typography (Google Sans).
*   **Responsive Sidebar & Layout:** A collapsible sidebar featuring online/offline connection status indicators, server control options, and an active uploads file list.
*   **PWA Ready:** Includes a `manifest.json` and a registered `service-worker.js` for offline caching and desktop installability.
*   **Rich Media & Code Rendering:**
    *   **Markdown Parsing:** Uses `Marked.js` to render paragraphs, lists, tables, and blockquotes beautifully.
    *   **Syntax Highlighting:** Uses `Highlight.js` with an `atom-one-dark` theme and a one-click copy button for code blocks.
    *   **Sanitization:** Uses `DOMPurify` to keep markdown rendering secure against XSS.
*   **Mobile-Optimized UX:** Features a responsive layout with a slide-out hamburger menu designed for mobile phones and tablets.

### 5. 📂 Contextual File upload & Manager
*   **Upload Panel:** Upload local files which are saved in the `uploads/` folder and registered in `uploaded_files.json`.
*   **Context Injections:** Toggle uploaded files on/off in the sidebar. When active, their text content is automatically appended to the Gemini prompt context.
*   **Binary File Support:** Auto-detects MIME types and uploads binary files (like images/docs) directly via the Gemini Files API.

### 6. 🔍 Spotlight Desktop Search Bar Widget
*   **Global Hotkey Activator:** Runs a background listener (`pynput`) that summons a Spotlight search bar widget whenever you press `Cmd + Shift + Space`.
*   **Tkinter Desktop Overlay:** A borderless, translucent desktop utility that lets you quickly search or ask Seele queries without having the web browser open.
*   **Dynamic UI Adjustments:** Shows loading animations and automatically resizes its height based on the AI's response content.

---

## 🛠️ Tech Stack

### Backend
*   **Framework:** Python 3 (Flask)
*   **Process Management:** Pseudo-terminals (`pty`), standard Python subprocesses, and thread-safe socket operations.
*   **API Client:** Google GenAI SDK (`google-genai`) for interfacing with Gemini.

### Frontend
*   **CSS & UI:** TailwindCSS, Custom Glassmorphism CSS, FontAwesome 6 Icons, Google Sans & Fira Code Fonts.
*   **JS Libraries:** `Marked.js` (markdown rendering), `DOMPurify` (HTML security sanitization), `Highlight.js` (code block highlighting).
*   **PWA Integrations:** HTML5 Web App Manifest, Service Workers.

### Desktop Widget
*   **GUI:** Python `tkinter` (Ttk)
*   **Keyboard Hook:** `pynput` (global OS-level hotkeys listener)
*   **Networking:** `requests` library

---

## 📁 Repository Structure

```
├── app.py                  # Main Flask server (chat logic, file upload, terminal execution)
├── seele_launcher.sh       # Bash entrypoint script to launch the hotkey listener
├── manifest.json           # PWA configuration manifest
├── service-worker.js       # Basic service worker for app caching
├── uploaded_files.json     # Metadata database for uploaded context files
├── uploads/                # Directory storing local user-uploaded files
├── logs/                   # Server activity log files (e.g. flask.log)
├── static/                 # Static assets (Seele icons)
├── templates/              # HTML layout files
│   └── index.html          # Seele's premium web chat UI
└── spotlight/              # Spotlight widget source files
    ├── hotkey.py           # Listens for keyboard triggers to open the widget
    ├── menu_controller.py  # Controls/monitors the Flask backend server
    └── spotlight.py        # Desktop Tkinter overlay search bar UI
```

---

## 🚀 Setup & Installation

### 1. Clone & Prepare Virtual Environment
Create a Python virtual environment named `myenv` inside the repository directory:
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```
*(Ensure `google-genai`, `flask`, `werkzeug`, `pynput`, and `requests` are installed in `myenv`)*.

### 2. Configure API Key
Configure your Gemini API key in your system environment variables:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Running the Server & Web App
Run the Flask server:
```bash
python app.py
```
Open your web browser and go to `http://localhost:5008` (or the local network IP shown in the console) to meet Seele!

### 4. Running the Desktop Widget
To run Seele's Spotlight widget overlay:
1. Ensure the Flask server is running.
2. Execute the launcher script:
```bash
./seele_launcher.sh
```
3. Press **`Cmd + Shift + Space`** on your keyboard to summon the search bar directly to your screen. Press **`Escape`** or click the **`×`** to hide it.
