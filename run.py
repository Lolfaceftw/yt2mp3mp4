#!/usr/bin/env python3
import sys
import subprocess
import importlib

# Mapping: import-name → pip-install-name
REQUIRED = {
    "tkinter":   None,       
    "PIL":       "Pillow",   
    "yt_dlp":    "yt-dlp",   
    "validators":"validators" 
}

MIN_PY = (3, 10)

def ensure_python_version():
    if sys.version_info < MIN_PY:
        v = ".".join(map(str, MIN_PY))
        print(f"ERROR: Python {v}+ is required (you have {sys.version.split()[0]})")
        sys.exit(1)

def check_and_install_deps():
    missing = []
    for module, pip_name in REQUIRED.items():
        try:
            __import__(module)
        except ImportError:
            # fall back: if pip_name is None, use module name
            missing.append(pip_name or module)
    if not missing:
        return

    print("Missing required packages:", ", ".join(missing))
    resp = input("Install missing packages now? [Y/n] ").strip().lower() or "y"
    if resp in ("y", "yes"):
        for pkg in missing:
            print(f"Installing {pkg}…")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✓ {pkg}")
            except subprocess.CalledProcessError:
                print(f"  ✗ failed to install {pkg}")
        # re-check
        still_missing = [
            pkg for pkg in missing
            if importlib.util.find_spec(pkg.split()[0]) is None
        ]
        if still_missing:
            print("Some packages still missing:", ", ".join(still_missing))
            print("Please install them manually and rerun.")
            sys.exit(1)
    else:
        print("Aborting. Please install required packages and rerun.")
        sys.exit(1)

def main():
    ensure_python_version()
    check_and_install_deps()

    # Now that deps are satisfied, import and run your GUI
    from gui import GUI
    GUI().run()

if __name__ == "__main__":
    main()
