"""
小红书笔记爬虫

"""

import json
import time
import logging
import random
import re

from utils import download_images
from data_writer import write_to_csv

NOTES_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
FEED_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/feed'

# from DrissionPage.common import Settings
# Settings.set_language(lang = 'zh_cn')

from DrissionPage import Chromium

def init():
    chrome = Chromium()
    tab = chrome.latest_tab
    tab.get('https://xiaohongshu.com/explore')
    # print("等待登录按钮显示")
    # loginBtn = tab.wait.ele_displayed('.login-btn')
    # while True:
    #     if loginBtn:
    #         print("请扫描二维码")
    #         qrCode = tab.ele('.qrcode-img')
    #         tab.wait(5)
    #     else:
    #         print("已为登录状态")
    #         break
    return chrome, tab

def search_by_keyword(tab, keyword: str):
    # 搜索
    tab.ele('#search-input').input(keyword)
    tab.ele('.input-button').click()
    tab.listen.start(NOTES_API)
    res = tab.listen.wait() # 等待并获取数据包
    print("获取到数据包")
    return res

# 搜索页面获取笔记大致信息
def get_feeds(res) -> list[dict]:
    res_dict = res.response.body
    items: list = res_dict["data"]['items']
    feeds: list[dict]  = []
    for item in items:
        try:
            id = item["id"]
            display_title = item["note_card"]["display_title"]
            user = item["note_card"]["user"]["nick_name"]
            liked_count = item["note_card"]["interact_info"]["liked_count"]
            cover = item["note_card"]["cover"]["url_default"]
            image_list = item["note_card"]["image_list"]
            # 将信息以字典形式推入列表
            feeds.append({
                "id": id,
                "display_title": display_title,
                "user": user,
                "liked_count": liked_count,
                "cover": cover,
                "image_list": image_list
            })
        except Exception as e:
            print(f"出现错误: {e}\n跳过对 {item} 的解析\n")

    return feeds


# ================================================================================================================
# ============================================= 获取详细页面信息 ====================================================
# ================================================================================================================

def get_note_elements(tab, href_dict: list[dict]) -> tuple[ int, list, list, bool ]:
    """
    获取笔记点击元素 20个左右有效元素(具体的值与页面尺寸有关) 2个无效广告
    获取每一个<section>独特的 href 链接, 以此作为特征识别和定位
    函数获得的点击元素在访问后页面会重载导致引用失效, 因此只能使用一次

    :param href_dict: 全局存储的 href 链接和 index 的字典列表
    :return: 笔记元素数量、点击元素列表、更新后的 href_dict 和是否有更新的标志
    """
    elements = []
    isRenewed = False # 标志变量, 记录本次是否有更新
    # 搜索DOM元素
    feedsContainer = tab.ele(".feeds-container")
    # 寻找<section>标签
    noteItems = feedsContainer.eles(".note-item", timeout = 0.5) # 提取这个标签下的 data-index
    print(f"获取到笔记元素: {len(noteItems)} 个")
    
    for index, noteItem in enumerate(noteItems, start = 0):
        try:
            dataIndex = noteItem.attr("data-index")

            # 检查是否已经存在于 href_index
            if any(entry["index"] == dataIndex for entry in href_dict):
                print(f"链接 {index} 已存在 [{dataIndex}], 跳过")
                continue
            
            # 获取 href 链接
            href_link = noteItem.ele(".cover ld mask", timeout = 0.5).attr("href")
            print(f"获取链接 {index} [{dataIndex}] 成功: {href_link}")
            
            # 生成点击元素
            element = noteItem.ele(".cover ld mask")
            elements.append(element)
            
            # 更新 href_dict
            href_dict.append({
                "index": dataIndex,
                "href": href_link
            })
            isRenewed = True
            
        except Exception as e:
            href_link = None
            print(f"获取链接 [{index}] 失败: {e}")

    # print(f"获取到href字典: {href_dict}")
    return len(noteItems), elements, href_dict, isRenewed

# ==================================================== 刷新点击元素 ============================================================

def renew_element(tab, index):
    """
    根据元素索引重新获取元素引用
    """
    sections = tab.eles('@tag()=section', timeout = 2)# .ele(".cover ld mask", timeout = 1)
    for section in sections:
        if section.attr("data-index") == index:
            element = section.ele(".cover ld mask")
            # print(f"更新的元素引用: {element}")
            return element
# ============================================================================================================================

# 访问帖子详情页面操作
def access_note(element, tab):
    """
    没有办法通过提前先拿到所有点击元素后再逐个点击获取帖子
    因为每次进入帖子详情访问退出后 页面会重载导致引用失效:
    The element object is invalid.
    This may be an overall refresh of the page, or a partial js refresh to replace or remove elements.

    因此只能每次访问一个帖子前都动态获取一下点击元素
    然后将回调函数作为参数传递给这个操作函数, 依次执行回调
    """
    """
    遍历元素列表, 为每个元素执行点击和回调操作
    :param element: 要点击的元素
    :param tab: 当前浏览器 tab 对象
    :param callback: 可变参数, 回调函数
    """
    try:
        # 点击进入详情页面
        tab.listen.start(FEED_API)
        element.click()
        # 等待笔记数据包
        notePack = tab.listen.wait()
        note_text = notePack.response.body
        print("获取到详情数据包")
        # 将str类型 转为 json 格式
        note_dict = json.dumps(note_text, ensure_ascii=False, indent=4)
        # get_note_info(note_dict, isDownload = True)
        
        # 关闭详情页面
        closeBtn = tab.ele(".close close-mask-dark")
        if closeBtn:
            print("开始随机等待")
            tab.wait(random.uniform(1.0, 2.0))
            closeBtn.click()
        print("已关闭页面")
        
        # 开始爬取下一个元素前等待一小段时间
        tab.wait(random.uniform(0.5, 1.0))
    except Exception as e:
        # 如果出现属性缺失则跳过(API里会混进来一些非笔记元素, 「大家都在搜」)
        print(f"处理元素时出现错误: {e}")

def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# 获取笔记详细信息
def get_note_info(note_dict, isDownload=False):
    """
    获取笔记详细信息
    :param note_dict: 笔记数据字典
    :param isDownload: 是否下载图片
    :return: 笔记信息字典列表
    """
    note_feed = []

    # 检查数据是否存在
    try:
        item = note_dict["data"]["items"][0]["note_card"]
        print("成功获取到 item 信息")
    except (KeyError, IndexError) as e:
        print(f"无法获取笔记详细信息: {e}")
        return []

    # 提取数据
    note_id = item.get("note_id", "未知")
    ip_location = item.get("ip_location", "无")
    time = item.get("time", "未知时间")
    note_title: str = item.get("title", "无标题")
    desc = item.get("desc", "无描述")
    user = item.get("user", {}).get("nickname", "匿名用户")

    # 提取图片列表
    image_urls = []
    for image in item.get("image_list", []):
        if "info_list" in image and image["info_list"]:
            image_urls.append(image["info_list"][-1].get("url", ""))

    # 提取标签列表
    tags = [tag.get("name", "未知标签") for tag in item.get("tag_list", [])]

    # 组织数据
    note_data = {
        "note_id": note_id,
        "ip_location": ip_location,
        "time": time,
        "note_title": note_title,
        "desc": desc,
        "user": user,
        "image_urls": image_urls,
        "tags": tags
    }
    note_feed.append(note_data)

    # 写入 CSV 文件
    sanitized_title = sanitize_filename(note_title)
    write_to_csv(f"{sanitized_title}.csv", note_feed)
    print(f"成功写入笔记: {sanitized_title}")

    # 下载图片
    if isDownload and image_urls:
        download_images(image_urls, img_names=sanitized_title)
    elif isDownload:
        print("没有可下载的图片")

    return note_feed

def quit(tab, chrome):
    print("退出浏览器")
    tab.close()
    chrome.quit()

def main():
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("程序开始运行")

        chrome, tab = init()
        tab.listen.start(FEED_API)
        # 获取搜索页面信息
        res = search_by_keyword(tab, "日本")
        tab.wait(2)
        # 获取笔记大致信息
        feeds = get_feeds(res)
        write_to_csv("feeds.csv", feeds)
        
        # 接下来是获取笔记详细信息
        href_dict = []
        # 初始化
        notesNum, elements, href_dict, isRenewed = get_note_elements(tab, href_dict)

        usedIndex: list[int] = []
        while True:
            if isRenewed:
                all_used = True
                for entry in href_dict:
                    index = entry["index"] # 提取 data-index 的值(字符串)
                    if int(index) in usedIndex:
                        continue # 对于已经处理过的 index 跳过本次循环

                    all_used = False # 发现尚未处理的 index, 进行标记
                    print(f"将会用来匹配的index: {index}")
                    element = renew_element(tab, index) # 刷新元素引用

                    if element: # 如果元素成功刷新
                        print("进入详情页面")
                        access_note(element, tab)
                        usedIndex.append(int(index))
                if all_used:
                    print("当前所有 index 已处理完, 等待新的数据包...")
                    isRenewed = False
            else:
                counter = 0
                while not isRenewed:
                    tab.scroll.down(300)
                    notesNum, elements, href_dict, isRenewed = get_note_elements(tab, href_dict)
                    counter += 1
                    if counter == 5: # 达到滚动次数上限时退出
                        return (print("采集完毕"))

    finally:
        quit(tab, chrome)
    
if __name__ == '__main__':
    main()
