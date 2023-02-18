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
        self.element[RowProgram.titlesColums[8]] = EditButton.Terminal(device=self.device, startStopButton=self.element[RowProgram.titlesColums[7]],program=self.program)
        
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
            self.process = subprocess.Popen(universal_newlines=True,shell=True, args=["echo OK"]
                            , stdout=subprocess.PIPE, stdin=subprocess.DEVNULL , stderr=subprocess.PIPE  )
            
            self.ssh = ssh
            self.device = device
            self.path = path
            self.blinking = False
            self.threadBlinking = None
            self.clicked.connect(self.function)
            

        def __del__(self):
            print('Destructor ', self.__class__.__name__)
            if self.blinking:
                self.blinking = False
                self.threadBlinking.join()



        def function(self):
            print("Basic Button")

        #blink dicionario{"color1":, "color2":, "text1":, "text2":, "period""}
        def set_style(self, color = None, text = None, blink = None):
            if blink is not None:
                self.blinking = True
                self.threadBlinking = Thread(target=self.blink,args=[blink], daemon=True)
                self.threadBlinking.start()
            else:
                if self.blinking:
                    self.blinking = False
                    self.threadBlinking.join()
                if text is not None:
                    self.setText(text)
                if color is not None:
                    self.setStyleSheet(color)

        def blink(self, configBlink):
            while self.blinking:
                self.setStyleSheet(configBlink["color1"])
                self.setText(configBlink["text1"])
                time.sleep(configBlink["period"])
                self.setStyleSheet(configBlink["color2"])
                self.setText(configBlink["text2"])
                time.sleep(configBlink["period"])


    class StartStop(BasicButton):
        def __init__(self,ssh=False, device=None, path=None, program=[], config="", parent=None):
            super(EditButton.StartStop, self).__init__(ssh, device, path, parent)

            self.program = program
            self.config = config
            self.run = False
            self.set_style(color="background-color: red", text="Start")            

        def __del__(self):
            super(EditButton.StartStop, self).__del__()
            if not self.process.poll() is None:
                self.stop_program()

        def function(self):
            if self.process.poll() is None:
                self.stop_program()
            else:
                self.launch_program()
            time.sleep(0.5)
        
        def stop_program (self):
            # self.process.stdin.close()
            # self.process.stderr.close()
            # self.process.stdout.close()
            self.process.kill()
            self.process.wait()
            self.set_style(color="background-color: red", text="Start") 
            self.run = False

        def launch_program(self):
            self.process = subprocess.Popen(universal_newlines=True, cwd=self.path, args=self.program + [self.config]
                            , stdout=subprocess.PIPE, stdin=subprocess.DEVNULL , stderr=subprocess.PIPE  )
            self.run = True
            self.set_style(color="background-color: green", text="Stop") 
            child = Thread(target=self.monitor_program, daemon=True)
            child.start()


        def monitor_program(self):
            status = self.process.poll()
            while status is None:
                status = self.process.poll()
                print(status)
                if status is not None: self.stop_program()
            if status !=0 and status is not None: 
                self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":str(status), "period":0.5})
            print ( "//////////////Resultado de programa: ", status, "//////////////////")

    class Terminal(BasicButton):
            def __init__(self, device=None, program = None,  startStopButton = None, parent=None):
                super(EditButton.Terminal, self).__init__(device=device,parent=parent)
                self.program = program
                self.startStopButton = startStopButton
                self.set_style(text="Terminal") 
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
                self.win =windowTerminal(buttonProcess=self.startStopButton, name=self.device+" "+self.program[-1])
            
            def close_window(self):
                if self.win is not None:
                    self.win.close()
                    self.win.__del__()
                    self.win = None



    class Clean(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Clean, self).__init__(ssh, device, path, parent)
                self.set_style(color="background-color: green", text="Clean") 

            def __del__(self):
                super(EditButton.Clean, self).__del__()
                if self.process.poll() is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.kill()

            def function(self):
                if self.process.poll() is not None:
                    self.launch_program()
            
            def launch_program(self):
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path + "/tmp", shell=True, 
                args=["make clean && rm -rf CMakeFiles cmake_install.cmake CMakeCache.txt Makefile"]
                                , stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL , stderr=subprocess.DEVNULL  )
                self.set_style(color="background-color: red", text="Cleaning") 
                self.process.wait()
                print("Clean: ", self.process.poll()) 
                if self.process.poll() != 0:
                    self.set_style(self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":str(self.process.poll()), "period":0.5})) 
                else:
                    self.set_style(color="background-color: green", text="Clean") 


    class Compile(BasicButton):
            def __init__(self,ssh=False, device=None, path=None, parent=None):
                super(EditButton.Compile, self).__init__(ssh, device, path, parent)   
                self.set_style(color="background-color: green", text="Compile")         

            def __del__(self):
                super(EditButton.Clean, self).__del__()
                if self.process.poll() is None: 
                    print ( "pid: ", self.process.poll())
                    self.process.kill()

            def function(self):
                if self.process.poll() is not None:
                    self.launch_program()
            
            def launch_program(self):
                
                self.process = subprocess.Popen(universal_newlines=True, cwd=self.path + "/tmp", shell=True, args=["cmake . && make -j20"]
                                , stdout=subprocess.PIPE, stdin=subprocess.DEVNULL , stderr=subprocess.STDOUT )
                self.set_style(color="background-color: red", text="Compiling")   

                self.process.wait()
                #Fallo de compilacion
                if self.process.poll() != 0:
                    self.set_style(self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":str(self.process.poll()), "period":0.5})) 
                    win = windowTerminal(buttonProcess=self.process, name=self.device+" "+self.program[-1])
                else:
                    self.set_style(color="background-color: green", text="Compile") 

class windowTerminal(QtWidgets.QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, buttonProcess, name ):
        super().__init__()
        self.buttonProcess = buttonProcess
        self.setWindowTitle(name)
        self.resize(500, 500)
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel(" ")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.show()
        self.runTerm = True
        self.term = Thread(target=self.monitor_terminal, daemon=True)
        self.term.start()
    
    def __del__(self):
        self.runTerm = False
        self.term.join()
        
    
    def monitor_terminal(self):
        while self.runTerm:
            if self.buttonProcess.process is not None:
                process = self.buttonProcess.process
                salida =[]
                print("monitoring")
                while self.runTerm:
                    try:
                        salida = (salida + [process.stdout.readline()])[-20:]
                        print("program ", process.args)
                        print("CAPTURADO POR LA PIPE: \n", ''.join(salida))
                        self.label.setText(' '.join(salida))
                        if salida[-1] == '' or process.poll() is not None: break  
                    except IOError:
                        break           
            
