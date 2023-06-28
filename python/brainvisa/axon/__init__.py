"""
This module enables to start Brainvisa in batch mode through a python script.

It is useful to write a Python script that uses Brainvisa. Usage:

  >>> import brainvisa.axon
  >>> brainvisa.axon.initializeProcesses()
  Loading toolbox ...

Then, Brainvisa, its processes and databases are loaded and it can be used as if it were started in batch mode (``brainvisa -b``).

At the end of your script, call a cleanup function. It would be called automatically at exit, but it is better to call it from the main thread:

  >>> brainvisa.axon.cleanup()

"""
import os
import sys

# Force QString API version in order to be compatible with recent version
# of enthought.traits.ui (3.6 for instance)
from soma.qt_gui.qt_backend import sip
PYQT_API_VERSION = 2
try:
    qt_api = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
              "QVariant"]
    qt_api_ver = None
    for qt_class in qt_api:
        try:
            qt_api_ver = sip.getapi(qt_class)
            if qt_api_ver == PYQT_API_VERSION:
                continue
        except Exception:
            pass  # getapi() fails: probably not set yet
        sip.setapi(qt_class, PYQT_API_VERSION)
    del qt_api, qt_class, qt_api_ver
except Exception:
    print("WARNING: impossible to use version %d of sip/Qt API."
          % PYQT_API_VERSION)

import brainvisa
brainvisa_path = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(brainvisa.__file__))), 'brainvisa')
argv = sys.argv
# Temporarily change argv[0] since it is used in neuroConfig initialization
# to set paths
sys.argv = [os.path.join(brainvisa_path, 'neuro.py'), '-b']
sys.path.insert(0, brainvisa_path)
try:
    import soma.somaqt  # force loading the right Qt
except ImportError:
    pass
from soma.qt_gui import qt_backend
qt_backend.set_qt_backend(compatible_qt5=True)
from brainvisa.configuration import neuroConfig
from brainvisa.processing import neuroLog
from brainvisa.axon.processes import initializeProcesses, cleanup

# set back argv[0] to its original value
sys.argv = argv
del argv

neuroConfig.initGlobalVariables()

# once imported and initialized, the modules do not need to be
# referenced any longer here.
del brainvisa, qt_backend, neuroConfig, neuroLog, sys, os, sip
