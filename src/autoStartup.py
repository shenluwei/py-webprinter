import platform
import sys
if platform.system() == "Windows":
    import winreg
# 判断是否已经是开机自启动了
def get_startup():
    if platform.system() == "Windows":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(key, "DplusPrinter")[0]
            return value == sys.executable
        except FileNotFoundError:
            return False
    else:
        return False
def set_startup(enable):
    if platform.system() == "Windows":
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, "DplusPrinter", 0, winreg.REG_SZ, sys.executable)
        else:
            winreg.DeleteValue(key, "DplusPrinter")
        winreg.CloseKey(key)
def onStartupCheckBoxChanged(checked):
    try:
        if checked != 0:
            set_startup(True)
        else:
            set_startup(False)
    except Exception as e:
        print(e)
    
