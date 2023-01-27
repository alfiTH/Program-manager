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
                print("No se añadió Nombre de usuario ni IP")
            else:
                print("No se añadió correctamente el nombre: ", device," Formato Usuario@IP ")
            sys.exit(-1)
        self.device = device
        self.element[RowProgram.titlesColums[0]] = device

        self.ssh = ["ssh", "-tt"] if ssh.lower()=="on" or ssh.lower()=="-x11" else []
        if ssh.lower() == "-x11": 
            self.ssh.append("-X11")

        self.ping = True if ping.lower()=="on" else False

        #Ruta de base del programa
        if path is None:
            print("No se añadió ruta de programa")
            sys.exit(-1)
        else : self.path = path if path[0] == '/' else os.path.expanduser('~') + "/" + path[0].replace('~', '') + path[1:]
        print(self.path)
        #TODO cOMPROBAR RUTA CON UN CD

        if len(program)>0: self.element[RowProgram.titlesColums[3]]  = program.split(sep=",")
        else:
            print("No se añadio un programa")
            sys.exit(-1)
        self.element[RowProgram.titlesColums[4]] = config
        self.element[RowProgram.titlesColums[5]] = EditButton.Clean(ssh=self.element["SSH"], device=self.element["Device"],path=self.path)
        self.element[RowProgram.titlesColums[6]] = EditButton.Compile(ssh=self.element["SSH"], device=self.element["Device"],path=self.path)
        self.element[RowProgram.titlesColums[7]] = EditButton.StartStop(ssh=self.element["SSH"], device=self.element["Device"],path=self.path, program=self.element["Program"], config=self.element["Config"])
        self.element[RowProgram.titlesColums[8]] = EditButton.Terminal(ssh=self.element["SSH"], device=self.element["Device"],path=self.path)
        
        
    def get_row(self):
        return self.element
        

    
class EditButton():

    class BasicButton(QtWidgets.QPushButton):
        def __init__(self, ssh=False, device=None, path=None, parent=None):
            super(EditButton.BasicButton, self).__init__(parent)
            #Proseso de ejecucion asignado al botón
            self.process = None
            self.ssh = ssh
            self.device = device
            self.path = path
            

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
                self.process = None
                self.run = False

        def launch_program(self):
            self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                            , stdout=subprocess.PIPE, stdin=subprocess.PIPE , stderr=subprocess.PIPE  )
            self.run = True
            self.setStyleSheet("background-color: green")
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
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Terminal, self).__init__(ssh, device, path, parent)

            def __del__(self):
                super(EditButton.Terminal, self).__del__()

            def function(self):
                self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                                , stdout=subprocess.PIPE, stdin=subprocess.PIPE , stderr=subprocess.PIPE  )
                child = Thread(target=self.monitor_program, daemon=True)
                child.start()

            def monitor_program(self):
                print("monitoring")
                aux = None
                a = 0
                while aux is None:
                    aux = self.process.stdout.readline()
                    print("program ", self.process.args)
                    if len(aux)>0: print("CAPTURADO POR PIPE", aux)
                    aux = self.process.poll()


    class Clean(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Clean, self).__init__(ssh, device, path, parent)

            def __del__(self):
                super(EditButton.Clean, self).__del__()
                if not self.process is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.stdout.close()
                    self.process.stdin.close()
                    self.process.stderr.close()
                    self.process.kill()

            def function(self):
                self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                                , stdout=subprocess.PIPE, stdin=subprocess.PIPE , stderr=subprocess.PIPE  )
                child = Thread(target=self.monitor_program, daemon=True)
                child.start()

            def monitor_program(self):
                print("monitoring")
                aux = None
                a = 0
                while aux is None:
                    aux = self.process.stdout.readline()
                    print("program ", self.process.args)
                    if len(aux)>0: print("CAPTURADO POR PIPE", aux)
                    aux = self.process.poll()


    class Compile(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Compile, self).__init__(ssh, device, path, parent)           

            def __del__(self):
                super(EditButton.Compile, self).__del__()
                if not self.process  is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.stdout.close()
                    self.process.stdin.close()
                    self.process.stderr.close()
                    self.process.kill()

            def function(self):
                self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                                , stdout=subprocess.PIPE, stdin=subprocess.PIPE , stderr=subprocess.PIPE  )
                child = Thread(target=self.monitor_program, daemon=True)
                child.start()

            def monitor_program(self):
                print("monitoring")
                aux = None
                a = 0
                while aux is None:
                    aux = self.process.stdout.readline()
                    print("program ", self.process.args)
                    if len(aux)>0: print("CAPTURADO POR PIPE", aux)
                    aux = self.process.poll()


