
PROJECT(Contador)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
# Indicamos la versión mínima que necesitamos de CMake

SET(Contador_SRC "src/contador.cpp")
# Creamos la variable MiProyecto_SRC y le asignamos el valor "src/main.cpp" que es la ubicación de nuestro archivo.
# Por defecto las variables son listas o arrays
# Si tenemos dos archivos sería SET(MiProyecto_SRC "src/main.cpp" "src/segundo.cpp")
# Se permite multilínea

ADD_EXECUTABLE(Contador ${Contador_SRC})

# Se creará un ejecutable llamado MiProyecto en Linux o MiProyecto.exe en Windows.
# Se hace referencia a las variables con ${NOMBRE_VARIABLE}.

set_target_properties(Contador PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

add_custom_target(clean
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_BINARY_DIR}/CMakeFiles/CMakeDirectoryInformation.cmake
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/CMakeFiles
    COMMAND ${CMAKE_COMMAND} -E remove ${CMAKE_BINARY_DIR}/CMakeCache.txt
    COMMAND ${CMAKE_COMMAND} -E remove ${CMAKE_BINARY_DIR}/cmake_install.cmake
    COMMAND ${CMAKE_COMMAND} -E remove ${CMAKE_BINARY_DIR}/Makefile
    COMMENT "Limpiando el proyecto..."
)