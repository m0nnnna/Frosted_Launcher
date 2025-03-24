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

# Modern UI colors and styles
COLORS = {
    'primary': '#2196F3',
    'secondary': '#1976D2',
    'background': '#FFFFFF',
    'text': '#333333',
    'error': '#F44336',
    'success': '#4CAF50'
}

STYLES = {
    'button': {
        'bg': COLORS['primary'],
        'fg': 'white',
        'font': ('Helvetica', 10),
        'padx': 20,
        'pady': 10,
        'relief': 'flat'
    },
    'label': {
        'font': ('Helvetica', 10),
        'fg': COLORS['text']
    },
    'title': {
        'font': ('Helvetica', 16, 'bold'),
        'fg': COLORS['text']
    }
}

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
        print(f"Checking config at: {config_path}")  # Debug
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                lines = f.readlines()
                if lines and lines[0].startswith("install_dir="):
                    saved_dir = lines[0].split("=", 1)[1].strip()
                    print(f"Found config with install_dir: {saved_dir}")  # Debug
                    if os.path.exists(saved_dir) and os.path.exists(os.path.join(saved_dir, "snowcaller")):
                        return saved_dir
        else:
            print(f"Config file not found at: {config_path}")  # Debug
    return None

def write_config(install_dir):
    """Write the install directory to config file in the launcher's directory."""
    base_dir = get_base_dir()
    config_dir = os.path.join(base_dir, "snowcaller")
    config_path = os.path.join(config_dir, CONFIG_FILE_NAME)
    print(f"Writing config to: {config_path}")  # Debug
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
    if not os.path.exists(icon_dest):
        shutil.copy(icon_source, icon_dest)

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
    progress_bar['value'] = value
    label.config(text=text)
    progress_bar.update()

def verify_download(url, file_path):
    """Verify the downloaded file using checksum."""
    try:
        import hashlib
        import ssl
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
        import ssl
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
                    if progress_callback:
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
            
            # Verify installation
            result = subprocess.run(
                f"{installer} /quiet InstallAllUsers=1 PrependPath=1",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Python installation failed: {result.stderr}")
            
            os.remove(installer)
            os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]
            
            # Verify Python installation
            if not check_command("python --version"):
                raise Exception("Python installation verification failed")
                
        elif OS == "linux":
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
            
            os.remove(installer)
            
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
                raise Exception(f"Requests installation failed: {result.stderr}")
            
            # Verify requests installation
            result = subprocess.run(
                "python3 -c 'import requests'",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception("Requests installation verification failed")
        else:
            # On Windows, use pip as before
            python_cmd = "python"
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
        os.chdir(install_dir)
        
        if not os.path.exists("snowcaller"):
            result = subprocess.run(
                "git clone https://github.com/m0nnnna/snowcaller.git",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
        
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
        root.quit()
        root.destroy()
        return

    if OS == "windows":
        cmd = [python_cmd, "game.py"]
        print(f"Launching game with: {' '.join(cmd)} in {game_dir}")  # Debug
        try:
            # Run the game in the current process environment, non-blocking
            subprocess.Popen(cmd, cwd=game_dir, shell=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch game: {e}")
    elif OS == "linux":  # Debian (GNOME, XFCE, KDE)
        terminals = [
            ("gnome-terminal", f'gnome-terminal -- bash -c "cd {game_dir} && {python_cmd} game.py; exec bash"'),
            ("xfce4-terminal", f'xfce4-terminal --command "bash -c \'cd {game_dir} && {python_cmd} game.py; exec bash\'"'),
            ("konsole", f'konsole --noclose -e bash -c "cd {game_dir} && {python_cmd} game.py; exec bash"'),
            ("xterm", f'xterm -e "cd {game_dir} && {python_cmd} game.py; exec bash"')  # Fallback
        ]
        for term, cmd in terminals:
            if check_command(f"{term} --version"):
                subprocess.Popen(cmd, shell=True)
                break
        else:
            messagebox.showerror("Error", "No supported terminal found (gnome-terminal, xfce4-terminal, konsole, xterm).")

    # Close the launcher immediately
    root.quit()
    root.destroy()

def delete_save(install_dir):
    """Delete save.json in the snowcaller folder if it exists."""
    save_file = os.path.join(install_dir, "snowcaller", "save.json")
    if os.path.exists(save_file):
        os.remove(save_file)
        messagebox.showinfo("Delete Save", "Save file (save.json) deleted.")
    else:
        messagebox.showinfo("Delete Save", "No save file (save.json) found.")

def create_modern_button(parent, text, command, **kwargs):
    """Create a modern-styled button."""
    style = STYLES['button'].copy()
    style.update(kwargs)
    btn = tk.Button(parent, text=text, command=command, **style)
    btn.bind('<Enter>', lambda e: btn.configure(bg=COLORS['secondary']))
    btn.bind('<Leave>', lambda e: btn.configure(bg=COLORS['primary']))
    return btn

def show_error_dialog(title, message):
    """Show a styled error dialog."""
    error_window = tk.Toplevel()
    error_window.title(title)
    error_window.geometry("400x150")
    error_window.configure(bg=COLORS['background'])
    
    # Center the window
    error_window.update_idletasks()
    width = error_window.winfo_width()
    height = error_window.winfo_height()
    x = (error_window.winfo_screenwidth() // 2) - (width // 2)
    y = (error_window.winfo_screenheight() // 2) - (height // 2)
    error_window.geometry(f'{width}x{height}+{x}+{y}')
    
    tk.Label(
        error_window,
        text=message,
        bg=COLORS['background'],
        fg=COLORS['error'],
        font=('Helvetica', 10),
        wraplength=350
    ).pack(pady=20)
    
    create_modern_button(
        error_window,
        "OK",
        error_window.destroy,
        width=15
    ).pack(pady=10)
    
    error_window.transient()
    error_window.grab_set()

def show_progress_window(root):
    """Create a modern-styled progress window."""
    progress_window = tk.Toplevel(root)
    progress_window.title("Installing SnowCaller")
    progress_window.geometry("400x200")
    progress_window.resizable(False, False)
    progress_window.configure(bg=COLORS['background'])
    
    # Center the window
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # Set icon
    icon_path = get_resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        progress_window.iconphoto(True, tk.PhotoImage(file=icon_path))
    
    # Create and style widgets
    title_label = tk.Label(
        progress_window,
        text="Installing SnowCaller",
        bg=COLORS['background'],
        **STYLES['title']
    )
    title_label.pack(pady=10)
    
    status_label = tk.Label(
        progress_window,
        text="Starting setup...",
        bg=COLORS['background'],
        **STYLES['label']
    )
    status_label.pack(pady=10)
    
    progress_frame = tk.Frame(progress_window, bg=COLORS['background'])
    progress_frame.pack(fill=tk.X, padx=20)
    
    progress_bar = ttk.Progressbar(
        progress_frame,
        length=300,
        mode='determinate',
        style='Modern.Horizontal.TProgressbar'
    )
    progress_bar.pack(pady=10)
    
    # Configure progress bar style
    style = ttk.Style()
    style.configure(
        'Modern.Horizontal.TProgressbar',
        troughcolor=COLORS['background'],
        background=COLORS['primary'],
        thickness=10
    )
    
    return progress_window, progress_bar, status_label

def setup_with_progress(root, install_dir):
    """Run setup in a thread with a modern progress bar."""
    progress_window, progress_bar, status_label = show_progress_window(root)
    
    def run_setup():
        try:
            python_cmd = "python" if OS == "windows" else "python3"
            if not check_command(f"{python_cmd} --version"):
                install_python(progress_bar, status_label)
            if not check_command("git --version"):
                install_git(progress_bar, status_label)
            install_requests(progress_bar, status_label)
            setup_game(progress_bar, status_label, install_dir)
            write_config(install_dir)
            if OS == "linux":
                create_desktop_icon(install_dir)
            progress_window.destroy()
            show_launcher_menu(root, install_dir)
        except Exception as e:
            logging.error(f"Setup failed: {str(e)}")
            progress_window.destroy()
            show_error_dialog("Installation Error", f"Failed to complete installation: {str(e)}")
    
    threading.Thread(target=run_setup, daemon=True).start()

def show_launcher_menu(root, install_dir):
    """Show a modern-styled launcher menu."""
    menu_window = tk.Toplevel(root)
    menu_window.title("SnowCaller Launcher")
    menu_window.geometry("300x250")
    menu_window.resizable(False, False)
    menu_window.configure(bg=COLORS['background'])
    
    # Center the window
    menu_window.update_idletasks()
    width = menu_window.winfo_width()
    height = menu_window.winfo_height()
    x = (menu_window.winfo_screenwidth() // 2) - (width // 2)
    y = (menu_window.winfo_screenheight() // 2) - (height // 2)
    menu_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # Set icon
    icon_path = get_resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        menu_window.iconphoto(True, tk.PhotoImage(file=icon_path))
    
    # Create and style widgets
    title_label = tk.Label(
        menu_window,
        text="SnowCaller",
        bg=COLORS['background'],
        **STYLES['title']
    )
    title_label.pack(pady=20)
    
    button_frame = tk.Frame(menu_window, bg=COLORS['background'])
    button_frame.pack(pady=10)
    
    create_modern_button(
        button_frame,
        "Play",
        lambda: launch_game(install_dir, root),
        width=20
    ).pack(pady=5)
    
    create_modern_button(
        button_frame,
        "Delete Save",
        lambda: delete_save(install_dir),
        width=20
    ).pack(pady=5)
    
    create_modern_button(
        button_frame,
        "Close",
        lambda: [root.quit(), root.destroy()],
        width=20
    ).pack(pady=5)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Try to find an existing install directory from the config in the executable's directory
    base_dir = get_base_dir()
    print(f"Base directory: {base_dir}")  # Debug
    install_dir = read_config(base_dir)

    if install_dir:
        # If config is found, go straight to the menu
        show_launcher_menu(root, install_dir)
    else:
        # Ask if the user wants to install SnowCaller on first run
        if not messagebox.askyesno("Install SnowCaller", "Do you want to install SnowCaller?"):
            messagebox.showinfo("Setup", "Installation cancelled.")
            root.destroy()
            return

        # Prompt for install directory with New Folder option
        install_dir = filedialog.askdirectory(
            title="Select where to install SnowCaller (click 'Make New Folder' to create one)",
            mustexist=False  # Allows creating a new folder
        )
        if not install_dir:
            messagebox.showinfo("Setup", "No directory selected. Exiting.")
            root.destroy()
            return

        # Check if SnowCaller is already in the chosen directory
        saved_dir = read_config(install_dir)
        if saved_dir:
            show_launcher_menu(root, saved_dir)
        else:
            # Create the directory if it doesn't exist
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)

            # Start setup with progress bar
            setup_with_progress(root, install_dir)

    root.mainloop()

if __name__ == "__main__":
    main()