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

# Detect the operating system
OS = platform.system().lower()
CONFIG_FILE_NAME = "launcher_config.txt"
ICON_FILE = "1.png"

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

def install_python(progress_bar, label):
    """Install Python based on the OS."""
    update_progress(progress_bar, label, 10, "Installing Python...")
    if OS == "windows":
        url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
        installer = "python_installer.exe"
        urllib.request.urlretrieve(url, installer)
        subprocess.run(f"{installer} /quiet InstallAllUsers=1 PrependPath=1", shell=True)
        os.remove(installer)
        os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]
    elif OS == "linux":  # Debian
        subprocess.run("sudo apt update && sudo apt install -y python3.11 python3-pip", shell=True)
    update_progress(progress_bar, label, 30, "Python installed.")

def install_git(progress_bar, label):
    """Install Git based on the OS."""
    update_progress(progress_bar, label, 40, "Installing Git...")
    if OS == "windows":
        url = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        installer = "git_installer.exe"
        urllib.request.urlretrieve(url, installer)
        subprocess.run(f"{installer} /SILENT /NORESTART", shell=True)
        os.remove(installer)
    elif OS == "linux":  # Debian
        subprocess.run("sudo apt update && sudo apt install -y git", shell=True)
    update_progress(progress_bar, label, 60, "Git installed.")

def install_requests(progress_bar, label):
    """Install the requests module."""
    update_progress(progress_bar, label, 70, "Installing requests module...")
    python_cmd = "python" if OS == "windows" else "python3"
    subprocess.run(f"{python_cmd} -m pip install requests", shell=True)
    update_progress(progress_bar, label, 80, "Requests module installed.")

def setup_game(progress_bar, label, install_dir):
    """Clone the repo and prepare the game."""
    update_progress(progress_bar, label, 90, "Downloading SnowCaller...")
    os.chdir(install_dir)
    if not os.path.exists("snowcaller"):
        subprocess.run("git clone https://github.com/m0nnnna/snowcaller.git", shell=True)
    os.chdir("snowcaller")
    update_progress(progress_bar, label, 100, "SnowCaller installed!")
    time.sleep(1)  # Brief pause to show completion

def launch_game(install_dir, root):
    """Launch the default terminal and exit the script."""
    game_dir = os.path.join(install_dir, "snowcaller")
    python_cmd = "python" if OS == "windows" else "python3"
    if OS == "windows":
        cmd = f'start cmd /k cd /d "{game_dir}" && {python_cmd} game.py'
        print(f"Launching Command Prompt with: {cmd}")  # Debug
        try:
            os.system(cmd)  # Use os.system for reliable Windows CMD launch
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Command Prompt: {e}")
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
    root.quit()  # Exit the Tkinter mainloop after launching

def delete_save(install_dir):
    """Delete save.json in the snowcaller folder if it exists."""
    save_file = os.path.join(install_dir, "snowcaller", "save.json")
    if os.path.exists(save_file):
        os.remove(save_file)
        messagebox.showinfo("Delete Save", "Save file (save.json) deleted.")
    else:
        messagebox.showinfo("Delete Save", "No save file (save.json) found.")

def setup_with_progress(root, install_dir):
    """Run setup in a thread with a progress bar."""
    progress_window = tk.Toplevel(root)
    progress_window.title("Installing SnowCaller")
    progress_window.geometry("300x150")
    progress_window.resizable(False, False)
    icon_path = get_resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        progress_window.iconphoto(True, tk.PhotoImage(file=icon_path))

    label = tk.Label(progress_window, text="Starting setup...", pady=10)
    label.pack()

    progress_bar = tk.ttk.Progressbar(progress_window, length=200, mode='determinate')
    progress_bar.pack(pady=10)

    def run_setup():
        python_cmd = "python" if OS == "windows" else "python3"
        if not check_command(f"{python_cmd} --version"):
            install_python(progress_bar, label)
        if not check_command("git --version"):
            install_git(progress_bar, label)
        install_requests(progress_bar, label)
        setup_game(progress_bar, label, install_dir)
        write_config(install_dir)  # Save config in launcher's directory
        if OS == "linux":
            create_desktop_icon(install_dir)  # Create desktop icon on Linux
        progress_window.destroy()
        show_launcher_menu(root, install_dir)  # Show menu after setup

    threading.Thread(target=run_setup, daemon=True).start()

def show_launcher_menu(root, install_dir):
    """Show the launcher menu with Play, Delete Save, and Close."""
    menu_window = tk.Toplevel(root)
    menu_window.title("SnowCaller Launcher")
    menu_window.geometry("200x150")
    menu_window.resizable(False, False)
    icon_path = get_resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        menu_window.iconphoto(True, tk.PhotoImage(file=icon_path))

    tk.Label(menu_window, text="SnowCaller", pady=10).pack()
    tk.Button(menu_window, text="Play", command=lambda: launch_game(install_dir, root)).pack(pady=5)
    tk.Button(menu_window, text="Delete Save", command=lambda: delete_save(install_dir)).pack(pady=5)
    tk.Button(menu_window, text="Close", command=root.quit).pack(pady=5)

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
            # Create the directory if it doesn’t exist
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)

            # Start setup with progress bar
            setup_with_progress(root, install_dir)

    root.mainloop()

if __name__ == "__main__":
    main()