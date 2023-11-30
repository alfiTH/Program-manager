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


def terminal_exists(terminal_name):
    assert isinstance(terminal_name, str) , "Terminal name must be a string"
    return subprocess.run(['xdotool', 'search', '--name', terminal_name], stdout=subprocess.DEVNULL).returncode == 0

def launch_terminal(terminal_name, command, comand_ssh=None, wait_close=True):
    assert isinstance(terminal_name, str) , "Terminal name must be a string"
    assert isinstance(command, str) , "Command must be a string"
    assert isinstance(comand_ssh, str) or comand_ssh is None , "Command SSH must be a string"
    if not terminal_exists(terminal_name):
        if comand_ssh is None:
            complete_command = ['gnome-terminal', '--title='+terminal_name, '--', 'bash', '-c', 
                                command +'; echo $? > /tmp/'+terminal_name+'.txt;']
        else:
            pass #TODO:

        if wait_close:
            complete_command[5] = complete_command[5] + 'read -p "Press enter to exit"' 
        
        subprocess.run(complete_command)
        time.sleep(0.1)
        # Encuentra la ventana y ocúltala
        subprocess.run(['xdotool', 'search', '--name', terminal_name, 'windowunmap'])
    else:
        print("WARNING: LA TERMINAL ", terminal_name, "EXISTE", file=sys.stderr)

def edit_terminal(terminal_name, show=True, position=None, size=None):
    assert isinstance(terminal_name, str) , "Terminal name must be a string"
    assert isinstance(show, bool) , "Show must be a boolean"
    assert position is None or ((isinstance(position, list) or isinstance(position, tuple) )and len(position)==2), "Terminal position must be a list or tuple, with 2 elements"
    assert size is None or ((isinstance(size, list) or isinstance(size, tuple) )and len(size)==2), "Terminal size must be a list or tuple, with 2 elements"

    if terminal_exists(terminal_name):
        if show:
            subprocess.run(['xdotool', 'search', '--name', terminal_name, 'windowmap'])
        else:
            subprocess.run(['xdotool', 'search', '--name', terminal_name, 'windowunmap'])

        if position is not None:
            pass #TODO
        if size is not None:
            pass #TODO  

#TODO muerte brusca
def exit_terminal(terminal_name):
    assert isinstance(terminal_name, str) , "Terminal name must be a string"
    if terminal_exists(terminal_name):
        subprocess.run(["killall", "-9", terminal_name.split("/")[1]])
        time.sleep(1)#TODO comprobar PID activo? y por ssh? elif '/tmp/'+terminal_name+'.txt':?
        subprocess.run(['xdotool', 'search', '--name', terminal_name, 'windowclose'])


class RowProgram():
    titlesColums=["Device", "SSH", "Ping", "Program", "Config", "Clean", "Compile", "Start/Stop", "Terminal", "Restart"]
    def __init__(self, device=None, ssh="off", ping ="off", path=None, program="", config=""):

        #TODO cambiar a diccionario pasar key en fuuncion get y value en la otra
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
        if len(command_ssh)==0:
            command_cd = path if path[0] == '/' else os.path.expanduser('~') + path[0].replace('~', '') + path[1:]
            assert os.path.exists(command_cd), ("La ruta especificada :"+command_cd+"no existe")
            command_cd = "cd " + command_cd
        else:
            pass #TODO dIFERENCIAR SSH

        assert len(program)>0, "No se añadió un programa"

        self.autoStart = QtWidgets.QCheckBox("")

        ##TODO unificar comand_ssh con command_cd
        self.element[RowProgram.titlesColums[3]] = QtWidgets.QLabel(text=program)
        self.element[RowProgram.titlesColums[4]] = QtWidgets.QLabel(text=config)
        self.element[RowProgram.titlesColums[5]] = EditButton.Clean(ssh=command_ssh, path=command_cd)
        self.element[RowProgram.titlesColums[6]] = EditButton.Compile(ssh=command_ssh, path=command_cd)
        self.element[RowProgram.titlesColums[7]] = EditButton.StartStop(ssh=command_ssh, path=command_cd, program=program+" "+ config)
        self.element[RowProgram.titlesColums[8]] = EditButton.Terminal(terminal_name=program+" "+config)
        self.element[RowProgram.titlesColums[9]] = self.autoStart
        
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

class EditButton():

    class BasicButton(QtWidgets.QPushButton):
        def __init__(self, ssh="", path="", parent=None):
            super(EditButton.BasicButton, self).__init__(parent)

            self.comand_ssh = ssh #TODO
            self.comand_cd = path
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
        def __init__(self, ssh, path, program, parent=None):
            super(EditButton.StartStop, self).__init__(ssh, path, parent)

            self.program = program
            self.run = False
            self.set_style(color="background-color: red", text="Start")            

        def __del__(self):
            super(EditButton.StartStop, self).__del__()
            exit_terminal(self.program)

##TODO mover al otro lado para tener centralizado por columnas llamando al check, meter en el basic
        def check(self):
            if self.run:
                if not terminal_exists(self.program):
                    self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":"No terminal", "period":0.5})
                    return False
                #elif '/tmp/'+terminal_name+'.txt': TODO
                    self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":"Finish", "period":0.5})
                    return False
                return True
            return False
        
        def function(self):
            if not terminal_exists(self.program):
                launch_terminal(self.program, self.comand_cd+" && "+self.program)
                self.set_style(color="background-color: green", text="Stop") 
                self.run = True
        
        def stop_program (self):
            exit_terminal(self.program)
            self.set_style(color="background-color: red", text="Start") 
            self.run = False

    class Terminal(BasicButton):
        def __init__(self, terminal_name, parent=None):
            super(EditButton.Terminal, self).__init__(parent=parent)
            self.terminal_name = terminal_name
            self.set_style(text="Terminal") 
            self.open = False

        def __del__(self):
            super(EditButton.Terminal, self).__del__()

        def function(self):
            if self.open:
                edit_terminal(self.terminal_name, False)
            else:
                edit_terminal(self.terminal_name, True)
            self.open = not self.open

    class Clean(BasicButton):
        def __init__(self,ssh, path, parent=None):
            super(EditButton.Clean, self).__init__(ssh, path, parent)
            self.set_style(color="background-color: green", text="Clean") 

        def __del__(self):
            super(EditButton.Clean, self).__del__()
            

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
        def __init__(self,ssh=False, path=None, parent=None):
            super(EditButton.Compile, self).__init__(ssh, path, parent)   
            self.set_style(color="background-color: green", text="Compile")    
            self.run = False     

        def __del__(self):
            super(EditButton.Clean, self).__del__()
            exit_terminal("compile "+self.path[2:])

        def check(self):
            if self.run:
                if not terminal_exists("compile "+self.path[2:]):
                    self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":"No terminal", "period":0.5})
                    return False
                #elif '/tmp/'+terminal_name+'.txt': TODO
                    self.set_style(blink={"color1":"background-color: red", 
                    "color2":"background-color: black", "text1":"ERROR", 
                    "text2":"Finish", "period":0.5})
                    return False
                return True
            return False

        def function(self):
            if not terminal_exists("compile "+self.path[2:]):
                launch_terminal("compile "+self.path[2:], self.comand_cd+" cmake . && make -j16", wait_close=False)
                self.set_style(color="background-color: red", text="Compiling")   
                self.run = True
