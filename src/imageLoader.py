# from PyQt6.QtCore import QUrl,QObject, pyqtSignal
# from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
# from PyQt6.QtGui import QImage,QTextCursor
# import requests
# import base64
# import re

# def extract_image_urls(html_text):
#     # 使用正则表达式提取所有 <img> 标签的 src 属性
#     img_pattern = re.compile(r'<img[^>]+src="([^">]+)"')
#     return img_pattern.findall(html_text)

# def download_image_to_base64(url):
#     # 发送 HTTP 请求下载图片
#     response = requests.get(url)
    
#     # 检查请求是否成功
#     if response.status_code == 200:
#         # 将图片内容转换为 Base64 编码
#         image_base64 = base64.b64encode(response.content).decode('utf-8')
#         return image_base64
#     else:
#         return None
    
# class HtmlImageLoader:
#     def __init__(self,printer, html_text, document):
#         self.printer = printer
#         self.html_text = html_text
#         self.document = document
#         self.image_urls = extract_image_urls(html_text)
#         self.image_cache = {} 
#     def getDocument(self):
#          # 下载所有图片
#         for url in self.image_urls:
#             if url.startswith("data:image") or not url.startswith("http"):
#                 continue
#             base64=download_image_to_base64(url)
#             if base64 is None:
#                 continue
#             self.image_cache[url] = base64

#         # 替换 HTML 中的网络图片 URL 为本地图片
#         updated_html = self.html_text
#         for url, image in self.image_cache.items():
#             updated_html = updated_html.replace(f'src="{url}"', f'src="data:image/png;base64,{image}"')

#         return updated_html