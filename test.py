"""
小红书笔记爬虫

"""

import json
import time

from utils import download_images

NOTES_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
FEED_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/feed'

# from DrissionPage.common import Settings
# Settings.set_language(lang = 'zh_cn')

from DrissionPage import Chromium
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

tab.ele('#search-input').input('日本')
tab.ele('.input-button').click()

tab.listen.start(NOTES_API)

res = tab.listen.wait() # 等待并获取数据包

# 外层能抓到的数据
# res_dict = res.response.body
# items: list = res_dict["data"]['items']
# id: str = items[0]["id"]
# display_title: str = items[0]["note_card"]["display_title"]
# user: str = items[0]["note_card"]["user"]["nick_name"]
# liked_count: str = items[0]["note_card"]["interact_info"]["liked_count"]
# cover: str = items[0]["note_card"]["cover"]["url_default"]
# image_list: list[dict] = items[0]["note_card"]["image_list"]

def get_note_info():
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
    use: str = item["user"]["nickname"]
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

    closeBtn = tab.ele(".close close-mask-dark")
    closeBtn.click()
    
    print(note_id)
    print(ip_location)
    print(time)
    print(note_title)
    print(desc)
    print(use)
    print(image_urls)
    print(tags)
    download_images(image_urls)

# 搜索DOM元素
noteItems = tab.eles(".note-item")
if noteItems:
    count = 1
    tab.listen.start(FEED_API)
    for noteItem in noteItems:
        try:
            link = noteItem.ele(".cover ld mask").attr('href')
        except Exception as e:
            print(f"No.{count} 出现错误: {e}")
            link = None
        if link:
            print(f"No.{count} 获取到链接: {link}")
            noteItem.ele(".cover ld mask").click()
            get_note_info()
            break
        print(f"No.{count}: {link}")
        count += 1
else:
    print("未找到元素")

# with open('data.json', 'w', encoding = 'utf-8') as f:
#     json.dump(res_dict, f, ensure_ascii = False, indent = 4)
#     print("写入完毕")

tab.scroll.down(1000)
tab.wait(2)

print("退出浏览器")
tab.close()
chrome.quit()



# from DrissionPage import SessionPage

# # 创建页面对象
# page = SessionPage()


