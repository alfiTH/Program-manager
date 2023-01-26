import sys
import os, signal
import time
from threading import Thread
from PySide6 import QtCore, QtWidgets, QtGui
from multiprocessing import Process
import subprocess

def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit()


# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGINT, handler)



class myButon(QtWidgets.QPushButton):
    def __init__(self,row=0, col=0, ruta="/", argument=["echo", "Vacio"], config="", parent=None):
        super(myButon, self).__init__(parent)
        self.row = row
        self.col = col
        self.ruta = ruta
        self.argument = argument
        self.config = config
        self.process = None

    def __del__(self):
        print('Destructor called, Employee deleted.')
        if self.process != None: 
            print ( "pid: ", self.process.poll())
            self.process.kill()
    
    def launch_program(self):
        self.process = subprocess.Popen(universal_newlines=True, stdout=subprocess.PIPE , cwd="/home/alfith/UNEX/Laboratorio/Program-manager/tmp",args=self.argument + [self.config])
        #os.set_blocking(self.process.stdout.fileno(), False)
        print ( "pid: ", self.process.pid)
        child = Thread(target=self.monitor_program, daemon=True)
        child.start()

    def monitor_program(self):
        print("monitoring")
        aux = None
        a = 0
        while aux==None:
            aux = self.process.stdout.readline()
            if len(aux)>0: print("esta term", aux)
            aux = self.process.poll()
            print("program ", self.process.args, " valor ", aux," contador", a)
            a+=1
        print("no leido", self.process.stdout.read())


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
            btn_sell = myButon('run', argument=program[index], config="ala")

            item_color = QtWidgets.QTableWidgetItem()
            item_color.setBackground(QtGui.QColor.fromRgb(0, 255, 0))
            self.table.setItem(index, 3, item_color)

            btn_sell.button_row = index
            btn_sell.button_column = 2
            btn_sell.clicked.connect(self.handleButtonClicked)
            self.table.setCellWidget(index,2,btn_sell)

    def handleButtonClicked(self):
        button = self.sender()
        print(button.button_row, "x", button.button_column)
        print (button.launch_program())

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