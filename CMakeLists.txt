cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

BRAINVISA_FIND_PACKAGE( soma-base REQUIRED )

find_package( python REQUIRED )

BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
math( EXPR result "${soma-base_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "soma-base" RUN ">= ${soma-base_VERSION};<< ${soma-base_VERSION_MAJOR}.${result}" )
math( EXPR result "${soma-qtgui_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "soma-qtgui" RUN ">= ${soma-qtgui_VERSION};<< ${soma-qtgui_VERSION_MAJOR}.${result}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 3.0" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python-qt4 RUN )
##BRAINVISA_DEPENDENCY( DEV DEPENDS python-qt4 DEV )

configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/config/config.py.in" "${CMAKE_BINARY_DIR}/python/brainvisa/config.py" @ONLY )
BRAINVISA_INSTALL( FILES "${CMAKE_BINARY_DIR}/python/brainvisa/config.py"
                   DESTINATION "python/brainvisa"
                   COMPONENT ${PROJECT_NAME} )
BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                                 ${PROJECT_NAME} )
BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/brainvisa"
                                 ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                          "share/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/doc" 
                          "share/doc/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                          bin
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/scripts"
                          scripts
                          ${PROJECT_NAME} )

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()


