set( soma_qt "soma_qt.sip" )
message("SIP VERSION: ${SIP_VERSION}" )
if( SIP_VERSION VERSION_GREATER_EQUAL "6.0.0" )
  set( soma_qt "soma_qt6.sip" )
endif()

if( DESIRED_QT_VERSION EQUAL 6 )
  add_definitions( ${Qt6Core_DEFINITIONS} )
  include_directories( ${Qt6Core_INCLUDE_DIRS} )
  set( QT_LIBRARIES Qt6::Core )
  message("QT libs: ${QT_LIBRARIES}" )
endif()
message("soma_qt module: ${soma_qt}" )

include_directories( ${SIP_INCLUDE_DIRS} )
BRAINVISA_ADD_SIP_PYTHON_MODULE( somaqt soma "${CMAKE_CURRENT_SOURCE_DIR}/${soma_qt}"
  SIP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/${soma_qt}" SIP_INCLUDE "${PYQT${DESIRED_QT_VERSION}_SIP_DIR}" )
target_link_libraries( somaqt "${PYTHON_LIBRARY}" ${QT_LIBRARIES} )
