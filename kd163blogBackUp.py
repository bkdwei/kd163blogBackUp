# coding: utf-8

import os
import sys
import requests
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from kdconfig import sshconfig
import backup_mood
import backup_blog
import fileutil


class kd163blogBackUp(QWidget):
    def __init__(self):
        super(kd163blogBackUp, self).__init__()
        loadUi("kd163blogBackUp.ui", self)
        backup_mood.tb_result = self.tb_result
        # ~ r = requests.get("http://qiyt72.blog.163.com/blog/static/1620782201711149821617/")
        # ~ print(r.text)
        # ~ with open("gg.html","w+") as a:
            # ~ a.write(r.text)

    def create_dir(self):
        self.backup_dir = os.getcwd() +"/" + self.le_blog_name.text() +"的博客备份/"
        fileutil.check_and_create_dir(self.backup_dir)
    @pyqtSlot()
    def on_pb_backup_mood_clicked(self):
        self.create_dir()
        # ~ self.add_show_info("正在备份心情随笔......")
        blog_name = self.le_blog_name.text()
        self.get_user_id()
        backup_mood.down_mood_source(self.backup_dir,blog_name,self.user_id)
        # ~ self.add_show_info("下载心情随笔成功,开始保存内容.....")
        backup_mood.convert_to_html_file(self.backup_dir,blog_name)
        self.add_show_info("备份随笔结束")
    @pyqtSlot()
    def on_pb_backup_blog_clicked(self):
        self.create_dir()
        self.add_show_info("正在备份日志......")
        blog_name = self.le_blog_name.text()
        self.get_user_id()
        backup_blog.down_blog_source(self.backup_dir,blog_name,self.user_id)
        self.add_show_info("下载日志成功,开始保存内容.....")
        backup_blog.convert_to_html_file(self.backup_dir,blog_name)
        self.add_show_info("备份日志成功")

    def add_show_info(self,msg):
        show_info = self.tb_result.toPlainText() + "\n"  + msg
        self.tb_result.setText(show_info)
    def get_user_id(self):
        r = requests.get("http://" + self.le_blog_name.text() + ".blog.163.com/")
        # ~ print("返回的结果:"+ r.text)
        pt_user_id  = re.compile(r'(?<=userId:").+?(?=,userName)')
        user_id =pt_user_id.match(r.text)
        user_id = re.search('(?<=userId:).+?(?=,)',r.text).group()
        print("您的用户id是" , user_id)
        self.add_show_info("您的用户id是" + user_id)
        self.user_id = user_id


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = kd163blogBackUp()
    win.show()
    sys.exit(app.exec_())
