cmake_minimum_required( VERSION 2.6 )

find_package( soma-infra REQUIRED )

SOMA_PROJECT()

SOMA_FIND_PACKAGE( soma-base REQUIRED )
SOMA_ADD_RUNTIME_DEPENDENCY( SOMA soma-base REQUIRED )

find_package( PythonInterp REQUIRED )
SOMA_ADD_RUNTIME_DEPENDENCY( THIRDPARTY PythonInterp REQUIRED )


SOMA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                            ${PROJECT_NAME} )
SOMA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/brainvisa"
                            ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                     "share/${PROJECT_NAME}-${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}"
                     ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                     bin
                     ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/scripts"
                     scripts
                     ${PROJECT_NAME} )

# SOMA_CREATE_CMAKE_CONFIG_FILES()


