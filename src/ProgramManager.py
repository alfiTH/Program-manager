#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''Programa de visualización y manejo de programas '''

import sys
from PySide6 import QtCore, QtWidgets, QtGui
import EditUI
import time
import pandas


__author__ = EditUI.__author__
__copyright__ = EditUI.__copyright__
__credits__ = EditUI.__credits__
__license__ = EditUI.__license__
__version__ = EditUI.__version__
__date__ = EditUI.__date__
__maintainer__ = EditUI.__maintainer__
__email__ = EditUI.__email__
__status__ = EditUI.__status__

def loadconfig(filename):
    return pandas.read_csv(filename,delimiter=";")


class MyWidget(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.table = QtWidgets.QTableWidget(self)
        columnas = EditUI.RowProgram.titlesColums
        self.table.setColumnCount(len(columnas))
        self.row = len(config.index)
        self.rows =[]
        #self.setCentralWidget(self.table)

        #Ajuste de columnas a estrechas
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode().ResizeToContents) 
        #Cantidad de filas
        self.table.setRowCount(self.row)
        #Tamaño y posicion tabla
        self.table.setGeometry(QtCore.QRect(50, 0, 950, 36*self.row))
        #Titulos de las columnas
        self.table.setHorizontalHeaderLabels(columnas)

        for y in range(self.row):
            self.rows.append(EditUI.RowProgram(ssh=config["SSH"].iloc[y], 
                    device=config["Device"].iloc[y],ping=config["Ping"].iloc[y],path=config["Path"].iloc[y],
                    program=config["Program"].iloc[y], config=config["Config"].iloc[y]))
            for x, cell in enumerate(self.rows[y].get_row().values()):
                self.table.setCellWidget(y,x,cell)

    def __del__ (self):
        print("delete all")
        for r in self.rows:
            r.__del__()

    def handleButtonClicked(self):
        button = self.sender()
        button.function()
        

if __name__ == "__main__":
    assert len(sys.argv) == 2, "Falta el config"
    
    app = QtWidgets.QApplication([])

    config = loadconfig(sys.argv[1]).astype("string")
    print(config.to_string())

    widget = MyWidget(config=config)
    widget.resize(1100, 600)
    widget.show()
    
    app.exec()
    widget.__del__()
    
    sys.exit()



#     from subprocess import Popen, PIPE


# def kill(pid, passwd):
#     pipe = Popen(['sudo', '-S', 'kill', '-9', str(pid)], 
#                  stdout=PIPE, 
#                  stdin=PIPE, 
#                  stderr=PIPE)
#     pipe.stdin.write(bytes(passwd + '\n', encoding='utf-8'))
#     pipe.stdin.flush()
#     # at this point, the process is killed, return output and errors
#     return (str(pipe.stdout.read()), str(pipe.stderr.read()))


# from __future__ import print_function,unicode_literals
# import subprocess

# sshProcess = subprocess.Popen(['ssh',
#                                '-tt'
#                                <remote client>],
#                                stdin=subprocess.PIPE, 
#                                stdout = subprocess.PIPE,
#                                universal_newlines=True,
#                                bufsize=0)
# sshProcess.stdin.write("ls .\n")
# sshProcess.stdin.write("echo END\n")
# sshProcess.stdin.write("uptime\n")
# sshProcess.stdin.write("logout\n")
# sshProcess.stdin.close()


# for line in sshProcess.stdout:
#     if line == "END\n":
#         break
#     print(line,end="")

# #to catch the lines up to logout
# for line in  sshProcess.stdout: 
#     print(line,end="")