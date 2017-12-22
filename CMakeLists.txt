cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()
enable_testing()

BRAINVISA_FIND_PACKAGE( soma-base REQUIRED )
BRAINVISA_FIND_PACKAGE( aims-free QUIET )
BRAINVISA_FIND_PACKAGE( soma-workflow )
BRAINVISA_FIND_PACKAGE( brainvisa-release QUIET )
BRAINVISA_FIND_PACKAGE( datamind QUIET )
if( NOT DESIRED_QT_VERSION )
  find_package( Qt REQUIRED )
endif()
find_package( PyQt${DESIRED_QT_VERSION} REQUIRED )

find_package( python REQUIRED )

# compiled sip module, if sip is found
find_package( SIP )
if( SIP_FOUND )

  if( DESIRED_QT_VERSION EQUAL 4 )
    find_package( Qt4 COMPONENTS QtCore QtGui REQUIRED )
    include( "${QT_USE_FILE}" )
  elseif( DESIRED_QT_VERSION EQUAL 5 )
    find_package( Qt5Widgets REQUIRED )
    add_definitions( ${Qt5Widgets_DEFINITIONS} )
    include_directories( ${Qt5Widgets_INCLUDE_DIRS} )
    set( QT_LIBRARIES ${Qt5Widgets_LIBRARIES} )
  endif()
  find_package( QtVersion REQUIRED )
  
  BRAINVISA_DEPENDENCY( RUN DEPENDS python-sip4 RUN )
  BRAINVISA_DEPENDENCY( DEV DEPENDS python-sip4 DEV )

  add_subdirectory( src/sipsomaqt )

endif()


BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
math( EXPR result "${soma-base_VERSION_MINOR}+1" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "soma-base" RUN ">= ${soma-base_VERSION};<< ${soma-base_VERSION_MAJOR}.${result}" )
if( aims-free_FOUND )
  math( EXPR result "${aims-free_VERSION_MINOR}+1" )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "aims-free" RUN ">= ${aims-free_VERSION};<< ${aims-free_VERSION_MAJOR}.${result}" )
endif()
if( datamind_FOUND )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "datamind" RUN ">= ${datamind_VERSION}" )
endif()
if( brainvisa-share_VERSION_MINOR )
  math( EXPR result "${brainvisa-share_VERSION_MINOR}+1" )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "brainvisa-share" RUN ">= ${brainvisa-share_VERSION};<< ${brainvisa-share_VERSION_MAJOR}.${result}" )
endif()

if( soma-workflow_FOUND )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "soma-workflow" RUN ">= ${soma-workflow_VERSION};" )
endif()
if( BRAINVISA-RELEASE_FOUND )
  BRAINVISA_DEPENDENCY( RUN RECOMMENDS "brainvisa-release" RUN BINARY_INDEPENDENT )
endif()

BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 3.0" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python-qt${DESIRED_QT_VERSION} RUN )
BRAINVISA_DEPENDENCY( DEV DEPENDS python-qt${DESIRED_QT_VERSION} DEV )
BRAINVISA_DEPENDENCY( RUN RECOMMENDS "python-matplotlib" RUN )

BRAINVISA_DEPENDENCY( RUN RECOMMENDS graphviz RUN )

configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/config/config.py.in" "${CMAKE_BINARY_DIR}/python/brainvisa/config.py" @ONLY )
BRAINVISA_INSTALL( FILES "${CMAKE_BINARY_DIR}/python/brainvisa/config.py"
                   DESTINATION "python/brainvisa"
                   COMPONENT ${PROJECT_NAME} )
BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                                 ${PROJECT_NAME} )

# For historical reasons, Axon needs to modify its encoding to iso-8859-1. 
# In Python this can only be done in an early step of Python startup. This
# is why axon installs the sitecustomize package created by bv_maker (see
# comments in bv_maker sources). That makes it possible to automatically 
# import modules at startup. The module python/sitecustomize/axon_encoding.py
# is loaded on startup and sets the encoding. The package sitecustomize is not
# supposed to be packaged (it is only used in build tree). This is an
# exception for axon component that should be removed when all string encoded
# in iso-8859-1 will be converted to utf8.
BRAINVISA_INSTALL( FILES "${CMAKE_BINARY_DIR}/python/sitecustomize/__init__.py"
                    DESTINATION "python/sitecustomize"
                    COMPONENT ${PROJECT_NAME} )
                                 
BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/brainvisa"
                                 ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                          "share/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/foms" 
                          "share/foms"
                          ${PROJECT_NAME} )
# this doc should be part of the "run" package.
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/doc" 
                          "share/doc/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                          bin
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/scripts"
                          scripts
                          ${PROJECT_NAME} )

# Docbook - obsolete.
# BRAINVISA_GENERATE_DOCBOOK_DOC()

# find_package( Epydoc )
# BRAINVISA_GENERATE_EPYDOC_DOC( "${CMAKE_BINARY_DIR}/python/brainvisa"
#      "share/doc/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/epydoc"
#      EXCLUDE brainvisa.*.qt3gui )

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "sphinxdoc/user_doc"
  "share/doc/axon-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/user_doc" USER )
BRAINVISA_GENERATE_SPHINX_DOC( "sphinxdoc/dev_doc"
  "share/doc/axon-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/dev_doc" )

BRAINVISA_COPY_FILES( ${PROJECT_NAME}
    "usecases.rst" "usecases_nb.ipynb"
    SOURCE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/sphinxdoc/dev_doc"
    DESTINATION "python/brainvisa/tests" )

# commands list, doc
set( axon-commands brainvisa;axon-runprocess
     CACHE INTERNAL "Commands list for component axon" FORCE )

brainvisa_add_test(axon-tests "${PYTHON_EXECUTABLE_NAME}" -m brainvisa.tests.test_axon)

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()


