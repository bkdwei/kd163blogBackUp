# coding=utf-8
import requests
import os
import fileutil
import re
import time
import json
import sys
from PyQt5.QtCore import QThread, pyqtSignal


class backup_mood(QThread):
    """ 下载心情随笔的线程 """

    show_status_signal = pyqtSignal(str)

    def __init__(self, backup_dir, blog_name, user_id, mood_count):
        super().__init__()
        self.mood_file = "心情随笔_原始数据.txt"
        self.mood_html_file = "心情随笔.html"

        self.backup_dir = backup_dir
        self.blog_name = blog_name
        self.user_id = user_id
        self.mood_count = mood_count

        self.post_mood_data = {
            "callCount": "1",
            "scriptSessionId": "187",
            "c0-scriptName": "FeelingsBeanNew",
            "c0-methodName": "getRecentFeelingCards",
            "c0-id": "0",
            # ~ "c0-param0": "",
            "c0-param1": "0",
            "c0-param2": "3",
            "batchId": "418342",
        }
        self.headers = {
            "contents-Type": "text/plain",
            "Referer": "http://api.blog.163.com/crossdomain.html?publish_time=20100205",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
        }

    def run(self):
        try:
            self.down_mood_source()
            self.convert_to_html_file()
            self.show_status_signal.emit("备份随笔结束")
        except:
            print(sys.exc_info())
            self.show_status_signal.emit("系统异常:" + str(sys.exc_info()[1]) + "\n下载失败")

    # ~ 下载原始数据
    def down_mood_source(self):
        self.show_status_signal.emit("开始下载{}条心情随笔".format(self.mood_count))

        get_mood_url = "http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingCards.dwr".format(
            self.blog_name
        )
        self.post_mood_data["c0-param0"] = self.user_id
        self.post_mood_data["c0-param2"] = self.mood_count
        print(
            "get_mood_url:{},self.post_mood_data:{}".format(
                get_mood_url, self.post_mood_data
            )
        )
        r = requests.post(get_mood_url, data=self.post_mood_data, headers=self.headers)
        # ~ print(r.text)

        fileutil.check_and_create(self.backup_dir + self.mood_file)
        with open(self.backup_dir + self.mood_file, "w+") as f:
            f.write(r.text)
            self.show_status_signal.emit("下载心情随笔的原始数据成功")

    # ~ 解析下载下来的数据并生成html文件
    def convert_to_html_file(self):
        with open(self.backup_dir + self.mood_file, "r") as f:
            str1 = f.read().strip()
            field_content = {}
            field_content["name"] = "content"
            field_content["pattern"] = r'(?<=content=").+?(?=";)'
            field_publishTime = {}
            field_publishTime["name"] = "publishTime"
            field_publishTime["pattern"] = r"(?<=publishTime=).+?(?=;)"
            field_commentCount = {}
            field_commentCount["name"] = "commentCount"
            field_commentCount["pattern"] = r"(?<=commentCount=).+?(?=;)"
            field_id = {}
            field_id["name"] = "id"
            field_id["pattern"] = r'(?<=id=").+?(?=";)'
            fields = [field_content, field_publishTime, field_commentCount, field_id]

            items = self.analyze_response(str1, fields)
            print("心情随笔:", items)

        html_content = "<html><meta charset='utf-8'><body>"
        items_count = len(items)
        for i, item in enumerate(items):
            self.show_status_signal.emit("进度:" + str(i + 1) + "/" + str(items_count))
            commentCount = item["commentCount"]
            html_content = (
                html_content
                + "<div class='item'><div class='content'>"
                + item["content"]
                + "</div><div class='publishTime'>"
                + item["publishTime"]
                + ",评论("
                + commentCount
                + ")</div><hr></div>"
            )
            if commentCount != "0":
                self.show_status_signal.emit(
                    "正在获取第{}条心情随笔的{}条评论".format(i + 1, commentCount)
                )
                comment_items = self.get_commet(item["id"], item["commentCount"])
                html_content += self.append_comment(comment_items)
        html_content += "</body></html>"

        fileutil.check_and_create(self.backup_dir + self.mood_html_file)
        with open(self.backup_dir + self.mood_html_file, "w+") as f2:
            f2.write(html_content)
        print("保存html格式的心情随笔成功", html_content)

    # ~ 将时间戳转换成格式化的字符串
    def convert_timestamp(self, t):
        publish_time_tmp = t[:-3]
        x = time.localtime(int(publish_time_tmp))
        return time.strftime("%Y-%m-%d %H:%M:%S", x)

    # ~ 解析\uXXX类型的文字为中文
    def str_decode(self, word):
        return eval("u'" + word + "'")

    # ~ 获取心情随笔的评论
    def get_commet(self, item_id, comment_count):
        get_mood_comment_url = "http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingsComment.dwr".format(
            self.blog_name
        )
        self.post_mood_data["c0-methodName"] = "getRecentFeelingsComment"
        self.post_mood_data["c0-param0"] = "string:" + item_id
        self.post_mood_data["c0-param1"] = comment_count
        self.post_mood_data["c0-param2"] = "0"
        print(
            "get_mood_comment_url:{},data:{}".format(
                get_mood_comment_url, self.post_mood_data
            )
        )
        r = requests.post(
            get_mood_comment_url, data=self.post_mood_data, headers=self.headers
        )
        # ~ print("评论:",r.text)

        field_content = {}
        field_content["name"] = "content"
        field_content["pattern"] = r'(?<=content=").+?(?=";)'
        field_publishTime = {}
        field_publishTime["name"] = "publishTime"
        field_publishTime["pattern"] = r"(?<=publishTime=).+?(?=;)"
        field_commentCount = {}
        field_commentCount["name"] = "publisherNickname"
        field_commentCount["pattern"] = r'(?<=publisherNickname=").+?(?=";)'
        fields = [field_content, field_publishTime, field_commentCount]

        items = self.analyze_response(r.text, fields)
        print("评论:", len(items))
        return items

    # ~ 给html文件附加心情随笔的评论
    def append_comment(self, items):
        html_content = ""
        for item in items:
            html_content += '<div class="comment"><div class="publisherNickname">{}</div><div class="comment_content">{}</div><div class="comment_publishTime">{}</div></div>'.format(
                item["publisherNickname"], item["content"], item["publishTime"]
            )
        # ~ print("拼接评论后的html:",html_content)
        return html_content

    # ~ 将原始数据解析成结构化的python对象
    def analyze_response(self, text, fields):
        results = []
        itemCounts = 0
        a = []
        for field in fields:
            matchs = re.findall(field["pattern"], text)
            itemCounts = len(matchs)

            matchItem = {}
            matchItem["field_name"] = field["name"]
            matchItem["result"] = matchs
            results.append(matchItem)
        # ~ print("itemCounts",itemCounts)
        for i in range(itemCounts):
            b = {}
            for matchItem in results:
                field_name = matchItem["field_name"]
                if field_name == "publishTime":
                    b[matchItem["field_name"]] = self.convert_timestamp(
                        matchItem["result"][i]
                    )
                else:
                    b[matchItem["field_name"]] = self.str_decode(matchItem["result"][i])
            a.append(b)
        print("a :", len(a))
        return a
