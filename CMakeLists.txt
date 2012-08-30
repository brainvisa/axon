cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()
enable_testing()

BRAINVISA_FIND_PACKAGE( soma-base REQUIRED )
BRAINVISA_FIND_PACKAGE( soma-qtgui REQUIRED )
find_package( PyQt${DESIRED_QT_VERSION} REQUIRED )

find_package( python REQUIRED )

BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
math( EXPR result "${soma-base_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "soma-base" RUN ">= ${soma-base_VERSION};<< ${soma-base_VERSION_MAJOR}.${result}" )
math( EXPR result "${soma-qtgui_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "soma-qtgui" RUN ">= ${soma-qtgui_VERSION};<< ${soma-qtgui_VERSION_MAJOR}.${result}" )
math( EXPR result "${aims-free_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN RECOMMENDS "aims-free" RUN ">= ${aims-free_VERSION};<< ${aims-free_VERSION_MAJOR}.${result}" )
if( brainvisa-share_VERSION_MINOR )
  math( EXPR result "${brainvisa-share_VERSION_MINOR}+1" )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "brainvisa-share" RUN ">= ${brainvisa-share_VERSION};<< ${brainvisa-share_VERSION_MAJOR}.${result}" )
endif()
BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 3.0" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python-qt${DESIRED_QT_VERSION} RUN )
BRAINVISA_DEPENDENCY( DEV DEPENDS python-qt${DESIRED_QT_VERSION} DEV )

BRAINVISA_DEPENDENCY( RUN RECOMMENDS graphviz RUN )

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
                          ${PROJECT_NAME}-usrdoc )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                          bin
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/scripts"
                          scripts
                          ${PROJECT_NAME} )

# Docbook
BRAINVISA_GENERATE_DOCBOOK_DOC()

# find_package( Epydoc )
# BRAINVISA_GENERATE_EPYDOC_DOC( "${CMAKE_BINARY_DIR}/python/brainvisa"
#      "share/doc/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/epydoc"
#      EXCLUDE brainvisa.*.qt3gui )

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "sphinxdoc/sphinx"
  "share/doc/axon-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/sphinx" )

BRAINVISA_COPY_FILES( ${PROJECT_NAME} "usecases.rst" SOURCE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/sphinxdoc/sphinx"      
                       DESTINATION "python/brainvisa/tests" )
add_test(axon-tests "${CMAKE_BINARY_DIR}/bin/bv_env" "${PYTHON_EXECUTABLE}" -m brainvisa.tests.test_axon)

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()


