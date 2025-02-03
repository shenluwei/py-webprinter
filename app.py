import sys
import time 
import os
from PyQt6.QtGui import QIcon,QAction
from PyQt6.QtCore import QTimer,Qt,QEventLoop
from PyQt6.QtWidgets import QApplication,QMainWindow,QSystemTrayIcon,QTextEdit, QVBoxLayout
from PyQt6.QtWidgets import QWidget, QPushButton,QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog,QPrintPreviewDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
import multiprocessing
from multiprocessing import Process, Queue
from server import *

# Windows API 常量
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

multiprocessing.freeze_support()  # 防止在 Windows 上无限递归
# 创建一个队列用于进程间通信
print_queue = Queue()
direct_print_queue = Queue()
preview_queue = Queue()

run_path=os.path.dirname(os.path.abspath(__file__))

class PrintApp(QMainWindow):
    def __init__(self, previewQueue,printQueue,directPrintQueue):
        super().__init__()
        self.previewQueue = previewQueue
        self.printQueue = printQueue
        self.directPrintQueue = directPrintQueue
        self.previewContent = ""
        self.initUI()
        self.create_tray_icon()

    def initUI(self):
        self.timerDirectPrint = QTimer(self)  # 创建定时器对象
        self.timerDirectPrint.timeout.connect(self.check_direct_print_queue)
        self.timerDirectPrint.start(1000) 

        self.timerPrint = QTimer(self)  # 创建定时器对象
        self.timerPrint.timeout.connect(self.check_print_queue)
        self.timerPrint.start(1000) 

        self.timerPreview = QTimer(self)  # 创建定时器对象
        self.timerPreview.timeout.connect(self.check_preview_queue)
        self.timerPreview.start(1000) 

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        central_widget = QWidget()  # 中心部件a# 设置中心部件
        layout = QVBoxLayout(central_widget)
        self.start_button = QPushButton('开启服务', self)
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.start_button.setEnabled(False)  # 初始时禁用停止按钮

        self.stop_button = QPushButton('停止服务', self)
        self.stop_button.clicked.connect(self.on_stop_button_clicked)

        # self.textPathEdit = QTextEdit(run_path,self)

        # 创建菜单栏
        menubar = self.menuBar()

        # 创建文件菜单
        fileMenu = menubar.addMenu('文件')

        # 添加打印预览动作
        printPreviewAction = QAction('打印预览', self)
        printPreviewAction.triggered.connect(self.handle_print_preview)
        fileMenu.addAction(printPreviewAction)

        self.textEdit = QTextEdit()
        self.textEdit.setText("正在等待打印请求...")
        self.textEdit.setReadOnly(True)
        self.textEdit.setFixedHeight(50)
        # layout.addWidget(self.textPathEdit)
        layout.addWidget(self.textEdit)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.mainLayout = layout
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setWindowTitle('店家打印服务')
        self.show()
        self.tray_icon=None
        self.http_process=None
        self.https_process=None
        self.isQuit=False

    # 创建系统托盘图标
    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(run_path+"/static/logo.png"))  # 提供一个默认图标路径
        # 创建右键菜单
        tray_menu = QMenu(self)
        
        # # 添加菜单项
        # restore_action = QAction("恢复", self)
        # restore_action.triggered.connect(self.show)
        # tray_menu.addAction(restore_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(lambda : self.quit_application())
        tray_menu.addAction(quit_action)

        # 设置菜单到托盘图标
        self.tray_icon.setContextMenu(tray_menu)
        
        # 当用户点击托盘图标时显示消息
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    # 当用户点击托盘图标时显示消息
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
    #当用户点击窗口的关闭按钮时，隐藏窗口，而不是关闭它
    def closeEvent(self, event):
        try:
            if self.isQuit == True:
                event.accept()
                return
            if not(self.tray_icon == None) and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
        except Exception as e:
            print(f"Error closing previewQueue: {e}")
    # 退出应用程序，释放各类资源，关停Web服务
    def quit_application(self):
        try:
            if self.http_process is not None and self.http_process.is_alive():
                self.http_process.terminate()
                self.http_process.join(timeout=3)
                self.http_process = None

            if self.https_process is not None and self.https_process.is_alive():
                self.https_process.terminate()
                self.https_process.join(timeout=3)
                self.https_process = None

            for queue in [self.previewQueue, self.printQueue, self.directPrintQueue]:
                try:
                    queue.close()
                    queue.join_thread()
                except Exception as e:
                    print(f"Error closing queue: {e}")

            self.isQuit = True
            QApplication.instance().quit()
        except Exception as e:
            print(f"Error in quit_application: {e}")


        self.isQuit=True
        QApplication.instance().quit()
    # 启动Flask服务器
    def on_start_button_clicked(self):
        multiprocessing.freeze_support()
        self.textEdit.setText("正在启动服务...")
        if (self.http_process!=None and self.http_process.is_alive) or (self.https_process!=None and self.https_process.is_alive):
            # 启用停止按钮
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            return

        # 启动 HTTP 服务
        self.http_process = Process(target=run_flask_server, args=(False,preview_queue,print_queue,direct_print_queue,))
        self.http_process.daemon = True  # 设置为守护进程
        self.http_process.start()

        # 启动 HTTPS 服务
        self.https_process = Process(target=run_flask_server, args=(True,preview_queue,print_queue,direct_print_queue,))
        self.https_process.daemon = True  # 设置为守护进程
        self.https_process.start()

        # 启用停止按钮
        self.start_button.setEnabled(False)

         # 创建一个 QTimer 实例
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)  # 设置为单次触发
        self.delay_timer.timeout.connect(self.start_delay_actions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
    def start_delay_actions(self):
        self.delay_timer.stop()
        self.delay_timer=None
        self.textEdit.setText("启动成功，正在等待打印请求...")
        self.stop_button.setEnabled(True)
    # 停止Flask服务器
    def on_stop_button_clicked(self):
        self.textEdit.setText("正在关闭服务...")
        if self.http_process != None and self.http_process.is_alive():
            self.http_process.kill()  # 强制终止子进程

        if self.https_process != None and self.https_process.is_alive():
            self.https_process.kill()  # 强制终止子进程
        
        self.stop_button.setEnabled(False)
        # 创建一个 QTimer 实例
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)  # 设置为单次触发
        self.delay_timer.timeout.connect(self.stop_delay_actions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
    def stop_delay_actions(self):
        self.delay_timer.stop()
        self.delay_timer=None
        # 在这里执行延时后的操作
        self.http_process = None
        self.https_process = None
        self.textEdit.setText("关闭成功")
        # 禁用停止按钮，启用启动按钮（可选，取决于您的需求）
        self.start_button.setEnabled(True)
       
    def on_load_finished(self, success,webView,printer,loop):
        if success:
            # 连接打印完成的信号
            webView.printFinished.connect(loop.quit)
            # 开始打印
            webView.print(printer)
        else:
            loop.quit()

    #打印的核心代码
    def printDocument(self, printer,data):
        webView = QWebEngineView()
        webView.setFixedWidth(1)
        webView.setFixedHeight(1)
        # 加载 HTML 文本并处理图片
        # html_loader = HtmlImageLoader(printer,html_content, doc)
        # doc.setHtml(html_loader.getDocument())
        webView.setHtml(data)
        self.mainLayout.addWidget(webView)
        # QEventLoop 的作用
        # QEventLoop 允许你创建一个局部的事件循环，用于等待某个异步操作完成。它的典型使用场景包括：
        # 等待信号触发：例如等待 QWebEngineView 的 loadFinished 以及 printFinished 信号。
        # 延迟执行：例如等待一段时间后再继续执行代码。
        # 异步操作：例如等待网络请求完成或文件读写完成。
        loop = QEventLoop()
        webView.loadFinished.connect(lambda success: self.on_load_finished(success,webView,printer,loop))
        loop.exec()
        self.mainLayout.removeWidget(webView)
        webView.deleteLater()
    # 打印预览
    def handle_print_preview(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(300)  # 设置打印机分辨率为300 DPI
        previewDialog = QPrintPreviewDialog(printer, self)

        previewDialog.paintRequested.connect(lambda printer: self.printDocument(printer,self.previewContent))
        previewDialog.setWindowFlags(previewDialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        previewDialog.exec()
        previewDialog.raise_()
        previewDialog.activateWindow()
    # 打印
    def handle_print(self,data):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(300)  # 设置打印机分辨率为300 DPI
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.printDocument(printer,data)
        # 设置对话框置顶显示
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dialog.raise_()
        dialog.activateWindow()
    # 直接打印
    def handle_direct_print(self,data):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(300)  # 设置打印机分辨率为300 DPI
        self.printDocument(printer,data)

    #检测预览队列
    def check_preview_queue(self):
        if not self.previewQueue.empty():
            self.previewContent = self.previewQueue.get()
            self.textEdit.setText("接收到预览指令")
            self.handle_print_preview()
            self.textEdit.setText("正在等待打印请求...")
     #检测打印队列
    def check_print_queue(self):
        if not self.printQueue.empty():
            data = self.printQueue.get()
            self.textEdit.setText("接收到打印指令")
            self.handle_print(data)
            self.textEdit.setText("正在等待打印请求...")
     #检测直接打印队列
    def check_direct_print_queue(self):
        if not self.directPrintQueue.empty():
            data = self.directPrintQueue.get()
            self.textEdit.setText("接收到直接打印指令")
            self.handle_direct_print(data)
            self.textEdit.setText("正在等待打印请求...")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(run_path+'/static/logo.png'))
        app.setQuitOnLastWindowClosed(False)
        # 确保系统托盘支持可用
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Systray", "I couldn't detect any system tray on this system.")
            sys.exit(1)
        # 启动PyQt6主应用
        ex = PrintApp(preview_queue,print_queue,direct_print_queue)
        ex.on_start_button_clicked()
        sys.exit(app.exec())
    except Exception as e:
        sys.exit(1)
    