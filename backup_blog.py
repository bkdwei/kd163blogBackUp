# coding=utf-8
import requests
import os
import fileutil
import re
import time
import json
import sys
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal


class backup_blog(QThread):
    """ 下载日志的线程 """

    show_status_signal = pyqtSignal(str)

    def __init__(self, backup_dir, blog_name, user_id, blog_count, continue_on_failure):
        super().__init__()
        self.blog_source_file = "日志/source_blog.txt"
        self.blog_html_file = "日志/blog.html"

        self.backup_dir = backup_dir
        self.blog_name = blog_name
        self.user_id = user_id
        self.blog_count = blog_count
        self.continue_on_failure = continue_on_failure
        self.continue_index = 0
        if continue_on_failure :
            fileutil.check_and_create(backup_dir + "config.json")
            with open(backup_dir + "config.json","r") as f:
                index_content = f.read().strip()
                if f.read().strip():
                    self.continue_index = int(index_content)

        self.post_blog_data = {
            "callCount": "1",
            "scriptSessionId": "187",
            "c0-scriptName": "BlogBeanNew",
            "c0-methodName": "getBlogsNewTheme",
            "c0-id": "0",
            # ~ "c0-param0": "",
            "c0-param1": "0",
            "c0-param2": "1",
            "batchId": "159937",
        }
        self.headers = {
            "contents-Type": "text/plain",
            "Referer": "http://api.blog.163.com/crossdomain.html?publish_time=20100205",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
        }

    def run(self):
        try:
            # ~ if self.continue_on_failure is not True:
            self.down_blog_source()
            self.convert_to_html_file()
            self.show_status_signal.emit("备份随笔结束")
        except:
            if self.continue_on_failure :
                fileutil.check_and_create(self.backup_dir + "config.json")
                with open(self.backup_dir + "config.json","r") as f:
                    f.write(str(self.continue_index))
            print(sys.exc_info())
            self.show_status_signal.emit("系统异常:" + str(sys.exc_info()[1]) + "\n下载失败")

    def down_blog_source(self):
        self.show_status_signal.emit("开始下载{}条日志".format(self.blog_count))

        get_blog_url = "http://api.blog.163.com/{}/dwr/call/plaincall/BlogBeanNew.getBlogsNewTheme.dwr".format(
            self.blog_name
        )
        self.post_blog_data["c0-param0"] = self.user_id
        self.post_blog_data["c0-param2"] = self.blog_count

        fileutil.check_and_create(self.backup_dir + self.blog_source_file)
        print(
            "get_blog_url:{},post_blog_data:{}".format(
                get_blog_url, self.post_blog_data
            )
        )
        r = requests.post(get_blog_url, data=self.post_blog_data, headers=self.headers)
        # ~ print(r.text)

        with open(self.backup_dir + self.blog_source_file, "w+") as f:
            f.write(r.text)
            self.show_status_signal.emit("下载日志的原始数据成功\n开始解析原始数据")

    def convert_to_html_file(self):
        fileutil.check_and_create(self.backup_dir + self.blog_html_file)
        with open(self.backup_dir + self.blog_source_file, "r") as f:
            str1 = f.read().strip()
            field_title = {}
            field_title["name"] = "title"
            field_title["pattern"] = r'(?<=title=").+?(?=";)'
            field_link = {}
            field_link["name"] = "link"
            field_link["pattern"] = r'(?<=permalink=").+?(?=";)'
            field_publishTime = {}
            field_publishTime["name"] = "publishTime"
            field_publishTime["pattern"] = r"(?<=publishTime=).+?(?=;)"
            field_accessCount = {}
            field_accessCount["name"] = "accessCount"
            field_accessCount["pattern"] = r"(?<=accessCount=).+?(?=;)"
            field_commentCount = {}
            field_commentCount["name"] = "commentCount"
            field_commentCount["pattern"] = r"(?<=commentCount=).+?(?=;)"
            field_id = {}
            field_id["name"] = "id"
            field_id["pattern"] = r'(?<=id=").+?(?=";)'
            fields = [
                field_title,
                field_link,
                field_publishTime,
                field_accessCount,
                field_commentCount,
                field_id,
            ]

            items = self.analyze_response(str1, fields)
            print("日志数量:{},日志内容:{}".format(len(items), items))

        html_content = "<html><meta charset='utf-8'><body>"
        items_count = len(items)
        for i, item in enumerate(items,self.continue_index -1):
            self.continue_index = i
            self.show_status_signal.emit("进度:{}/{},{}".format(i + 1, items_count, item["title"]))
            commentCount = item["commentCount"]
            html_content = (
                html_content
                + "<div class='item'><div class='title'>{}</div><div class='publishTime'>{},评论({})</div><div class='link'>{}</div><hr></div>".format(
                    item["title"], item["publishTime"], commentCount, item["link"]
                )
            )
            try:
                self.get_single_blog(item, i + 1)
            except:
                self.show_status_signal.emit("系统异常:" + str(sys.exc_info()[1]) + "\n下载失败")
            # ~ if commentCount != "0":
            # ~ self.show_status_signal.emit(
            # ~ "正在获取第{}条日志的{}条评论".format(i + 1, commentCount)
            # ~ )
            # ~ comment_items = get_commet(self.blog_name,item["id"],item["commentCount"],html_content)
            # ~ html_content = append_comment(html_content,comment_items)
        html_content += "</body></html>"

        fileutil.check_and_create(self.backup_dir + self.blog_html_file)
        with open(self.backup_dir + self.blog_html_file, "w+") as f2:
            f2.write(html_content)
        print("保存html格式的日志成功")

    def convert_timestamp(self, t):
        publish_time_tmp = t[:-3]
        x = time.localtime(int(publish_time_tmp))
        return time.strftime("%Y-%m-%d %H:%M:%S", x)

    def str_decode(self, word):
        return eval("u'" + word + "'")

    def get_single_blog(self, item, item_index):
        link = item["link"]
        blog_title = item["title"]
        url = "http://{}.blog.163.com/{}".format(self.blog_name, link)
        print("url:", url)
        r = requests.get(url)
        html_doc = r.text
        fileutil.check_and_create_dir(self.backup_dir + "日志/source/")
        with open(self.backup_dir + "日志/source/" + blog_title + ".txt", "w+") as f:
            f.write(r.text)
        soup = BeautifulSoup(html_doc, "lxml")
        blog_sep = soup.find("span", class_="blogsep")
        blog_catelog = soup.find("a", class_="fc03 m2a")
        if blog_sep is None :
            print("无权限访问:" + item["title"])
            pass
            return
        print("发表时间:{},分类:{}".format(blog_sep.string, blog_catelog.string))
        blog_body = soup.find_all("div", class_="bct fc05 fc11 nbw-blog ztag")
        if blog_body:
            blog_imgs = BeautifulSoup(str(blog_body[0]), "lxml").find_all("img")
            print("正文:", blog_body[0])

        single_blog_dir = (
            self.backup_dir + "日志/" + blog_catelog.string + "/" + blog_title + "/"
        )
        fileutil.check_and_create_dir(single_blog_dir)
        with open(
            self.backup_dir + "日志/" + blog_catelog.string + "/" + blog_title + ".html",
            "w+",
        ) as f:
            content = "<html><meta charset='utf-8'><body><h1>{}</h1><div class='tag'>{} | 分类:  {}</div><hr>".format(
                blog_title, blog_sep.string, blog_catelog.string
            )
            if blog_body:
                # ~ content += str(blog_body[0])
                str_body = str(blog_body[0])
                # r'(?<=title=").+?(?=";)'
                # ~ r'(?<=src=").+?(?/=\d{5})'
                pattern = re.compile(r'(?<=src=").+?(?=/\d{5})')
                print(pattern.findall(str_body))
                content += re.sub(pattern, blog_title, str_body)
            content += "<br>阅读({}) |  评论({})".format(
                item["accessCount"], item["commentCount"]
            )
            content += "</body></html>"
            f.write(content)

            # ~ 下载图片
            if blog_imgs:
                self.show_status_signal.emit(
                    "正在获取日志:{}的{}张图片".format(item["title"], len(blog_imgs))
                )
                for img in blog_imgs:
                    print(img)
                    if img["src"]:
                        img_name = img["src"][img["src"].rindex("/") + 1 :]
                        print("下载图片:", img["src"], img_name)
                        self.show_status_signal.emit(
                            '下载图片:{}'.format(img["src"])
                        )
                        r = requests.get(img["src"])
                        img["src"] = blog_title + "/" + img_name
                        with open(single_blog_dir + img_name, "wb+") as f:
                            f.write(r.content)

    def get_commet(self, item_id, comment_count, html_content):
        get_blog_comment_url = "http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingsComment.dwr".format(
            self.blog_name
        )
        self.post_blog_data["c0-methodName"] = "getRecentFeelingsComment"
        self.post_blog_data["c0-param0"] = "string:" + item_id
        self.post_blog_data["c0-param1"] = comment_count
        self.post_blog_data["c0-param2"] = "0"
        print(
            "get_blog_comment_url:{},data:{}".format(
                get_blog_comment_url, self.post_blog_data
            )
        )
        r = requests.post(
            get_blog_comment_url, data=self.post_blog_data, headers=self.headers
        )
        print("评论:", r.text)

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
        print("评论:", items)
        return items

    def append_comment(self, html_content, items):
        for item in items:
            html_content = (
                html_content
                + '<div class="comment"><div class="publisherNickname">{}</div><div class="comment_content">{}</div><div class="comment_publishTime">{}</div></div>'.format(
                    item["publisherNickname"], item["content"], item["publishTime"]
                )
            )
        print("拼接评论后的html:", html_content)
        return html_content

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
        print("itemCounts", itemCounts)
        for i in range(itemCounts):
            b = {}
            for matchItem in results:
                field_name = matchItem["field_name"]
                if field_name == "publishTime":
                    print("i:", i)
                    b[matchItem["field_name"]] = self.convert_timestamp(
                        matchItem["result"][i]
                    )
                else:
                    b[matchItem["field_name"]] = self.str_decode(matchItem["result"][i])
            a.append(b)
        print("a :", len(a))
        return a
