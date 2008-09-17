# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
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

import sys, os, traceback, htmllib
from neuroConfig import *
import neuroConfig
import neuroLog
from backwardCompatibleQt import *
from soma.html import htmlEscape

class HTMLMessage:
  """
  This class enables to create an error message in HTML format.
  Create an instance of this class to raise an error with an HTML message. 
  Example : raise RuntimeError( HTMLErrorMessage("<b>Error ...</b>") )
  """
  def __init__(self, msg):
    self.html=msg
    
  def __str__(self):
    return self.html  
   
def exceptionHTML( beforeError='', afterError='', exceptionInfo=None ):
  if exceptionInfo is None:
    exceptionInfo = sys.exc_info()

  msg = exceptionMessageHTML( exceptionInfo, beforeError=beforeError, afterError=afterError ) + '<hr>' + \
        exceptionTracebackHTML( exceptionInfo )
  return msg

def exceptionMessageHTML( exceptionInfo, beforeError='', afterError='' ):
  e, v, t = exceptionInfo
  #tb = traceback.extract_tb( t )
  txt="<b>"+htmlEscape( unicode(v) )+"</b>"
  if v is not None: # could occur when raising string exception (deprecated)
    if isinstance(v, Exception):
      if v.args:
        message=v.args[0]
        if isinstance(message, HTMLMessage): # if the exception message is in html, don't escape
          txt=message.html
        elif message and len(v.args)==1: # should be a user message in unicode
          txt="<b>"+htmlEscape( unicode(message) )+"</b>"
        else: # if there is no message, we must use str(v) to get the message. It should be a system exception and the message is encoded with console encoding. So we decode it with console encoding to get unicode string. 
          enco = sys.stdout.encoding
          if not enco:
            enco = 'utf8'
          txt="<b>"+htmlEscape( str(v).decode(enco) )+"</b>"
  msg = '<table border=0><tr><td width=50><img alt="' + _t_('ERROR') + '" src="' \
    + os.path.join( neuroConfig.iconPath, 'error.png' ) + '"></td><td><font color=red> ' \
    + beforeError \
    +" "+ txt + " " + afterError + '</font></td></tr></table>'
  return msg

def warningMessageHTML(message):
  msg =  '<table border=0><tr><td width=50><img alt="WARNING: " src="' \
      + os.path.join( neuroConfig.iconPath, 'warning.png' ) + '"></td><td><font color=orange><b>' + message+ '</b></font></td></tr></table>'
  return msg

def exceptionTracebackHTML( exceptionInfo ):
  e, v, t = exceptionInfo
  try:
    name = e.__name__
  except:
    name = str(e)
  tb = traceback.extract_tb( t )
  msg = '<font color=red><b>' + name + '</b><br>'
  for file, line ,function, text in tb:
    if text is None:
      text = '?'
    msg += htmlEscape( os.path.basename( file ) + ' (' + str(line) + ') in ' + function + ': '  ) + \
           '<blockquote> ' + htmlEscape( text ) + '</blockquote>'
  msg += '</font>'
  return msg


class ShowException( QDialog ):
  _theExceptionDialog = None 
  
  def __init__( self, messageHTML, detailHTML, parent = None, caption=None ):
    QDialog.__init__( self, parent, None, False, Qt.WType_Dialog + Qt.WGroupLeader + Qt.WShowModal )
#    QVBox.__init__( self, parent, None, Qt.WType_Dialog + Qt.WGroupLeader + Qt.WShowModal )
    layout = QVBoxLayout( self )
    
    layout.setMargin( 10 )
    layout.setSpacing( 5 )
    if caption is None:
      caption = _t_( 'Error' )
    self.setCaption( caption )
    self.teHTML = QTextEdit( self )
    self.teHTML.setReadOnly( True )
    layout.addWidget( self.teHTML )
    self.teHTML.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    self.messageHTML = [ messageHTML ] 
    self.detailHTML = [ detailHTML ]
    self.advancedMode = False
    self.updateText()
        
    hb = QHBoxLayout( layout )
#    layout.addLayout( hb )
    self.btnOk = QPushButton( _t_( 'Ok' ), self )
    hb.addWidget( self.btnOk )
    self.btnOk.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.btnOk.setDefault( True )
    self.btnOk.setAutoDefault( True )
    self.connect( self.btnOk, SIGNAL( 'clicked()' ), self, SLOT( 'close()' ) )
    
    self.btnAdvanced = QPushButton( _t_( 'more info' ), self )
    hb.addWidget( self.btnAdvanced )
    self.btnAdvanced.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    self.connect( self.btnAdvanced, SIGNAL( 'clicked()' ), self.changeAdvancedMode )
    self.updateText()
    
    self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding ) )
    self.resize( 640, 400 )
    ShowException._theExceptionDialog = self

  
  def changeAdvancedMode( self ):
    if self.advancedMode:
      self.advancedMode = False
      self.btnAdvanced.setText( _t_( 'more info' ) )
    else:
      self.advancedMode = True
      self.btnAdvanced.setText( _t_( 'hide info' ) )
    self.updateText()
      
  def updateText( self ):
    if self.advancedMode:
      self.teHTML.setText( '<hr>\n'.join( [i + '<hr>\n' + j for i, j in zip( self.messageHTML, self.detailHTML) ] ) )
    else:
      self.teHTML.setText( '<hr>\n'.join( self.messageHTML ) )
    self.teHTML.scrollToBottom()
    
  
  def appendException( self, messageHTML, detailHTML ):
    self.messageHTML.append( messageHTML )
    self.detailHTML.append( detailHTML )
    self.updateText()
    
  def close( self, alsoDelete ):
    self.hide()
    ShowException._theExceptionDialog = None
    return 1
  
def logException( beforeError='', afterError='', exceptionInfo=None, 
                  context=None ):
  if exceptionInfo is None:
    exceptionInfo = sys.exc_info()
  messageHTML = exceptionMessageHTML( exceptionInfo, beforeError=beforeError, afterError=afterError ) 
  detailHTML =  exceptionTracebackHTML( exceptionInfo ) 
  if context is None:
    neuroLog.log( 'Error', html=messageHTML + '<hr>' + detailHTML , icon='error.png' )
  else:
    context.log( 'Error', html=messageHTML + '<hr>' + detailHTML , icon='error.png' )
  return ( messageHTML, detailHTML )


def showException( beforeError='', afterError='', parent = None, 
                   gui=None, exceptionInfo=None ):
  if gui is None:
    gui = neuroConfig.gui
  try:
    messageHTML, detailHTML = logException( beforeError=beforeError,
                  afterError=afterError,
                  exceptionInfo=exceptionInfo )

    if gui and neuroConfig.guiLoaded:
      import neuroProcessesGUI
      if ShowException._theExceptionDialog is not None:
        neuroProcessesGUI.mainThreadActions().push( ShowException._theExceptionDialog.appendException, messageHTML, detailHTML )
      else:
        w = neuroProcessesGUI.mainThreadActions().call( ShowException, \
              messageHTML, \
              detailHTML, \
              parent=parent )
        neuroProcessesGUI.mainThreadActions().push( w.show )
    else:
      htmllib.HTMLParser( formatter.AbstractFormatter( 
        formatter.DumbWriter( sys.stdout, 80 ) ) )\
        .feed( messageHTML + '<hr>' + detailHTML ) 
  except Exception, e:
    traceback.print_exc()
    
def showWarning( message, parent = None, gui=None):
  if gui is None:
    gui = neuroConfig.gui
  try:
    messageHTML = warningMessageHTML( message )

    if gui and neuroConfig.guiLoaded:
      import neuroProcessesGUI
      if ShowException._theExceptionDialog is not None:
        neuroProcessesGUI.mainThreadActions().push( ShowException._theExceptionDialog.appendException, messageHTML, "" )
      else:
        w = neuroProcessesGUI.mainThreadActions().call( ShowException, \
              messageHTML, \
              "", \
              parent=parent )
        neuroProcessesGUI.mainThreadActions().push( w.show )
    else:
      htmllib.HTMLParser( formatter.AbstractFormatter( 
        formatter.DumbWriter( sys.stdout, 80 ) ) )\
        .feed( messageHTML + '<hr>' + "" ) 
  except Exception, e:
    traceback.print_exc()

def exceptionHook( exceptType, value, traceback ):
  showException( exceptionInfo=( exceptType, value, traceback ) )
