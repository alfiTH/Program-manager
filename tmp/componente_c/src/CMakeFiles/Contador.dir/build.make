# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.22

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src

# Include any dependencies generated for this target.
include CMakeFiles/Contador.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/Contador.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/Contador.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/Contador.dir/flags.make

CMakeFiles/Contador.dir/contador.cpp.o: CMakeFiles/Contador.dir/flags.make
CMakeFiles/Contador.dir/contador.cpp.o: contador.cpp
CMakeFiles/Contador.dir/contador.cpp.o: CMakeFiles/Contador.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/Contador.dir/contador.cpp.o"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/Contador.dir/contador.cpp.o -MF CMakeFiles/Contador.dir/contador.cpp.o.d -o CMakeFiles/Contador.dir/contador.cpp.o -c /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/contador.cpp

CMakeFiles/Contador.dir/contador.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/Contador.dir/contador.cpp.i"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/contador.cpp > CMakeFiles/Contador.dir/contador.cpp.i

CMakeFiles/Contador.dir/contador.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/Contador.dir/contador.cpp.s"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/contador.cpp -o CMakeFiles/Contador.dir/contador.cpp.s

# Object files for target Contador
Contador_OBJECTS = \
"CMakeFiles/Contador.dir/contador.cpp.o"

# External object files for target Contador
Contador_EXTERNAL_OBJECTS =

Contador: CMakeFiles/Contador.dir/contador.cpp.o
Contador: CMakeFiles/Contador.dir/build.make
Contador: CMakeFiles/Contador.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable Contador"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/Contador.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/Contador.dir/build: Contador
.PHONY : CMakeFiles/Contador.dir/build

CMakeFiles/Contador.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/Contador.dir/cmake_clean.cmake
.PHONY : CMakeFiles/Contador.dir/clean

CMakeFiles/Contador.dir/depend:
	cd /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src /home/robolab/Documentos/Alejandro/Program-manager/tmp/componente_c/src/CMakeFiles/Contador.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/Contador.dir/depend
