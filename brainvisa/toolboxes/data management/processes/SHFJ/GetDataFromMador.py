#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.
from neuroProcesses import *
from backwardCompatibleQt import *
from brainvisa.data import ftpDirectory
import shfjGlobals
import re

name = 'Get Data From Mador'
userLevel = 0

signature = Signature()


def splitExtension( fileName ):
  extension =  fileName[ fileName.rfind( '.' ): ][ 1 : ]
  if extension:
    withoutExtension = fileName[ : len( fileName ) - len( extension ) -1 ]
  else:
    withoutExtension = fileName
  return withoutExtension, extension


def readableSize( size ):
  size = float( size )
  unit = ''
  for n in ( 'b', 'Kb', 'Mb' ):
    if size < 1024:
      unit = n
      break
    size /= 1024
  if not unit: unit = 'Gb'
  return str( size ) + ' ' + unit
  
class Scanner:
  def __init__( self, name, baseDirectory=None ):
    self.name = name
    if baseDirectory is None:
      baseDirectory = '/imageurs/' + name
    self.storage = ftpDirectory.FTPDirectory( name, 'mador', 'base', 
                            '\x61\x72\x63\x68\x69\x76\x65\x31',
                            baseDirectory = baseDirectory )
    
  def retrieveFile( self, storageItem, fileName, bufferSize = 2048 ):
    input = storageItem.reader()
    output = open( fileName, 'wb' )
    while 1:
      data = input.read( bufferSize )
      output.write( data )
      if len( data ) < bufferSize: break
    input.close()
    

  def retrieveFiles( self, storageItems, outputDirectory,
                     preferedFormat = None ,
                     context = None, startDownloadFunction = None,
                     progressFunction = None ):
    if context is None:
      context = defaultContext()
    
    conversion = 0
    if preferedFormat is not None:
      conversion = 1

    for storageItem in storageItems:
      context.write( _t_( '<b>Processing %s</b>' ) % ( str(storageItem), ) )
      withoutExtension, extension = splitExtension( storageItem.name() )
      if extension == 'gz':
        # Retrieve data in a temporary file
        tmp = getTemporary( 'File' )
        context.write( _t_( 'downloading to <em>%s</em>' ) % ( tmp.fullPath(), ) )
        self.retrieveFile( storageItem, tmp.fullPath() )
        if conversion:
          # Uncompress in a temporary file
          fileToConvert = getTemporary( 'File', 
                                  name=os.path.basename( withoutExtension ) )
          context.write( _t_( 'uncompress from <em>%s</em> to <em>%s</em>' ) % \
                         ( tmp.fullPath(), fileToConvert.fullPath() ) )
          os.system( "gunzip -c '" + tmp.fullPath() + "' > '" + \
                          fileToConvert.fullPath() + "'" )
        else:
          # Uncompress in final location
          context.write( _t_( 'uncompress from <em>%s</em> to <em>%s</em>' ) % \
                         ( tmp.fullPath(), 
                           os.path.join( outputDirectory, 
                                         os.path.basename( withoutExtension ))))
          os.system( "gunzip -c " + tmp.fullPath() + " > " + os.path.join( outputDirectory, 
                          os.path.basename( withoutExtension ) ) )
      elif extension == 'Z':
       # Retrieve data in a temporary file
        tmp = getTemporary( 'File' )
        context.write( _t_( 'downloading to <em>%s</em>' ) % ( tmp.fullPath(), ) )
        self.retrieveFile( storageItem, tmp.fullPath() )
        context.system( 'mv', tmp.fullPath(), tmp.fullPath() + ".Z" )
        if conversion:
          # Uncompress in a temporary file
          fileToConvert = getTemporary( 'File', 
                                  name=os.path.basename( withoutExtension ) )
          context.write( _t_( 'uncompress from <em>%s</em> to <em>%s</em>' ) % \
                         ( tmp.fullPath(), fileToConvert.fullPath() ) )
          os.system( "uncompress -c " + tmp.fullPath() + ".Z" + " > " + fileToConvert.fullPath() )
        else:
          # Uncompress in final location
          context.write( _t_( 'uncompress from <em>%s</em> to <em>%s</em>' ) % \
                         ( tmp.fullPath(), 
                           os.path.join( outputDirectory, 
                                         os.path.basename( withoutExtension ))))
          os.system( "uncompress -c " + tmp.fullPath() + ".Z" + " > " + os.path.join( outputDirectory, 
                          os.path.basename( withoutExtension ) ) )
      else:
        if conversion:
          # Retrieve data in a temporary file
          fileToConvert = getTemporary( 'File', name=storageItem.name() )
          context.write( _t_( 'downloading to <em>%s</em>' ) % \
                         ( fileToConvert.fullPath(), ) )
          self.retrieveFile( storageItem, fileToConvert.fullPath() )
        else:
          # Retrieve data in final location
          context.write( _t_( 'downloading to <em>%s</em>' ) % ( os.path.join( outputDirectory, storageItem.name() ), ) )
          self.retrieveFile( storageItem, os.path.join( outputDirectory, storageItem.name() ) )
      if conversion:
        context.write( _t_( 'convert from <em>%s</em> to <em>%s</em>' ) % ( fileToConvert.fullPath(), os.path.join( outputDirectory, os.path.basename( withoutExtension ) + '.' + preferedFormat ) ) )
        context.system( 'AimsFileConvert', '-i', fileToConvert, '-o', os.path.join( outputDirectory, os.path.basename( withoutExtension ) + '.' + preferedFormat ) )
      context.write( 'done' )


# The following class should be specialized (mainly by redefinition of retrieveFiles) for SHFJ Bruker scanner
class BrukerScanner( Scanner ):
  def __init__( self ):
    Scanner.__init__( self, 'bruker' )

  

def initialization( self ):
  self.scanners = {
    'HR+ 1': Scanner( 'hrplus' ),
    'HR+ 2': Scanner( 'hrplus2' ),
    # Now high resolution scanners put images in new directories
    'HRRT': Scanner( 'hrrt', baseDirectory = '/hrimageurs/hrrt/images' ),
    'FOCUS': Scanner( 'focus',baseDirectory = '/hrimageurs/focus/images' ),
  }
  # 3T Bruker is available only if expert userLevel is selected
  if neuroConfig.userLevel >= 2:
    self.scanners[ '3T Bruker' ] = BrukerScanner()
  
  # Associate a format name with an extension recognized by AimsFileConvert
  self.formats = [
    ( 'Automatic', None ),
    ( 'GIS', 'ima' ),
    ( 'Analyse / SPM', 'img' ),
  ]

class ImaservGUI( QVBox ):
  class DirectoryDialog( QFileDialog ):
    def __init__( self, parent ):
      QFileDialog.__init__( self, parent )
      self.setMode( QFileDialog.DirectoryOnly )
      
    def accept( self ):
      self.emit( PYSIGNAL( 'accept' ), () )
      QFileDialog.accept( self )
  
  def __init__( self, values, context, parent ):
    self.parentDirectory = None
    self.context = None
    QVBox.__init__( self, parent )
    if getattr( ImaservGUI, 'pixBrowse', None ) is None:
      setattr( ImaservGUI, 'pixBrowse', QPixmap( os.path.join( neuroConfig.iconPath, 'browse_write.png' ) ) )

    hb = QHBox( self )
    QLabel( 'Scanner: ', hb )
    self.cmbScanner = QComboBox( hb, 'cmbScanner' )
    if context is not None:
      scannerNames = context.process.scanners.keys()
      scannerNames.sort()
      for scanner in scannerNames:
        self.cmbScanner.insertItem( scanner )
    self.connect( self.cmbScanner, SIGNAL( 'activated( int )' ),
                  self.scannerChanged )
    self.currentScanner = None
    
    self.labDirectory = QLabel( 'Directory:', self )
    self.lbxDirectories = QListBox( self )
    self.connect( self.lbxDirectories, SIGNAL( 'highlighted( int )' ), 
                  self.directorySelected )
    QLabel( 'Files: ', self )
    self.lbxFiles = QListBox( self )
    self.lbxFiles.setSelectionMode( QListBox.Multi )
    # self.lbxFiles.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding ) )
    self._acceptDirectorySelection = 1
    self.scannerChanged( 0 )
    
    hb = QHBox( self )
    QLabel( 'Output format: ', hb )
    self.cmbFormats = QComboBox( hb, 'cmbFormats' )
    if context is not None:
      for f in context.process.formats:
        self.cmbFormats.insertItem( f[0] )

    hb = QHBox( self )
    QLabel( 'Output directory: ', hb )
    self.ledOutputDirectory = QLineEdit( hb )
    btn = QPushButton( hb )
    btn.setPixmap( self.pixBrowse )
    btn.setFocusPolicy( QWidget.NoFocus )
    self.connect( btn, SIGNAL( 'clicked()' ), self.browseOutputDirectory )
    self.browseDialog = None
  
    hb = QHBox( self )
    btn = QPushButton( 'retrieve', hb )
    # btn.setSizePolicy( QSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed ) )
    if context is not None:
      self.connect( btn, SIGNAL( 'clicked()' ), context._runButton )
    self.context = context

  def scannerChanged( self, index ):
    scannerName = str( self.cmbScanner.text( index ).latin1() )
    if self.context is not None:
      self.currentScanner = self.context.process.scanners[ scannerName ]
      self.parentDirectories = []
      self.currentDirectory = self.currentScanner.storage.get( '' )
      self.changeDirectory()
    
  
  def changeDirectory( self ):
    self._acceptDirectorySelection = 0
    try:
      self.lbxDirectories.clear()
      self.directoryItems = []
      self.lbxFiles.clear()
      self.fileItems = []
      self.labDirectory.setText( 'Directory: <b>' + str( self.currentDirectory ) + \
                                 '</b>')
      if self.parentDirectories:
        self.lbxDirectories.insertItem( '..' )
        self.directoryItems.append( None )
      for item in self.currentDirectory.children():
        if item.hasChildren():
          self.lbxDirectories.insertItem( item.name() )
          self.directoryItems.append( item )
        else:
          self.lbxFiles.insertItem( item.name() + '  ' + readableSize( item.size() ) )
          self.fileItems.append( item )
    finally:
      self._acceptDirectorySelection = 1

  def directorySelected( self, index ):
    if self._acceptDirectorySelection:
      if index >= 0:
        newDirectory = self.directoryItems[ index ]
        if newDirectory is None:
          # '..' has been choosen
          self.currentDirectory = self.parentDirectories.pop()
          self.changeDirectory()
        else:
          self.parentDirectories.append( self.currentDirectory )
          self.currentDirectory = self.directoryItems[ index ]
          self.changeDirectory()

  def browseOutputDirectory( self ):
    if self.browseDialog is None:
      self.browseDialog = self.DirectoryDialog( self.topLevelWidget() )
      self.connect( self.browseDialog, 
                    PYSIGNAL( 'accept' ),
                    self.browseOutputDirectoryAccepted )
    self.browseDialog.show()
    
  def browseOutputDirectoryAccepted( self ):
    self.ledOutputDirectory.setText( self.browseDialog.selectedFile() )

  
    
def inlineGUI( self, values, context, parent ):
  result = ImaservGUI( values, context, parent )
  return result


def execution( self, context ):
  gui = context.inlineGUI
  outputDirectory = str( gui.ledOutputDirectory.text().latin1() )
  if not outputDirectory:
    raise RuntimeError( _t_( 'You must choose an output directory' ) )
  if not os.path.isdir( outputDirectory ):
    answer = context.ask( _t_( '<em>%s</em> is not an existing directory. Do you want to create it ?' ) % outputDirectory, 
                          _t_( 'Yes' ), _t_( 'Cancel' ) )
    if answer == 1: 
      context.write( '<font color=orange>' + _t_( 'Directory not created. Operation canceled.' ) + '</font>' )
      return
    os.mkdir( outputDirectory )

  files = []
  for i in xrange( gui.lbxFiles.count() ):
    if gui.lbxFiles.isSelected( i ):
      files.append( gui.fileItems[ i ] )
  gui.currentScanner.retrieveFiles( files, 
    outputDirectory, 
    preferedFormat = self.formats[ gui.cmbFormats.currentItem() ][ 1 ],
    context = gui.context,
#    startDownloadFunction = gui._startDownload, 
#    progressFunction = gui._downloadProgress
  )



