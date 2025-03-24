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
            # First, ensure python3-venv is installed
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "python3-venv"],
                check=True,
                capture_output=True
            )
            
            # Use system Python for virtual environment creation
            system_python = "/usr/bin/python3"
            if not os.path.exists(system_python):
                system_python = "/usr/bin/python"
            
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
            
            # Make sure the Python executable is executable
            os.chmod(VENV_PYTHON, 0o755)
            
            # Upgrade pip in the virtual environment
            subprocess.run(
                [VENV_PIP, "install", "--upgrade", "pip"],
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
        # For Linux, try to install required system packages
        if OS == "linux":
            try:
                # Update package lists
                subprocess.run(
                    ["sudo", "apt-get", "update"],
                    check=True,
                    capture_output=True
                )
                
                # Install MinGW and required packages for cross-compilation
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", 
                     "mingw-w64",
                     "mingw-w64-tools",
                     "mingw-w64-x86-64-dev",
                     "python3-pip",
                     "build-essential",
                     "python3-dev"],
                    check=True,
                    capture_output=True
                )
                
                logging.info("MinGW and build dependencies installed successfully")
                
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install MinGW: {e.stderr}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error during MinGW installation: {str(e)}")
                raise
        
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
    
    # Build Linux executable
    logging.info("Building Linux executable...")
    linux_cmd = [
        VENV_PYTHON,
        "-m",
        "PyInstaller",
        "--name", f"{APP_NAME}_linux",
        "--onefile",
        "--noconsole",
        "--clean",
        "--add-data", f"{ICON_FILE}{os.pathsep}.",
        "--icon", f"{APP_NAME}{ICON_EXTENSION}",
        "--version-file", "version_info.txt",
        "--add-binary", f"git.exe{os.pathsep}.",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        "launcher.py"
    ]
    
    # Build Windows executable
    logging.info("Building Windows executable...")
    if OS == "linux":
        # For Linux, use MinGW for cross-compilation
        # Set up cross-compilation environment
        os.environ["CC"] = "x86_64-w64-mingw32-gcc"
        os.environ["CXX"] = "x86_64-w64-mingw32-g++"
        os.environ["PYTHONPATH"] = os.pathsep.join([os.getcwd(), os.environ.get("PYTHONPATH", "")])
        
        # Convert icon for Windows
        convert_icon()
        
        # Create version info for Windows
        create_version_info()
        
        windows_cmd = [
            VENV_PYTHON,
            "-m",
            "PyInstaller",
            "--name", f"{APP_NAME}_windows",
            "--onefile",
            "--noconsole",
            "--clean",
            "--add-data", f"{ICON_FILE}{os.pathsep}.",
            "--icon", f"{APP_NAME}{ICON_EXTENSION}",
            "--version-file", "version_info.txt",
            "--add-binary", f"git.exe{os.pathsep}.",
            "--target-architecture", "x86_64",
            "--distpath", "dist",
            "--workpath", "build",
            "--specpath", ".",
            "launcher.py"
        ]
    else:
        # For Windows, use local Python
        python_executable = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
        windows_cmd = [
            python_executable,
            "-m",
            "PyInstaller",
            "--name", f"{APP_NAME}_windows",
            "--onefile",
            "--noconsole",
            "--clean",
            "--add-data", f"{ICON_FILE}{os.pathsep}.",
            "--icon", f"{APP_NAME}{ICON_EXTENSION}",
            "--version-file", "version_info.txt",
            "--add-binary", f"git.exe{os.pathsep}.",
            "launcher.py"
        ]
    
    # Build Linux executable
    try:
        logging.info("Running Linux build command:")
        logging.info(" ".join(linux_cmd))
        result = subprocess.run(
            linux_cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=current_dir
        )
        logging.info("Linux build output:")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Linux build failed: {e.stderr}")
        raise
    
    # Build Windows executable
    try:
        logging.info("Running Windows build command:")
        logging.info(" ".join(windows_cmd))
        result = subprocess.run(
            windows_cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=current_dir
        )
        logging.info("Windows build output:")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Windows build failed: {e.stderr}")
        raise
    
    # Verify both executables were created
    linux_executable = os.path.join("dist", f"{APP_NAME}_linux")
    windows_executable = os.path.join("dist", f"{APP_NAME}_windows")
    
    if not os.path.exists(linux_executable):
        raise FileNotFoundError(f"Linux executable not created at {linux_executable}")
    if not os.path.exists(windows_executable):
        raise FileNotFoundError(f"Windows executable not created at {windows_executable}")
    
    # Rename Windows executable to add .exe extension
    windows_exe = windows_executable + ".exe"
    if os.path.exists(windows_exe):
        os.remove(windows_exe)
    os.rename(windows_executable, windows_exe)
    
    # Set permissions for Linux executable
    os.chmod(linux_executable, 0o755)
    
    logging.info(f"Build completed successfully. Created:")
    logging.info(f"Linux executable: {linux_executable}")
    logging.info(f"Windows executable: {windows_exe}")

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
                        # First try with wget
                        try:
                            result = subprocess.run(
                                ["wget", "--no-verbose", "--show-progress", url, "-O", output_file],
                                check=True,
                                capture_output=True,
                                text=True
                            )
                        except subprocess.CalledProcessError as e:
                            logging.warning(f"wget failed, trying curl: {e.stderr}")
                            # If wget fails, try curl
                            result = subprocess.run(
                                ["curl", "-L", url, "-o", output_file],
                                check=True,
                                capture_output=True,
                                text=True
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
                        if os.path.exists(output_file):
                            os.remove(output_file)  # Clean up partial download
                        raise
                    except Exception as e:
                        logging.error(f"Unexpected error downloading {name}: {str(e)}")
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