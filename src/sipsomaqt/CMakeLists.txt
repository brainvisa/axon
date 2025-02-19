set( soma_qt "soma_qt.sip" )
message("SIP VERSION: ${SIP_VERSION}" )
if( QT_VERSION VERSION_GREATER_EQUAL "6.0.0" )
  set( soma_qt "soma_qt6.sip" )
endif()

set( AXON_RELATIVE_SIP_DIRECTORY
     "share/axon-${${PROJECT_NAME}_VERSION_MAJOR}.${${PROJECT_NAME}_VERSION_MINOR}/sip" )

file( GLOB _sipSources "${CMAKE_CURRENT_SOURCE_DIR}/*.sip" )

include_directories( ${SIP_INCLUDE_DIRS} )
BRAINVISA_ADD_SIP_PYTHON_MODULE( somaqt soma "${CMAKE_CURRENT_SOURCE_DIR}/${soma_qt}"
  SIP_SOURCES "${_sipSources}"
  SIP_INCLUDE "${PYQT${DESIRED_QT_VERSION}_SIP_DIR}" "${CMAKE_BINARY_DIR}/${AXON_RELATIVE_SIP_DIRECTORY}" )
target_link_libraries( somaqt "${PYTHON_LIBRARY}" ${QT_LIBRARIES} )
