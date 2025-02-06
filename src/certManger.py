import tempfile
import requests

httpKeyPath = 'https://file.dianplus.cn/ssl/localhost.dianjia.io.key'
httpCertPath = 'https://file.dianplus.cn/ssl/localhost.dianjia.io.pem'

certFileCaches={}
# 下载文件到临时文件
def downloadFileToTempfile(url):
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
# 读取文件到字符串
def downloadFileToString(url):
    # 发送 HTTP GET 请求下载文件
    response = requests.get(url, stream=True, verify=False)
    # 检查请求是否成功
    if response.status_code == 200:
        # 将文件内容读取为字符串
        file_content = response.text
        return file_content
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")
# 将文本内容写到文件，覆盖原有的内容
def writeStringToFile(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
# 下载文件并将文件存储到临时目录
def readTempFileToString(url):
    path = downloadFileToTempfile(url)
    # 打开临时文件并读取内容为字符串
    with open(path, 'r') as file:
        fileContent=file.read()
    if(certFileCaches.get(url)==None):
        certFileCaches[url]=fileContent
    return path

key_temp_path = readTempFileToString(httpKeyPath)
cert_temp_path = readTempFileToString(httpCertPath)

# 判定文件是否更新了
def isCertFileChanged():
    try:
        keyContent=downloadFileToString(httpKeyPath)
        certContent=downloadFileToString(httpCertPath)
        # 检测文件是否有变化
        if(certFileCaches.get(httpKeyPath)!=keyContent) or (certFileCaches.get(httpCertPath)!=certContent):
            writeStringToFile(key_temp_path,keyContent)
            writeStringToFile(cert_temp_path,certContent)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False
    