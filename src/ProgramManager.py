#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Programa de visualización y manejo de programas '''

import sys
from PySide6 import QtCore, QtWidgets, QtGui
import EditUI
import time
import threading

__author__ = EditUI.__author__
__copyright__ = EditUI.__copyright__
__credits__ = EditUI.__credits__
__license__ = EditUI.__license__
__version__ = EditUI.__version__
__date__ = EditUI.__date__
__maintainer__ = EditUI.__maintainer__
__email__ = EditUI.__email__
__status__ = EditUI.__status__




class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.table = QtWidgets.QTableWidget(self)
        columnas=["Disp", "IP", "Ping", "SSH", "Prog", "Config", "Status","Start/Stop", "Terminal", "Clean", "Compile"]
        self.table.setColumnCount(len(columnas))
        #self.setCentralWidget(self.table)
        data1 = ['hola','hola2','calculator']
        data2 = ['1.3.4.','2.05.5.5.','3.051','35.6.7.9999']
        filas=4

        program = [["python3" ,"hola.py"], 
            ["python3" ,"calculator.py"], 
            ["./cc.o"]]

        #Ajuste de columnas a estrechas
        header = self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode().ResizeToContents) 
        #Cantidad de columnas
        self.table.setRowCount(3)
        #Tamaño y posicion tabla
        self.table.setGeometry(QtCore.QRect(50, 0, 950, 36*filas))
        #Titulos de las columnas
        self.table.setHorizontalHeaderLabels(columnas)

        for index in range(3):

            item1 = QtWidgets.QTableWidgetItem(data1[index])
            self.table.setItem(index,0,item1)
            
            item2 = QtWidgets.QTableWidgetItem(data2[index])
            self.table.setItem(index,1,item2)
            
            row = EditUI.RowProgram(ssh="OFF", device="robolab@192.168.1.123", path= "Documentos/Alejandro/Program-manager/tmp",argument=program[index], config="ala")

            item_color = QtWidgets.QTableWidgetItem()
            item_color.setBackground(QtGui.QColor.fromRgb(0, 255, 0))
            self.table.setItem(index, 3, item_color)

            btn_sell = row.startStop
            btn_sell.clicked.connect(self.handleButtonClicked)
            self.table.setCellWidget(index,2,btn_sell)
        
        child = threading.Thread(target=self.process_widget, daemon=True)
        child.start()

    def process_widget(self):
        while True:
            time.sleep(1) 
            self.table.setRowCount(5)
            time.sleep(0.0001) 


        


    def handleButtonClicked(self):
        button = self.sender()
        button.function()
        

if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    widget = MyWidget()
    widget.resize(1100, 600)
    widget.show()
    
    
    sys.exit(app.exec())



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