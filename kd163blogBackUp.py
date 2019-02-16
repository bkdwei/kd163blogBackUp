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


class kd163blogBackUp(QWidget):
    def __init__(self):
        super(kd163blogBackUp, self).__init__()
        loadUi("kd163blogBackUp.ui", self)

    def on_pb_backup_mood_clicked(self):
        self.add_show_info("正在备份心情随笔......")
        blog_name = self.le_blog_name.text()
        # ~ self.get_user_id()
        # ~ backup_mood.down_mood_source(blog_name,self.user_id)
        self.add_show_info("下载心情随笔成功,开始保存内容.....")
        backup_mood.convert_to_json_file(blog_name)
        self.add_show_info("保存内容成功,\n下载心情随笔结束")


    def add_show_info(self,msg):
        show_info = self.tb_result.toPlainText() + "\n"  + msg
        self.tb_result.setText(show_info)
    def get_user_id(self):
        r = requests.get("http://" + self.le_blog_name.text() + ".blog.163.com/")
        print("返回的结果:"+ r.text)
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
