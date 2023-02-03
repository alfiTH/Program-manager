#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Agrupación de clases heredaras de PySide6 para ejecuciones precisas'''

import sys, os
import time
from threading import Thread
from PySide6 import QtCore, QtWidgets, QtGui
import subprocess

__author__ = "Alejandro Torrejón Harto"
__copyright__ = "Copyright 2023, The Program Manager Project"
__credits__ = ["Alejandro Torrejón Harto"]
__license__ = "GNU General Public License v3.0"
__version__ = "0.0.2"
__date__ = "26/01/2023"
__maintainer__ = "Alejandro Torrejón Harto"
__email__ = "atorrejo@alumnos.unex.es"
__status__ = "Prototype"



class RowProgram():
    titlesColums=["Device", "SSH", "Ping", "Program", "Config", "Clean", "Compile", "Start/Stop", "Terminal"]
    def __init__(self, device=None, ssh="off", ping ="off", path=None, program="", config=""):

        #TODO cambiar a diccionario pasar key en fuuncion get y value en la otra
        self.element={}

        #Usuario@IP para ssh y visulización
        if not "@" in device:
            if device is None:
                print("No se añadió Nombre de usuario ni IP", file=sys.stderr)
            else:
                print("No se añadió correctamente el nombre: ", device," Formato Usuario@IP ", file=sys.stderr)
            sys.exit(-1)
        self.device = device
        self.element[RowProgram.titlesColums[0]] = QtWidgets.QLabel(text=device)

        self.ssh = ["ssh", "-tt"] if ssh.lower()=="on" or ssh.lower()=="-x11" else []
        if ssh.lower() == "-x11": 
            self.ssh.append("-X11")
        self.element[RowProgram.titlesColums[1]] = QtWidgets.QLabel(text=ssh)

        self.ping = True if ping.lower()=="on" else False
        if self.ping:
            threadPing = Thread(target=self.fping, daemon=True)
            threadPing.start()
        self.element[RowProgram.titlesColums[2]] = QtWidgets.QLabel(text=str(self.ping))

        #Ruta de base del programa
        if path is None:
            print("No se añadió ruta de programa", file=sys.stderr)
            sys.exit(-1)
        else : self.path = path if path[0] == '/' else os.path.expanduser('~') + "/" + path[0].replace('~', '') + path[1:]
        #TODO dIFERENCIAR SSH
        if not os.path.exists(self.path):
            print("La ruta especificada :", self.path, "no existe", file=sys.stderr)
            sys.exit(-1)
        

        if len(program)>0: self.program  = program.split(sep=" ")
        else:
            print("No se añadio un programa")
            sys.exit(-1)
        self.config = config
        self.element[RowProgram.titlesColums[3]] = QtWidgets.QLabel(text=program)
        self.element[RowProgram.titlesColums[4]] = QtWidgets.QLabel(text=config)
        self.element[RowProgram.titlesColums[5]] = EditButton.Clean(ssh=self.ssh, device=self.device,path=self.path)
        self.element[RowProgram.titlesColums[6]] = EditButton.Compile(ssh=self.ssh, device=self.device,path=self.path)
        self.element[RowProgram.titlesColums[7]] = EditButton.StartStop(ssh=self.ssh, device=self.device,path=self.path, program=self.program, config=self.config)
        self.element[RowProgram.titlesColums[8]] = EditButton.Terminal(device=self.device,program=self.program)
        
    def __del__(self):
        self.ping = False


    def get_row(self):
        return self.element

    def fping(self):
        command = ['ping', "-c", '1', self.device[self.device.find("@")+1:]]
        while self.ping:
            ret = subprocess.run(args=command,universal_newlines=True, stdout=subprocess.PIPE)
            if (ret.returncode == 0):
                out = ret.stdout
                #print(command, out[out.find("time=")+5:out.find("ms")])
                self.element[RowProgram.titlesColums[2]].setText(out[out.find("time=")+5:out.find("ms")+2])
            else:
                #print(command, "--")
                self.element[RowProgram.titlesColums[2]].setText("--")
    
            time.sleep(1)

    

class EditButton():

    class BasicButton(QtWidgets.QPushButton):
        def __init__(self, ssh=False, device=None, path=None, parent=None):
            super(EditButton.BasicButton, self).__init__(parent)
            #Proseso de ejecucion asignado al botón
            self.process = None
            self.ssh = ssh
            self.device = device
            self.path = path
            self.clicked.connect(self.function)
            

        def __del__(self):
            print('Destructor ', self.__class__.__name__)
            

        def function(self):
            print("Basic Button")



    class StartStop(BasicButton):
        def __init__(self,ssh=False, device=None, path=None, program=[], config="", parent=None):
            super(EditButton.StartStop, self).__init__(ssh, device, path, parent)

            self.program = program
            self.config = config
            self.run = False
            self.setStyleSheet("background-color: red")
            self.setText("Start")
            

        def __del__(self):
            super(EditButton.StartStop, self).__del__()
            if not self.process is None:
                self.stop_program()


        def function(self):
            if self.run:
                self.stop_program()
            else:
                self.launch_program()
            time.sleep(0.5)
        
        def stop_program (self):
            if not self.process is None: 
                self.process.stdin.close()
                self.process.stderr.close()
                self.process.stdout.close()
                self.process.kill()
                self.setStyleSheet("background-color: red")
                self.setText("Start")
                self.process = None
                self.run = False

        def launch_program(self):
            self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                            , stdout=subprocess.PIPE, stdin=subprocess.PIPE , stderr=subprocess.PIPE  )
            self.run = True
            self.setStyleSheet("background-color: green")
            self.setText("Stop")
            child = Thread(target=self.monitor_program, daemon=True)
            child.start()


        def monitor_program(self):
            print("monitoring")
            while self.run:
                try:
                    salida = self.process.stdout.readline()
                    print("program ", self.process.args)
                    if len(salida)>0: print("CAPTURADO POR LA PIPE", salida)
                    status = self.process.poll()
                    if not status is None: self.stop_program()
                except:
                    pass
                    
            print ( "//////////////Resultado de programa: ", status, "//////////////////")

    class Terminal(BasicButton):
            def __init__(self, device=None, program = None,  startStopButton = None, parent=None):
                super(EditButton.Terminal, self).__init__(device=device,parent=parent)
                self.program = program
                self.startStopButton = startStopButton
                self.setText("Terminal")
                self.win = None

            def __del__(self):
                super(EditButton.Terminal, self).__del__()
                self.close_window()

            def function(self):
                print(self.win)
                if self.win is None :
                    self.show_window()
                else:
                    self.close_window()    
            
            def show_window(self):
                self.win =windowTerminal(program=self.startStopButton, name=self.device+" "+self.program[-1])
            
            def close_window(self):
                if self.win is not None:
                    self.win.close()
                    self.win = None



    class Clean(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Clean, self).__init__(ssh, device, path, parent)
                self.setStyleSheet("background-color: green")
                self.setText("Clean")

            def __del__(self):
                super(EditButton.Clean, self).__del__()
                if not self.process is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.kill()

            def function(self):
                if self.process is None:
                    self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, shell=True, args="rm -rf Cmake Makefile"
                                , stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL , stderr=subprocess.DEVNULL  )
                self.setStyleSheet("background-color: red")
                while self.process.poll() is None: time.sleep(0.1)
                print("Clean: ", self.process.returncode)
                self.process = None
                self.setStyleSheet("background-color: green")


    class Compile(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Compile, self).__init__(ssh, device, path, parent)           
                self.setStyleSheet("background-color: green")
                self.setText("Compile")

            def __del__(self):
                super(EditButton.Clean, self).__del__()
                if not self.process is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.kill()

            def function(self):
                if self.process is None:
                    self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, shell=True, args=["cmake .",";","make -j20"]
                                , stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL , stderr=subprocess.DEVNULL  )
                self.setStyleSheet("background-color: red")
                while self.process.poll() is None: time.sleep(0.5)
                print("Compile: ", self.process.returncode)
                self.process = None
                self.setStyleSheet("background-color: green")
                
    


class windowTerminal(QtWidgets.QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, program, name ):
        super().__init__()
        self.setWindowTitle(name)
        self.resize(500, 500)
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel(name)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.show()
        self.term = Thread(target=self.monitor_terminal, daemon=True)
        self.term.start()
    
    def monitor_terminal(self):
        pass