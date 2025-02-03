
# 以下代码的作用是创建一个快捷方式，将应用程序添加到Windows的启动项中，还有待进一步验证
# from win32com.client import Dispatch
# def create_startup_shortcut():
#     startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
#     script_path = os.path.abspath(sys.argv[0])
#     shortcut_path = os.path.join(startup_folder, "MyApp.lnk")

#     shell = Dispatch('WScript.Shell')
#     shortcut = shell.CreateShortCut(shortcut_path)
#     shortcut.Targetpath = sys.executable  # Python executable path
#     shortcut.Arguments = script_path
#     shortcut.WorkingDirectory = os.path.dirname(script_path)
#     shortcut.save()

# def create_launch_agent_plist():
#     plist_content = f"""\
#         <?xml version="1.0" encoding="UTF-8"?>
#         <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
#         <plist version="1.0">
#         <dict>
#             <key>Printer</key>
#             <string>cn.dianplus</string>

#             <key>ProgramArguments</key>
#             <array>
#                 <string>{os.path.join('/usr', 'local', 'bin', 'python3')}</string>
#                 <string>{os.path.abspath(__file__)}</string>
#             </array>

#             <key>RunAtLoad</key>
#             <true/>
#         </dict>
#         </plist>
#         """
#     launch_agents_path = os.path.expanduser("~/Library/LaunchAgents/cn.dianplus.plist")
#     with open(launch_agents_path, "w") as file:
#         file.write(plist_content)
#     print(f"Plist 文件已创建: {launch_agents_path}")