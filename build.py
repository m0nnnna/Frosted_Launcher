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
import time
import urllib.request
import ssl

# Set up logging
def setup_logging():
    """Set up logging with unique log file for each run."""
    try:
        # Generate a unique log file name using timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = f'build_{timestamp}.log'
        
        # Set up new logging configuration with unique file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logging.info(f"Logging to file: {log_file}")
        return
    except Exception as e:
        # If file logging fails, fall back to console-only logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logging.warning(f"Could not set up file logging: {str(e)}. Logging to console only.")

# Call setup_logging instead of direct logging.basicConfig
setup_logging()

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
    VENV_PYTHON = os.path.join("venv", "Scripts", "python.exe")
    VENV_PIP = os.path.join("venv", "Scripts", "pip.exe")
else:
    EXECUTABLE_EXTENSION = ""
    ICON_EXTENSION = ".png"
    VENV_PYTHON = os.path.join("venv", "bin", "python")
    VENV_PIP = os.path.join("venv", "bin", "pip")

def create_virtual_environment():
    """Create a virtual environment for building."""
    if not os.path.exists("venv"):
        logging.info("Creating virtual environment...")
        try:
            # Use system Python for virtual environment creation
            system_python = sys.executable
            
            logging.info(f"Using system Python: {system_python}")
            
            # Remove existing venv directory if it exists
            if os.path.exists("venv"):
                shutil.rmtree("venv")
            
            # Create virtual environment using system Python
            subprocess.run(
                [system_python, "-m", "venv", "venv"],
                check=True,
                capture_output=True
            )
            
            # Wait a moment for the filesystem to sync
            time.sleep(1)
            
            # Verify virtual environment was created
            if not os.path.exists(VENV_PYTHON):
                raise FileNotFoundError(f"Virtual environment Python not found at {VENV_PYTHON}")
            
            # Make sure the Python executable is executable (Unix-like systems only)
            if OS != "windows":
                os.chmod(VENV_PYTHON, 0o755)
            
            # Upgrade pip in the virtual environment using python -m pip
            subprocess.run(
                [VENV_PYTHON, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True
            )
            
            logging.info("Virtual environment setup complete")
            logging.info(f"Virtual environment Python path: {VENV_PYTHON}")
            logging.info(f"Virtual environment exists: {os.path.exists(VENV_PYTHON)}")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Virtual environment setup failed: {e.stderr}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during virtual environment setup: {str(e)}")
            raise
    else:
        logging.info("Virtual environment already exists")
        if not os.path.exists(VENV_PYTHON):
            logging.error(f"Virtual environment exists but Python not found at {VENV_PYTHON}")
            raise FileNotFoundError(f"Virtual environment Python not found at {VENV_PYTHON}")
        logging.info(f"Using existing virtual environment at {VENV_PYTHON}")

def check_dependencies():
    """Check if required build dependencies are installed."""
    try:
        # Create virtual environment first
        create_virtual_environment()
        
        # Install dependencies in virtual environment using python -m pip
        required_packages = [
            "pyinstaller",
            "pillow",
            "requests"
        ]
        
        for package in required_packages:
            logging.info(f"Installing {package}...")
            subprocess.run(
                [VENV_PYTHON, "-m", "pip", "install", package],
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
    dirs_to_clean = ['build', 'dist']
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
    # Get absolute paths
    current_dir = os.path.abspath(os.path.dirname(__file__))
    icon_path = os.path.join(current_dir, ICON_FILE)
    launcher_path = os.path.join(current_dir, "launcher.py")
    
    # Verify files exist
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"Icon file not found: {icon_path}")
    if not os.path.exists(launcher_path):
        raise FileNotFoundError(f"Launcher file not found: {launcher_path}")
    
    # Build executable for current platform
    logging.info(f"Building {OS} executable...")
    cmd = [
        VENV_PYTHON,
        "-m",
        "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--noconsole",
        "--clean",
        "--add-data", f"{ICON_FILE}{os.pathsep}.",
        "--icon", f"{APP_NAME}{ICON_EXTENSION}",
        "--version-file", "version_info.txt",
        "launcher.py"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logging.info(f"Build successful! Executable is in the 'dist' folder as '{APP_NAME}{EXECUTABLE_EXTENSION}'")
    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during build: {str(e)}")
        raise

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
        if os_name == "windows":  # Always download Windows dependencies for cross-compilation
            for name, url in deps.items():
                output_file = f"{name}{'.exe' if os_name == 'windows' else '.deb'}"
                if not os.path.exists(output_file):
                    logging.info(f"Downloading {name}...")
                    try:
                        # Create SSL context that ignores certificate verification
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        # Download the file
                        with urllib.request.urlopen(url, context=context) as response:
                            if response.status != 200:
                                raise Exception(f"Download failed with status code: {response.status}")
                            
                            # Get total size for progress tracking
                            total_size = int(response.headers.get('content-length', 0))
                            block_size = 8192
                            downloaded = 0
                            
                            with open(output_file, 'wb') as f:
                                while True:
                                    buffer = response.read(block_size)
                                    if not buffer:
                                        break
                                    downloaded += len(buffer)
                                    f.write(buffer)
                                    # Log progress
                                    if total_size > 0:
                                        progress = (downloaded / total_size) * 100
                                        logging.info(f"Download progress: {progress:.1f}%")
                        
                        # Verify the downloaded file
                        if os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            if file_size == 0:
                                raise Exception(f"Downloaded file {output_file} is empty")
                            logging.info(f"Successfully downloaded {output_file} (size: {file_size} bytes)")
                        else:
                            raise FileNotFoundError(f"Download completed but file not found: {output_file}")
                            
                    except Exception as e:
                        logging.error(f"Failed to download {name}: {str(e)}")
                        if os.path.exists(output_file):
                            os.remove(output_file)  # Clean up partial download
                        raise
                else:
                    logging.info(f"File already exists: {output_file}")
                    
                # Verify the file is valid
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    if file_size < 1000000:  # Git installer should be at least 1MB
                        logging.error(f"Downloaded file {output_file} is too small ({file_size} bytes)")
                        os.remove(output_file)
                        raise Exception(f"Invalid download: {output_file} is too small")
                    logging.info(f"Verified {output_file} is valid (size: {file_size} bytes)")

def main():
    """Main build process"""
    try:
        logging.info("Starting build process...")
        
        # Check if virtual environment exists and is valid
        if not os.path.exists(VENV_PYTHON):
            logging.info("Virtual environment not found or invalid. Creating new one...")
            create_virtual_environment()
        else:
            logging.info("Using existing virtual environment")
        
        # Clean previous build artifacts
        clean_build()
        
        # Check and install dependencies
        check_dependencies()
        
        # Download required files first
        logging.info("Downloading required dependencies...")
        download_dependencies()
        
        # Create version info file for Windows
        if OS == "windows":
            logging.info("Creating version info file...")
            create_version_info()
        
        # Convert icon for Windows
        if OS == "windows":
            logging.info("Converting icon...")
            convert_icon()
        
        # Verify downloaded files exist and are valid
        required_files = [
            "git.exe",
            ICON_FILE
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"Required file not found: {file}")
            file_size = os.path.getsize(file)
            logging.info(f"Verified file exists: {file} (size: {file_size} bytes)")
        
        # Build executable
        build_executable()
        
        logging.info("Build completed successfully!")
        
    except Exception as e:
        logging.error(f"Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()