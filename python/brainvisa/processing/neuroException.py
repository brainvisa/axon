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
"""
The functions are used to display error and warning messages in Brainvisa.

:py:func:`showException` can be used to display a message describing the last exception that occured in Brainvisa error window or in the console. In the same way, the function :py:func:`showWarning` can be used to display warning message.

*Example*

>>> try:
>>>   <code that can raise an exception>
>>> except:
>>>   neuroException.showException(beforeError="The following error occured when...:")

"""
from __future__ import absolute_import
import sys
import os
import traceback
import formatter
from brainvisa.configuration.neuroConfig import *
from brainvisa.configuration import neuroConfig
from soma.html import htmlEscape
import six
if sys.version_info[0] >= 3:
    from html.parser import HTMLParser

else:
    from htmllib import HTMLParser


class HTMLMessage:

    """
    This class enables to create an error message in HTML format.
    Creates an instance of this class to raise an error with an HTML message.

    Example: raise RuntimeError( HTMLMessage("<b>Error ...</b>") )
    """

    def __init__(self, msg):
        self.html = msg

    def __str__(self):
        return self.html


def exceptionHTML(beforeError='', afterError='', exceptionInfo=None):
    """
    Generates an HTML message that describes the given exception with its traceback.

    :param tuple exceptionInfo: (type, value, traceback) describing the exception.
    :param string beforeError: Message that will be displayed before the text of the exception.
    :param string afterError: Message that will be displayed after the text of the exception.
    :rtype: string
    :returns: the message in HTML format.

    """
    if exceptionInfo is None:
        exceptionInfo = sys.exc_info()

    msg = exceptionMessageHTML( exceptionInfo, beforeError=beforeError, afterError=afterError ) + '<hr>' + \
        exceptionTracebackHTML(exceptionInfo)
    return msg


def exceptionMessageHTML(exceptionInfo, beforeError='', afterError=''):
    """
    Generates an HTML message that describes the given exception. The traceback of the exception is not included in the message.

    :param tuple exceptionInfo: (type, value, traceback) describing the exception.
    :param string beforeError: Message that will be displayed before the text of the exception.
    :param string afterError: Message that will be displayed after the text of the exception.
    :rtype: string
    :returns: the message in HTML format.
    """

    e, v, t = exceptionInfo
    message = '<br>'.join(
        htmlEscape(line) for line in traceback.format_exception_only(e, v)
    )
    txt = "<b>" + message + "</b>"
    if isinstance(v, BaseException) and len(v.args) == 1:
        if isinstance(v.args[0], HTMLMessage):
            # if the exception message is in html, don't escape
            txt = v.args[0].html
    msg = '<table border=0><tr><td width=50><img alt="' + _t_('ERROR') + '" src="' \
        + os.path.join( neuroConfig.iconPath, 'error.png' ) + '"></td><td><font color=red> ' \
        + beforeError \
        + " " + txt + " " + afterError + '</font></td></tr></table>'
    return msg


def warningMessageHTML(message):
    msg =  '<table border=0><tr><td width=50><img alt="WARNING: " src="' \
        + os.path.join(neuroConfig.iconPath, 'warning.png' ) + \
                       '"></td><td><font color=orange><b>' + \
                           message + '</b></font></td></tr></table>'
    return msg


def exceptionTracebackHTML(exceptionInfo):
    """
    Generates an HTML message that describes the traceback of the given exception.

    :param tuple exceptionInfo: (type, value, traceback) describing the exception.
    :rtype: string
    :returns: the message in HTML format.
    """
    e, v, t = exceptionInfo
    try:
        name = e.__name__
    except AttributeError:
        name = str(e)
    msg = '<font color=red><b>' + name + '</b><br>'
    if(t is not None):
        tb = traceback.extract_tb(t)
        for file, line, function, text in tb:
            if text is None:
                text = '?'
            msg += htmlEscape( os.path.basename( file ) + ' (' + str(line) + ') in ' + function + ': '  ) + \
                '<blockquote> ' + htmlEscape(text) + '</blockquote>'
    msg += '</font>'
    return msg


def logException(beforeError='', afterError='', exceptionInfo=None,
                 context=None):
    """
    Generates two HTML messages to represent the current exception: a short one and a detailed version.
    The exception is also stored in Brainvisa log file.
    The detailed message shows the traceback of the exception.
    The short message is generated with the function :py:func:`exceptionMessageHTML` and the detailed one with :py:func:`exceptionTracebackHTML`.

    :param string beforeError: Message that will be displayed before the text of the exception.
    :param string afterError: Message that will be displayed after the text of the exception.
    :param tuple exceptionInfo: tuple (type, value, traceback) describing the exception. If None, :py:func:`sys.exc_info` is used to get the exception.
    :param context: :py:class:`brainvisa.processes.ExecutionContext` that can be used to store the message at the right place in the log file.
      Indeed, the current log could be the log of a process execution.
      If None, the default context is used.
    :rtype: tuple
    :returns: A short HTML message and a detailed version of the message.
    """
    if exceptionInfo is None:
        exceptionInfo = sys.exc_info()
    messageHTML = exceptionMessageHTML(
        exceptionInfo, beforeError=beforeError, afterError=afterError)
    detailHTML = exceptionTracebackHTML(exceptionInfo)
    from brainvisa.processing import neuroLog
    if context is None:
        neuroLog.log('Error', html=messageHTML +
                     '<hr>' + detailHTML, icon='error.png')
    else:
        context.log('Error', html=messageHTML +
                    '<hr>' + detailHTML, icon='error.png')
    return (messageHTML, detailHTML)


def showException(beforeError='', afterError='', parent=None,
                  gui=None, exceptionInfo=None):
    """
    Displays an error message describing the last exception that occurred or the exception information given in parameter.
    The message can be displayed in Brainvisa error window or in the console.
    The generated message is in HTML format and have a style adapted to error messages (icon, font color).

    :param string beforeError: Message that will be displayed before the text of the exception.
    :param string afterError: Message that will be displayed after the text of the exception.
    :param parent: A parent widget for the exception widget. Optional.
    :param boolean gui: If True, the graphical interface is used to display the exception. Else, it is displayed in the console.
      If None, it is displayed with the graphical interface if Brainvisa is in graphical mode.
    :param tuple exceptionInfo: tuple (type, value, traceback) describing the exception. If None, :py:func:`sys.exc_info` is used to get the exception.
    """
    if gui is None:
        gui = neuroConfig.gui
    try:
        messageHTML, detailHTML = logException(beforeError=beforeError,
                                               afterError=afterError,
                                               exceptionInfo=exceptionInfo)

        if gui and neuroConfig.guiLoaded:
            from brainvisa.processing.qtgui.neuroExceptionGUI import ShowException
            if ShowException._theExceptionDialog is not None:
                from brainvisa.processes import mainThreadActions
                mainThreadActions().push(
                    ShowException._theExceptionDialog.appendException, messageHTML,
                  detailHTML)
            else:
                from brainvisa.processes import mainThreadActions
                w = mainThreadActions().call(ShowException,
                                             messageHTML,
                                             detailHTML,
                                             parent=parent)
                mainThreadActions().push(w.show)
        else:
            if sys.version_info[0] >= 3:
                HTMLParser().feed(messageHTML + '<hr>' + detailHTML)
            else:
                HTMLParser(formatter.AbstractFormatter(
                          formatter.DumbWriter(sys.stdout, maxcol=80)))\
                    .feed(messageHTML + '<hr>' + detailHTML)
    except Exception as e:
        traceback.print_exc()
    # why this violent exit ??
    # if neuroConfig.fastStart and not neuroConfig.gui:
        # sys.exit( 1 )


def showWarning(message, parent=None, gui=None):
    """
    Shows a warning message.
    The message can be displayed in Brainvisa error window or in the console.
    The generated message is in HTML format and have a style adapted to warning messages (icon, font color).

    :param string message: Warning message that will be displayed.
    :param parent: A parent widget for the exception widget. Optional.
    :param boolean gui: If True, the graphical interface is used to display the exception. Else, it is displayed in the console.
      If None, it is displayed with the graphical interface if Brainvisa is in graphical mode.
    """
    if gui is None:
        gui = neuroConfig.gui
    try:
        messageHTML = warningMessageHTML(message)

        if gui and neuroConfig.guiLoaded:
            from brainvisa.processes import mainThreadActions
            from brainvisa.processing.qtgui.neuroExceptionGUI import ShowException
            if ShowException._theExceptionDialog is not None:
                mainThreadActions().push(
                    ShowException._theExceptionDialog.appendException, messageHTML, "")
            else:
                w = mainThreadActions().call(ShowException,
                                             messageHTML,
                                             "",
                                             parent=parent)
                mainThreadActions().push(w.show)
        else:
            HTMLParser(formatter.AbstractFormatter(
                       formatter.DumbWriter( sys.stdout, 80 ) ) )\
                .feed(messageHTML + '<hr>' + "")
    except Exception as e:
        traceback.print_exc()


def exceptionHook(exceptType, value, traceback):
    from brainvisa.processing.qtgui.neuroExceptionGUI import ShowException
    showException(exceptionInfo=(exceptType, value, traceback))
