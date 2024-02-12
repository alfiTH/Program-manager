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

class Terminal():
    def __init__(self, terminal_name:str, command:str):
        assert isinstance(terminal_name, str) , "Terminal name must be a string"
        assert isinstance(command, str) , "Command must be a string"

        self.terminal_name = terminal_name
        self.pathAuxFile = '/tmp/ProgramManager/'+self.terminal_name.replace(" ","_").replace("/","-")+'.txt'
        self.command = command


    def terminal_exists(self):
        return subprocess.run(['xdotool', 'search', '--name', self.terminal_name], stdout=subprocess.DEVNULL).returncode == 0
    
    def terminal_finish(self):
        ret = None
        if os.path.exists(self.pathAuxFile):
            with open(self.pathAuxFile, 'r') as archivo:
                ret = archivo.read().strip()=='0'
            os.remove(self.pathAuxFile)
        return ret

    def launch_terminal(self, wait_close=True):
        if not self.terminal_exists():
            complete_command = ['gnome-terminal', '--title='+self.terminal_name, '--', 'bash', '-c', 
                                self.command +'; echo $? > '+self.pathAuxFile+';']


            if wait_close:
                complete_command[5] = complete_command[5] + 'read -p "Press enter to exit"' 
            
            subprocess.run(complete_command)
            time.sleep(0.1)
            # Encuentra la ventana y ocúltala
            subprocess.run(['xdotool', 'search', '--name', self.terminal_name, 'windowunmap'])
        else:
            print("WARNING: LA TERMINAL ", self.terminal_name, "EXISTE", file=sys.stderr)

    def edit_terminal(self, show=True, position=None, size=None):
        assert isinstance(show, bool) , "Show must be a boolean"
        assert position is None or ((isinstance(position, list) or isinstance(position, tuple) )and len(position)==2), "Terminal position must be a list or tuple, with 2 elements"
        assert size is None or ((isinstance(size, list) or isinstance(size, tuple) )and len(size)==2), "Terminal size must be a list or tuple, with 2 elements"

        if self.terminal_exists():
            if show:
                subprocess.run(['xdotool', 'search', '--name', self.terminal_name, 'windowmap'])
            else:
                subprocess.run(['xdotool', 'search', '--name', self.terminal_name, 'windowunmap'])

            if position is not None:
                pass #TODO
            if size is not None:
                pass #TODO  

    #TODO muerte brusca
    def exit_terminal(self):
        if self.terminal_exists():
            # subprocess.run(["killall", "-9", self.terminal_name.split("/")[1]])
            # time.sleep(1)#TODO comprobar PID activo? y por ssh? elif '/tmp/'+terminal_name+'.txt':?
            subprocess.run(['xdotool', 'search', '--name', self.terminal_name, 'windowclose'])


class RowProgram():
    titlesColums=["Device", "SSH", "Ping", "Program", "Config", "Clean", "Compile", "Start/Stop", "Terminal", "Restart"]
    def __init__(self, num_program=0, device=None, ssh="off", ping ="off", path=None, program="", config=""):

        self.element={}

        #Usuario@IP para ssh y visulización
        if not "@" in device:
            assert device is not None, "No se añadió Nombre de usuario ni IP"
            assert  "@" in device, ("No se añadió correctamente el nombre: "+device+" Formato Usuario@IP ")
        self.element[RowProgram.titlesColums[0]] = QtWidgets.QLabel(text=device)

        #TODO JUTAR CD CON SSH?
        if ssh.lower()=="on" or ssh.lower()=="-x11":
            command_ssh = "ssh "
            if ssh.lower() == "-x11": 
                command_ssh += "-X "
            command_ssh +=  command_ssh + device
        else :
            command_ssh = ""
        self.element[RowProgram.titlesColums[1]] = QtWidgets.QLabel(text=ssh)

        self.ping = True if ping.lower()=="on" else False
        if self.ping:
            threadPing = Thread(target=self.fping, args=(device,), daemon=True)
            threadPing.start()
        self.element[RowProgram.titlesColums[2]] = QtWidgets.QLabel(text=str(self.ping))

        #Ruta de base del programa
        assert path is not None, "No se añadió ruta de programa"
        command_cd = path if path[0] == '/' else os.path.expanduser('~') + path[0].replace('~', '') + path[1:]

        assert os.path.exists(command_cd), ("La ruta especificada :"+command_cd+"no existe")
        command_cd = "cd " + command_cd

        command_cd = command_ssh + command_cd

        assert len(program)>0, "No se añadió un programa"


        ##TODO unificar comand_ssh con command_cd
        self.element[RowProgram.titlesColums[3]] = QtWidgets.QLabel(text=program)
        self.element[RowProgram.titlesColums[4]] = QtWidgets.QLabel(text=config)
        self.element[RowProgram.titlesColums[5]] = EditButton.Clean(path=command_cd)
        self.element[RowProgram.titlesColums[6]] = EditButton.Compile(path=command_cd)
        self.element[RowProgram.titlesColums[7]] = EditButton.StartStop(num_program=num_program, path=command_cd, program=program, config=config)
        self.element[RowProgram.titlesColums[8]] = self.element[RowProgram.titlesColums[7]].get_buttonTerminal()
        self.element[RowProgram.titlesColums[9]] = QtWidgets.QCheckBox("")#Autostart
        
    def __del__(self):
        self.ping = False

    def get_row(self):
        return self.element

    def fping(self, device):
        command = ['ping', "-c", '1', device[device.find("@")+1:]]
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

    def check_buttons(self):
        self.element[RowProgram.titlesColums[6]].check()
        self.element[RowProgram.titlesColums[7]].check()


class EditButton():

    class BasicButton(QtWidgets.QPushButton):
        def __init__(self, path="", parent=None):
            super(EditButton.BasicButton, self).__init__(parent)

            self.path = path
            self.blinking = False
            self.threadBlinking = None
            self.clicked.connect(self.function)
            

        def __del__(self):
            print('Destructor ', self.__class__.__name__)
            
            self.blinking = False
            if self.threadBlinking is not None:
                self.threadBlinking.join()

        def check(self):
            print('Checking Basic Button')

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
        def __init__(self, num_program, path, program, config, parent=None):
            super(EditButton.StartStop, self).__init__(path, parent)
            self.terminal = Terminal(terminal_name="Program"+str(num_program)+" "+program+" "+config, command=self.path + " && " +program + " " + config)
            self.buttonTerminal = EditButton.Terminal(self.terminal)
            self.run = False
            self.set_style(color="background-color: red", text="Start")            

        def __del__(self):
            super(EditButton.StartStop, self).__del__()
            self.terminal.exit_terminal()

        def get_buttonTerminal(self):
            return self.buttonTerminal

##TODO mover al otro lado para tener centralizado por columnas llamando al check, meter en el basic
        def check(self):
            if self.run:
                isFinish = self.terminal.terminal_finish()
                existTerminal = self.terminal.terminal_exists()
                if not (existTerminal and isFinish is None):            # NOT Program working
                    if isFinish is not None and isFinish:               #Finish program
                        self.set_style(blink={"color1":"background-color: green", 
                        "color2":"background-color: white", "text1":"Finish",
                        "text2":":)", "period":1})
                    elif not existTerminal:                                               # Error by Terminal or bad exit
                        self.set_style(blink={"color1":"background-color: red", 
                        "color2":"background-color: yellow", "text1":"ERROR", 
                        "text2":"No terminal", "period":1})
                    elif not isFinish:                                               # Error by Terminal or bad exit
                        self.set_style(blink={"color1":"background-color: red", 
                        "color2":"background-color: yellow", "text1":"ERROR", 
                        "text2":"Failure", "period":1})
                    self.run = False
        
        def function(self):
            if not self.terminal.terminal_exists() and self.run==False:
                self.terminal.launch_terminal()
                self.set_style(color="background-color: green", text="Stop") 
                self.run = True
            else:
                self.terminal.exit_terminal()
        
        def stop_program (self):
            self.terminal.exit_terminal()
            self.set_style(color="background-color: red", text="Start") 
            self.run = False

    class Terminal(BasicButton):
        def __init__(self, terminal, parent=None):
            super(EditButton.Terminal, self).__init__(parent=parent)
            self.terminal = terminal
            self.set_style(text="Terminal") 
            self.open = False

        def __del__(self):
            super(EditButton.Terminal, self).__del__()

        def function(self):
            if self.open:
                self.terminal.edit_terminal(show=False)
            else:
                self.terminal.edit_terminal(show=True)
            self.open = not self.open

    class Clean(BasicButton):
        def __init__(self, path, parent=None):
            super(EditButton.Clean, self).__init__(path, parent)
            self.set_style(color="background-color: green", text="Clean") 

        def __del__(self):
            super(EditButton.Clean, self).__del__()
            

        def function(self):
            self.launch_program()
        
        def launch_program(self):
            self.set_style(color="background-color: red", text="Cleaning") 
            subprocess.run(['cd '+self.path[3:]+' && make clean && rm -rf CMakeFiles cmake_install.cmake CMakeCache.txt Makefile'], shell=True, stdout=subprocess.DEVNULL)
            self.set_style(color="background-color: green", text="Clean") 


    class Compile(BasicButton):
        def __init__(self, path, parent=None):
            super(EditButton.Compile, self).__init__(path, parent)   
            self.terminal = Terminal(terminal_name=str(time.time_ns())+"Compile "+self.path[2:], command=self.path+" && "+" cmake . && make -j16")
            self.set_style(color="background-color: green", text="Compile")    
            self.run = False     

        def __del__(self):
            super(EditButton.Compile, self).__del__()
            self.terminal.exit_terminal()

        def check(self):
            if self.run:
                isFinish = self.terminal.terminal_finish()
                if isFinish is not None:            # NOT Program working
                    if isFinish:               #Finish program
                        self.set_style(color="background-color: green", text="Compile")  
                        self.terminal.exit_terminal()  
                    else:                                               # Error by Terminal or bad exit
                        self.set_style(blink={"color1":"background-color: red", 
                        "color2":"background-color: yellow", "text1":"ERROR", 
                        "text2":":(", "period":1})
                        self.terminal.edit_terminal(show=True)
                    self.run = False

        def function(self):
            if not self.terminal.terminal_exists():
                self.terminal.launch_terminal(wait_close=True)
                self.set_style(color="background-color: red", text="Compiling")   
                self.run = True
