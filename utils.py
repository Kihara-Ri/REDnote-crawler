import requests
import os

def create_folder(folder_path):
    """
    创建目录，如果不存在
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"创建目录: {folder_path}")
    else:
        print(f"目录已存在: {folder_path}")

def download_image(url, folder_path, img_name=None):
    """
    下载单张图片到指定文件夹
    :param url: 图片 URL
    :param folder_path: 保存图片的文件夹路径
    :param img_name: 图片文件名（不含扩展名）
    """
    try:
        # 创建文件夹
        create_folder(folder_path)
        
        # 请求图片数据
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # 如果未指定文件名，使用 URL 的最后部分作为文件名
            file_name = img_name if img_name else url.split("/")[-1].split("?")[0]
            file_path = os.path.join(folder_path, file_name)

            # 确保文件扩展名正确
            if not file_path.lower().endswith(".jpg"):
                file_path += ".jpg"
            
            # 保存图片数据
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"下载成功: {file_path}")
        else:
            print(f"下载失败，HTTP状态码: {response.status_code}, URL: {url}")
    except Exception as e:
        print(f"下载失败，URL: {url}，错误信息: {e}")

def download_images(urls, base_folder="images", appendix="", img_names=None):
    """
    批量下载图片到指定文件夹
    :param urls: 图片 URL 列表
    :param base_folder: 基础文件夹路径
    :param appendix: 子目录
    :param img_names: 图片文件名的前缀（自动加索引）
    """
    # 生成完整的保存路径
    folder_path = os.path.join(base_folder, appendix)
    
    # 确保文件夹存在
    create_folder(folder_path)
    
    # 下载每张图片
    for index, url in enumerate(urls, start=1):
        # 如果指定文件名前缀，生成带索引的文件名
        img_name = f"{img_names}({index})" if img_names else None
        download_image(url, folder_path, img_name=img_name)
