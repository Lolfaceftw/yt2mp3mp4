import sys
import importlib.util
import subprocess
import time


# TODO: Replace pytube dependency with yt-dlp
req_modules = ['tkinter', 'yt-dlp', 'threading', 'time', 'os', 'webbrowser']
missing_modules = []

if sys.version_info < (3, 10):
    print(f"Python version 3.10 is required to run yt2mp3mp4.Your version is {sys.version}. Please update accordingly.")
else:
    for module in req_modules:
        if not module in sys.modules and importlib.util.find_spec(module) == None:
            missing_modules.append(module)
            print(f'Required module is not found: {module}')
        else:
            print(f'Module is installed: {module}')

    if missing_modules:
        print("The following module/s is/are required:")
        for module in missing_modules:
            print(module)
        install = input("Install the missing modules with pip? (Y/n) ")
        if install == 'y' or install == 'Y':
            for module in missing_modules:
                try:
                    pip = subprocess.Popen([sys.executable, '-m', 'pip3', 'install', 'module'])
                    pip.wait()
                except Exception as e:
                    pass
                if not module in sys.modules and importlib.util.find_spec(module) == None:
                    print(f'Failed to install: {module}')
                else:
                    print(f'Installed: {module}')
                    missing_modules.remove(module)

if missing_modules:
    print("Install these modules manually:")
    for module in missing_modules: print(module)
    input("Press <ENTER> key to continue...")
else:
    import yt2mp3
    yt2mp3.GUI().run()
    