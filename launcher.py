"""
SnowCaller Launcher - A modern, frost-themed game launcher with installation capabilities.
This module provides a GUI for managing game installation, saves, and launching the game.
"""

import os
import platform
import subprocess
import sys
import urllib.request
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import time
import shutil
import logging
from pathlib import Path
import json
from datetime import datetime
import random
import math
import hashlib
import ssl
from tkinter import Canvas, PhotoImage
import webbrowser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('launcher.log'),
        logging.StreamHandler()
    ]
)

# Detect the operating system
OS = platform.system().lower()
CONFIG_FILE_NAME = "launcher_config.txt"
ICON_FILE = "1.png"
STATS_FILE = "game_stats.json"

# Modern color theme
COLORS = {
    'primary': '#4FC3F7',      # Light blue
    'secondary': '#29B6F6',    # Medium blue
    'background': '#E3F2FD',   # Very light blue
    'text': '#1565C0',         # Dark blue
    'error': '#EF5350',        # Red
    'success': '#26A69A',      # Teal
    'frost': '#B3E5FC',        # Very light blue
    'ice': '#E1F5FE',          # Almost white blue
    'snow': '#FFFFFF',         # Pure white
    'dark_accent': '#0D47A1',  # Deep blue
    'button_hover': '#03A9F4', # Bright blue
    'shadow': '#BBDEFB'        # Light blue shadow
}

# Modern styling
STYLES = {
    'button': {
        'fg': COLORS['snow'],
        'font': ('Helvetica', 11),
        'padx': 25,
        'pady': 12,
        'relief': 'flat',
        'borderwidth': 0,
        'cursor': 'hand2'
    },
    'label': {
        'font': ('Helvetica', 11),
        'fg': COLORS['text']
    },
    'title': {
        'font': ('Helvetica', 18, 'bold'),
        'fg': COLORS['dark_accent']
    },
    'subtitle': {
        'font': ('Helvetica', 14, 'bold'),
        'fg': COLORS['text']
    },
    'stats': {
        'font': ('Helvetica', 12),
        'fg': COLORS['text']
    }
}

class FrostButton(tk.Button):
    """A modern button with frost effect animation."""
    def __init__(self, master, **kwargs):
        self.hover_bg = kwargs.pop('hover_bg', COLORS['button_hover']) 
        super().__init__(master, **kwargs)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
        # Configure button appearance
        self.configure(
            bg=COLORS['primary'],
            fg=COLORS['snow'],
            font=('Helvetica', 11, 'bold'),
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=12,
            activebackground=COLORS['secondary'],
            activeforeground=COLORS['snow'],
            cursor='hand2'
        )
        
    def on_enter(self, event):
        self.config(bg=self.hover_bg)
        
    def on_leave(self, event):
        self.config(bg=COLORS['primary'])

class SnowflakeCanvas(Canvas):
    """Canvas with animated snowflakes"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=COLORS['background'], highlightthickness=0)
        self.snowflakes = []
        self.animation_ids = []
        self.create_snowflakes()
        
    def create_snowflakes(self):
        """Create the snowflake particles"""
        width = self.winfo_width() or 500
        height = self.winfo_height() or 500
        
        for _ in range(30):
            x = random.randint(0, width)
            y = random.randint(-50, height)
            size = random.randint(2, 5)
            speed = random.uniform(1, 3)
            snowflake = self.create_oval(
                x, y, x+size, y+size,
                fill=COLORS['snow'],
                outline=COLORS['snow']
            )
            self.snowflakes.append({
                'id': snowflake,
                'speed': speed,
                'drift': random.uniform(-0.5, 0.5)
            })
        
        self.animate_snowflakes()
    
    def animate_snowflakes(self):
        """Animate the snowflakes falling with slight drift"""
        width = self.winfo_width() or 500
        height = self.winfo_height() or 500
        
        for snowflake in self.snowflakes:
            # Move snowflake down and with a slight drift
            self.move(snowflake['id'], snowflake['drift'], snowflake['speed'])
            
            # Get current position
            pos = self.coords(snowflake['id'])
            if not pos:
                continue
                
            if pos[1] > height or pos[0] < 0 or pos[0] > width:
                # Reset position when out of bounds
                size = pos[2] - pos[0]
                new_x = random.randint(0, width)
                self.coords(
                    snowflake['id'],
                    new_x, -size,
                    new_x + size, 0
                )
                # Randomize drift for variation
                snowflake['drift'] = random.uniform(-0.5, 0.5)
        
        # Schedule next animation frame
        anim_id = self.after(50, self.animate_snowflakes)
        self.animation_ids.append(anim_id)
    
    def stop_animations(self):
        """Clean up all animations"""
        for anim_id in self.animation_ids:
            self.after_cancel(anim_id)
        self.animation_ids.clear()

class FrostFrame(tk.Frame):
    """A modern frame with frost/snow theme"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=COLORS['background'])
        
        # Create snowflake background
        self.canvas = SnowflakeCanvas(self)
        self.canvas.place(relwidth=1, relheight=1)
        
        # Create content frame over the canvas
        self.content = tk.Frame(self, bg=COLORS['background'])
        self.content.place(relwidth=1, relheight=1)
        
        # Ensure the frame is properly configured
        self.update_idletasks()
        self.lift()
        self.focus_force()
    
    def cleanup(self):
        """Stop animations and clean up resources"""
        if hasattr(self, 'canvas'):
            self.canvas.stop_animations()

# Utility functions
def get_base_dir():
    """Get the base directory for the config file, handling PyInstaller."""
    if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
        return os.path.dirname(sys.executable)
    else:  # Running as script
        return os.path.abspath(os.path.dirname(__file__))

def get_resource_path(relative_path):
    """Get the path to bundled resources (e.g., icon) in PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def check_command(command):
    """Check if a command exists in the system."""
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def read_config(base_dir=None):
    """Read the install directory from config file if it exists."""
    if base_dir:
        config_path = os.path.join(base_dir, "snowcaller", CONFIG_FILE_NAME)
        logging.info(f"Checking config at: {config_path}")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                lines = f.readlines()
                if lines and lines[0].startswith("install_dir="):
                    saved_dir = lines[0].split("=", 1)[1].strip()
                    logging.info(f"Found config with install_dir: {saved_dir}")
                    if os.path.exists(saved_dir) and os.path.exists(os.path.join(saved_dir, "snowcaller")):
                        return saved_dir
        else:
            logging.info(f"Config file not found at: {config_path}")
    return None

def write_config(install_dir):
    """Write the install directory to config file in the launcher's directory."""
    base_dir = get_base_dir()
    config_dir = os.path.join(base_dir, "snowcaller")
    config_path = os.path.join(config_dir, CONFIG_FILE_NAME)
    logging.info(f"Writing config to: {config_path}")
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    with open(config_path, 'w') as f:
        f.write(f"install_dir={install_dir}")

def create_desktop_icon(install_dir):
    """Create a .desktop file on the Desktop for Linux."""
    if OS != "linux":
        return
    
    base_dir = get_base_dir()
    executable_path = os.path.join(base_dir, "SnowCallerLauncher")
    icon_source = get_resource_path(ICON_FILE)
    icon_dir = os.path.expanduser("~/.snowcaller")
    icon_dest = os.path.join(icon_dir, "snowcaller.png")
    desktop_dest = os.path.expanduser("~/Desktop/snowcaller.desktop")

    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    
    if os.path.exists(icon_source) and not os.path.exists(icon_dest):
        shutil.copy(icon_source, icon_dest)
    else:
        logging.warning(f"Icon source not found: {icon_source}")

    desktop_content = f"""[Desktop Entry]
Name=SnowCaller
Exec={executable_path}
Type=Application
Icon={icon_dest}
Terminal=false
Categories=Game;
Comment=Launch the SnowCaller game
"""
    with open(desktop_dest, 'w') as f:
        f.write(desktop_content)
    
    os.chmod(desktop_dest, 0o755)

def update_progress(progress_bar, label, value, text):
    """Update the progress bar and label."""
    if progress_bar:
        progress_bar['value'] = value
    if label:
        label.config(text=text)
    if progress_bar:
        progress_bar.update()

def verify_download(url, file_path):
    """Verify the downloaded file using checksum."""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=context) as response:
            if response.status != 200:
                raise Exception(f"Download failed with status code: {response.status}")
            
            # Read the file in chunks to handle large files
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Download verification failed: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

def download_file(url, file_path, progress_callback=None):
    """Download a file with progress tracking and verification."""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=context) as response:
            if response.status != 200:
                raise Exception(f"Download failed with status code: {response.status}")
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress)
        
        return True
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

def install_python(progress_bar, label):
    """Install Python based on the OS with improved error handling."""
    update_progress(progress_bar, label, 10, "Installing Python...")
    try:
        if OS == "windows":
            url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
            installer = "python_installer.exe"
            
            def update_progress_bar(progress):
                progress_bar['value'] = 10 + (progress * 0.2)  # 10-30%
                label.config(text=f"Downloading Python... {progress:.1f}%")
                progress_bar.update()
            
            download_file(url, installer, update_progress_bar)
            
            # Run Python installer with appropriate flags
            result = subprocess.run(
                f"{installer} /quiet InstallAllUsers=1 PrependPath=1",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Python installation failed: {result.stderr}")
            
            if os.path.exists(installer):
                os.remove(installer)
                
            # Update PATH environment variable for this process
            os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]
            
            # Verify Python installation
            if not check_command("python --version"):
                raise Exception("Python installation verification failed")
                
        elif OS == "linux":
            # Check if Python is already installed
            if check_command("python3 --version"):
                update_progress(progress_bar, label, 30, "Python already installed.")
                return
                
            # Check if user has sudo privileges
            if os.geteuid() != 0:
                if not messagebox.askyesno(
                    "Permission Required",
                    "This operation requires sudo privileges. Would you like to continue?"
                ):
                    raise Exception("User cancelled sudo operation")
            
            result = subprocess.run(
                "sudo apt update && sudo apt install -y python3.11 python3-pip",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Python installation failed: {result.stderr}")
            
            # Verify Python installation
            if not check_command("python3 --version"):
                raise Exception("Python installation verification failed")
        
        update_progress(progress_bar, label, 30, "Python installed successfully.")
        
    except Exception as e:
        logging.error(f"Python installation failed: {str(e)}")
        raise

def install_git(progress_bar, label):
    """Install Git based on the OS with improved error handling."""
    update_progress(progress_bar, label, 40, "Installing Git...")
    try:
        # First check if Git is already installed
        if check_command("git --version"):
            update_progress(progress_bar, label, 60, "Git already installed.")
            return
            
        if OS == "windows":
            url = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
            installer = "git_installer.exe"
            
            def update_progress_bar(progress):
                progress_bar['value'] = 40 + (progress * 0.2)  # 40-60%
                label.config(text=f"Downloading Git... {progress:.1f}%")
                progress_bar.update()
            
            download_file(url, installer, update_progress_bar)
            
            result = subprocess.run(
                f"{installer} /SILENT /NORESTART",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Git installation failed: {result.stderr}")
            
            if os.path.exists(installer):
                os.remove(installer)
            
            # Update PATH environment variable for this process
            os.environ["PATH"] = "C:\\Program Files\\Git\\cmd" + os.pathsep + os.environ["PATH"]
            
            # Verify Git installation
            if not check_command("git --version"):
                raise Exception("Git installation verification failed")
                
        elif OS == "linux":
            if os.geteuid() != 0:
                if not messagebox.askyesno(
                    "Permission Required",
                    "This operation requires sudo privileges. Would you like to continue?"
                ):
                    raise Exception("User cancelled sudo operation")
            
            result = subprocess.run(
                "sudo apt update && sudo apt install -y git",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Git installation failed: {result.stderr}")
            
            # Verify Git installation
            if not check_command("git --version"):
                raise Exception("Git installation verification failed")
        
        update_progress(progress_bar, label, 60, "Git installed successfully.")
        
    except Exception as e:
        logging.error(f"Git installation failed: {str(e)}")
        raise

def install_requests(progress_bar, label):
    """Install the requests module with improved error handling."""
    update_progress(progress_bar, label, 70, "Installing requests module...")
    try:
        python_cmd = "python" if OS == "windows" else "python3"
        
        # Check if requests is already installed
        check_cmd = f"{python_cmd} -c \"import requests; print('Module exists')\""
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if "Module exists" in result.stdout:
            update_progress(progress_bar, label, 80, "Requests module already installed.")
            return
            
        if OS == "linux":
            # On Debian, use apt to install python3-requests
            if os.geteuid() != 0:
                if not messagebox.askyesno(
                    "Permission Required",
                    "This operation requires sudo privileges. Would you like to continue?"
                ):
                    raise Exception("User cancelled sudo operation")
            
            result = subprocess.run(
                "sudo apt update && sudo apt install -y python3-requests",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Fall back to pip if apt install fails
                result = subprocess.run(
                    f"{python_cmd} -m pip install --user requests",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise Exception(f"Requests installation failed: {result.stderr}")
        else:
            # On Windows, use pip
            result = subprocess.run(
                f"{python_cmd} -m pip install requests",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Requests installation failed: {result.stderr}")
        
        # Verify requests installation
        result = subprocess.run(
            f"{python_cmd} -c 'import requests'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception("Requests installation verification failed")
        
        update_progress(progress_bar, label, 80, "Requests module installed successfully.")
        
    except Exception as e:
        logging.error(f"Requests installation failed: {str(e)}")
        raise

def setup_game(progress_bar, label, install_dir):
    """Clone the repo and prepare the game with improved error handling."""
    update_progress(progress_bar, label, 90, "Downloading SnowCaller...")
    try:
        # Create target directory if it doesn't exist
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
            
        os.chdir(install_dir)
        
        if not os.path.exists("snowcaller"):
            result = subprocess.run(
                "git clone https://github.com/m0nnnna/snowcaller.git",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Git clone output: {result.stdout}")
                logging.error(f"Git clone error: {result.stderr}")
                raise Exception(f"Git clone failed: {result.stderr}")
        
        # Change to game directory to verify files
        os.chdir("snowcaller")
        
        # Verify game files
        required_files = ["game.py"]
        for file in required_files:
            if not os.path.exists(file):
                raise Exception(f"Required game file not found: {file}")
        
        update_progress(progress_bar, label, 100, "SnowCaller installed successfully!")
        time.sleep(1)  # Brief pause to show completion
        
    except Exception as e:
        logging.error(f"Game setup failed: {str(e)}")
        raise

def launch_game(install_dir, root):
    """Launch the game directly and close the launcher."""
    game_dir = os.path.join(install_dir, "snowcaller")
    python_cmd = "python" if OS == "windows" else "python3"
    game_script = os.path.join(game_dir, "game.py")

    if not os.path.exists(game_dir) or not os.path.exists(game_script):
        messagebox.showerror("Error", f"Game directory or script not found: {game_script}")
        return False

    # Start time tracking
    start_time = time.time()
    
    def on_game_exit():
        # Calculate time played
        time_played = int(time.time() - start_time)
        update_stats(time_played=time_played)
        root.quit()
        root.destroy()

    try:
        if OS == "windows":
            cmd = [python_cmd, "game.py"]
            logging.info(f"Launching game with: {' '.join(cmd)} in {game_dir}")
            
            # Run the game in the current process environment, non-blocking
            process = subprocess.Popen(cmd, cwd=game_dir, shell=False)
            
            # Monitor the process
            def check_process():
                if process.poll() is not None:
                    on_game_exit()
                else:
                    root.after(1000, check_process)
                    
            root.after(1000, check_process)
            return True
            
        elif OS == "linux":  # Debian (GNOME, XFCE, KDE)
            terminals = [
                ("gnome-terminal", f'gnome-terminal -- bash -c "cd {game_dir} && {python_cmd} game.py; exec bash"'),
                ("xfce4-terminal", f'xfce4-terminal --command "bash -c \'cd {game_dir} && {python_cmd} game.py; exec bash\'"'),
                ("konsole", f'konsole --noclose -e bash -c "cd {game_dir} && {python_cmd} game.py; exec bash"'),
                ("xterm", f'xterm -e "cd {game_dir} && {python_cmd} game.py; exec bash"')  # Fallback
            ]
            
            for term, cmd in terminals:
                if check_command(f"{term} --version"):
                    process = subprocess.Popen(cmd, shell=True)
                    
                    # Monitor the process
                    def check_process():
                        if process.poll() is not None:
                            on_game_exit()
                        else:
                            root.after(1000, check_process)
                            
                    root.after(1000, check_process)
                    return True
            
            # If no terminal was found
            messagebox.showerror(
                "Error", 
                "No supported terminal found (gnome-terminal, xfce4-terminal, konsole, xterm)."
            )
            return False
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch game: {str(e)}")
        logging.error(f"Launch failed: {str(e)}")
        return False

def load_stats():
    """Load game statistics from JSON file."""
    stats_file = os.path.join(get_base_dir(), STATS_FILE)
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'total_deaths': 0, 'total_time': 0, 'last_session': None}
    return {'total_deaths': 0, 'total_time': 0, 'last_session': None}

def save_stats(stats):
    """Save game statistics to JSON file."""
    stats_file = os.path.join(get_base_dir(), STATS_FILE)
    with open(stats_file, 'w') as f:
        json.dump(stats, f)

def update_stats(deaths=0, time_played=0):
    """Update game statistics."""
    stats = load_stats()
    stats['total_deaths'] += deaths
    stats['total_time'] += time_played
    stats['last_session'] = datetime.now().isoformat()
    save_stats(stats)

def format_time(seconds):
    """Format time in seconds to human readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

def delete_save(install_dir):
    """Delete save.json in the snowcaller folder if it exists and update stats."""
    save_file = os.path.join(install_dir, "snowcaller", "save.json")
    if os.path.exists(save_file):
        try:
            os.remove(save_file)
            update_stats(deaths=1)  # Increment death counter
            messagebox.showinfo("Delete Save", "Save file deleted and death recorded.")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete save file: {str(e)}")
            return False
    else:
        messagebox.showinfo("Delete Save", "No save file found.")
        return False

class ModernDialog(tk.Toplevel):
    """Base class for modern dialog windows"""
    def __init__(self, parent, title, width=400, height=200):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(bg=COLORS['background'])
        self.transient(parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Style
        self.content_frame = tk.Frame(self, bg=COLORS['background'], padx=20, pady=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Set icon
        icon_path = get_resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            try:
                self.iconphoto(True, tk.PhotoImage(file=icon_path))
            except Exception as e:
                logging.error(f"Failed to load icon: {str(e)}")

class ErrorDialog(ModernDialog):
    """Modern error dialog"""
    def __init__(self, parent, title, message):
        super().__init__(parent, title, width=450, height=200)
        
        tk.Label(
            self.content_frame,
            text=message,
            wraplength=400,
            bg=COLORS['background'],
            fg=COLORS['error'],
            font=('Helvetica', 11),
            pady=15
        ).pack(expand=True)
        
        FrostButton(
            self.content_frame,
            text="OK",
            command=self.destroy,
            width=15
        ).pack(pady=10)

class ProgressDialog(ModernDialog):
    """Modern progress dialog"""
    def __init__(self, parent, title):
        super().__init__(parent, title, width=450, height=220)
        
        self.title_label = tk.Label(
            self.content_frame,
            text=title,
            bg=COLORS['background'],
            **STYLES['subtitle']
        )
        self.title_label.pack(pady=10)
        
        self.status_label = tk.Label(
            self.content_frame,
            text="Starting...",
            bg=COLORS['background'],
            **STYLES['label']
        )
        self.status_label.pack(pady=10)
        
        self.progress_frame = tk.Frame(self.content_frame, bg=COLORS['background'])
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        # Custom style for progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            'Modern.Horizontal.TProgressbar',
            troughcolor=COLORS['background'],
            background=COLORS['primary'],
            thickness=12,
            borderwidth=0
        )
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            style='Modern.Horizontal.TProgressbar',
            orient='horizontal',
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=5, padx=5, fill=tk.X)
        
    def update_progress(self, value, text):
        """Update progress bar and text"""
        self.progress_bar['value'] = value
        self.status_label.config(text=text)
        self.update()

class LauncherApp:
    """Main launcher application"""
    def __init__(self, root):
        self.root = root
        
        # Main frame with frost effect
        self.frost_frame = FrostFrame(self.root)
        self.frost_frame.pack(fill=tk.BOTH, expand=True)
        
        # Check for existing installation
        self.base_dir = get_base_dir()
        self.install_dir = read_config(self.base_dir)
        
        if self.install_dir:
            self.show_launcher_menu()
        else:
            self.show_welcome_screen()
            
        # Cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set icon
        icon_path = get_resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
            except Exception as e:
                logging.error(f"Failed to load icon: {str(e)}")
    
    def center_window(self):
        """Center the application window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.lift()  # Bring window to front
        self.root.focus_force()  # Force focus on the window
    
    def show_welcome_screen(self):
        """Show the welcome screen with installation options"""
        # Clear the content frame
        for widget in self.frost_frame.content.winfo_children():
            widget.destroy()
            
        # Logo or title
        tk.Label(
            self.frost_frame.content,
            text="SnowCaller",
            bg=COLORS['background'],
            fg=COLORS['dark_accent'],
            font=('Helvetica', 24, 'bold')
        ).pack(pady=(60, 10))
        
        tk.Label(
            self.frost_frame.content,
            text="A modern, frost-themed adventure game",
            bg=COLORS['background'],
            fg=COLORS['text'],
            font=('Helvetica', 12)
        ).pack(pady=(0, 40))
        
        # Welcome message
        message_frame = tk.Frame(self.frost_frame.content, bg=COLORS['frost'], padx=20, pady=20)
        message_frame.pack(fill=tk.X, padx=40, pady=20)
        
        tk.Label(
            message_frame,
            text="Welcome to SnowCaller!",
            bg=COLORS['frost'],
            fg=COLORS['dark_accent'],
            font=('Helvetica', 14, 'bold')
        ).pack(pady=(0, 10))
        
        tk.Label(
            message_frame,
            text="This launcher will help you install and play the game.\nWould you like to install SnowCaller now?",
            bg=COLORS['frost'],
            fg=COLORS['text'],
            font=('Helvetica', 11),
            justify=tk.CENTER
        ).pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.frost_frame.content, bg=COLORS['background'])
        button_frame.pack(pady=30)
        
        FrostButton(
            button_frame,
            text="Install Game",
            command=self.start_installation,
            width=20
        ).pack(pady=10)
        
        FrostButton(
            button_frame,
            text="Exit",
            command=self.on_closing,
            width=20,
            bg=COLORS['secondary']
        ).pack(pady=10)
        
    def start_installation(self):
        """Start the installation process"""
        install_dir = filedialog.askdirectory(
            title="Select where to install SnowCaller"
        )
        
        if not install_dir:
            messagebox.showinfo("Installation", "Installation cancelled.")
            return
            
        # Create progress dialog
        progress_dialog = ProgressDialog(self.root, "Installing SnowCaller")
        
        # Run installation in thread
        def run_installation():
            try:
                python_cmd = "python" if OS == "windows" else "python3"
                if not check_command(f"{python_cmd} --version"):
                    install_python(progress_dialog.progress_bar, progress_dialog.status_label)
                    
                if not check_command("git --version"):
                    install_git(progress_dialog.progress_bar, progress_dialog.status_label)
                    
                install_requests(progress_dialog.progress_bar, progress_dialog.status_label)
                setup_game(progress_dialog.progress_bar, progress_dialog.status_label, install_dir)
                
                # Save config
                write_config(install_dir)
                if OS == "linux":
                    create_desktop_icon(install_dir)
                    
                # Update instance variable
                self.install_dir = install_dir
                
                # Close progress dialog and show menu
                progress_dialog.destroy()
                self.show_launcher_menu()
                
            except Exception as e:
                logging.error(f"Installation failed: {str(e)}")
                progress_dialog.destroy()
                ErrorDialog(self.root, "Installation Error", 
                           f"Failed to complete installation: {str(e)}\n\nSee launcher.log for details.")
        
        threading.Thread(target=run_installation, daemon=True).start()
    
    def show_launcher_menu(self):
        """Show the main launcher menu"""
        # Clear the content frame
        for widget in self.frost_frame.content.winfo_children():
            widget.destroy()
            
        # Header with logo/title
        tk.Label(
            self.frost_frame.content,
            text="SnowCaller",
            bg=COLORS['background'],
            fg=COLORS['dark_accent'],
            font=('Helvetica', 24, 'bold')
        ).pack(pady=(40, 5))
        
        tk.Label(
            self.frost_frame.content,
            text="Game Launcher",
            bg=COLORS['background'],
            fg=COLORS['text'],
            font=('Helvetica', 12)
        ).pack(pady=(0, 30))
        
        # Stats section
        stats_frame = tk.Frame(self.frost_frame.content, bg=COLORS['frost'], padx=25, pady=20)
        stats_frame.pack(fill=tk.X, padx=40, pady=10)
        
        stats = load_stats()
        
        tk.Label(
            stats_frame,
            text="Game Statistics",
            bg=COLORS['frost'],
            fg=COLORS['dark_accent'],
            font=('Helvetica', 14, 'bold')
        ).pack(pady=(0, 15))
        
        # Stats display in a grid
        stats_grid = tk.Frame(stats_frame, bg=COLORS['frost'])
        stats_grid.pack(fill=tk.X)
        
        # Deaths
        death_icon = "☠️"  # Skull emoji
        tk.Label(
            stats_grid, 
            text=death_icon, 
            bg=COLORS['frost'],
            font=('Helvetica', 16)
        ).grid(row=0, column=0, padx=5, pady=5)
        
        tk.Label(
            stats_grid,
            text=f"Total Deaths: {stats['total_deaths']}",
            bg=COLORS['frost'],
            fg=COLORS['text'],
            font=('Helvetica', 12)
        ).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Play time
        time_icon = "⏱️"  # Stopwatch emoji
        tk.Label(
            stats_grid, 
            text=time_icon, 
            bg=COLORS['frost'],
            font=('Helvetica', 16)
        ).grid(row=1, column=0, padx=5, pady=5)
        
        tk.Label(
            stats_grid,
            text=f"Total Play Time: {format_time(stats['total_time'])}",
            bg=COLORS['frost'],
            fg=COLORS['text'],
            font=('Helvetica', 12)
        ).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Last played
        if stats['last_session']:
            calendar_icon = "📅"  # Calendar emoji
            tk.Label(
                stats_grid, 
                text=calendar_icon, 
                bg=COLORS['frost'],
                font=('Helvetica', 16)
            ).grid(row=2, column=0, padx=5, pady=5)
            
            last_played = datetime.fromisoformat(stats['last_session'])
            tk.Label(
                stats_grid,
                text=f"Last Played: {last_played.strftime('%Y-%m-%d %H:%M')}",
                bg=COLORS['frost'],
                fg=COLORS['text'],
                font=('Helvetica', 12)
            ).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # Action buttons
        button_frame = tk.Frame(self.frost_frame.content, bg=COLORS['background'])
        button_frame.pack(pady=30)
        
        play_button = FrostButton(
            button_frame,
            text="Play Game",
            command=self.play_game,
            width=25
        )
        play_button.pack(pady=8)
        
        delete_button = FrostButton(
            button_frame,
            text="Delete Save",
            command=self.delete_save,
            width=25
        )
        delete_button.pack(pady=8)
        
        # Support section
        support_frame = tk.Frame(self.frost_frame.content, bg=COLORS['background'])
        support_frame.pack(pady=(10, 0))
        
        def open_github():
            webbrowser.open("https://github.com/m0nnnna/snowcaller")
        
        support_button = FrostButton(
            support_frame,
            text="Project GitHub",
            command=open_github,
            bg=COLORS['secondary'],
            width=25
        )
        support_button.pack(pady=5)
        
        exit_button = FrostButton(
            support_frame,
            text="Exit",
            command=self.on_closing,
            bg="#64B5F6",  # Lighter blue for exit
            width=25
        )
        exit_button.pack(pady=8)
    
    def play_game(self):
        """Launch the game"""
        if not self.install_dir:
            ErrorDialog(self.root, "Error", "Game installation not found.")
            return
            
        success = launch_game(self.install_dir, self.root)
        if not success:
            # If launch failed but we didn't quit, show an error dialog
            ErrorDialog(self.root, "Launch Error", "Failed to launch the game. Check the logs for details.")
    
    def delete_save(self):
        """Delete save file"""
        if not self.install_dir:
            ErrorDialog(self.root, "Error", "Game installation not found.")
            return
            
        delete_save(self.install_dir)
        
        # Refresh stats display
        self.show_launcher_menu()
    
    def on_closing(self):
        """Clean up and close the app"""
        if hasattr(self, 'frost_frame'):
            self.frost_frame.cleanup()
        self.root.quit()
        self.root.destroy()

def main():
    """Main entry point"""
    # Set up the theme for ttk widgets
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    
    # Create root window
    root = tk.Tk()
    
    # Configure root window
    root.title("SnowCaller Launcher")
    root.geometry("540x600")
    root.resizable(False, False)
    root.configure(bg=COLORS['background'])
    
    # Set icon
    icon_path = get_resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        try:
            root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception as e:
            logging.error(f"Failed to load icon: {str(e)}")
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Create app instance
    app = LauncherApp(root)
    
    # Ensure window is visible and focused
    root.lift()
    root.focus_force()
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
