# -*- coding: iso-8859-1 -*-
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

from brainvisa.processes import *
from soma.wip.application.api import Application
import soma
import soma.minf.api as minfio
from soma import aims
from PyQt4 import QtGui, QtCore
import shfjGlobals
from tempfile import mkstemp
import os, fnmatch, glob, csv, math
import anatomist.api as ana
from anatomist.cpp.paletteEditor import PaletteEditor
import numpy as np

name = 'Display SPM analysis results'
userLevel = 0

signature = Signature( 
  'spm_mat', ReadDiskItem( 'Matlab SPM file', 'Matlab file' ),
  'title', String(),
  'pvalue_adjustment', Choice( 'FDR', 'FWE', 'none' ),
  'pvalue_threshold', Float(),
  'pvalue_extent_threshold', Integer(),
  'result_image_type', Choice( 'Thresholded SPM', 'All clusters (binary)', 'All clusters (n-ary)' ),
  'comment', String(),
  'display_glass_brain', Choice( 'Yes', 'No' )
)

def locateFile( pattern, root = os.curdir ):
    """
    Locates a file in a directory tree
    
    :param string pattern:
        The pattern to find
    
    :param string root:
        The search root directory
    
    :returns:
        The first found occurence
    """
    for path, dirs, files in os.walk( os.path.abspath( root ) ):
        for filename in fnmatch.filter( files, pattern ):
            return os.path.join( path, filename )

def initialization( self ):
    # Default parameters
    self.pvalue_adjustment = 'FDR'
    self.pvalue_threshold = 0.05
    self.pvalue_extent_threshold = 30
    self.result_image_type = 'Thresholded SPM'
    self.setOptional( 'comment' )
    self.title = "SPM analysis results"
    self.display_glass_brain = 'Yes'
    self.result_image_type_dic = {
                                  'Thresholded SPM' : 'thresh',
                                  'All clusters (binary)' : 'binary',
                                  'All clusters (n-ary)' : 'n-ary' 
                                  }
    
    # Boolean for blocking the 3D cursor signals
    self.blockCursorUpdate = False
    
    # MNI bounding box
    self.mniBbox = [ [ -90, -126, -72 ], [ 90, 90, 108 ] ]

def execution( self, context ):
    # Check if SPM standalone is defined in BrainVISA preferences
    self.configuration = Application().configuration
    if not self.configuration.SPM.spm8_standalone_command \
        or not self.configuration.SPM.spm8_standalone_mcr_path:
        return
    
    # Save the previous directory path
    previousDir = os.getcwd()
    
    # Set the current directory to the current SPM analysis path
    self.spmMatPath = os.path.dirname( os.path.realpath( self.spm_mat.fullPath() ) )
    if not os.path.exists( self.spmMatPath ):
        return
    os.chdir( self.spmMatPath )

    # Find the single subject MRI
    self.singleSubject = locateFile( "single_subj_T1.nii",
                                     root = os.path.dirname( self.configuration.SPM.spm8_standalone_command ) )

    # Init the atlas parameters
    self.setAtlasFiles()
    
    # Set the output files
    self.resultMap = os.path.join( self.spmMatPath, "result_map.img" )
    self.statsCsv = os.path.join( self.spmMatPath, "stats.csv" )
    self.threshInfo = os.path.join( self.spmMatPath, "thresholding.info" )
    
    # Compute SPM analysis results
    self.computeResults( context )
    
    # Init Anatomist
    self.a = ana.Anatomist('-b')
        
    # Display SPM analysis results
    mainThreadActions().call( self.display, context )
 
    # Back to the previous directory
    os.chdir( previousDir )

def setAtlasFiles( self ):
    """
    Checks the available atlases and gets their pathes if found
    """
    self.atlasFiles = {
                       "AAL" : "aal_MNI_V4.img",
                       "Brodmann" : "TD_brodmann.img",
                       "Hemisphere" : "TD_hemisphere.img",
                       "Label" : "TD_label.img",
                       "Lobe" : "TD_lobe.img",
                       "Type" : "TD_type.img",
                       }

    self.pickAtlasPath = self.configuration.SPM.spm8_wfu_pickatlas_path
    for k, v in self.atlasFiles.items():
        atlasLocation = locateFile( v, root = self.pickAtlasPath )
        print atlasLocation
        if not atlasLocation:
            del self.atlasFiles[ k ]
        else:
            self.atlasFiles.update( { k : atlasLocation } )

def isAtlasAvailable( self ):
    """
    Checks if at least one atlas is available
    
    :returns:
        True if an atlas is available
    """
    return len( self.atlasFiles ) > 0

def isGlassBrainAvailable( self ):
    """
    Checks if the glass brain views must be displayed
    
    :returns:
        The display_glass_brain parameter value
    """
    return self.display_glass_brain == 'Yes'

def computeResults( self, context ):
    """
    Computes the SPM analysis results according to the spm_mat parameter
    """
    # Write the SPM script
    matFileFi, matFile = mkstemp( suffix = ".m" )
    matFileFd = os.fdopen( matFileFi, "w" )
    matFileFd.write( \
"""
spm_get_defaults('stats.topoFDR', 0);
spm_get_defaults('cmdline', true);
spm_jobman('initcfg');
matlabbatch{1}.spm.stats.results.spmmat = { '%s' };
matlabbatch{1}.spm.stats.results.conspec.titlestr = '%s';
matlabbatch{1}.spm.stats.results.conspec.contrasts = 1;
matlabbatch{1}.spm.stats.results.conspec.threshdesc = '%s';
matlabbatch{1}.spm.stats.results.conspec.thresh = %s;
matlabbatch{1}.spm.stats.results.conspec.extent = %s;
matlabbatch{1}.spm.stats.results.conspec.mask = struct('contrasts', {}, 'thresh', {}, 'mtype', {});
matlabbatch{1}.spm.stats.results.units = 1;
matlabbatch{1}.spm.stats.results.print = true;
spm_jobman('run', matlabbatch);
XYZ = xSPM.XYZ;
switch lower( '%s' )
    case 'thresh'
        Z = xSPM.Z;

    case 'binary'
        Z = ones(size(xSPM.Z));

    case 'n-ary'
        Z       = spm_clusters(XYZ);
        num     = max(Z);
        [n, ni] = sort(histc(Z,1:num), 2, 'descend');
        n       = size(ni);
        n(ni)   = 1:num;
        Z       = n(Z);
end
spm_write_filtered( Z, XYZ, xSPM.DIM, xSPM.M, '', '%s' );
tmpfile = [ '%s' ];
fid = fopen(tmpfile,'wt');
fprintf(fid,[repmat('%%s,',1,11) '%%d,,\\n'],TabDat.hdr{1,:});
fprintf(fid,[repmat('%%s,',1,12) '\\n'],TabDat.hdr{2,:});
fmt = TabDat.fmt;
[fmt{2,:}] = deal(','); fmt = [fmt{:}];
fmt(end:end+1) = '\\n'; fmt = strrep(fmt,' ',',');
for i=1:size(TabDat.dat,1)
  fprintf(fid,fmt,TabDat.dat{i,:});
end
fclose(fid);

tmpfile = [ '%s' ];
fid = fopen(tmpfile, 'wt');
fprintf(fid, '%%s', sprintf('Height threshold %%c = %%0.2f {%%s}', xSPM.STAT, xSPM.u, xSPM.thresDesc));
fprintf(fid, '\\n' );
fprintf(fid, '%%s', sprintf('Extent threshold k = %%0.0f voxels', xSPM.k));
fclose(fid);
""" \
    % ( self.spm_mat.fullPath(),
        self.title,
        self.pvalue_adjustment,
        self.pvalue_threshold,
        self.pvalue_extent_threshold,
        self.result_image_type_dic[ self.result_image_type ],
        self.resultMap,
        self.statsCsv,
        self.threshInfo ) )
    matFileFd.close()
    
    # Launch SPM standalone
    mexe = self.configuration.SPM.spm8_standalone_command
    cmd = [ mexe,
            self.configuration.SPM.spm8_standalone_mcr_path,
            'script',
            matFile ]
    context.write( 'SPM analysis: computing T-map' )
    context.system( *cmd )

def display( self, context ):
    """
    Displays the results (statistics and views)
    """
    mainDialog = QtGui.QDialog()
    
    # Set the window title
    title = ""
    try:
        pass
    except:
        title = ""
    title = "SPM analysis results"
    mainDialog.setWindowTitle( title )
    mainDialog.setWindowFlags( QtCore.Qt.WindowTitleHint |
                               QtCore.Qt.WindowMinMaxButtonsHint |
                               QtCore.Qt.WindowCloseButtonHint )
    
    palette = mainDialog.palette();
    palette.setColor( mainDialog.backgroundRole(), QtGui.QColor( 255, 255, 255 ) );
    mainDialog.setPalette( palette );
    mainDialog.setAutoFillBackground( True );
    mainVlay = QtGui.QVBoxLayout( mainDialog )
    mainVlay.setMargin( 0 )
    self.awin = QtGui.QFrame()
    mainVlay.addWidget( self.awin )
    vlay = QtGui.QVBoxLayout( self.awin )
    vlay.setMargin( 0 )
    splitter = QtGui.QSplitter( QtCore.Qt.Vertical, self.awin )
    vlay.addWidget( splitter )
    
    # Create the bottom part (stats) of the window
    self.createBottom( context, splitter )
    # Create the top part (graphics + information) of the window
    self.createTop( context, splitter )
    
    try:
        # Select the global maxima in the table
        self.tableClicked( 2, 9 )
    except:
        pass
    
    splitter.widget( 0 ).resize( 10000, 10000 )
    splitter.widget( 1 ).resize( 10000, 10000 )
    splitter.setStretchFactor( 0, 1 )
    splitter.setStretchFactor( 1, 1 )
    
    # Create the "OK" and "Print" buttons
    hlay = QtGui.QHBoxLayout()
    mainVlay.addLayout( hlay )
    hlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    printBt = QtGui.QPushButton( "Print", self.awin )
    hlay.addWidget( printBt )
    okBt = QtGui.QPushButton( "OK", self.awin )
    hlay.addWidget( okBt )
    mainDialog.connect( printBt,
                        QtCore.SIGNAL( 'clicked()' ),
                        self.printClicked )
    mainDialog.connect( okBt,
                        QtCore.SIGNAL( 'clicked()' ),
                        mainDialog.accept )
    
    # Add a 3D cursor notifier
    self.a.onCursorNotifier.add( self.cursorMoveHandler )
    
    mainDialog.showMaximized()
    mainDialog.exec_()
    
    # Remove the 3D cursor notifier
    self.a.onCursorNotifier.remove( self.cursorMoveHandler )
    
    # Clean up
    del self.awin
    del self.aviews
    del self.asingleSubject
    if self.isGlassBrainAvailable():
        del self.aviewGlass

def createTop( self, context, splitter ):
    """
    Creates the top part of the result window. It contains the views and the information.
    
    :param splitter:
        The vertical splitter of the main dialog
    """
    frame = QtGui.QFrame( self.awin )
    splitter.insertWidget( 0, frame )
    vlay = QtGui.QVBoxLayout( frame )
    vlay.setMargin( 0 )    
    lay = QtGui.QGridLayout()
    lay.setHorizontalSpacing( 0 )
    lay.setVerticalSpacing( 0 )
    lay.setMargin( 0 )
    vlay.addLayout( lay )

    # Create the T-map/single subject views
    self.aviews = []
    orientation = [ 'Axial', 'Sagittal', 'Coronal' ]
    for i in range(3): 
        newWin = self.a.createWindow( orientation[i], no_decoration=True )
        lay.addWidget( newWin.getInternalRep(), 0, i)
        self.a.execute( 'WindowConfig', windows=[ newWin ],
                        light={ 'background' : [ 0., 0., 0., 1. ] } )
        self.aviews.append( newWin )
    self.a.linkWindows( self.aviews )
    
    if self.isGlassBrainAvailable():
        # Create the glass brain views
        self.aviewGlass = []
        orientation = [ 'Axial', 'Axial', 'Axial' ]
        for i in range(3): 
            newWin = self.a.createWindow( orientation[i], no_decoration=True )
            lay.addWidget( newWin.getInternalRep(), 0, i)
            self.a.execute( 'WindowConfig', windows=[ newWin ],
                            light={ 'background' : [ 0., 0., 0., 1. ] } )
            self.aviewGlass.append( newWin )
            self.a.linkWindows( newWin )

        for view in self.aviewGlass:
            view.hide()

    self.asingleSubject = self.a.loadObject( self.singleSubject )
    athreshImg = self.a.loadObject( self.resultMap )
    
    # Create T-map LUT
    customPalette = self.a.createPalette( "customPalette" )
    paletteColors = [ 255, 255, 255 ]
    for x in xrange( 255 ):
        paletteColors.extend( [ 255, x, 0 ] )
    customPalette.setColors( colors=paletteColors )
    athreshImg.setPalette( customPalette, minVal=0, maxVal=1 )
    
    self.fusion = self.a.fusionObjects( [ self.asingleSubject, athreshImg ], "Fusion2DMethod" )
    self.fusion.addInWindows( self.aviews )
    self.a.execute( "Fusion2DParams", object=self.fusion, mode="linear_on_defined", rate=0 )
    bbox = self.asingleSubject.boundingbox()
    position = ( bbox[1] - bbox[0] ) * 0.5
    t = self.a.getTransformation( self.asingleSubject.getReferential(),
                                  self.aviews[0].getReferential() )
    if t:
        position = t.transform( position )
    self.a.execute( 'LinkedCursor', window=self.aviews[0], position=position )
    
    if self.isGlassBrainAvailable():
        # Create glass brain with grid
        try:
            self.createGlassBrain( context )
        except:
            # Disable glass brain
            self.display_glass_brain = 'No'

    gridlay = QtGui.QGridLayout()
    vlay.addLayout( gridlay )

    # Add title
    gb = QtGui.QGroupBox( "", frame )
    gb.setStyleSheet( self.getGroupBoxStyle() )
    childhlay = QtGui.QHBoxLayout()
    gridlay.addLayout( childhlay, 0, 0 )
    childhlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    childhlay.addWidget( gb )
    childhlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    bgVlay = QtGui.QVBoxLayout( gb )
    lbl = QtGui.QLabel( self.title )
    font = lbl.font()
    font.setBold( True )
    font.setPointSize( 12 )
    lbl.setFont( font )
    bgVlay.addWidget( lbl )
    
    # Add tools for view editing
    toolVlay = QtGui.QVBoxLayout()
    gridlay.addLayout( toolVlay, 0, 1 )
    toolVlay.setSpacing( 0 )
    toolVlay.setMargin( 0 )
    # Add T-map LUT editor
    self.paletteEditor = PaletteEditor( image = athreshImg,
                                        parent = frame,
                                        palette_filter = [],
                                        real_max = self.tMax )
    toolVlay.addWidget( self.paletteEditor )
    bgHlay = QtGui.QHBoxLayout()
    toolVlay.addLayout( bgHlay )
    bgHlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    # Add T-map transparency editor
    bgHlay.addWidget( QtGui.QLabel( "T-map transparency", frame ) )
    self.sliderMixingRate = QtGui.QSlider( QtCore.Qt.Horizontal, frame )
    self.sliderMixingRate.setToolTip( "Change the T-map transparency" )
    bgHlay.addWidget( self.sliderMixingRate )
    self.labelMixingRate = QtGui.QLabel( "0", frame )
    bgHlay.addWidget( self.labelMixingRate )
    bgHlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    frame.connect( self.sliderMixingRate,
                   QtCore.SIGNAL( 'valueChanged( int )' ),
                   self.mixingRateValueChanged )
    # Add T-map/glass brain switcher
    bgHlay = QtGui.QHBoxLayout()
    toolVlay.addLayout( bgHlay )
    self.tmapRadioBt = QtGui.QRadioButton( "T-map" )
    self.tmapRadioBt.setChecked( True )
    bgHlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    bgHlay.addWidget( self.tmapRadioBt )
    self.glassBrainRadioBt = QtGui.QRadioButton( "Glass brain" )
    self.glassBrainRadioBt.setEnabled( self.isGlassBrainAvailable() )
    bgHlay.addWidget( self.glassBrainRadioBt )
    bgHlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    toolVlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, vPolicy = QtGui.QSizePolicy.Expanding ) )
    
    # Add comment if not empty
    if self.comment != "" and self.comment is not None:
        comment = QtGui.QLabel( self.comment, frame )
        comment.setFrameStyle( QtGui.QFrame.Panel )
        font = comment.font()
        font.setBold( True )
        comment.setFont( font )
        toolVlay.addWidget( comment, alignment = QtCore.Qt.AlignCenter )

    self.awin.connect( self.tmapRadioBt,
                       QtCore.SIGNAL( 'clicked()' ),
                       self.displayTypeChanged )
    self.awin.connect( self.glassBrainRadioBt,
                       QtCore.SIGNAL( 'clicked()' ),
                       self.displayTypeChanged )

    # Add SPM threshold parameter information
    gb = QtGui.QGroupBox( "Threshold parameters", frame )
    gb.setStyleSheet( self.getGroupBoxStyle() )
    childhlay = QtGui.QHBoxLayout()
    gridlay.addLayout( childhlay, 0, 2 )
    childhlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    childhlay.addWidget( gb )
    childhlay.addSpacerItem( QtGui.QSpacerItem( 20, 20, hPolicy = QtGui.QSizePolicy.Expanding ) )
    bgVlay = QtGui.QVBoxLayout( gb )
    bgVlay.addWidget( QtGui.QLabel( open( self.threshInfo, 'r').read() ) )
    gridlay.setColumnStretch( 0, 1 )
    gridlay.setColumnStretch( 1, 1 )
    gridlay.setColumnStretch( 2, 1 )
    vlay.setStretch( 0, 6 )
    vlay.setStretch( 1, 1 )

def createBottom( self, context, splitter ):
    """
    Creates the bottom part of the result window. It contains the SPM statistics.
    
    :param splitter:
        The vertical splitter of the main dialog
    """
    frame = QtGui.QFrame( self.awin )
    splitter.addWidget( frame )
    vlay = QtGui.QVBoxLayout( frame )
    vlay.setMargin( 0 )
    
    gb = QtGui.QGroupBox( "Statistics: p-values adjusted for search volume", self.awin )
    gb.setStyleSheet( self.getGroupBoxStyle() )
    vlay.addWidget( gb )
    gbVlay = QtGui.QVBoxLayout( gb )
    hlay = QtGui.QHBoxLayout()
    gbVlay.addLayout( hlay )
    self.table = QtGui.QTableWidget( 0, 17, gb )
    hlay.addWidget( self.table )
    
    # Fill the Qt table view according to the SPM CSV file
    fd = open( self.statsCsv, 'rb' )
    fdCsv = csv.reader( fd, delimiter=',' )
    
    textReplace = {
                   "peak" : "local maxima",
                   "z {mm}" : "z",
                   "equivk" : "size"
                   }
    
    font = gb.font()
    headerColor = [ 150, 150, 150 ]
    subheaderColor = [ 202, 202, 202 ]
    self.tMax = -10000
    tCol = -1
    row = 0
    for line in fdCsv:
        self.table.insertRow( row )
        col = 0
        gridCol = 0
        for el in line:
            try:
                el = textReplace[ el ]
            except:
                pass
            if col == 0 or col == 1:
                col += 1
                continue
            if col >= 11 and row == 0:
                el = "mm (MNI)"
            if row == 1 and el == "T":
                tCol = gridCol
            if gridCol == tCol and row > 1 and float(el) > self.tMax:
                self.tMax = float( el )
            item = QtGui.QTableWidgetItem( el )
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled )
            color = [ 255, 255, 255 ]
            if row == 0:
                color = headerColor
            elif row == 1:
                color = subheaderColor
            item.setBackgroundColor( QtGui.QColor( color[0], color[1], color[2] ) )
            if row > 1 and col == 2 and el != "":
                font.setBold( True )
            item.setFont( font )
            item.setTextAlignment( QtCore.Qt.AlignCenter )
            self.table.setItem( row, gridCol, item )
            col += 1
            gridCol += 1
        row += 1
        font.setBold( False )

    if self.tMax == -10000:
        self.tMax = 100

    # Add Talairach coordinates in Qt table view
    self.addTalairachCoords()
    
    # Add atlas coordinate mapping in Qt table view
    self.addAtlases()

    # Merge column groups
    self.table.setSpan( 0, 0, 1, 4 )
    self.table.setSpan( 0, 4, 1, 5 )
    self.table.setSpan( 0, 9, 1, 3 )
    
    # Set look options
    self.table.verticalHeader().setHidden( True )
    self.table.horizontalHeader().setHidden( True )
    self.table.setGridStyle( QtCore.Qt.NoPen )
    self.table.setSelectionMode( QtGui.QAbstractItemView.NoSelection )
    self.table.setFocusPolicy( QtCore.Qt.NoFocus )
    self.table.setFrameStyle( QtGui.QFrame.NoFrame )
    self.table.setSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding);
    self.table.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )    
    self.table.resizeRowsToContents()
    self.table.horizontalHeader().setResizeMode( QtGui.QHeaderView.Stretch )
    
    self.table.connect( self.table,
                        QtCore.SIGNAL( 'cellClicked( int, int)' ),
                        self.tableClicked )

def mixingRateValueChanged( self, value ):
    """
    Manages T-map transparency
    
    :param int value:
        The fusion transparency value
    """
    self.a.execute( "Fusion2DParams", object=self.fusion, mode="linear_on_defined", rate=float(value)/100. )
    self.labelMixingRate.setText( str( value ) )

def printClicked( self ):
    """
    Displays a dialog to print the main window
    """
    # Get the window capture in a QPixmap
    pix = QtGui.QPixmap.grabWindow( self.awin.winId() )
    
    # Set the printer options
    printer = QtGui.QPrinter()
    printer.setOrientation( QtGui.QPrinter.Landscape )
    printer.setPageMargins( 0., 0., 0., 0., QtGui.QPrinter.Millimeter )
    
    # Set the default PDF path
    pdfPath = os.path.join( os.getenv( "HOME" ), "Desktop" )
    pdfName = "spm_analysis_results"
    pdfName += ".pdf"
    printer.setOutputFileName( os.path.join( pdfPath, pdfName ) )
    
    # Create the print dialog
    printDialog = QtGui.QPrintDialog( printer )
    if printDialog.exec_() != QtGui.QDialog.Accepted:
        return
    
    # Scale the pixmap to a full size page
    pix = pix.scaled( printer.pageRect().size(),
                      aspectRatioMode=QtCore.Qt.KeepAspectRatio,
                      transformMode=QtCore.Qt.SmoothTransformation )

    painter = QtGui.QPainter( printer )
    painter.drawPixmap( QtGui.QPoint( 0, 0 ), pix )
    painter.end()

def getGroupBoxStyle( self ):
    """
    Sets a QGroupBox style
    """
    return """QGroupBox {
                          background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                            stop: 0 #FFFFFF, stop: 1 #FFFFFF);
                          border: 1px solid gray;
                          border-radius: 5px;
                          margin-top: 1.1ex;
                          font-weight: bold;
                         }
              QGroupBox::title {
                                 subcontrol-origin: margin;
                                 subcontrol-position: top center;
                                 padding: 0 0.1px;
                                }"""

def tableClicked( self, x, y ):
    """
    Updates the 3D cursors according to the coordinates of the clicked table line.
    
    :param int x:
        The clicked row number
    
    :param int y:
        The clicked column number
    """
    if x < 2:
        return
    
    try:
        coords = [ int( self.table.item( x, 9 ).text() ),
                   int( self.table.item( x, 10 ).text() ),
                   int( self.table.item( x, 11 ).text() ) ]
    except:
        return
    
    # Get the Anatomist coordinates according the MNI ones
    coords = self.getAnatomistCoordFromMNI( coords )

    position = aims.AimsVector_FLOAT_3( coords )
    t = self.a.getTransformation( self.asingleSubject.getReferential(),
                                  self.aviews[0].getReferential() )
    if t:
        position = t.transform( position )
    
    # Move the 3D cursor in single subject views
    self.a.execute( 'LinkedCursor', window=self.aviews[0], position=position )
    
    if self.isGlassBrainAvailable():
        try:
            # Move the 3D cursor in glass brain views
            img = aims.read( self.singleSubject )
            img.header()[ 'voxel_size' ]
            coords[0] = coords[0] / img.header()[ 'voxel_size' ][0]
            coords[1] = coords[1] / img.header()[ 'voxel_size' ][1]
            coords[2] = coords[2] / img.header()[ 'voxel_size' ][2]
            self.aviewGlass[ 0 ].moveLinkedCursor( [ coords[0], coords[1], 0 ] )
            self.aviewGlass[ 1 ].moveLinkedCursor( [ coords[1], coords[2], 0 ] )
            self.aviewGlass[ 2 ].moveLinkedCursor( [ coords[0], coords[2], 0 ] )
        except:
            pass

    # Color the table cells
    self.colorTableCells( row=x )

def getAnatomistCoordFromMNI( self, coords ):
    """
    Gets the Anatomist coordinates according to MNI ones
    
    :param coords:
        The MNI coordinates
    """
    anatCoords = [ self.mniBbox[ 1 ][ 0 ] - coords[ 0 ],
                   self.mniBbox[ 1 ][ 1 ] - coords[ 1 ],
                   self.mniBbox[ 1 ][ 2 ] - coords[ 2 ] ]
    
    return anatCoords
    
def addTalairachCoords( self ):
    """
    Adds Talairach coordinates to the Qt table view
    """
    font = self.table.font()

    item = QtGui.QTableWidgetItem( "mm (Talairach)" )
    item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled )
    item.setBackgroundColor( QtGui.QColor( 150, 150, 150 ) )
    item.setTextAlignment( QtCore.Qt.AlignCenter )
    font.setBold( True )
    item.setFont( font )
    self.table.setItem( 0, 12, item )
    self.table.setSpan( 0, 12, 1, 3 )
    
    font.setBold( False )
    labels = [ "x", "y", "z" ]
    for i in xrange( len( labels ) ):
        item = QtGui.QTableWidgetItem( labels[i] )
        item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled )
        item.setBackgroundColor( QtGui.QColor( 202, 202, 202 ) )
        item.setTextAlignment( QtCore.Qt.AlignCenter )
        self.table.setItem( 1, 12+i, item )
    
    for i in xrange( 2, self.table.rowCount() ):
        try:
            coords = [ int( self.table.item( i, 9 ).text() ),
                       int( self.table.item( i, 10 ).text() ),
                       int( self.table.item( i, 11 ).text() ) ]
        except:
            continue
        coords = self.getTalairachCoordsFromMNI( coords )
        
        if self.table.item( i, 2 ).text() == "":
            font.setBold( False )
        else:
            font.setBold( True )
        
        for j in xrange( 3 ):
            item = QtGui.QTableWidgetItem( str( round( float( coords[j] ), 1 ) ) )
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled )
            item.setBackgroundColor( QtGui.QColor( 255, 255, 255 ) )
            item.setTextAlignment( QtCore.Qt.AlignCenter )
            item.setFont( font )
            self.table.setItem( i, 12+j, item )

def cursorMoveHandler( self, eventName, params ):
    """
    Manages the 3D cursor updates
    """
    self.colorTableCells()
    
    if self.blockCursorUpdate or \
       not self.isGlassBrainAvailable():
        return
    
    try:
        clickedWin = None
        for i in self.aviewGlass:
            if params[ 'window' ] == i:
                clickedWin = i
                break
        if clickedWin is None:
            return
        
        self.blockCursorUpdate = True
        
        pos = params[ 'position' ]
        if clickedWin == self.aviewGlass[ 0 ]:
            # Axial
            currPos = None
            for k, v in self.aviewGlass[ 1 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 1 ].moveLinkedCursor( [ pos[1], currPos[1], currPos[2] ] )
            currPos = None
            for k, v in self.aviewGlass[ 2 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 2 ].moveLinkedCursor( [ pos[0], currPos[1], currPos[2] ] )
            
        elif clickedWin == self.aviewGlass[ 1 ]:
            # Sagittal
            currPos = None
            for k, v in self.aviewGlass[ 0 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 0 ].moveLinkedCursor( [ currPos[0], pos[0], currPos[2] ] )
            currPos = None
            for k, v in self.aviewGlass[ 2 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 2 ].moveLinkedCursor( [ currPos[0], pos[1], currPos[2] ] )
        elif clickedWin == self.aviewGlass[ 2 ]:
            # Coronal
            currPos = None
            for k, v in self.aviewGlass[ 1 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 1 ].moveLinkedCursor( [ currPos[0], pos[1], currPos[2] ] )
            currPos = None
            for k, v in self.aviewGlass[ 0 ].getInfos().iteritems():
                if k == 'position':
                    currPos = v
            self.aviewGlass[ 0 ].moveLinkedCursor( [ pos[0], currPos[1], currPos[2] ] )
        else:
            print "Error..."
            
    except:
        pass
    
    self.blockCursorUpdate = False

def colorTableCells( self, row=None ):
    """
    Manages the Qt table cell colors
    """
    for i in xrange( 2, self.table.rowCount() ):
        for j in xrange( self.table.columnCount() ):
            if row and i == row:
                try:
                    self.table.item( i, j ).setBackgroundColor( QtGui.QColor( 217, 255, 217 ) )
                except:
                    pass
            else:
                try:
                    self.table.item( i, j ).setBackgroundColor( QtGui.QColor( 255, 255, 255 ) )
                except:
                    pass

def getTalairachCoordsFromMNI( self, coords ):
    """
    Gets the Talairach coordinates according to MNI ones
    """
    def computeMatrix( P ):
        T = np.matrix( [ [ 1, 0, 0, P[0] ],
                         [ 0, 1, 0, P[1] ],
                         [ 0, 0, 1, P[2] ],
                         [ 0, 0, 0, 1    ] ] )
        R1 = np.matrix( [ [ 1, 0, 0, 0 ],
                          [ 0, np.cos( P[3] ), np.sin( P[3] ),  0 ],
                          [ 0, -np.sin( P[3] ), np.cos( P[3] ), 0 ],
                          [ 0, 0, 0, 1 ] ] )
        R2 = np.matrix( [ [ np.cos( P[4] ), 0, np.sin( P[4] ), 0 ],
                          [ 0, 1, 0, 0 ],
                          [ -np.sin( P[4] ), 0, np.cos( P[4] ), 0 ],
                          [ 0, 0, 0, 1 ] ] )
        R3 = np.matrix( [ [ np.cos( P[5] ), np.sin( P[5] ), 0, 0 ],
                          [ -np.sin( P[5] ), np.cos( P[5] ), 0, 0 ],
                          [ 0, 0, 1, 0 ],
                          [ 0, 0, 0, 1 ] ])
        R = R1*R2*R3
        Z = np.matrix( [ [ P[6], 0, 0, 0 ],
                         [ 0, P[7], 0, 0 ],
                         [ 0, 0, P[8], 0 ],
                         [ 0, 0, 0, 1 ] ] )

        return T*R*Z
    
    result = np.matrix( coords + [ 0 ] )
    result = result.T
    if result[2] < 0:
        downT = computeMatrix( [ 0, 0, 0, 0.05, 0, 0, 0.99, 0.97, 0.84 ] )
        result = downT * result
    else:
        upT = computeMatrix( [ 0, 0, 0, 0.05, 0, 0, 0.99, 0.97, 0.92 ] )
        result = upT * result

    return result

def addAtlases( self ):
    """
    Adds the atlas mapping
    """
    item = QtGui.QTableWidgetItem( "Region" )
    item.setBackgroundColor( QtGui.QColor( 202, 202, 202 ) )
    item.setTextAlignment( QtCore.Qt.AlignCenter )    
    self.table.setItem( 1, 15, item )
    cBox = QtGui.QComboBox( self.table )

    if self.isAtlasAvailable():
        for k in sorted( self.atlasFiles.keys() ):
            cBox.addItem( "Atlas: " + k )
    else:
        # Disable the combobox if there is no atlas available
        cBox.addItem( "Atlas: none" )
        cBox.setEnabled( False )
    
    self.awin.connect( cBox,
                       QtCore.SIGNAL( 'currentIndexChanged( const QString& )' ),
                       self.atlasChanged )
    
    self.atlasChanged( cBox.currentText() )
    self.table.setCellWidget( 0, 15, cBox )
    self.table.setSpan( 0, 15, 1, 2 )

def atlasChanged( self, atlasName ):
    """
    Manages the atlas user choice
    """
    atlasName = atlasName.replace( "Atlas: ", "" )
    
    try:
        atlasImg = self.atlasFiles[ atlasName ]
    except:
        for i in xrange( 2, self.table.rowCount() ):
            item = QtGui.QTableWidgetItem( "-" )
            item.setBackgroundColor( self.table.item( i, 14 ).backgroundColor() )
            item.setTextAlignment( QtCore.Qt.AlignCenter )
            self.table.setItem( i, 15, item )
        for i in xrange( 0, self.table.columnCount() ):
            self.table.setSpan( i, 15, 1, 2 )
        return
    
    atlasTxt = os.path.splitext( atlasImg )[ 0 ] + ".txt"

    aimsImg = aims.read( atlasImg )
    
    labelDic = {}
    labelFile = open( atlasTxt )
    for line in labelFile.readlines():
        fields = line.split()
        labelDic.update( { fields[0] : fields[1] } )
        
    for i in xrange( 2, self.table.rowCount() ):
        try:
            coords = [ int( self.table.item( i, 9 ).text() ),
                       int( self.table.item( i, 10 ).text() ),
                       int( self.table.item( i, 11 ).text() ) ]
        except:
            continue

        # Image already flipped R/L
        anatCoords = [ 90 + coords[ 0 ],
                       self.mniBbox[ 1 ][ 1 ] - coords[ 1 ],
                       self.mniBbox[ 1 ][ 2 ] - coords[ 2 ] ]
        anatIdx = [ int( v/2 ) for v in anatCoords ]

        value = aimsImg.value( anatIdx[0], anatIdx[1], anatIdx[2] )
        
        try:
            label = labelDic[ str( value ) ]
        except:
            label = "N/A"
        
        item = QtGui.QTableWidgetItem( label )
        item.setBackgroundColor( self.table.item( i, 14 ).backgroundColor() )
        item.setTextAlignment( QtCore.Qt.AlignCenter )
        
        self.table.setItem( i, 15, item )

    for i in xrange( 0, self.table.columnCount() ):
        self.table.setSpan( i, 15, 1, 2 )


def enablePaletteEditor( self, enable ):
    """
    Enables the LUT editor
    
    :param boolean enable:
        The enable state
    """
    self.paletteEditor.setEnabled( enable )
    self.sliderMixingRate.setEnabled( enable )
    
def displayTypeChanged( self ):
    """
    Changes the display type (T-map or glass brain)
    """
    if self.tmapRadioBt.isChecked():
        for i in self.aviews:
            i.show()
        for i in self.aviewGlass:
            i.hide()            
        self.enablePaletteEditor( True )
    elif self.glassBrainRadioBt.isChecked():
        for i in self.aviewGlass:
            i.show()            
        for i in self.aviews:
            i.hide()
        
        self.enablePaletteEditor( False )        
    else:
        print "Error..."

def createGlassBrain( self, context ):
    "Creates the glass brain images"
    self.createBrainMIPWithGrid( context )
    
    img = aims.read( self.resultMap )
    arr = np.array( img, copy=False )
    # Get shape
    sh = arr.shape
    # Glass brain axial
    imgAx = aims.Volume_FLOAT( 91, 109 )
    imgAx.fill( 0 )
    arrAx = np.array( imgAx, copy=False )
    for i in xrange( sh[0] ):
        for j in xrange( sh[1] ):
            arrAx[ i, j ] = np.nanmax( arr[ i, j, :, : ] )
    tmpAx = context.temporary( 'NIFTI-1 image' )
    aims.write( imgAx, tmpAx.fullPath() )
    # Glass brain sagittal
    imgSa = aims.Volume_FLOAT( 109, 91 )
    imgSa.fill( 0 )
    arrSa = np.array( imgSa, copy=False )
    for i in xrange( sh[1] ):
        for j in xrange( sh[0] ):
            arrSa[ i, j ] = np.nanmax( arr[ :, i, j, : ] )
    tmpSa = context.temporary( 'NIFTI-1 image' )
    aims.write( imgSa, tmpSa.fullPath() )
    # Glass brain frontal
    imgFr = aims.Volume_FLOAT( 91, 91 )
    imgFr.fill( 0 )
    arrFr = np.array( imgFr, copy=False )
    for i in xrange( sh[0] ):
        for j in xrange( sh[2] ):
            arrFr[ i, j ] = np.nanmax( arr[ i, :, j, : ] )
    tmpFr = context.temporary( 'NIFTI-1 image' )
    aims.write( imgFr, tmpFr.fullPath() )

    aglassAx = self.a.loadObject( tmpAx.fullPath() )
    aglassSa = self.a.loadObject( tmpSa.fullPath() )
    aglassFr = self.a.loadObject( tmpFr.fullPath() )
    amaskAx = self.a.loadObject( self.mipAndGrids[ 0 ].fullPath() )
    amaskSa = self.a.loadObject( self.mipAndGrids[ 1 ].fullPath() )
    amaskFr = self.a.loadObject( self.mipAndGrids[ 2 ].fullPath() )
    
    aglassAx.setPalette( "B-W LINEAR", minVal=1, maxVal=0 )
    amaskAx.setPalette( "B-W LINEAR", minVal=3, maxVal=0 )
    aglassSa.setPalette( "B-W LINEAR", minVal=1, maxVal=0 )
    amaskSa.setPalette( "B-W LINEAR", minVal=3, maxVal=0 )
    aglassFr.setPalette( "B-W LINEAR", minVal=1, maxVal=0 )
    amaskFr.setPalette( "B-W LINEAR", minVal=3, maxVal=0 )
    
    self.glassFusionAx = self.a.fusionObjects( [ amaskAx, aglassAx ], "Fusion2DMethod" )
    self.a.execute( "Fusion2DParams", object=self.glassFusionAx, mode="linear_on_defined", rate=0. )
    self.glassFusionSa = self.a.fusionObjects( [ amaskSa, aglassSa ], "Fusion2DMethod" )
    self.a.execute( "Fusion2DParams", object=self.glassFusionSa, mode="linear_on_defined", rate=0. )
    self.glassFusionFr = self.a.fusionObjects( [ amaskFr, aglassFr ], "Fusion2DMethod" )
    self.a.execute( "Fusion2DParams", object=self.glassFusionFr, mode="linear_on_defined", rate=0. )

    self.glassFusionAx.addInWindows( [ self.aviewGlass[0] ] )
    self.glassFusionSa.addInWindows( [ self.aviewGlass[1] ] )
    self.glassFusionFr.addInWindows( [ self.aviewGlass[2] ] )

def createBrainMIPWithGrid( self, context ):
    """
    Creates the brain MIP and the ACPC grid
    """
    mipMat = locateFile( "MIP.mat", self.configuration.SPM.spm8_path )
    if not mipMat:
        return
    
    gridFileFi, gridFile = mkstemp( suffix = ".txt" )
    maskFileFi, maskFile = mkstemp( suffix = ".txt" )
    matFileFi, matFile = mkstemp( suffix = ".m" )
    matFileFd = os.fdopen( matFileFi, "w" )
    matFileFd.write( \
"""
spm_get_defaults('cmdline', true);
spm_jobman('initcfg');
load('/home_local/jmartini/tools/spm8_x64/MIP.mat');

[r,c,v] = find( grid_all > 0 );
fid = fopen( '%s', 'wt' );
for i=1:length( r )
  fprintf( fid, '(%%d,%%d)\\n', r(i), c(i) );
end
fclose(fid);
[r,c,v] = find( mask_all > 0 )
fid = fopen( '%s', 'wt' );
for i=1:length( r )
  fprintf( fid, '(%%d,%%d)\\n', r(i), c(i) );
end
fclose(fid);
""" \
    % ( gridFile,
        maskFile ) )
    matFileFd.close()
    mexe = self.configuration.SPM.spm8_standalone_command
    cmd = [ mexe,
            self.configuration.SPM.spm8_standalone_mcr_path,
            'script',
            matFile ]
    context.system( *cmd )

    coordGrid = []
    f = open( gridFile, 'r' )
    for l in f.readlines():
        try:
            coordGrid.append( eval( l ) )
        except:
            pass

    coordMask = []
    f = open( maskFile, 'r' )
    for l in f.readlines():
        try:
            coordMask.append( eval( l ) )
        except:
            pass

    imgAx = aims.Volume_FLOAT( 91, 109 )
    imgSa = aims.Volume_FLOAT( 109, 91 )
    imgFr = aims.Volume_FLOAT( 91, 91 )
    arrAx = np.array( imgAx, copy=False )
    arrSa = np.array( imgSa, copy=False )
    arrFr = np.array( imgFr, copy=False )

    gridValue = 2
    for i in coordGrid:
        if i[0] <= 198:
            if i[1] <= 157:
                curr_x = math.floor( i[1] * 0.5 )
                curr_y = math.floor( i[0] * 0.5 )
                arrAx[ curr_x, curr_y ] = gridValue
            else:
                curr_x = math.floor( i[0] * 0.5 )
                curr_y = math.floor( ( i[1] - 182 ) * 0.5 )
                arrSa[ curr_x, curr_y ] = gridValue
        else:
            curr_x = math.floor( ( i[0] - 217 ) * 0.5 )
            curr_y = math.floor( ( i[1] - 182 ) * 0.5 )
            arrFr[ curr_x, curr_y ] = gridValue

    orientations = [ "axial", "coronal", "sagittal" ]
    arrays = {
              "axial" : arrAx,
              "coronal" : arrFr,
              "sagittal" : arrSa
              }
    acpc = {
            "axial" : ( 45, 63 ),
            "coronal" : ( 45, 36 ),
            "sagittal" : ( 63, 36 )
            }
    for k in orientations:
        for i in xrange( arrays[ k ].shape[0] ):
            for j in xrange( arrays[ k ].shape[1] ):
                if i == acpc[ k ][ 0 ]:
                    continue
                if j == acpc[ k ][ 1 ]:
                    continue
                if i < arrays[ k ].shape[0] and i > 0 and \
                   arrays[ k ][i][j] == gridValue and arrays[ k ][i-1][j] == gridValue and arrays[ k ][i+1][j] == gridValue:
                    arrays[ k ][i][j] = 0
                if j < arrays[ k ].shape[1] and j > 0 and \
                   arrays[ k ][i][j] == gridValue and arrays[ k ][i][j-1] == gridValue and arrays[ k ][i][j+1] == gridValue:
                    arrays[ k ][i][j] = 0
    for i in coordMask:
        if i[0] <= 198:
            if i[1] <= 157:
                curr_x = math.floor( i[1] * 0.5 )
                curr_y = math.floor( i[0] * 0.5 )
                if arrAx[ curr_x, curr_y ] != gridValue:
                    arrAx[ curr_x, curr_y ] = 1
            else:
                curr_x = math.floor( i[0] * 0.5 )
                curr_y = math.floor( ( i[1] - 182 ) * 0.5 )
                if arrSa[ curr_x, curr_y ] != gridValue:
                    arrSa[ curr_x, curr_y ] = 1
        else:
            curr_x = math.floor( ( i[0] - 217 ) * 0.5 )
            curr_y = math.floor( ( i[1] - 182 ) * 0.5 )
            if arrFr[ curr_x, curr_y ] != gridValue:
                arrFr[ curr_x, curr_y ] = 1

    self.mipAndGrids = [ context.temporary( 'NIFTI-1 image' ),
                         context.temporary( 'NIFTI-1 image' ),
                         context.temporary( 'NIFTI-1 image' ) ]
    aims.write( imgAx, self.mipAndGrids[0].fullPath() )
    aims.write( imgSa, self.mipAndGrids[1].fullPath() )
    aims.write( imgFr, self.mipAndGrids[2].fullPath() )
    for i in self.mipAndGrids:
        context.system( 'AimsFlip',
                        '-i', i.fullPath(),
                        '-o', i.fullPath(),
                        '-m', 'XXYY' )
