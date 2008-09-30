# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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


'''
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


from qt import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QPushButton

from soma.wip.configuration import ConfigurationGroup
from soma.signature.api import Signature, Unicode, FileName, Sequence, Boolean
from soma.qt3gui.api import Qt3GUI
from soma.signature.qt3gui.signature_qt3gui import HasSignature_Qt3GUI


#------------------------------------------------------------------------------
class MatlabConfiguration( ConfigurationGroup ):
  label = 'Matlab'
  icon = 'matlab.png'
  signature = Signature(
    'enable_matlab', Boolean, dict( defaultValue=False, doc='if unchecked, matlab is disabled' ),
    'executable', FileName, dict( defaultValue='matlab', doc='location of the Matlab program' ),
    'version', Unicode, dict( defaultValue=u'', doc='Matlab version' ),
    'options', Unicode, dict( defaultValue=u'-nosplash -nojvm', doc='Options passed to Matlab executable.' ),
    'path', Sequence( Unicode ), dict( defaultValue=[], doc='List of directories that will be added to Matlab path.' ),
    'startup', Sequence( Unicode ), dict( defaultValue=[], doc='List of Matlab commands to execute at startup.' ),
  )


#------------------------------------------------------------------------------
class MatlabConfiguration_Qt3GUI( Qt3GUI ):
  '''
  This class adds a 'guess configuration' button to default GUI.
  '''
  def __init__( self, instance ):
    Qt3GUI.__init__( self, instance )
    self._defaultGUI = HasSignature_Qt3GUI( instance )
  
  
  def editionWidget( self, value, parent=None, name=None, live=False ):
    widget = QWidget( parent, name )
    layout = QVBoxLayout( widget, 0, 6 )
    self._defaultWidget = self._defaultGUI.editionWidget( value, parent=widget, live=live )
    layout.addWidget( self._defaultWidget )

    layout2 = QHBoxLayout( None, 0, 6 )
    spacer = QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum )
    layout2.addItem( spacer )
    self.btnGuess = QPushButton(  _t_( 'guess configuration' ), widget )
    self.btnGuess.setEnabled( False )
    layout2.addWidget( self.btnGuess )
    spacer = QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum )
    layout2.addItem( spacer )
    
    layout.addLayout( layout2 )
    return widget
  
  
  def closeEditionWidget( self, editionWidget ):
    self.btnGuess.deleteLater()
    self._defaultGUI.closeEditionWidget( self._defaultWidget )
    editionWidget.close()
    editionWidget.deleteLater()
  
  
  def setObject( self, editionWidget, value ):
    self._defaultGUI.setObject( self._defaultWidget, value )


  def updateEditionWidget( self, editionWidget, value ):
    self._defaultGUI.updateEditionWidget( self._defaultWidget, value )


_valid = None
_validchecked = None


#import distutils, os
#from brainvisa.validation import ValidationError
#import neuroProcesses, neuroLog
#from brainvisa import matlab


#def detect_matlab_version( matexe, log=None ):
  #if matlab.matlabRelease:
    #mver =  matlab.matlabRelease
    #if log is not None:
      #log[0] += _t_( 'matlab release is forced in config' ) + '<br>'
  #else:
    #if log is not None:
      #log[0] += _t_( 'opening matlab to guess release version' ) + '<br>'
    #tmp = neuroProcesses.defaultContext().temporary( 'File' )
    #cmd = "fid = fopen( '" + tmp.fullPath() + "', 'w' ); fprintf( fid, version('-release'), '%s' ); fclose( fid ); exit"
    #try:
      #try:
        ## Valid only since Python 2.4
        #import subprocess
        #out, err = subprocess.Popen( ( matexe, '-nodesktop', '-nosplash', '-r', cmd ), 
                                     #stdout=subprocess.PIPE, stderr=subprocess.PIPE ).communicate()
      #except ImportError:
        ## Work with earlier Python version but generates the following error at exit:
        ## Exception exceptions.TypeError: TypeError("'NoneType' object is not callable",) in <bound method Popen3.__del__ of <popen2.Popen3 instance at 0xb7303c2c>> ignored
        #stdin, stdout, stderr = os.popen3( matexe + ' "-nodesktop" "-nosplash" "-r" "' + cmd + '"' )
        #stdin.close()
        #err = stderr.read()
        #out = stdout.read()
        #stdout.close()
        #stderr.close()
        #del stdout, stderr, stdin
      #if log is not None:
        #log[0] += _t_( 'matlab seems to work. How lucky you are.' ) + '<br>'
        #if err:
          #log[0] += '<b>' + _t_( 'matlab error output' ) + '</b>: ' + err \
                    #+ '<br>'
      #if log is not None and not os.path.exists( tmp.fullPath() ):
        #log[0] += _t_( "matlab didn't write the verison file it should" ) \
                  #+ '<br>'
        #return None
      #f = open( tmp.fullPath() )
      #mver = f.readline()
      #f.close()
    #except Exception, e:
      #import traceback
      #traceback.print_exc()
      #if log is not None:
        #log[0] += _t_( 'Matlab could not start' ) + ':' + str(e) + '<br>'
      #return None
    #matlab.matlabRelease = mver
  #mver = mver.split( '.' )[0]
  #if matlab.matlabRelease.startswith( '20' ) and len( mver ) >= 5:
    ## new style: '2006a'
    #return '7' # for now it's only matlab 7
  #else:
    #mver = int( mver )
    #if mver < 12:
      #return '5'
    #elif mver < 14:
      #return '6'
    #else:
      #return '7'
