import os
from flask import Flask, request, jsonify,render_template
import tempfile
import requests
from gunicorn.app.base import BaseApplication
from urllib.parse import unquote

run_path=os.path.dirname(os.path.abspath(__file__))
# Flask Web服务器定义
flaskApp = Flask(__name__,template_folder=run_path+'/templates')
@flaskApp.route('/')
def index():
    return render_template('index.html', message="欢迎来到我的主页")
# 预览
@flaskApp.route('/preview', methods=['POST'])
def preview():
    data_to_print = request.json.get('data')
    if not data_to_print:
        return jsonify({"error": "No data to print"}), 400
    preview_queue.put(unquote(data_to_print))  # 将数据放入队列中
    return jsonify({"success": True}), 200
# 打印
@flaskApp.route('/print', methods=['POST'])
def print():
    data_to_print = request.json.get('data')
    if not data_to_print:
        return jsonify({"error": "No data to print"}), 400
    print_queue.put(unquote(data_to_print))  # 将数据放入队列中
    return jsonify({"success": True}), 200
# 直接打印
@flaskApp.route('/direct_print', methods=['POST'])
def direct_print():
    data_to_print = request.json.get('data')
    if not data_to_print:
        return jsonify({"error": "No data to print"}), 400
    direct_print_queue.put(unquote(data_to_print))  # 将数据放入队列中
    return jsonify({"success": True}), 200
def download_file_to_tempfile(url):
    # 创建一个临时文件
    with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
        # 发送 HTTP GET 请求下载文件
        response = requests.get(url, stream=True, verify=False)
        # 检查请求是否成功
        if response.status_code == 200:
            # 将文件内容写入临时文件
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            # 返回临时文件的路径
            return temp_file.name
        else:
            raise Exception(f"Failed to download file. Status code: {response.status_code}")
        
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

def run_http():
    try:
        options = {
            "bind": ["0.0.0.0:5100"],  # 绑定 HTTP 端口
            "graceful-timeout": 1,  # 超时时间
        }
        gunicornApp = GunicornApp(flaskApp, options)
        gunicornApp.run()
    except Exception as e:
        print(f"Error running HTTP server: {e}")

# 启动 HTTPS 服务（端口 443）
def run_https():
    try:
        # 创建一个临时文件，用于保存下载的文件
        key_temp_path = download_file_to_tempfile('http://mugua-file.oss-cn-hangzhou.aliyuncs.com/ssl/private_key.pem')
        cert_temp_path = download_file_to_tempfile('http://mugua-file.oss-cn-hangzhou.aliyuncs.com/ssl/certificate.pem')
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

def run_flask_server(https,previewQueue,printQueue,directPrintQueue):
    global preview_queue,print_queue,direct_print_queue
    preview_queue = previewQueue
    print_queue = printQueue
    direct_print_queue = directPrintQueue
    if https:
        run_https()
    else:
        run_http()
