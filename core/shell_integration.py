"""Windows shell integration for ProducerOS."""

import sys
import os

# Windows registry support
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False


def get_app_path():
    """Get the path to the ProducerOS executable or script."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script - use pythonw to avoid console window
        python_exe = sys.executable
        if python_exe.endswith('python.exe'):
            pythonw = python_exe.replace('python.exe', 'pythonw.exe')
            if os.path.exists(pythonw):
                python_exe = pythonw

        main_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
        return f'"{python_exe}" "{main_script}"'


def is_shell_integration_enabled():
    """Check if shell integration is currently enabled."""
    if not WINREG_AVAILABLE:
        return False

    try:
        key_path = r"Software\Classes\Directory\shell\AddToProducerOS"
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def enable_shell_integration():
    """Add 'Add to ProducerOS' to Windows Explorer context menu for folders."""
    if not WINREG_AVAILABLE:
        return False, "Windows registry not available"

    try:
        app_path = get_app_path()

        # Create registry keys for folder context menu
        # HKEY_CURRENT_USER\Software\Classes\Directory\shell\AddToProducerOS
        key_path = r"Software\Classes\Directory\shell\AddToProducerOS"

        # Create the main key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Add to ProducerOS")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "")  # Optional: add icon path
        winreg.CloseKey(key)

        # Create the command key
        command_path = key_path + r"\command"
        command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path)
        command = f'{app_path} "%V"'
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(command_key)

        # Also add for directory background (right-click in folder)
        bg_key_path = r"Software\Classes\Directory\Background\shell\AddToProducerOS"
        bg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, bg_key_path)
        winreg.SetValueEx(bg_key, "", 0, winreg.REG_SZ, "Add to ProducerOS")
        winreg.CloseKey(bg_key)

        bg_command_path = bg_key_path + r"\command"
        bg_command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, bg_command_path)
        winreg.SetValueEx(bg_command_key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(bg_command_key)

        return True, "Shell integration enabled successfully"

    except PermissionError:
        return False, "Permission denied. Try running as administrator."
    except Exception as e:
        return False, f"Error: {str(e)}"


def disable_shell_integration():
    """Remove 'Add to ProducerOS' from Windows Explorer context menu."""
    if not WINREG_AVAILABLE:
        return False, "Windows registry not available"

    try:
        # Delete folder context menu entry
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Classes\Directory\shell\AddToProducerOS\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Classes\Directory\shell\AddToProducerOS")
        except FileNotFoundError:
            pass

        # Delete background context menu entry
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Classes\Directory\Background\shell\AddToProducerOS\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Classes\Directory\Background\shell\AddToProducerOS")
        except FileNotFoundError:
            pass

        return True, "Shell integration disabled successfully"

    except PermissionError:
        return False, "Permission denied. Try running as administrator."
    except Exception as e:
        return False, f"Error: {str(e)}"
