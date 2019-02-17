# coding=utf-8
import requests
import os
import fileutil
import re
import time
import json
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QInputDialog

blog_source_file =  "日志/source_blog.txt"
blog_html_file = "日志/blog.html"


post_blog_data = {
    "callCount": "1",
    "scriptSessionId": "187",
    "c0-scriptName": "BlogBeanNew",
    "c0-methodName": "getBlogsNewTheme",
    "c0-id": "0",
    # ~ "c0-param0": "",
    "c0-param1": "0",
    "c0-param2": "1",
    "batchId": "159937"
}
headers = {"contents-Type": "text/plain",
           'Referer': 'http://api.blog.163.com/crossdomain.html?publish_time=20100205',
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}


def down_blog_source(backup_dir,blog_name,user_id):
    num,ok=QInputDialog.getInt(None,"心情的数量",'请输入数字')
    if ok:
        print("心情的数量",num)
        post_blog_data["c0-param2"] = num
    else :
        post_mood_data["c0-param2"] = 1
    get_blog_url = "http://api.blog.163.com/{}/dwr/call/plaincall/BlogBeanNew.getBlogsNewTheme.dwr".format(blog_name)

    post_blog_data["c0-param0"] = user_id
    fileutil.check_and_create(backup_dir + blog_source_file)
    print("get_blog_url:{},post_blog_data:{}".format(get_blog_url,post_blog_data))
    r = requests.post(get_blog_url, data=post_blog_data, headers=headers)
    print(r.text)

    with open(backup_dir + blog_source_file ,"w+") as f:
        f.write(r.text)
        print("保存日志成功")

def convert_to_html_file(backup_dir, blog_name):
    fileutil.check_and_create(backup_dir + blog_html_file)
    with open(backup_dir+ blog_source_file,"r") as f:
        str1 = f.read()

        field_title = {}
        field_title["name"] = "title"
        field_title["pattern"] = r'(?<=title=").+?(?=";)'
        field_link = {}
        field_link["name"] = "link"
        field_link["pattern"] = r'(?<=permalink=").+?(?=";)'
        field_publishTime = {}
        field_publishTime["name"] = "publishTime"
        field_publishTime["pattern"] = r'(?<=publishTime=).+?(?=;)'
        field_accessCount = {}
        field_accessCount["name"] = "accessCount"
        field_accessCount["pattern"] = r'(?<=accessCount=).+?(?=;)'
        field_commentCount = {}
        field_commentCount["name"] = "commentCount"
        field_commentCount["pattern"] = r'(?<=commentCount=).+?(?=;)'
        field_id = {}
        field_id["name"] = "id"
        field_id["pattern"] = r'(?<=id=").+?(?=";)'
        fields = [field_title,field_link,field_publishTime,field_accessCount,field_commentCount,field_id]

        items = analyze_response(str1,fields)
        print("日志数量:{},日志内容:{}".format(len(items),items))
    html_content = "<html><meta charset='utf-8'><body>"
    items_count = len(items)
    for i,item in enumerate(items):
        print("进度:",i,"/",items_count)
        commentCount = item["commentCount"]
        html_content = html_content +"<div class='item'><div class='title'>{}</div><div class='publishTime'>{},评论({})</div><div class='link'>{}</div><hr></div>".format(item["title"],item["publishTime"],commentCount,item["link"])
        get_single_blog(backup_dir, blog_name,item)
        # ~ if commentCount != "0":
            # ~ comment_items = get_commet(blog_name,item["id"],item["commentCount"],html_content)
            # ~ html_content = append_comment(html_content,comment_items)
    html_content += "</body></html>"

    fileutil.check_and_create(backup_dir + blog_html_file)
    with open(backup_dir + blog_html_file ,"w+") as f2:
        f2.write(html_content)
    print("保存html格式的日志成功")


def convert_timestamp(t):
    publish_time_tmp =t[:-3]
    x = time.localtime(int(publish_time_tmp))
    return time.strftime('%Y-%m-%d %H:%M:%S',x)

def str_decode(word):
    return eval("u'"+word+"'")

def get_single_blog(backup_dir, blog_name,item):
    link = item["link"]
    blog_title = item["title"]
    url = "http://{}.blog.163.com/{}".format(blog_name,link)
    print("url:",url)
    r = requests.get(url)
    html_doc = r.text
    fileutil.check_and_create_dir(backup_dir + "日志/source/")
    with open(backup_dir + "日志/source/"+blog_title+".txt","w+") as f:
        f.write(r.text)
    soup = BeautifulSoup(html_doc,"lxml")
    blog_sep = soup.find("span",class_="blogsep")
    blog_catelog = soup.find("a",class_="fc03 m2a")
    print("发表时间:{},分类:{}".format(blog_sep.string,blog_catelog.string))
    blog_body = soup.find_all("div",class_="bct fc05 fc11 nbw-blog ztag")
    if blog_body:
        blog_imgs = BeautifulSoup(str(blog_body[0]),"lxml").find_all("img")
        print("正文:",blog_body[0])


    single_blog_dir = backup_dir + "日志/" +  blog_catelog.string + "/" + blog_title +"/"
    fileutil.check_and_create_dir(single_blog_dir)
    with open(backup_dir  + "日志/"  + blog_catelog.string+ "/" + blog_title+".html","w+") as f:
        content = "<html><meta charset='utf-8'><body><h1>{}</h1><div class='tag'>{} | 分类:  {}</div><hr>".format(blog_title,blog_sep.string,blog_catelog.string)
        if blog_body:
            # ~ content += str(blog_body[0])
            str_body= str(blog_body[0])
            # r'(?<=title=").+?(?=";)'
            pattern = re.compile(r'(?<=src=").+?(?=/\d+)')
            print(pattern.findall(str_body))
            content += re.sub(pattern, blog_title, str_body)
        content += "<br>阅读({}) |  评论({})".format(item["accessCount"],item["commentCount"])
        content += "</body></html>"
        f.write(content)

            # ~ 下载图片
        if blog_imgs is  None:
            for img in blog_imgs:
                print(img)
                img_name = img["src"][img["src"].rindex("/")+1:]
                print("下载图片:",img["src"],img_name)
                r = requests.get(img["src"])
                img["src"] = blog_title +"/" + img_name
                with open(single_blog_dir + img_name,"wb+") as f:
                    f.write(r.content)


def get_commet(blog_name,item_id,comment_count,html_content):
    get_blog_comment_url ="http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingsComment.dwr".format(blog_name)
    post_blog_data["c0-methodName"] ="getRecentFeelingsComment"
    post_blog_data["c0-param0"] = "string:" + item_id
    post_blog_data["c0-param1"] = comment_count
    post_blog_data["c0-param2"] = "0"
    print("get_blog_comment_url:{},data:{}".format(get_blog_comment_url,post_blog_data))
    r = requests.post(get_blog_comment_url, data=post_blog_data, headers=headers)
    print("评论:",r.text)

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
    print("评论:",items)
    return items



def append_comment(html_content,items):
    for item in items:
        html_content = html_content + '<div class="comment"><div class="publisherNickname">{}</div><div class="comment_content">{}</div><div class="comment_publishTime">{}</div></div>'.format(item["publisherNickname"],item["content"],item["publishTime"])
    print("拼接评论后的html:",html_content)
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
    print("itemCounts",itemCounts)
    for i in range(itemCounts):
        b = {}
        for matchItem in results :
            field_name = matchItem["field_name"]
            if field_name == "publishTime" :
                print("i:",i)
                b[matchItem["field_name"]] = convert_timestamp(matchItem["result"][i])
            else :
                b[matchItem["field_name"]] = str_decode(matchItem["result"][i])
        a.append(b)
    print("a :",len(a))
    return a
