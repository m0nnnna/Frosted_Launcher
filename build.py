"""
Build script for SnowCaller Launcher
This script handles building and packaging the launcher for different platforms.
"""

import os
import sys
import shutil
import subprocess
import platform
import logging
import venv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler()
    ]
)

# Configuration
APP_NAME = "SnowCallerLauncher"
ICON_FILE = "1.png"
VERSION = "1.0.0"
DESCRIPTION = "SnowCaller Game Launcher"
AUTHOR = "m0nnnna"
REPO_URL = "https://github.com/m0nnnna/snowcaller"

# Platform-specific settings
OS = platform.system().lower()
if OS == "windows":
    EXECUTABLE_EXTENSION = ".exe"
    ICON_EXTENSION = ".ico"
    VENV_PYTHON = "venv/Scripts/python.exe"
    VENV_PIP = "venv/Scripts/pip.exe"
else:
    EXECUTABLE_EXTENSION = ""
    ICON_EXTENSION = ".png"
    VENV_PYTHON = "venv/bin/python"
    VENV_PIP = "venv/bin/pip"

def create_virtual_environment():
    """Create a virtual environment for building."""
    if not os.path.exists("venv"):
        logging.info("Creating virtual environment...")
        try:
            # Use system Python for virtual environment creation
            system_python = "/usr/bin/python3"
            if not os.path.exists(system_python):
                system_python = "/usr/bin/python"
            
            logging.info(f"Using system Python: {system_python}")
            
            # Create virtual environment using system Python
            subprocess.run(
                [system_python, "-m", "venv", "venv"],
                check=True,
                capture_output=True
            )
            
            # Verify virtual environment was created
            if not os.path.exists(VENV_PYTHON):
                raise FileNotFoundError(f"Virtual environment Python not found at {VENV_PYTHON}")
            
            # Upgrade pip in the virtual environment
            subprocess.run(
                [VENV_PIP, "install", "--upgrade", "pip"],
                check=True,
                capture_output=True
            )
            
            logging.info("Virtual environment setup complete")
        except subprocess.CalledProcessError as e:
            logging.error(f"Virtual environment setup failed: {e.stderr}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during virtual environment setup: {str(e)}")
            raise

def check_dependencies():
    """Check if required build dependencies are installed."""
    try:
        # For Linux, try to install python3-full first
        if OS == "linux":
            try:
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "python3-full", "python3-venv"],
                    check=True,
                    capture_output=True
                )
                logging.info("Successfully installed python3-full and python3-venv")
            except subprocess.CalledProcessError as e:
                logging.warning(f"Failed to install system packages: {e.stderr}")
        
        # Create virtual environment first
        create_virtual_environment()
        
        # Install dependencies in virtual environment
        required_packages = [
            "pyinstaller",
            "pillow",
            "requests"
        ]
        
        for package in required_packages:
            logging.info(f"Installing {package}...")
            subprocess.run(
                [VENV_PIP, "install", package],
                check=True,
                capture_output=True
            )
        
        logging.info("Successfully installed all dependencies in virtual environment")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Dependency installation failed: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during dependency installation: {str(e)}")
        raise

def convert_icon():
    """Convert PNG icon to ICO format for Windows."""
    if OS == "windows" and os.path.exists(ICON_FILE):
        try:
            from PIL import Image
            img = Image.open(ICON_FILE)
            icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
            img.save(f"{APP_NAME}{ICON_EXTENSION}", format='ICO', sizes=icon_sizes)
            logging.info("Icon converted successfully")
        except Exception as e:
            logging.error(f"Failed to convert icon: {str(e)}")
            raise

def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ['build', 'dist', 'venv']
    files_to_clean = [
        f"{APP_NAME}.spec",
        f"{APP_NAME}{ICON_EXTENSION}",
        "build.log",
        "version_info.txt"
    ]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            logging.info(f"Cleaned directory: {dir_name}")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            logging.info(f"Cleaned file: {file_name}")

def build_executable():
    """Build the executable using PyInstaller."""
    # Determine which Python to use
    python_executable = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    
    # Get absolute paths
    current_dir = os.path.abspath(os.path.dirname(__file__))
    icon_path = os.path.join(current_dir, ICON_FILE)
    launcher_path = os.path.join(current_dir, "launcher.py")
    
    # Verify files exist
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"Icon file not found: {icon_path}")
    if not os.path.exists(launcher_path):
        raise FileNotFoundError(f"Launcher file not found: {launcher_path}")
    
    # Base PyInstaller command
    cmd = [
        python_executable,
        "-m",
        "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--noconsole",
        "--clean",
        "--add-data", f"{ICON_FILE}{os.pathsep}.",
        "launcher.py"
    ]
    
    # Add platform-specific options
    if OS == "windows":
        cmd.extend([
            "--icon", f"{APP_NAME}{ICON_EXTENSION}",
            "--version-file", "version_info.txt",
            "--add-binary", f"git-2.43.0-64-bit.exe{os.pathsep}."
        ])
    elif OS == "linux":
        cmd.extend([
            "--icon", ICON_FILE
        ])
    
    # Print command for debugging
    logging.info("Running PyInstaller command:")
    logging.info(" ".join(cmd))
    
    # Run PyInstaller with detailed error output
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=current_dir  # Set working directory
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed with error code: {e.returncode}")
        logging.error("Build output:")
        logging.error(e.stdout)
        logging.error("Build errors:")
        logging.error(e.stderr)
        raise
    
    logging.info("Build completed successfully")
    
    # Make executable on Linux
    if OS == "linux":
        executable_path = os.path.join("dist", APP_NAME)
        if os.path.exists(executable_path):
            os.chmod(executable_path, 0o755)
            logging.info(f"Set executable permissions on {executable_path}")
        else:
            logging.warning(f"Executable not found at {executable_path}")

def create_version_info():
    """Create version info file for Windows."""
    if OS == "windows":
        version_info = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{AUTHOR}'),
           StringStruct(u'FileDescription', u'{DESCRIPTION}'),
           StringStruct(u'FileVersion', u'{VERSION}'),
           StringStruct(u'InternalName', u'{APP_NAME}'),
           StringStruct(u'LegalCopyright', u'Copyright (c) 2024 {AUTHOR}'),
           StringStruct(u'OriginalFilename', u'{APP_NAME}{EXECUTABLE_EXTENSION}'),
           StringStruct(u'ProductName', u'{APP_NAME}'),
           StringStruct(u'ProductVersion', u'{VERSION}')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        with open("version_info.txt", "w") as f:
            f.write(version_info)
        logging.info("Version info file created")

def download_dependencies():
    """Download required dependencies for the build."""
    dependencies = {
        "windows": {
            "git": "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        }
    }
    
    for os_name, deps in dependencies.items():
        if os_name == OS:
            for name, url in deps.items():
                output_file = f"{name}{'.exe' if os_name == 'windows' else '.deb'}"
                if not os.path.exists(output_file):
                    logging.info(f"Downloading {name}...")
                    try:
                        # Use wget for all downloads
                        subprocess.run(
                            ["wget", "--no-verbose", "--show-progress", url, "-O", output_file],
                            check=True,
                            capture_output=True
                        )
                        
                        # Verify the downloaded file
                        if os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            if file_size == 0:
                                raise Exception(f"Downloaded file {output_file} is empty")
                            logging.info(f"Successfully downloaded {output_file} (size: {file_size} bytes)")
                        else:
                            raise FileNotFoundError(f"Download completed but file not found: {output_file}")
                            
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Failed to download {name}: {e.stderr}")
                        raise
                    except Exception as e:
                        logging.error(f"Unexpected error downloading {name}: {str(e)}")
                        raise

def main():
    """Main build process"""
    try:
        logging.info("Starting build process...")
        
        # Clean previous build
        clean_build()
        
        # Check and install dependencies (this will create the virtual environment)
        check_dependencies()
        
        # Verify virtual environment exists
        if not os.path.exists(VENV_PYTHON):
            raise FileNotFoundError(f"Virtual environment Python not found at {VENV_PYTHON}")
        
        # Download required files first
        logging.info("Downloading required dependencies...")
        download_dependencies()
        
        # Convert icon for Windows
        if OS == "windows":
            convert_icon()
        
        # Create version info for Windows
        if OS == "windows":
            create_version_info()
        
        # Build executable
        build_executable()
        
        logging.info("Build completed successfully!")
        
    except Exception as e:
        logging.error(f"Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()