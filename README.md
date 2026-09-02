<div align="center">

# 🎬 Polynomial Studio

**Web-based polynomial visualization and analysis**

*Built with Flask · SymPy · NumPy · Manim*

![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![uv](https://img.shields.io/badge/uv-Package_Manager-2684FF?style=for-the-badge&logo=uv&logoColor=white)

</div>

---

## 📋 Requirements

| Dependency | Version | Notes |
|:----------:|:-------:|:------|
| 🪟 **Windows** | 10/11 | Development environment |
| 📦 **uv** | Latest | Python package manager |
| 🐍 **Python** | 3.13 | Managed automatically by uv |
| 🎞️ **FFmpeg** | Latest | Required by Manim for video rendering |
| 📐 **LaTeX** | MiKTeX or TeX Live | Required by Manim for text/math rendering |

---

## 📐 Installing LaTeX (Required for Manim)

Manim uses LaTeX to render text and math in animations. Install **MiKTeX** on D drive:

```powershell
# Download MiKTeX from https://miktex.org/download
# During install, choose D drive as the installation directory
# Example: D:\Program Files\MiKTeX

# After installing MiKTeX, open a new terminal and verify:
latex --version

# MiKTeX will auto-install missing packages on first use.
# If prompted, click "Install" to let it download what it needs.
```

Alternatively, install **TeX Live** on D drive:

```powershell
# Download TeX Live from https://www.tug.org/texlive/acquire-netinstall.html
# Choose custom install and set install directory to D:\texlive
```

> ⚠️ **Important:** After installing LaTeX, restart your terminal so the `latex` command is on your PATH.

---

## 🛠️ Setup

### 1. Open the project

```powershell
cd "D:\vs code projects\polynomial-studio"
```

### 2. Install Python 3.13 with uv

If Python 3.13 is not already installed:

```powershell
uv python install 3.13
```

### 3. Create the virtual environment

```powershell
uv venv --python 3.13
```

### 4. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your prompt should show:

```
(polynomial-studio) PS D:\vs code projects\polynomial-studio>
```

### 5. Install dependencies

```powershell
uv pip install -r requirements.txt
```

> ⚠️ **Important:** Do not use `python -m pip install requirements.txt`. The `-r` flag tells pip/uv that `requirements.txt` contains a list of dependencies.

### 6. Verify the Python environment

```powershell
python --version
```

Expected:

```
Python 3.13.x
```

Verify Python is from the project environment:

```powershell
python -c "import sys; print(sys.executable)"
```

Expected path:

```
D:\vs code projects\polynomial-studio\.venv\Scripts\python.exe
```

### 7. Verify all dependencies

```powershell
python -c "import flask, sympy, numpy, manim; print('All dependencies installed successfully')"
```

---

## ▶️ Running the Project

Make sure the virtual environment is activated:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then start the Flask application:

```powershell
python app.py
```

Open in your browser:

> **http://127.0.0.1:5000**

<details>
<summary><strong>💡 Running with uv Without Activating the Environment</strong></summary>

You can also run commands through the project environment without manually activating `.venv`:

```powershell
uv run --python .venv\Scripts\python.exe app.py
```

For most development work, activating `.venv` first is recommended.

</details>

---

## 🎬 Manim

Polynomial Studio uses Manim for mathematical animation/video rendering.

After installing the dependencies, verify Manim:

```powershell
python -c "import manim; print(manim.__version__)"
```

You can also check that the Manim command is available:

```powershell
manim --version
```

---

## 🔄 Recommended Development Workflow

Every time you open a **new PowerShell terminal**:

```powershell
cd "D:\vs code projects\polynomial-studio"
.\.venv\Scripts\Activate.ps1
python app.py
```

If the virtual environment **does not exist yet**:

```powershell
uv python install 3.13
uv venv --python 3.13
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

<details>
<summary><strong>❌ "py is not recognized"</strong></summary>

The project does not require the Windows `py` launcher.

Use uv instead:

```powershell
uv python install 3.13
uv venv --python 3.13
```

</details>

<details>
<summary><strong>❌ Python shows version 3.14</strong></summary>

Make sure the virtual environment is activated:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then check:

```powershell
python --version
```

It should show `Python 3.13.x`.

</details>

<details>
<summary><strong>❌ PowerShell refuses to activate .venv</strong></summary>

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

</details>

<details>
<summary><strong>❌ requirements.txt installation fails</strong></summary>

Make sure you're using the project environment:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

Then reinstall:

```powershell
uv pip install -r requirements.txt
```

</details>

<details>
<summary><strong>❌ Do NOT use the global Python installation</strong></summary>

Avoid installing the project's dependencies into your global Python:

```powershell
# ❌ WRONG — installs into global Python
python -m pip install -r requirements.txt
```

Instead, always activate `.venv` first, or use `uv pip install`.

</details>

<details>
<summary><strong>❌ ImportError from system Python 3.14</strong></summary>

If you see errors like `cannot import name 'Union' from '_typing'`, it means
PYTHONHOME is pointing to the wrong Python. Clear it and re-activate:

```powershell
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
.\.venv\Scripts\Activate.ps1
```

</details>

<details>
<summary><strong>❌ dvisvgm PYTHONHOME error during rendering</strong></summary>

If you see `Fatal Python error: Failed to import encodings module` during
video rendering, dvisvgm (LaTeX SVG converter) is picking up a mismatched
PYTHONHOME. The app now automatically clears PYTHONHOME/PYTHONPATH when
running Manim, but if the error persists:

```powershell
# Clear the environment variables before starting the server
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
.\.venv\Scripts\Activate.ps1
python app.py
```

Also ensure MiKTeX or TeX Live is installed and `latex --version` works in
your terminal. Manim requires LaTeX for rendering math equations.

</details>

---

## 📁 Project Architecture

```
Polynomial Studio
       │
       ├── Python 3.13
       │      └── managed by uv
       │
       └── .venv  (inside project folder)
              ├── Flask
              ├── SymPy
              ├── NumPy
              └── Manim
```

All dependencies live inside the project folder — no C drive paths.
The `.venv` directory is self-contained within `polynomial-studio/`.

---

<div align="center">

**Run `python app.py` and open http://127.0.0.1:5000**

</div>
