# coding=utf-8
import requests
import os
import fileutil
import re
import time
import json
import sys
from PyQt5.QtCore import QThread, pyqtSignal


class backup_album(QThread):
    """ 下载心情随笔的线程 """

    show_status_signal = pyqtSignal(str)

    def __init__(self, backup_dir, blog_name):
        super().__init__()
        self.album_file = "相册_原始数据.txt"
        self.album_catelog_file = "相册目录_原始数据.txt"
        self.album_html_file = "相册.html"

        self.backup_dir = backup_dir + "相册/"
        self.blog_name = blog_name
        self.img_url_prex = "http://img2.ph.126.net"

        self.post_album_data = {
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
            # ~ "Content-Type":"application/javascript;charset=utf-8",
            # ~ "Referer": "http://qiyt72.blog.163.com/album/",
            # ~ "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
            # ~ "Host":"s1.ph.126.net"
            "User-Agent": "Mozilla/5.0(X11;Ubuntu;Linuxx86_64;rv:65.0)Gecko/20100101Firefox/65.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip,deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.post_catelog_data = {
            "callCount": "1",
            "scriptSessionId": "${scriptSessionId}187",
            "c0-scriptName": "AlbumBean",
            "c0-methodName": "getAlbumData ",
            "c0-id": "0",
            "c0-param0": "number:242741846 ",
            "c0-param1": "string:",
            "c0-param2": "string:",
            "c0-param3": "number:-191529279",
            "c0-param4": "boolean:false",
            "batchId": "594448 ",
        }
        self.post_userspace_data = {
            "callCount": "1",
            "scriptSessionId": "${scriptSessionId}187",
            "c0-scriptName": "UserSpaceBean",
            "c0-methodName": "getUserSpace",
            "c0-id": "0",
            "c0-param0": "string:bkdwei",
            "batchId": "445975",
        }

    def run(self):
        try:
            self.down_album_source()
            self.show_status_signal.emit("备份随笔结束")
        except:
            print(sys.exc_info())
            self.show_status_signal.emit("系统异常:" + str(sys.exc_info()[1]) + "\n下载失败")

    # ~ 下载原始数据
    def down_album_source(self):
        self.show_status_signal.emit("开始获取相册目录")

        self.get_userspace_url()
        catelog_outline_info = "相册总数:{}\n图片总数:{}\n相册目录地址:{}\n用户id:{}".format(
            self.albumCount, self.photoCount, self.cacheFileUrl, self.userId
        )
        self.show_status_signal.emit(catelog_outline_info)

        catelog_items = self.get_catelog_info()
        catelog_detail_info = ""
        for item in catelog_items:
            catelog_detail_info += "相册:{},图片数量:{},描述:{},id:{}\n".format(
                item["name"], item["count"], item["desc"], item["idd"]
            )
        self.show_status_signal.emit(catelog_detail_info)

        fileutil.check_and_create_dir(self.backup_dir + "source")
        for i, item in enumerate(catelog_items):
            try:
                self.show_status_signal.emit(
                    "相册进度:{}/{},{}".format(i + 1, len(catelog_items), item["name"])
                )
                self.down_single_album(item)
            except:
                print(sys.exc_info())
                self.show_status_signal.emit(
                    "系统异常:" + str(sys.exc_info()[1]) + "\n单个相册下载失败,相册:" + item["name"]
                )

    def down_single_album(self, item):
        if item["purl"].strip() != "":
            print(
                "cd {};wget http://{} -O {}.txt".format(
                    self.backup_dir + "source", item["purl"], item["name"]
                )
            )
            os.system(
                "cd {};wget http://{} -O {}.txt".format(
                    self.backup_dir + "source", item["purl"], item["name"].strip()
                )
            )

            with open(
                self.backup_dir + "source/{}.txt".format(item["name"].strip()),
                "r+",
                encoding="gb2312",
            ) as f:
                content = f.read().strip()
                # ~ print("content:",content)
                field_desc = {}
                field_desc["name"] = "desc"
                field_desc["pattern"] = r"(?<=desc:\').*?(?=\',)"
                # ~ field_desc["pattern"] = r"var"
                field_purl = {}
                field_purl["name"] = "murl"
                field_purl["pattern"] = r"(?<=murl:\').*?(?=\',)"
                fields = [field_desc, field_purl]
                photos = self.analyze_response(str(content), fields)
                print(item["name"], "相册目录信息:", photos)

                if len(photos) > 0:
                    fileutil.check_and_create_dir(self.backup_dir + item["name"])
                for i, photo in enumerate(photos):
                    try:
                        r = requests.get(self.img_url_prex + photo["murl"][1:])
                        if photo["desc"] == "":
                            slash_index = photo["murl"].rindex("/")
                            photo["desc"] = photo["murl"][slash_index:]
                        else:
                            slash_index = photo["murl"].rindex(".")
                            photo["desc"] = (
                                photo["desc"].replace(".JPG", "")
                                + photo["murl"][slash_index:]
                            )
                        print("下载图片:{},{}".format(photo["desc"], photo["murl"]))
                        self.show_status_signal.emit(
                            "相册:{},{}/{},图片:{}".format(
                                item["name"], i, len(photos), photo["desc"]
                            )
                        )
                        with open(
                            self.backup_dir + item["name"] + "/" + photo["desc"], "wb+"
                        ) as f:
                            f.write(r.content)
                    except:
                        print(sys.exc_info())
                        self.show_status_signal.emit(
                            "系统异常:"
                            + str(sys.exc_info()[1])
                            + "\n单张图片下载失败,图片:"
                            + photo["desc"]
                        )
        else:
            self.show_status_signal.emit("空相册:{}".format(item["name"]))

    # ~ 获取相册目录
    def get_catelog_info(self):
        fileutil.check_and_create_dir(self.backup_dir + "source")
        print(self.cacheFileUrl)
        print(
            "cd {};wget http://{} -O {}.txt".format(
                self.backup_dir + "source", self.cacheFileUrl, "catelog_info.txt"
            )
        )
        os.system(
            "cd {};wget http://{} -O {}.txt".format(
                self.backup_dir + "source", self.cacheFileUrl, "catelog_info"
            )
        )

        with open(
            self.backup_dir + "source/catelog_info.txt", "r", encoding="gb2312"
        ) as f:
            content = f.read().strip()
            self.show_status_signal.emit("获取相册目录成功")

            field_name = {}
            field_name["name"] = "name"
            field_name["pattern"] = r"(?<=name:\').+?(?=\',)"
            field_desc = {}
            field_desc["name"] = "desc"
            field_desc["pattern"] = r"(?<=desc:\').*?(?=\',)"
            field_count = {}
            field_count["name"] = "count"
            field_count["pattern"] = r"(?<=count:).+?(?=,)"
            field_purl = {}
            field_purl["name"] = "purl"
            field_purl["pattern"] = r"(?<=purl:\').*?(?=\'})"
            field_id = {}
            field_id["name"] = "idd"
            field_id["pattern"] = r"(?<={id:).+?(?=,)"
            fields = [field_name, field_desc, field_count, field_purl, field_id]
            catelog_items = self.analyze_response(content, fields)
            print("相册目录信息:", catelog_items)
            return catelog_items

    # ~ 获取相册概览信息
    def get_userspace_url(self):
        album_catelog_url = "http://photo.163.com/photo/{}/dwr/call/plaincall/UserSpaceBean.getUserSpace.dwr?u={}".format(
            self.blog_name, self.blog_name
        )
        self.post_userspace_data["c0-param0"] = self.blog_name
        r = requests.post(
            album_catelog_url, data=self.post_userspace_data, headers=self.headers
        )
        fileutil.check_and_create(self.backup_dir + self.album_file)
        with open(self.backup_dir + self.album_catelog_file, "w+") as f:
            f.write(r.text)
            self.show_status_signal.emit("下载心情随笔的原始数据成功\n开始解析原始数据")
            self.albumCount = re.search(r"(?<=albumCount:).+?(?=,)", r.text)[0]
            self.photoCount = re.search(r"(?<=photoCount:).+?(?=,)", r.text)[0]
            self.userId = re.search(r"(?<=userId:).+?(?=,)", r.text)[0]
            self.usedSpace = re.search(r"(?<=usedSpace:).+?(?=,)", r.text)[0]
            self.cacheFileUrl = re.search(r'(?<=cacheFileUrl:").+?(?=",)', r.text)[0]
            print(self)

    # ~ 将时间戳转换成格式化的字符串
    def convert_timestamp(self, t):
        publish_time_tmp = t[:-3]
        x = time.localtime(int(publish_time_tmp))
        return time.strftime("%Y-%m-%d %H:%M:%S", x)

    # ~ 解析\uXXX类型的文字为中文
    def str_decode(self, word):
        return eval("u'" + word + "'")

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
            print(field["pattern"], itemCounts)
            print("itemCounts", itemCounts)
        for i in range(itemCounts):
            print("i:", i)
            b = {}
            for matchItem in results:
                print("field_name:" + matchItem["field_name"], matchItem["result"][i])
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
