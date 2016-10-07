include_directories( ${SIP_INCLUDE_DIRS} )
BRAINVISA_ADD_SIP_PYTHON_MODULE( somaqt soma "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt.sip"
  SIP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt.sip" SIP_INCLUDE "${PYQT${DESIRED_QT_VERSION}_SIP_DIR}" )
target_link_libraries( somaqt "${PYTHON_LIBRARY}" ${QT_LIBRARIES} )
