
from brainvisa.processes import *

userLevel = 0
roles = ('viewer', )

signature = Signature(
    'document', ReadDiskItem('PDF file', 'PDF file'),
)


def execute_mainthread(self, context):
    #return runHtmlBrowser(self.document.fullPath())
    from soma.qt_gui.qt_backend import QtWebEngineWidgets, QtCore

    view = QtWebEngineWidgets.QWebEngineView()
    settings = view.settings()
    settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled,
                          True)
    url = QtCore.QUrl(self.document.fullPath())
    print('url:', url)
    view.load(url)
    view.show()

    return view


def execution(self, context):
    #return mainThreadActions().call(self.execute_mainthread, context)
    context.pythonSystem('bv_pdf_viewer', self.document)

