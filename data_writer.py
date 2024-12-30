import csv
from typing import List, Dict

def write_to_csv(file_name: str, data: List[Dict], mode='w'):
    """
    将数据写入 CSV 文件
    :param file_name: 输出的 CSV 文件名
    :param data: 包含字典数据的列表
    :param mode: 写入模式 ('w' 覆盖, 'a' 追加)
    """
    if not data:
        print("数据为空，无法写入 CSV 文件")
        return
    
    # 提取字段名（默认取第一个字典的键）
    fieldnames = data[0].keys()
    
    try:
        # 检查文件是否已存在，避免重复写入表头（在追加模式下）
        file_exists = mode == 'a'
        if file_exists:
            try:
                with open(file_name, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.reader(csvfile)
                    file_exists = any(reader)  # 检查文件是否有内容
            except FileNotFoundError:
                file_exists = False
        
        # 打开文件并写入数据
        with open(file_name, mode=mode, encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 写入表头（仅在文件为空或非追加模式时写入）
            if not file_exists or mode == 'w':
                writer.writeheader()
            
            # 写入数据行
            writer.writerows(data)
        
        print(f"数据成功写入到文件 {file_name}")
    except Exception as e:
        import traceback
        print(f"写入 CSV 文件时出错: {e}")
        traceback.print_exc()


# 调试示例
if __name__ == "__main__":
    # 测试数据
    note_feed = [
        {
            "note_id": "12345",
            "ip_location": "北京",
            "time": 1681296000,
            "note_title": "如何烤出完美的面包",
            "desc": "分享一款简单又美味的面包配方。",
            "user": "面包达人",
            "image_urls": ["http://example.com/image1.jpg", "http://example.com/image2.jpg"],
            "tags": ["烘焙", "美食"]
        },
        {
            "note_id": "67890",
            "ip_location": "上海",
            "time": 1681382400,
            "note_title": "我的健身心得",
            "desc": "每天坚持锻炼，拥有健康体魄。",
            "user": "健身爱好者",
            "image_urls": ["http://example.com/image3.jpg"],
            "tags": ["健身", "健康"]
        }
    ]

    write_to_csv("notes.csv", note_feed)
