import os
from flask import Flask, request, jsonify,render_template
import uuid
import json
import time
from gunicorn.app.base import BaseApplication
from urllib.parse import unquote

# Flask Web服务器定义
flaskApp = Flask(__name__,template_folder=os.path.dirname(os.path.abspath(__file__))+'/templates')
@flaskApp.route('/')
def index():
    return render_template('index.html', message="欢迎来到我的主页")
# 指令组装
def createCmd(request):
    # 获取请求体中的数据
    unique_id = uuid.uuid1().hex
    # 打印的唯一口令，如果用户没传入就自动用uuid生成一个
    taskKey = request.json.get('taskKey') if request.json.get('taskKey') != None else unique_id
    # 打印的内容
    content = request.json.get('content') if request.json.get('content') != None else ""
    # 打印的选项
    options = request.json.get('options') if request.json.get('options') != None else {}
    # 返回的指令
    cmd={"taskKey":taskKey,"html":unquote(content),"options":options}
    return cmd
# 预览
@flaskApp.route('/preview', methods=['POST'])
def preview():
    preview_queue.put(createCmd(request))  # 将数据放入队列中
    return jsonify({"success": True}), 200
# 打印
@flaskApp.route('/print', methods=['POST'])
def prints():
    print_queue.put(createCmd(request))  # 将数据放入队列中
    return jsonify({"success": True}), 200
# 直接打印
@flaskApp.route('/direct_print', methods=['POST'])
def direct_print():
    direct_print_queue.put(createCmd(request))  # 将数据放入队列中
    return jsonify({"success": True}), 200
# 向主进程发送通信指令
def sendCmd(cmd):
    child_conn.send(cmd)
    i=100
    while True or i>0:
        data = child_conn.recv()
        time.sleep(0.1)
        i=i-1
        if data:
            break
    return data
# 展示打印机列表
@flaskApp.route('/printer_status', methods=['GET','POST'])
def printer_status():
    result=sendCmd("printer_status")
    return jsonify({"success": True, "printerInfos": json.loads(result)}), 200
# 获取打印进度
@flaskApp.route('/print_tasks', methods=['GET','POST'])
def print_tasks():
    result=sendCmd("print_tasks" )
    return jsonify({"success": True, "printTasks": json.loads(result)}), 200

class GunicornApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
# 启动 HTTP 服务（端口 5100）
def runHttpServer(previewQueue,printQueue,directPrintQueue,conn):
    global preview_queue,print_queue,direct_print_queue,child_conn
    preview_queue = previewQueue
    print_queue = printQueue
    direct_print_queue = directPrintQueue
    child_conn = conn
    try:
        options = {
            "bind": ["0.0.0.0:5100"],  # 绑定 HTTP 端口
            "graceful-timeout": 1,  # 超时时间
        }
        gunicornApp = GunicornApp(flaskApp, options)
        gunicornApp.run()
    except Exception as e:
        print(f"Error running HTTP server: {e}")

# 启动 HTTPS 服务（端口 5443）
def runHttpsServer(previewQueue,printQueue,directPrintQueue,conn,keyPath,certPath):
    global preview_queue,print_queue,direct_print_queue,child_conn,key_temp_path,cert_temp_path
    preview_queue = previewQueue
    print_queue = printQueue
    direct_print_queue = directPrintQueue
    child_conn = conn
    key_temp_path = keyPath
    cert_temp_path = certPath
    try:
        options = {
            "bind": ["0.0.0.0:5443"],  # 绑定 HTTPS 端口
            'keyfile': key_temp_path,
            'certfile': cert_temp_path,
            "workers": 2,
            "graceful-timeout": 1,  # 超时时间
        }
        gunicornApp = GunicornApp(flaskApp, options)
        gunicornApp.run()
    except Exception as e:
        print(f"Error running HTTP server: {e}")
