"""
小红书笔记爬虫

"""

import json
import time
import logging
import random

from utils import download_images

NOTES_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
FEED_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/feed'

# from DrissionPage.common import Settings
# Settings.set_language(lang = 'zh_cn')

from DrissionPage import Chromium

def init():
    chrome = Chromium()
    tab = chrome.latest_tab
    tab.get('https://xiaohongshu.com/explore')
    print("等待登录按钮显示")
    loginBtn = tab.wait.ele_displayed('.login-btn')
    while True:
        if loginBtn:
            print("请扫描二维码")
            qrCode = tab.ele('.qrcode-img')
            tab.wait(5)
        else:
            print("已为登录状态")
            break
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
            id: str = item["id"]
            display_title: str = item["note_card"]["display_title"]
            user: str = item["note_card"]["user"]["nick_name"]
            liked_count: str = item["note_card"]["interact_info"]["liked_count"]
            cover: str = item["note_card"]["cover"]["url_default"]
            image_list: list[dict] = item["note_card"]["image_list"]
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
            print(f"出现错误: {e}\n跳过对 {item} 的解析")

    return feeds

# 获取笔记点击元素 22个有效元素 2个无效广告
def get_note_elements(tab) -> tuple[ int, list ]:
    # 搜索DOM元素
    feedsContainer = tab.ele(".feeds-container")
    noteItems = feedsContainer.eles(".note-item")
    
    elements = []
    if noteItems:
        print(f"获取到笔记元素: {len(noteItems)} 个")
        # 监听 feed API  成功的点击操作会返回这个帖子的数据包
        tab.listen.start(FEED_API)
        for index, noteItem in enumerate(noteItems, start = 1):
            try:
                link = noteItem.ele(".cover ld mask", timeout = 0.5).attr("href") # 过滤掉广告
                print(f"获取链接 [{index}] 成功: {link}")
                # 生成点击元素
                element = noteItem.ele(".cover ld mask")
                elements.append(element)
            except Exception as e:
                link = None
                print(f"获取链接 [{index}] 失败: {e}")

        return len(noteItems), elements
    else:
        print("未找到笔记元素")

"""
没有办法通过提前先拿到所有点击元素后再逐个点击获取帖子
因为每次进入帖子详情访问退出后 页面会重载导致引用失效:
The element object is invalid.
This may be an overall refresh of the page, or a partial js refresh to replace or remove elements.

因此只能每次访问一个帖子前都动态获取一下点击元素
然后将回调函数作为参数传递给这个操作函数, 依次执行回调
"""
# 访问帖子详情页面操作
def access_note(element, tab, *callbacks):
    """
    遍历元素列表, 为每个元素执行点击和回调操作
    :param element: 要点击的元素
    :param tab: 当前浏览器 tab 对象
    :param callback: 可变参数, 回调函数
    """
    try:
        # 点击进入详情页面
        element.click()
        
        # 执行回调函数
        for callback in callbacks:
            callback()
        
        # 关闭详情页面
        closeBtn = tab.ele(".close close-mask-dark")
        if closeBtn:
            print("开始随机等待")
            tab.wait(random.uniform(1.0, 2.0))
            closeBtn.click()
        
        # 开始爬取下一个元素前等待一小段时间
        tab.wait(random.uniform(0.5, 1.0))
    except Exception as e:
        # 如果出现属性缺失则跳过(API里会混进来一些非笔记元素, 「大家都在搜」)
        print(f"处理元素时出现错误: {e}")

# 获取笔记详细信息
def get_note_info(tab, isDownload = False):
    note_feed = []
    # 等待笔记数据包
    notePack = tab.listen.wait()
    note_dict = notePack.response.body
    # with open('noteItem.json', 'w', encoding = 'utf-8') as file:
    #     json.dump(note_dict, file, ensure_ascii= False, indent = 4)
    # print("写入noteItem.json")
    item = note_dict["data"]["items"][0]["note_card"]

    note_id: str = item["note_id"]
    ip_location: str = item["ip_location"]
    time: int = item["time"]
    note_title: str = item["title"]
    desc: str = item["desc"]
    user: str = item["user"]["nickname"]
    
    image_list: list[dict] = item["image_list"]
    tag_list: list[dict] = item["tag_list"]

    if image_list:
        image_urls = []
        for image in image_list:
            image_urls.append(image["info_list"][-1]["url"])

    if tag_list:
        tags = []
        for tag in tag_list:
            tags.append(tag["name"])
            
    note_feed.append({
        "note_id": note_id,
        "ip_location": ip_location,
        "time": time,
        "note_title": note_title,
        "desc": desc,
        "user": user,
        "image_urls": image_urls,
        "tags": tags
    })

    # print(note_id)
    # print(ip_location)
    # print(time)
    # print(note_title)
    # print(desc)
    # print(use)
    # print(image_urls)
    # print(tags)
    if isDownload:
        download_images(image_urls)
    # print(note_feed)
    return note_feed

# tab.scroll.down(1000)
# tab.wait(2)

def quit(tab, chrome):
    print("退出浏览器")
    tab.close()
    chrome.quit()

def main():
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("程序开始运行")

        chrome, tab = init()
        # 获取搜索页面信息
        res = search_by_keyword(tab, "日本")
        
        tab.wait(5)
        
        # 获取笔记大致信息
        feeds = get_feeds(res)

        with open('feeds.json', 'w', encoding = 'utf-8') as f:
            json.dump(feeds, f, ensure_ascii = False, indent = 4)
            print("feeds.json写入完毕")
        
        # 接下来是获取笔记详细信息
        index = 0
        while True:
            notesNum, elements = get_note_elements(tab)
            print("接下来开始获取笔记详细信息")
            access_note(elements[index], tab, lambda: get_note_info(tab, isDownload = False))
            index += 1
            if index >= notesNum:
                break
        print("采集完毕")
    
    finally:
        quit(tab, chrome)
    
if __name__ == '__main__':
    main()
