import sys
import os
from PyQt6.QtGui import QIcon,QAction,QPageLayout, QPageSize
from PyQt6.QtCore import QTimer,Qt,QEventLoop,QSizeF,QMarginsF
from PyQt6.QtWidgets import QApplication,QMainWindow,QSystemTrayIcon,QTextEdit, QVBoxLayout
from PyQt6.QtWidgets import QWidget, QPushButton,QSystemTrayIcon, QMenu, QMessageBox,QToolButton
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog,QPrintPreviewDialog,QPrinterInfo
from PyQt6.QtWebEngineWidgets import QWebEngineView
import multiprocessing
from multiprocessing import Process, Queue,Pipe
import json
from server import *

multiprocessing.freeze_support()  # 防止在 Windows 上无限递归
# 打印状态
printTasks={}

# 创建队列用于进程间通信
print_queue = Queue()
direct_print_queue = Queue()
preview_queue = Queue()
# 指令通道
parent_conn, child_conn = Pipe()

run_path=os.path.dirname(os.path.abspath(__file__))

class PrintApp(QMainWindow):
    def __init__(self, previewQueue,printQueue,directPrintQueue):
        super().__init__()
        self.previewQueue = previewQueue
        self.printQueue = printQueue
        self.directPrintQueue = directPrintQueue
        self.previewCmd = ""
        self.initUI()
        self.createTrayIcon()

    def initUI(self):
        self.timerPreview = QTimer(self)  # 预览指令监听器
        self.timerPreview.timeout.connect(self.checkPreviewQueue)
        self.timerPreview.start(1000) 

        self.timerPrint = QTimer(self)  # 打印指令监听器
        self.timerPrint.timeout.connect(self.checkPrintQueue)
        self.timerPrint.start(1000) 

        self.timerDirectPrint = QTimer(self)  # 直接打印指令监听器
        self.timerDirectPrint.timeout.connect(self.checkDirectPrintQueue)
        self.timerDirectPrint.start(1000) 

        self.timerPrinterStatus = QTimer(self)  # 打印机状态监听器
        self.timerPrinterStatus.timeout.connect(self.checkPrintStatuses)
        self.timerPrinterStatus.start(1000) 

        self.timerCmds = QTimer(self)  # 其他指令监听器
        self.timerCmds.timeout.connect(self.cmds)
        self.timerCmds.start(100) 

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        centralWidget = QWidget()  # 中心部件a# 设置中心部件
        layout = QVBoxLayout(centralWidget)
        self.startWebButton = QPushButton('开启服务', self)
        self.startWebButton.clicked.connect(self.onStartWebButtonClicked)
        self.startWebButton.setEnabled(False)  # 初始时禁用停止按钮

        self.stopWebButton = QPushButton('停止服务', self)
        self.stopWebButton.clicked.connect(self.onStopWebButtonClicked)

        # 创建菜单栏
        menubar = self.menuBar()
        # 创建文件菜单
        fileMenu = menubar.addMenu('文件')
        # 添加打印预览动作
        printPreviewAction = QAction('打印预览', self)
        printPreviewAction.triggered.connect(self.handlePrintPreview)
        fileMenu.addAction(printPreviewAction)

        self.textEdit = QTextEdit()
        self.textEdit.setText("正在等待打印请求...")
        self.textEdit.setReadOnly(True)
        self.textEdit.setFixedHeight(50)
        # layout.addWidget(self.textPathEdit)
        layout.addWidget(self.textEdit)
        layout.addWidget(self.startWebButton)
        layout.addWidget(self.stopWebButton)
        self.mainLayout = layout
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle('店家打印服务')
        self.show()
        self.trayIcon=None
        self.httpProcess=None
        self.httpsProcess=None
        self.isQuit=False

    # 创建系统托盘图标
    def createTrayIcon(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(run_path+"/static/logo.png"))  # 提供一个默认图标路径
        # 创建右键菜单
        trayMenu = QMenu(self)
        
        # # 添加菜单项
        # restore_action = QAction("恢复", self)
        # restore_action.triggered.connect(self.show)
        # tray_menu.addAction(restore_action)

        quitAction = QAction("退出", self)
        quitAction.triggered.connect(lambda : self.quitApplication())
        trayMenu.addAction(quitAction)

        # 设置菜单到托盘图标
        self.trayIcon.setContextMenu(trayMenu)
        
        # 当用户点击托盘图标时显示消息
        self.trayIcon.activated.connect(self.trayIconActivated)
        
        # 显示托盘图标
        self.trayIcon.show()
    # 当用户点击托盘图标时显示消息
    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
    #当用户点击窗口的关闭按钮时，隐藏窗口，而不是关闭它
    def closeEvent(self, event):
        try:
            if self.isQuit == True:
                event.accept()
                return
            if not(self.trayIcon == None) and self.trayIcon.isVisible():
                self.hide()
                event.ignore()
        except Exception as e:
            print(f"Error closing previewQueue: {e}")
    # 退出应用程序，释放各类资源，关停Web服务
    def quitApplication(self):
        try:
            if self.httpProcess is not None and self.httpProcess.is_alive():
                self.httpProcess.terminate()
                self.httpProcess.join(timeout=3)
                self.httpProcess = None

            if self.httpsProcess is not None and self.httpsProcess.is_alive():
                self.httpsProcess.terminate()
                self.httpsProcess.join(timeout=3)
                self.httpsProcess = None

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
    # 启动Web服务器
    def onStartWebButtonClicked(self):
        multiprocessing.freeze_support()
        self.textEdit.setText("正在启动服务...")
        if (self.httpProcess!=None and self.httpProcess.is_alive) or (self.httpsProcess!=None and self.httpsProcess.is_alive):
            # 启用停止按钮
            self.startWebButton.setEnabled(False)
            self.stopWebButton.setEnabled(True)
            return

        # 启动 HTTP 服务
        self.httpProcess = Process(target=run_flask_server, args=(False,preview_queue,print_queue,direct_print_queue,child_conn))
        self.httpProcess.daemon = True  # 设置为守护进程
        self.httpProcess.start()
        # 启动 HTTPS 服务
        self.httpsProcess = Process(target=run_flask_server, args=(True,preview_queue,print_queue,direct_print_queue,child_conn))
        self.httpsProcess.daemon = True  # 设置为守护进程
        self.httpsProcess.start()

        # 启用停止按钮
        self.startWebButton.setEnabled(False)

         # 创建一个 QTimer 实例
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)  # 设置为单次触发

        def startDelayActions():
            self.delay_timer.stop()
            self.delay_timer=None
            self.textEdit.setText("启动成功，正在等待打印请求...")
            self.stopWebButton.setEnabled(True)

        self.delay_timer.timeout.connect(startDelayActions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
    
    # 停止Web服务器
    def onStopWebButtonClicked(self):
        self.textEdit.setText("正在关闭服务...")
        if self.httpProcess != None and self.httpProcess.is_alive():
            self.httpProcess.kill()  # 强制终止子进程

        if self.httpsProcess != None and self.httpsProcess.is_alive():
            self.httpsProcess.kill()  # 强制终止子进程
        # 创建一个 QTimer 实例
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)  # 设置为单次触发

        def stopDelayActions():
            self.delay_timer.stop()
            self.delay_timer=None
            # 在这里执行延时后的操作
            self.httpProcess = None
            self.httpsProcess = None
            self.textEdit.setText("关闭成功")
            # 禁用停止按钮，启用启动按钮（可选，取决于您的需求）
            self.startWebButton.setEnabled(True)
            self.stopWebButton.setEnabled(False)

        self.delay_timer.timeout.connect(stopDelayActions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
       
    #打印的核心代码
    def printDocument(self,printer,taskKey, html):
        webView = QWebEngineView()
        webView.setFixedWidth(1)
        webView.setFixedHeight(1)
        # 加载 HTML 文本并处理图片
        webView.setHtml(html)
        self.mainLayout.addWidget(webView)
        # QEventLoop 的作用
        # QEventLoop 允许你创建一个局部的事件循环，用于等待某个异步操作完成。它的典型使用场景包括：
        # 等待信号触发：例如等待 QWebEngineView 的 loadFinished 以及 printFinished 信号。
        # 延迟执行：例如等待一段时间后再继续执行代码。
        # 异步操作：例如等待网络请求完成或文件读写完成。
        loop = QEventLoop()
           # 加载HTML后打印并打印
        def onWebViewLoadFinished(success):
            if success:
                # 连接打印完成的信号
                webView.printFinished.connect(loop.quit)
                # 开始打印
                webView.print(printer)
            else:
                loop.quit()

        webView.loadFinished.connect(lambda success: onWebViewLoadFinished(success))

        loop.exec()

        self.mainLayout.removeWidget(webView)

        webView.deleteLater()
            

    # 准备打印机
    def prepareQPrinter(self,taskKey,options):
        printerName = options.get('printerName')
        pageRect = options.get('pageRect')
        margins = options.get('margins')
        resolution = options.get('resolution')
        orientation = options.get('orientation')
        duplex = options.get('duplex')
        colorMode = options.get('colorMode')
        pageScopes = options.get('pageScopes')

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        # 指定打印机
        if printerName:
            printer.setPrinterName(printerName)
        # 设置页面大小
        if pageRect:
            # 单位为毫米
            width=pageRect.get('width') if pageRect.get('width') != None else 210
            height=pageRect.get('height') if pageRect.get('height') != None else 297
            pageSize = QPageSize(QSizeF(width, height), QPageSize.Unit.Millimeter)
            printer.setPageSize(pageSize)

        # 设置边距
        if margins:
            left=margins.get('left') if margins.get('left') != None else 0
            top=margins.get('top') if margins.get('top') != None else 0
            right=margins.get('right') if margins.get('right') != None else 0
            bottom=margins.get('bottom') if margins.get('bottom') != None else 0
            pageMargin = QMarginsF(left, top, right, bottom)
            printer.setPageMargins(pageMargin, QPageLayout.Unit.Millimeter)
        # # 设置打印方向
        if orientation:
            if(orientation=='landscape'):
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            else:
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        # 设置打印机分辨率
        if resolution:
            printer.setResolution(resolution)  
        else:
            # 300 DPI
            printer.setResolution(300)

        # 设置双面打印
        if duplex:
            if(duplex=='long'):
                printer.setDuplex(QPrinter.DuplexMode.DuplexLongSide)
            elif (duplex=='short'):
                printer.setDuplex(QPrinter.DuplexMode.DuplexShortSide)
            elif (duplex=='auto'):
                printer.setDuplex(QPrinter.DuplexMode.DuplexAuto)
            else:
                printer.setDuplex(QPrinter.DuplexMode.DuplexNone)

        # 设置打印颜色模式
        if colorMode:
            if(colorMode=='color'):
                printer.setColorMode(QPrinter.ColorMode.Color)
            else:
                printer.setColorMode(QPrinter.ColorMode.GrayScale)

        # 设置打印起止页码
        if pageScopes:
            startPage = pageScopes.get('from') if pageScopes.get('from') != None else 1
            endPage = pageScopes.get('to') if pageScopes.get('to') != None else 1
            printer.setFromTo(startPage, endPage)

        printTasks[taskKey]={
            "active":False,
            "status":'init',
            "printer":printer,
            "time":time.time()
        }
        return printer
    # 打印预览
    def handlePrintPreview(self):
        taskKey = self.previewCmd.get('taskKey')
        options = self.previewCmd.get('options')
        html = self.previewCmd.get('html')
        printer:QPrinter=self.prepareQPrinter(taskKey,options)

        previewDialog = QPrintPreviewDialog(printer, self)
        widgets = self.findChildren(QToolButton)
        for widget in widgets:
            if widget.text() == "Print":
                printBtn = widget
        if printBtn:
            def handle_print_button_clicked():
                printTasks[taskKey]['active'] = True
            printBtn.clicked.connect(handle_print_button_clicked)

        previewDialog.paintRequested.connect(lambda printer: self.printDocument(printer,taskKey,html))
        previewDialog.setWindowFlags(previewDialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        previewDialog.exec()
        previewDialog.raise_()
        previewDialog.activateWindow()

    # 打印
    def handlePrint(self,cmd):
        taskKey = cmd.get('taskKey')
        options = cmd.get('options')
        html = cmd.get('html')
        printer=self.prepareQPrinter(taskKey,options)
        
        dialog = QPrintDialog(printer, self)
         # 设置对话框置顶显示
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dialog.raise_()
        dialog.activateWindow()

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            printTasks[taskKey]['active'] = True
            self.printDocument(printer,taskKey,html)
    # 直接打印
    def handleDirectPrint(self,cmd):
        taskKey = cmd.get('taskKey')
        options = cmd.get('options')
        html = cmd.get('html')
        printer=self.prepareQPrinter(taskKey,options)
        printTasks[taskKey]['active'] = True
        self.printDocument(printer,taskKey,html)
       

    #检测预览队列
    def checkPreviewQueue(self):
        if not self.previewQueue.empty():
            self.previewCmd = self.previewQueue.get()
            self.textEdit.setText("接收到预览指令")
            self.handlePrintPreview()
            self.textEdit.setText("正在等待打印请求...")
     #检测打印队列
    def checkPrintQueue(self):
        if not self.printQueue.empty():
            cmd = self.printQueue.get()
            self.textEdit.setText("接收到打印指令")
            self.handlePrint(cmd)
            self.textEdit.setText("正在等待打印请求...")
     #检测直接打印队列
    def checkDirectPrintQueue(self):
        if not self.directPrintQueue.empty():
            cmd = self.directPrintQueue.get()
            self.textEdit.setText("接收到直接打印指令")
            self.handleDirectPrint(cmd)
            self.textEdit.setText("正在等待打印请求...")
    
    # 检查已激活的打印机状态
    def checkPrintStatuses(self):
         keys=list(printTasks.keys())
         for key in keys:
            process=printTasks[key]
            # 删除超时的
            if time.time() - process['time'] > 180:
                del printTasks[key]
                continue

            if process['active']:
                printer:QPrinter=process['printer']
                if printer.printerState() == QPrinter.PrinterState.Idle:
                    process['status'] = "success"
                elif printer.printerState() == QPrinter.PrinterState.Aborted:
                    process['status'] = "aborted"
                elif printer.printerState() == QPrinter.PrinterState.Error:
                    process['status']  = "error"
                elif printer.printerState() == QPrinter.PrinterState.Active:
                    # 更新时间
                    process['status']  = "active"
                    process['time'] = time.time()
    # 接收http服务子进程指令
    def cmds(self):
       result = parent_conn.poll()
       # 判断子进程是否有信息，如果没有则退出
       if result==False:
           return
       # 发现了信号
       result = parent_conn.recv()

       # 打印机状态
       if result=="printer_status":
            printers = QPrinterInfo.availablePrinters()
            printerInfos = []
            for printer in printers:
                info = {
                    "name": printer.printerName(),
                    "description": printer.description(),
                    "location": printer.location(),
                    "is_default": printer.isDefault(),
                    "is_remote": printer.isRemote(),
                    "supported_resolutions": [printer.supportedResolutions()]
                }
                printerInfos.append(info)
            parent_conn.send(json.dumps(printerInfos))

       if result=="print_tasks":
            keys=list(printTasks.keys())
            printInfos=[]
            for key in keys:
                process=printTasks[key]
                printInfos.append({
                    "taskKey":key,
                    "status":process['status'],
                    "active":process['active'],
                    "printer":process['printer'].printerName()
                })
            parent_conn.send(json.dumps(printInfos))

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
        ex.onStartWebButtonClicked()
        sys.exit(app.exec())
    except Exception as e:
        sys.exit(1)
    