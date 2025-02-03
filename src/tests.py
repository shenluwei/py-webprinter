# import sys
# from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
# from PyQt6.QtCore import QUrl,QEventLoop
# from PyQt6.QtPrintSupport import QPrinter, QPrintDialog,QPrintPreviewDialog
# from PyQt6.QtWebEngineWidgets import QWebEngineView

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("HTML Viewer and Printer")
#         self.setGeometry(100, 100, 800, 600)
        
#         # Create a web engine view to display HTML content
#         self.web_view = QWebEngineView()
#         self.web_view.setFixedWidth(1)
#         self.web_view.setFixedHeight(1)
#         html_content = f"""
#             <h1 style="color:red;">{111}!</h1>
#             <p>This is a test document for printing HTML content.</p>
#             <p><b>This text is bold.</b></p>
#             <p><i>This text is italic.</i></p>
#             <p><img style="width:100px;height:100px;" src="https://mugua-file.oss-cn-hangzhou.aliyuncs.com/assets/qywx.png" alt="BaiDu Logo"></p>
#             <div style="width:100px;height:100px;border:1px solid #333;background-color:red;">3</div>
#         """
#         self.web_view.setHtml(html_content)
#         # Create a button to trigger the print dialog
#         self.print_button = QPushButton("Print")
#         self.print_button.clicked.connect(self.print_document)
        
#         # Layout and widgets setup
#         layout = QVBoxLayout()
#         layout.addWidget(self.web_view)
#         layout.addWidget(self.print_button)
        
#         container = QWidget()
#         container.setLayout(layout)
#         self.setCentralWidget(container)
    
    
    
#     def on_load_finished(self, success,printer,loop):
#         if success:
#             print("HTML content loaded successfully.")
#             # 连接打印完成的信号
#             self.web_view.printFinished.connect(loop.quit)
#             # 开始打印
#             self.web_view.print(printer)
#         else:
#             print("Failed to load HTML content.")

#     def printDocument(self, printer,data):
#         html_content = f"""
#             <h1 style="color:red;">{data}!</h1>
#             <p>This is a test document for printing HTML content.</p>
#             <p><b>This text is bold.</b></p>
#             <p><i>This text is italic.</i></p>
#             <p><img style="width:100px;height:100px;" src="https://mugua-file.oss-cn-hangzhou.aliyuncs.com/assets/qywx.png" alt="BaiDu Logo"></p>
#             <div style="width:100px;height:100px;border:1px solid #333;background-color:red;">3</div>
#         """
#         self.web_view.setHtml(html_content)
#         loop = QEventLoop()
#         self.web_view.loadFinished.connect(lambda success: self.on_load_finished(success,printer,loop))
#         loop.exec()

#     def print_document(self):
#         printer = QPrinter(QPrinter.PrinterMode.HighResolution)
#         printer.setResolution(300)  # Set printer resolution to 300 DPI
#         preview_dialog = QPrintPreviewDialog(printer, self)
#         preview_dialog.paintRequested.connect(lambda printer: self.printDocument(printer,111))
#         preview_dialog.exec()
 
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())