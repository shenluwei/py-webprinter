import platform
import sys
import os

#判定程序是windows系统
if platform.system() == "Windows":
    import winreg
# 判断是否是mac系统
if platform.system() == "Darwin":
    import plistlib
    import subprocess
# 判断是否已经是开机自启动了
def get_startup():
    #判定程序是windows系统
    if platform.system() == "Windows":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(key, "DplusPrinter")[0]
            return value == sys.executable
        except FileNotFoundError:
            return False
    # 判断是否是mac系统
    elif platform.system() == "Darwin":
       # 定义 LaunchAgent 的路径
        agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DpulsPrinter.plist')
        
        # 检查文件是否存在
        if os.path.exists(agent_path):
            # 读取文件内容
            with open(agent_path, 'rb') as f:
                agent_dict = plistlib.load(f)
            
            # 验证内容是否正确
            if agent_dict.get('Label') == 'cn.dianplus.DpulsPrinter' and \
               agent_dict.get('ProgramArguments') == ['/Applications/DpulsPrinter.app/Contents/MacOS/DpulsPrinter'] and \
               agent_dict.get('RunAtLoad') is True:
                return True
        return False
    else:
        return False
def set_startup(enable):
    # 判定程序是windows系统
    if platform.system() == "Windows":
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, "DplusPrinter", 0, winreg.REG_SZ, sys.executable)
        else:
            winreg.DeleteValue(key, "DplusPrinter")
        winreg.CloseKey(key)
    # 判断是否是mac系统
    elif platform.system() == "Darwin":
        app_path = '/Applications/DpulsPrinter.app/Contents/MacOS/DpulsPrinter'
        if enable:
            # 定义 LaunchAgent 的路径
            agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DpulsPrinter.plist')
            # 定义 LaunchAgent 的内容
            agent_dict = {
                'Label': 'cn.dianplus.DpulsPrinter',
                'ProgramArguments': [app_path],
                'RunAtLoad': True
            }
            
            # 创建或更新 LaunchAgent 文件
            with open(agent_path, 'wb') as f:
                plistlib.dump(agent_dict, f)
            
            # 加载 LaunchAgent
            subprocess.run(['launchctl', 'load', agent_path])
            print(f"LaunchAgent created and loaded: {agent_path}")
        else:
            # 定义 LaunchAgent 的路径
            agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DpulsPrinter.plist')
            
            # 卸载 LaunchAgent
            subprocess.run(['launchctl', 'unload', agent_path])
            
            # 删除 LaunchAgent 文件
            if os.path.exists(agent_path):
                os.remove(agent_path)
            print(f"LaunchAgent removed: {agent_path}")

def onStartupCheckBoxChanged(checked):
    try:
        if checked != 0:
            set_startup(True)
        else:
            set_startup(False)
    except Exception as e:
        print(e)
    
