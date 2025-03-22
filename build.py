import os
import sys
import platform
import subprocess

# Detect the operating system
OS = platform.system().lower()
SCRIPT_NAME = "launcher.py"
ICON_PNG = "1.png"
ICON_ICO = "1.ico"
OUTPUT_NAME = "SnowCallerLauncher"

def check_files():
    """Ensure required files exist."""
    for file in [SCRIPT_NAME, ICON_PNG, ICON_ICO]:
        if not os.path.exists(file):
            print(f"Error: {file} not found in current directory.")
            sys.exit(1)

def build():
    """Build the executable with PyInstaller."""
    check_files()
    
    if OS == "linux":  # Debian
        cmd = [
            "pyinstaller",
            "--onefile",
            f"--add-data={ICON_PNG}:.",
            f"--add-data={ICON_ICO}:.",
            "--name", OUTPUT_NAME,
            SCRIPT_NAME
        ]
    elif OS == "windows":
        cmd = [
            "pyinstaller",
            "--onefile",
            f"--add-data={ICON_PNG};.",
            f"--add-data={ICON_ICO};.",
            "--icon", ICON_ICO,
            "--name", OUTPUT_NAME,
            SCRIPT_NAME
        ]
    else:
        print("Unsupported OS. This build script supports Debian (Linux) and Windows.")
        sys.exit(1)

    try:
        subprocess.run(" ".join(cmd), shell=True, check=True)
        print(f"Build successful! Executable is in 'dist/{OUTPUT_NAME}'")
        if OS == "linux":
            os.chmod(f"dist/{OUTPUT_NAME}", 0o755)  # Make executable on Linux
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()