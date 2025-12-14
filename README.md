![CI](https://github.com/nondeletable/ComfyLauncher/actions/workflows/ci.yml/badge.svg)

# 🚀 ComfyLauncher

A desktop launcher for managing and running **ComfyUI** builds with ease.  
Built with **Python** and **PyQt6**, featuring a clean UI, system checks, and flexible configuration management.

---

## ✨ Features

- 🧭 Build manager — select your local ComfyUI build and validate its structure before launch.
- ⚙️ Pre-launch check — verifies that required files (e.g. python.exe, main.py) exist in the selected build.
- 💻 Automatic GPU/CPU mode — detects NVIDIA GPU via nvidia-smi and switches launch mode accordingly.
- 🪟 Modern interface — clean, minimal, and responsive PyQt6 UI with custom window frame and theme support.
- 🎨 Themes system — light and dark modes with future support for user-created themes.
- 🔧 Settings panel — manage paths, active theme, and interface preferences.
- 💬 Integrated console output — view ComfyUI logs directly in the launcher without opening a terminal.
- 🧠 Persistent configuration — saves user preferences and paths in user_config.json.
- 🪄 User-friendly flow — the launcher starts ComfyUI seamlessly without exposing background console windows.
---

## 🧠 Technologies

- **Python 3.12+**
- **PyQt6** — for desktop UI  
- **Subprocess** — to handle ComfyUI execution  
- **JSON** — to store user preferences  
- **PyInstaller** — to build `.exe` releases

---

## 🧩 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/nondeletable/ComfyLauncher.git
cd ComfyLauncher
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python main.py
```

## 🖼️ Screenshots
Main window:


Settings page:


## 📦 Build Executable
To create a standalone .exe build:

```bash
pyinstaller launcher.spec --noconfirm
```

or manually:

```bash
pyinstaller --onefile --noconsole main.py
```
The output will appear in the dist/ folder.

## ⬇️ Download
You can download the latest build from the Releases page.

## 📬 Contacts
- Telegram: @nondeletable

- Email: nondeletable@gmail.com

Thanks for using ComfyLauncher!
We hope it makes your ComfyUI experience smoother and more organized 🪄