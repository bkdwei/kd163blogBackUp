# coding=utf-8
import requests
import os
import fileutil
import re
import time
import json
from PyQt5.QtWidgets import QInputDialog

mood_file ="心情随笔_原始数据.txt"
mood_html_file ="心情随笔.html"


post_mood_data = {
    "callCount": "1",
    "scriptSessionId": "187",
    "c0-scriptName": "FeelingsBeanNew",
    "c0-methodName": "getRecentFeelingCards",
    "c0-id": "0",
    # ~ "c0-param0": "",
    "c0-param1": "0",
    "c0-param2": "3",
    "batchId": "418342"
}
headers = {"contents-Type": "text/plain",
           'Referer': 'http://api.blog.163.com/crossdomain.html?publish_time=20100205',
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}


def down_mood_source(backup_dir,blog_name,user_id):
    num,ok=QInputDialog.getInt(None,"心情的数量",'请输入数字')
    if ok:
        print("心情的数量",num)
        post_mood_data["c0-param2"] = num
    else :
        post_mood_data["c0-param2"] = 1
    get_mood_url = "http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingCards.dwr".format(blog_name)

    post_mood_data["c0-param0"] = user_id
    fileutil.check_and_create(backup_dir + mood_file)
    print("get_mood_url:{},post_mood_data:{}".format(get_mood_url,post_mood_data))
    r = requests.post(get_mood_url, data=post_mood_data, headers=headers)
    # ~ print(r.text)

    with open(backup_dir + mood_file ,"w+") as f:
        f.write(r.text)
        print("下载心情随笔成功")

def add_show_info(msg):
    show_info = tb_result.toPlainText() + "\n"  + msg
    tb_result.setText(show_info)

def convert_to_html_file(backup_dir,blog_name):
    with open(backup_dir + mood_file,"r") as f:
        str1 = f.read().strip()

        if str1 == "":
            print("str1 is null")
            return

        field_content = {}
        field_content["name"] = "content"
        field_content["pattern"] = r'(?<=content=").+?(?=";)'
        field_publishTime = {}
        field_publishTime["name"] = "publishTime"
        field_publishTime["pattern"] = r'(?<=publishTime=).+?(?=;)'
        field_commentCount = {}
        field_commentCount["name"] = "commentCount"
        field_commentCount["pattern"] = r'(?<=commentCount=).+?(?=;)'
        field_id = {}
        field_id["name"] = "id"
        field_id["pattern"] = r'(?<=id=").+?(?=";)'
        fields = [field_content,field_publishTime,field_commentCount,field_id]

        items = analyze_response(str1,fields)
        print("心情随笔:",items)

    html_content = "<html><meta charset='utf-8'><body>"
    items_count = len(items)
    for i,item in enumerate(items):
        print("进度:",i+1,"/",items_count)
        commentCount = item["commentCount"]
        html_content = html_content +"<div class='item'><div class='content'>"+item["content"] + "</div><div class='publishTime'>" + item["publishTime"] +",评论(" +commentCount +")</div><hr></div>"
        if commentCount != "0":
            comment_items = get_commet(blog_name,item["id"],item["commentCount"])
            html_content += append_comment(comment_items)
    html_content += "</body></html>"

    fileutil.check_and_create(backup_dir + mood_html_file)
    with open(backup_dir + mood_html_file ,"w+") as f2:
        f2.write(html_content)
    print("保存html格式的心情随笔成功",html_content)


def convert_timestamp(t):
    publish_time_tmp =t[:-3]
    x = time.localtime(int(publish_time_tmp))
    return time.strftime('%Y-%m-%d %H:%M:%S',x)

def str_decode(word):
    return eval("u'"+word+"'")

def get_commet(blog_name,item_id,comment_count):
    get_mood_comment_url ="http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingsComment.dwr".format(blog_name)
    post_mood_data["c0-methodName"] ="getRecentFeelingsComment"
    post_mood_data["c0-param0"] = "string:" + item_id
    post_mood_data["c0-param1"] = comment_count
    post_mood_data["c0-param2"] = "0"
    print("get_mood_comment_url:{},data:{}".format(get_mood_comment_url,post_mood_data))
    r = requests.post(get_mood_comment_url, data=post_mood_data, headers=headers)
    # ~ print("评论:",r.text)

    field_content = {}
    field_content["name"] = "content"
    field_content["pattern"] = r'(?<=content=").+?(?=";)'
    field_publishTime = {}
    field_publishTime["name"] = "publishTime"
    field_publishTime["pattern"] = r'(?<=publishTime=).+?(?=;)'
    field_commentCount = {}
    field_commentCount["name"] = "publisherNickname"
    field_commentCount["pattern"] = r'(?<=publisherNickname=").+?(?=";)'
    fields = [field_content,field_publishTime,field_commentCount]

    items = analyze_response(r.text,fields)
    print("评论:",len(items))
    return items



def append_comment(items):
    html_content =""
    for item in items:
        html_content +=  '<div class="comment"><div class="publisherNickname">{}</div><div class="comment_content">{}</div><div class="comment_publishTime">{}</div></div>'.format(item["publisherNickname"],item["content"],item["publishTime"])
    # ~ print("拼接评论后的html:",html_content)
    return html_content
def analyze_response(text,fields):
    results=[]
    itemCounts = 0
    a = []
    for field in fields :
        matchs = re.findall(field["pattern"],text)
        itemCounts = len(matchs)

        matchItem ={}
        matchItem["field_name"] = field["name"]
        matchItem["result"] = matchs
        results.append(matchItem)
    # ~ print("itemCounts",itemCounts)
    for i in range(itemCounts):
        b = {}
        for matchItem in results :
            field_name = matchItem["field_name"]
            if field_name == "publishTime" :
                b[matchItem["field_name"]] = convert_timestamp(matchItem["result"][i])
            else :
                b[matchItem["field_name"]] = str_decode(matchItem["result"][i])
        a.append(b)
    print("a :",len(a))
    return a
