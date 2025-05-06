#!/usr/bin/env python3
# run.py
"""
Entry point for the YouTube Downloader application.
Checks Python version, manages dependencies, and launches the GUI.
"""
import sys
import subprocess
import importlib.util
import config # Use the config module

# Minimum required Python version (major, minor)
MIN_PYTHON_VERSION = (3, 10)

# Mapping: import-name -> pip-install-name (None if part of stdlib or no direct pip name)
REQUIRED_DEPENDENCIES = {
    "tkinter": None,        # Standard library, but check availability
    "PIL": "Pillow",        # Imported as PIL, installed as Pillow
    "yt_dlp": "yt-dlp",     # The core downloader library
    "validators": "validators" # For URL validation
}

def _ensure_python_version():
    """Checks if the current Python version meets the minimum requirement."""
    if sys.version_info < MIN_PYTHON_VERSION:
        required_str = ".".join(map(str, MIN_PYTHON_VERSION))
        current_str = ".".join(map(str, sys.version_info[:3]))
        print(f"ERROR: Python {required_str}+ is required (you have {current_str}).")
        print("Please upgrade your Python installation.")
        sys.exit(1)
    print(f"Python version {sys.version.split()[0]} meets requirement ({'.'.join(map(str, MIN_PYTHON_VERSION))}+).")

def _check_module(module_name: str) -> bool:
    """Checks if a module can be imported."""
    # Special handling for tkinter which might not have a standard spec path always
    if module_name == "tkinter":
        try:
            importlib.util.find_spec(module_name)
            # Further check if Tkinter root window can be initialized (optional but more robust)
            # import tkinter
            # try:
            #     tkinter.Tk().destroy() # Try creating and destroying a root window
            #     return True
            # except tkinter.TclError:
            #     print(f"Warning: Found tkinter module but failed to initialize Tk root window. GUI might not work.", file=sys.stderr)
            #     return False # Treat as missing if GUI cannot start
            return True # Assume find_spec is enough for now
        except ImportError:
             return False
    # Standard check for other modules
    return importlib.util.find_spec(module_name) is not None

def _get_missing_dependencies() -> list[tuple[str, str]]:
    """
    Identifies missing dependencies based on REQUIRED_DEPENDENCIES.
    Returns a list of tuples (module_name, install_name) for missing ones.
    """
    print("Checking required dependencies...")
    missing = []
    for module_name, install_name in REQUIRED_DEPENDENCIES.items():
        print(f"  Checking for {module_name}...", end="")
        if not _check_module(module_name):
            print(" MISSING")
            # Determine the correct name for installation instructions
            if install_name: # Use pip name if provided
                 missing.append((module_name, install_name))
            elif module_name == "tkinter": # Special instruction for tkinter
                 missing.append((module_name, "python3-tk (Linux) or ensure Tkinter is included in your Python installation (Windows/macOS)"))
            else: # Should not happen with current list, but fallback
                 missing.append((module_name, module_name))
        else:
            print(" OK")
    return missing

def _prompt_install_missing(missing_deps: list[tuple[str, str]]) -> bool:
    """Prompts the user to attempt installation of missing dependencies via pip."""
    print("\nMissing required packages:")
    installable_count = 0
    for _, install_name in missing_deps:
        # Only list packages that have a direct pip install name
        if install_name and not install_name.startswith("python3-tk"): 
            print(f"  - {install_name}")
            installable_count += 1
        elif install_name: # Handle tkinter message separately
             print(f"  - Tkinter (GUI Library): Please install '{install_name}'")


    if installable_count == 0:
        print("\nCannot automatically install all missing dependencies (e.g., Tkinter).")
        print("Please install them manually and rerun the application.")
        return False

    try:
        response = input("Attempt to install missing packages using pip? [Y/n] ").strip().lower()
        return response in ("y", "yes", "")
    except EOFError: # Handle non-interactive environments
        print("\nNon-interactive environment detected. Cannot prompt for installation.")
        return False


def _install_dependency(pip_name: str) -> bool:
    """Installs a single dependency using pip."""
    # Ensure pip is available
    if importlib.util.find_spec("pip") is None:
        print("  Error: 'pip' module not found. Cannot install packages automatically.", file=sys.stderr)
        return False
        
    print(f"  Attempting to install {pip_name}...")
    try:
        # Use subprocess to run pip install
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name],
            check=False, # Don't raise exception on failure, check return code instead
            capture_output=True, # Capture stdout/stderr
            text=True, # Decode output as text
            timeout=300 # 5 minute timeout per package
        )
        
        if result.returncode == 0:
            print(f"  ✓ Successfully installed {pip_name}")
            return True
        else:
            print(f"  ✗ Failed to install {pip_name}. Pip exit code: {result.returncode}")
            print("  --- Pip Output ---")
            print(result.stdout)
            print(result.stderr)
            print("  ------------------")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Installation of {pip_name} timed out.")
        return False
    except FileNotFoundError:
        # This should be caught by the pip check above, but as a fallback
        print(f"  ✗ Failed to install {pip_name}. '{sys.executable} -m pip' command not found?")
        return False
    except Exception as e:
        print(f"  ✗ An unexpected error occurred during installation of {pip_name}: {e}")
        return False


def manage_dependencies():
    """Checks for dependencies and attempts to install missing ones if requested."""
    missing_deps = _get_missing_dependencies()
    if not missing_deps:
        print("All dependencies satisfied.")
        return True # Indicate success

    # Filter for dependencies installable via pip
    pip_installable = [(mod, name) for mod, name in missing_deps if name and not name.startswith("python3-tk")]
    
    if not _prompt_install_missing(missing_deps):
        print("Aborting due to missing dependencies.")
        return False # Indicate failure

    if not pip_installable:
         print("No packages found to install via pip. Please install manually.")
         return False # Indicate failure (as user was prompted but nothing could be done)

    print("\nStarting installation process...")
    all_installed_successfully = True
    successfully_installed_modules = []

    for module_name, pip_name in pip_installable:
        if _install_dependency(pip_name):
            successfully_installed_modules.append(module_name)
        else:
            all_installed_successfully = False
            # Optionally break on first failure:
            # print(f"Stopping installation attempt due to failure installing {pip_name}.")
            # break 

    # Re-verify installations after attempting installs
    print("\nRe-verifying dependencies...")
    final_missing = _get_missing_dependencies()

    if final_missing:
        print("\nERROR: Some dependencies are still missing after installation attempt:")
        for _, install_name in final_missing:
             print(f"  - {install_name}")
        print("Please install them manually and restart the application.")
        return False # Indicate failure
    
    print("Dependency check passed.")
    return True # Indicate success


def main():
    """Main function to check environment and run the application."""
    print(f"--- Starting {config.APP_NAME} V{config.APP_VERSION} ---")
    _ensure_python_version()

    if not manage_dependencies():
        sys.exit(1) # Exit if dependencies are not met

    print("Launching GUI...")
    try:
        # Import GUI class only after dependencies are confirmed
        from gui import YoutubeDownloaderApp
        app = YoutubeDownloaderApp()
        app.run()
    except ImportError as e:
         print(f"\nERROR: Failed to import application components: {e}", file=sys.stderr)
         print("This might happen if required files (gui.py, etc.) are missing or if there was an issue during dependency installation.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
         print(f"\nCRITICAL ERROR: An unexpected error occurred while running the application: {e}", file=sys.stderr)
         print("--- Traceback ---", file=sys.stderr)
         import traceback
         traceback.print_exc()
         print("-----------------", file=sys.stderr)
         # Attempt to close logger cleanly if possible
         try:
             from logger import logger
             logger.log(f"CRITICAL ERROR encountered: {e}\n{traceback.format_exc()}", file_only=True)
             logger.close()
         except Exception:
             pass # Avoid further errors during cleanup
         sys.exit(1)

    print(f"--- {config.APP_NAME} Exited ---")


if __name__ == "__main__":
    main()