# coding: utf-8

import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QDialog
from PyQt5.uic import loadUi
from fileutil import check_and_create


class sshconfig(QDialog):
    def __init__(self):
        super(sshconfig, self).__init__()
        loadUi("kdconfig.ui", self)
        self.config_file = os.environ["HOME"] + "/.config/kdssh/conf.json"
        self.init_confs()

    def init_confs(self):
        check_and_create(self.config_file)
        with open(self.config_file, "r") as f:
            content = f.read()
            if content.strip() != "":
                json_content = json.loads(content)
                self.confs = json_content
            else:
                self.confs = []

    @pyqtSlot()
    def on_buttonBox_accepted(self):
        conf = {}
        conf["solution"] = self.le_solution.text()
        conf["host"] = self.le_host.text()
        conf["port"] = self.le_port.text()
        conf["name"] = self.le_name.text()
        conf["password"] = self.le_password.text()

        if self.new_item_flag:
            self.confs.append(conf)
            # 更新界面的列表
            self.lw_confs.addItem(conf["solution"])
        else:
            for item in self.confs:
                if self.temp_solution == item["solution"]:
                    self.confs.remove(item)
                    self.confs.append(conf)

                    # 更新界面的列表
                    if self.temp_solution != conf["solution"]:
                        self.lw_confs.removeItemWidget(
                            self.lw_confs.takeItem(self.lw_confs.currentRow())
                        )
                        self.lw_confs.addItem(conf["solution"])
        self.update_confs()

    def edit_conf(self, solution):
        for conf in self.confs:
            if conf["solution"] == solution:
                self.le_solution.setText(conf["solution"])
                self.le_host.setText(conf["host"])
                self.le_port.setText(conf["port"])
                self.le_name.setText(conf["name"])
                self.le_password.setText(conf["password"])
                self.temp_solution = solution

    def del_conf(self, conf_solution):
        for item in self.confs:
            if conf_solution == item["solution"]:
                self.confs.remove(item)
                print("删除元素")
                self.update_confs()

    def update_confs(self):
        with open(self.config_file, "w+") as f:
            f.write(json.dumps(self.confs))
            f.flush()
