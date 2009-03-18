cmake_minimum_required( VERSION 2.6 )

find_package( soma-infra REQUIRED )

SOMA_PROJECT( brainvisa 4 0 0 "CEA - IFR 49" )

SOMA_FIND_PACKAGE( soma-base REQUIRED )

find_package( PythonInterp REQUIRED )


SOMA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                            ${PROJECT_NAME}-python ${PROJECT_NAME} )
SOMA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/brainvisa"
                            ${PROJECT_NAME}-brainvisa ${PROJECT_NAME} )
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


