# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.

from __future__ import absolute_import
from brainvisa.processing.qtgui.backwardCompatibleQt import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QSizePolicy, QSpacerItem, QPushButton, QMenu, QTextEdit
from soma.wip.application.api import Application
from soma.qtgui.api import ApplicationQtGUI
from brainvisa.configuration import neuroConfig
from brainvisa.configuration.api import setSPM99Compatibility, DatabaseSettings
from brainvisa.data import neuroHierarchy
import brainvisa.processes
from brainvisa.processing import neuroLog
import brainvisa.mailing as mailing
import smtplib
import string
import os
import six

#------------------------------------------------------------------------------


def editConfiguration():
    """
    Opens Brainvisa options window. When the user closes the window, the configuration is saved in Brainvisa options file.

    Some options are taken into account immediately:

    * if databases selection has changed, databases are reloaded
    * if userLevel has changed, the list of available processes is updated
    * new HTML browser and new text editors are taken into account
    * language change is applied to documentation pages.

    Some other options are not applied directly but are saved in the options file and will be applied next time Brainvisa is started.
    """
    from brainvisa.data.qtgui.updateDatabases import warnUserAboutDatabasesToUpdate
    configuration = Application().configuration
    appGUI = ApplicationQtGUI()
    if appGUI.edit(configuration, live=False, modal=True):
        configuration.save(neuroConfig.userOptionFile)
        setSPM99Compatibility(configuration.brainvisa.SPM)
    newDataPath = [
        x for x in neuroConfig.dataPath if hasattr(x, 'builtin') and x.builtin]
    for fso in configuration.databases.fso:
        if fso.selected and fso.directory and os.path.exists(fso.directory):
            #newDataPath.append(DatabaseSettings(fso.directory,
                                                #read_only=fso.read_only))
            newDataPath.append(neuroConfig.get_database_settings(
                fso.directory, read_only=fso.read_only))
    if neuroConfig.dataPath != newDataPath:
        neuroConfig.dataPath = newDataPath
        neuroHierarchy.openDatabases()
        warnUserAboutDatabasesToUpdate()

    neuroHierarchy.update_soma_workflow_translations()

    if neuroConfig.userLevel != configuration.brainvisa.userLevel:
        neuroConfig.userLevel = configuration.brainvisa.userLevel
        brainvisa.processes.updateProcesses()
    neuroConfig.HTMLBrowser = configuration.brainvisa.htmlBrowser
    neuroConfig.textEditor = configuration.brainvisa.textEditor
    if neuroConfig.language != configuration.brainvisa.language \
            and configuration.brainvisa.language is not None:
        neuroConfig.language = configuration.brainvisa.language
        neuroConfig.docPath = os.path.join(
            neuroConfig.mainDocPath, neuroConfig.language)
        os.environ['LANGUAGE'] = neuroConfig.language
        brainvisa.processes.updateProcesses()

#----------------------------------------------------------------------------
bugReportDialog = None


class BugReportDialog(QWidget):

    def __init__(self, parent=None, name=None):
        QWidget.__init__(self, parent)
        if name:
            self.setObjectName(name)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        self.setWindowTitle(_t_('Bug report'))
        for field in ('From', 'To', 'Cc', 'Bcc'):
            hb = QHBoxLayout()
            label = QLabel(_t_(field))
            hb.addWidget(label)
            lineEdit = QLineEdit()
            setattr(self, 'led' + field, lineEdit)
            hb.addWidget(lineEdit)
            layout.addLayout(hb)

        label = QLabel(_t_('Message'))
        layout.addWidget(label)
        self.tedMessage = QTextEdit()
        layout.addWidget(self.tedMessage)

        self.chkSendLog = QCheckBox(_t_('Attach log file'))
        self.chkSendLog.setChecked(1)
        layout.addWidget(self.chkSendLog)

        self.ledFrom.setText(neuroConfig.userEmail)
        self.ledTo.setText(neuroConfig.supportEmail)

        hb = QHBoxLayout()
        layout.addLayout(hb)
        hb.setSpacing(6)
        hb.setContentsMargins(6, 6, 6, 6)
        spacer = QSpacerItem(
            20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hb.addItem(spacer)
        btn = QPushButton(_t_('Send'))
        hb.addWidget(btn)
        btn.clicked.connect(self._ok)
        btn = QPushButton(_t_('Cancel'))
        hb.addWidget(btn)
        btn.clicked.connect(self._cancel)

    def _ok(self):
        # Build email message
        outer = mailing.MIMEMultipart()
        outer['Subject'] = '[BrainVISA ' + \
            neuroConfig.versionString() + '] Bug report'
        for field in ('From', 'Cc', 'Bcc'):
            value = six.text_type(getattr(self, 'led' + field).text())
            if value:
                outer[field] = value
        to = six.text_type(self.ledTo.text())
        to = [x.strip() for x in to.split(',')]
        outer['To'] = ', '.join(to)
        if outer.get("Cc", None):
            to.extend([x.strip() for x in outer["Cc"].split(',')])
        if outer.get("Bcc", None):
            to.extend([x.strip() for x in outer["Bcc"].split(',')])

        outer.preamble = '\n'
        # To guarantee the message ends with a newline
        outer.epilogue = ''

        msg = mailing.MIMEText(
            six.text_type(self.tedMessage.toPlainText()), 'plain')
        outer.attach(msg)
        if self.chkSendLog.isChecked() and neuroConfig.logFileName:
            # Copy and expand log file
            tmp = brainvisa.processes.defaultContext().temporary('File')
            neuroLog.expandedCopy(neuroConfig.logFileName, tmp.fullPath())

            # Attach log file content
            file = open(tmp.fullPath(), 'rb')
            msg = mailing.MIMEBase('application', 'octet-stream')
            msg.set_payload(file.read())
            file.close()
            mailing.email.Encoders.encode_base64(msg)
            msg.add_header(
                'Content-Disposition', 'attachment', filename=neuroConfig.logFileName)
            outer.attach(msg)

        # Send message
        s = smtplib.SMTP(neuroConfig.SMTP_server_name)
        content = outer.as_string()
        s.sendmail(outer['From'], to, content)
        s.close()
        self.close()

    def _cancel(self):
        self.close()


#----------------------------------------------------------------------------
def showBugReport():
    global bugReportDialog

    if bugReportDialog is None:
        bugReportDialog = BugReportDialog()
    bugReportDialog.hide()
    bugReportDialog.show()
    bugReportDialog.raise_()


#----------------------------------------------------------------------------
def addSupportMenu(widget, menuBar):
    if mailing.canMail:
        supportMenu = menuBar.addMenu(_t_("&Support"))
        try:
            supportMenu.addAction(_t_('Bug report'), showBugReport)
        except Exception:
            showException()
    else:
        brainvisa.processes.defaultContext().log(_t_('Feature disabled'),
                                                 html=_t_('Bug report feature is disabled due to '
                                                          'missing email module in python'),
                                                 icon='warning.png')
