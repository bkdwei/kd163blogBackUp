#!/usr/bin/env  python3
#-*- coding:utf-8 -*-

import os
import sys
import requests
import re
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QInputDialog
from kdconfig import sshconfig
from backup_mood import backup_mood
from backup_blog import backup_blog
from backup_album import backup_album
import fileutil


class kd163blogBackUp(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("kd163blogBackUp.ui", self)
        self.user_id = None

    # ~ 生成个人的备份目录
    def create_dir(self):
        self.backup_dir = os.getcwd() + "/" + self.le_blog_name.text() + "的博客备份/"
        fileutil.check_and_create_dir(self.backup_dir)

    @pyqtSlot()
    def on_pb_backup_mood_clicked(self):
        num, ok = QInputDialog.getInt(None, "心情随笔的数量", "请输入要备份的数量")
        if ok:
            mood_count = num
        else:
            return

        self.create_dir()
        blog_name = self.le_blog_name.text()
        self.get_user_id()

        # ~ 启动下载线程
        self.backup_mood_thread = backup_mood(
            self.backup_dir, self.le_blog_name.text(), self.user_id, mood_count
        )
        self.backup_mood_thread.show_status_signal.connect(self.add_show_info)
        self.backup_mood_thread.start()

    @pyqtSlot()
    def on_pb_backup_blog_clicked(self):
        num, ok = QInputDialog.getInt(None, "日志的数量", "请输入要备份的数量")
        if ok:
            blog_count = num
        else:
            blog_count = 1

        self.create_dir()
        blog_name = self.le_blog_name.text()
        self.get_user_id()

        # ~ 启动下载线程
        self.backup_blog_thread = backup_blog(
            self.backup_dir,
            self.le_blog_name.text(),
            self.user_id,
            blog_count,
            self.chkB_continue_on_failure.isChecked(),
        )
        self.backup_blog_thread.show_status_signal.connect(self.add_show_info)
        self.backup_blog_thread.start()

    def add_show_info(self, msg):
        # ~ show_info = self.tb_result.toPlainText() + msg + "\n"
        self.tb_result.append(msg +"\n")
        self.tb_result.moveCursor(self.tb_result.textCursor().End)

    def get_user_id(self):
        if self.user_id is not None:
            pass
        else:
            print("开始查询用户id")
            r = requests.get("http://" + self.le_blog_name.text() + ".blog.163.com/")
            # ~ print("返回的结果:"+ r.text)
            pt_user_id = re.compile(r'(?<=userId:").+?(?=,userName)')
            user_id = pt_user_id.match(r.text)
            user_id = re.search("(?<=userId:).+?(?=,)", r.text).group()
            print("您的用户id是", user_id)
            self.add_show_info("您的用户id是" + user_id)
            self.user_id = user_id

    @pyqtSlot()
    def on_pb_backup_album_clicked(self):
        self.create_dir()
        blog_name = self.le_blog_name.text()

        # ~ 启动下载线程
        self.backup_album_thread = backup_album(
            self.backup_dir,
            self.le_blog_name.text()
        )
        self.backup_album_thread.show_status_signal.connect(self.add_show_info)
        self.backup_album_thread.start()

    @pyqtSlot()
    def on_pb_open_blog_clicked(self):
        webbrowser.open_new_tab(
            "http://{}.blog.163.com".format(self.le_blog_name.text())
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = kd163blogBackUp()
    win.show()
    sys.exit(app.exec_())
