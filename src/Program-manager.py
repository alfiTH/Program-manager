import sys
import os, signal
import time
from threading import Thread
from PySide6 import QtCore, QtWidgets, QtGui

def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit()


# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGINT, handler)



class myButon(QtWidgets.QPushButton):
    def __init__(self,row=0, col=0, function=os.system, argument="echo Vacio", parent=None):
        super(myButon, self).__init__(parent)
        self.row = row
        self.col = col
        self.function = function
        self.argument = argument
    
    def launch_function(self):

        child_pid = os.fork()

        #padre
        if child_pid > 0:
            pid, status = os.waitpid(child_pid, 0)
            print ("wait returned, pid = %d, status = %d" % (pid, status))
            pid, status = os.wait()
            print ("wait returned, pid = %d, status = %d" % (pid, status))
            
            '''
            if (result == 0) {
            // Child still alive
            } else if (result == -1) {
            // Error 
            } else {
            // Child exited
            }'''
            time.sleep(0.5)
        #hijo
        else:
            self.function(self.argument)
            os._exit(0)


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
        program = ["python3 ../tmp/hola.py", "python3 ../tmp/hola2.py", "python3 ../tmp/calculator.py"]

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
            btn_sell = myButon('run', argument=program[index])

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
        print (button.launch_function())

def launch_IU():
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    widget.resize(1100, 600)
    widget.show()
    app.exec()

if __name__ == "__main__":
    widget = None

    t = Thread(target=launch_IU, args=[])

    t.start()

    t.join()
    
    sys.exit()