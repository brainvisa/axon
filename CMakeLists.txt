cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()
enable_testing()

BRAINVISA_FIND_PACKAGE( soma-base REQUIRED )
BRAINVISA_FIND_PACKAGE( aims-free QUIET )
BRAINVISA_FIND_PACKAGE( soma-workflow )
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

BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.7" )
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

# build and install shared database files

add_custom_command( OUTPUT "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database-2.3.sqlite"
                    "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database-2.3.sqlite.minf"
                    "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database_fso.html"
                    "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database_fso.html.minf"
                    COMMAND brainvisa -b --setup )

add_custom_target( axon_build_shared_index
                   DEPENDS "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database-2.3.sqlite"
                   "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database-2.3.sqlite.minf"
                   "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database_fso.html"
                   "${CMAKE_BINARY_DIR}/share/brainvisa-share-${brainvisa-share_VERSION_MAJOR}.${brainvisa-share_VERSION_MINOR}/database_fso.html.minf" )

# build it also in a regular build (just once)
add_dependencies( axon_target_1 axon_build_shared_index )

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

# ensure the installed database file is newer than the rest - rebuild it after
# all toolboxes are installed
add_custom_target( axon_install_shared_index
    COMMAND if [ -f \"$(BRAINVISA_INSTALL_PREFIX)/bin/bv_env\" ] \; then "$(BRAINVISA_INSTALL_PREFIX)/bin/bv_env" brainvisa -b --setup \; fi
)

add_dependencies( post-install axon_install_shared_index )

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/bin/bv_create_ontology_doc" )
  set( CREATE_ONTOLOGY_DOC "${CMAKE_CURRENT_SOURCE_DIR}/bin/bv_create_ontology_doc" )
endif()


# Documentation of axon processes and ontologies
add_custom_target( bv_ontology_doc
  COMMAND "${CMAKE_BINARY_DIR}/bin/bv_env${CMAKE_EXECUTABLE_SUFFIX}" "${PYTHON_EXECUTABLE}" ${CREATE_ONTOLOGY_DOC} ${CMAKE_BINARY_DIR}
  )

add_custom_target( install-bv_ontology_doc
  COMMAND "${CMAKE_BINARY_DIR}/bin/bv_env${CMAKE_EXECUTABLE_SUFFIX}" "${PYTHON_EXECUTABLE}" ${CREATE_ONTOLOGY_DOC} $(BRAINVISA_INSTALL_PREFIX)  )

# commands docs help

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/scripts/brainvisa/bv_create_commands_doc" )
  set( CREATE_COMMANDS_DOC "${CMAKE_CURRENT_SOURCE_DIR}/scripts/brainvisa/bv_create_commands_doc" )
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/scripts/brainvisa/bv_create_doc_index" )
  set( CREATE_DOC_INDEX "${CMAKE_CURRENT_SOURCE_DIR}/scripts/brainvisa/bv_create_doc_index" )
endif()

BRAINVISA_GENERATE_COMMANDS_HELP()
BRAINVISA_GENERATE_COMMANDS_HELP_INDEX()

# create global doc index after all is installed
# Index of all documentation
add_custom_target( bv_doc_index
  COMMAND "${CMAKE_BINARY_DIR}/bin/bv_env${CMAKE_EXECUTABLE_SUFFIX}" "${PYTHON_EXECUTABLE}" ${CREATE_DOC_INDEX} ${CMAKE_BINARY_DIR}/share/doc
  )
add_dependencies( bv_doc_index bv_commands_doc )
add_dependencies( bv_doc_index usrdoc devdoc)
add_dependencies( bv_doc_index bv_ontology_doc )
add_dependencies( ${PROJECT_NAME}-doc bv_doc_index)

add_custom_target( install-bv_doc_index
  COMMAND "${CMAKE_BINARY_DIR}/bin/bv_env${CMAKE_EXECUTABLE_SUFFIX}" "${PYTHON_EXECUTABLE}" ${CREATE_DOC_INDEX} $(BRAINVISA_INSTALL_PREFIX)/share/doc
  )
add_dependencies( install-bv_doc_index install-bv_commands_doc )
add_dependencies( install-${PROJECT_NAME}-doc install-bv_doc_index )

# FIXME: the latter components of documentation (ontology and index) are
# completely rebuilt during installation, which is kind of wasteful. Is there
# any good reason to keep doing it this way?
# answer: this was for the modular install, which could install selected
# components only, then build docs pointers to them only. This is not used any
# longer since modularity is gone using containers.

# add_dependencies( install-bv_doc_index install-bv_ontology_doc)


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
if(WIN32)
    # Add bat extension for brainvisa command
    brainvisa_add_executable(brainvisa.bat IS_SCRIPT 
                             HELP_COMMAND cmd /Q /C "bin/brainvisa.bat" -h)
else()
    brainvisa_add_executable(brainvisa IS_SCRIPT)
endif()

brainvisa_add_executable(axon-runprocess IS_SCRIPT)

brainvisa_add_test(axon-tests "${PYTHON_EXECUTABLE_NAME}" -m brainvisa.tests.test_axon)
brainvisa_add_test(axon-tests "${PYTHON_EXECUTABLE_NAME}" -m brainvisa.tests.test_core)
brainvisa_add_test(axon-tests "${PYTHON_EXECUTABLE_NAME}" -m brainvisa.tests.test_history)
brainvisa_add_test(axon-tests "${PYTHON_EXECUTABLE_NAME}" -m brainvisa.tests.test_registration)

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()
