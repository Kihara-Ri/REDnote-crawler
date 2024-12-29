import requests
import os

def create_folder(folder_path):
  if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"创建目录: {folder_path}")
  else:
    print(f"目录已存在: {folder_path}")

def download_image(url, base = os.getcwd() + "/images", appendix = ""):
  folder_path = os.path.join(base, appendix)
  try:
    response = requests.get(url, stream = True)
    if response.status_code == 200:
      file_name = os.path.join(folder_path, url.split("/")[-1])
      with open(file_name + ".jpg", 'wb') as file:
        for chunk in response:
          file.write(chunk)
      print(f"下载成功: {file_name}")
    else:
      print(f"下载失败: {url}")
  except Exception as e:
    print(f"下载失败: {url}，错误信息: {e}")

def download_images(urls, base = os.getcwd() + "/images", appendix = ""):
  folder_path = os.path.join(base, appendix)
  create_folder(folder_path)
  for url in urls:
    download_image(url, folder_path)