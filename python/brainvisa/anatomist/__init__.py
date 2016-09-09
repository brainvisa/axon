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
from __future__ import print_function
import sys, os
from brainvisa import registration
from brainvisa.configuration import neuroConfig
from brainvisa.processing import neuroLog
from brainvisa.processing import neuroException
from brainvisa.data import neuroData
from brainvisa.validation import ValidationError
from soma.qtgui.api import QtThreadCall
import distutils.spawn
import weakref, types, threading
import atexit
import copy
from brainvisa.processing.qtgui import backwardCompatibleQt as qt
from brainvisa.processing.qtgui import neuroProcessesGUI
try:
  import anatomist
  anatomist.setDefaultImplementation( neuroConfig.anatomistImplementation )
  exec("import "+anatomist.getDefaultImplementationModuleName()+" as anatomistModule")
  anatomistImport=True
  if neuroConfig.anatomistImplementation != 'socket':
    from . import reusablewinhook
except Exception as e:
  print(e)
  anatomistImport=False

if sys.version_info[0] >= 3:
    def next(iterator):
        return iterator.__next__()
else:
    def next(iterator):
        return iterator.next()

"""
This module enables to generate an implementation of anatomist api specialized for brainvisa.
It can use either socket or direct(sip bindings) implementation.

To use this implementation, load the module using :

anatomistModule = anatomistapi.bvimpl.loadAnatomistModule(anatomistapi.api.SOCKET) # or DIRECT)
a=anatomistModule.Anatomist()
...
It can be used only in brainvisa application because it uses modules that are loaded in brainvisa.

Returned module contains an Anatomist class which inherits from choosen Anatomist class implementation, and is a thread safe singleton.
Specificities added for brainvisa are :
  - loading referentials and transformation on loading an object using brainvisa database informations.
  - writing messages in brainvisa log file.
"""

def validation():
  if not anatomistImport:
    raise ValidationError('Cannot find anatomist module')
  elif distutils.spawn.find_executable('anatomist') is None:
    raise ValidationError( 'Cannot find Anatomist executable' )

if anatomistImport:
  # dynamic class Anatomist inherits from one implementation of anatomist api
  class Anatomist(anatomistModule.Anatomist):
    # We shouldn't change the defaultRefType in fact. 
    # Indeed, if Anatomist from brainvisa takes only weak shared references on objects and windows,
    # the user can close a window that is still used by python and it can creates pbs 
    # Fo example, an id that is free for Anatomist C++ is reused for a new object in Anatomist python but python still have references 
    # on this id for another object, so when this other object is released in python layer, it can lead to the destruction of the new object.
    # But with this change, the user won't be able to really close windows or delete objects in Anatomist of Brainvisa manually.
    #defaultRefType="WeakShared"

    def __new__(cls, *args, **kwargs ):
      instance=super(Anatomist, cls).__new__(cls, *args, **kwargs)
      if instance and '-b' not in args \
        and neuroConfig.anatomistImplementation != 'socket':
        if not instance.getControlWindow():
          mainThread=QtThreadCall()
          instance.createControlWindow()
          win=instance.getControlWindow()
          if win:
            win.enableClose( False )
            mainThread.push( qt.QObject.connect, win, qt.SIGNAL("destroyed(QObject *)"), instance.anatomist_closed )
      return instance
      
    def __singleton_init__(self, *args, **kwargs):
      communicationLog = neuroConfig.mainLog.subTextLog()
      self.communicationLogFile = open( communicationLog.fileName,'w' )
      super(Anatomist, self).__singleton_init__(*args, **kwargs)
      anatomistParameters=[]
      for a in args:
        anatomistParameters.append(a)
      try:
        if neuroConfig.anatomistImplementation == 'socket':
          anatomistModule.Anatomist.anatomistExecutable = \
            eval("neuroConfig.anatomistExecutable")
        # log file for writing traces from this class
        # log for writing traces from anatomist process
        self.outputLog=neuroConfig.mainLog.subTextLog()
        # add a trace in brainvisa main log
        neuroConfig.mainLog.append( 'Anatomist ', html=self.outputLog,
                children = [ neuroLog.LogFile.Item('Communications', html = communicationLog ) ],
                icon='anaIcon_small.png' )
        if neuroConfig.anatomistImplementation == 'socket':
          anatomistParameters+=[ '--cout', self.outputLog.fileName, '--cerr', self.outputLog.fileName ]
      except:
        neuroException.showException()
        self.communicationLogFile=None
        self.outputLog=None
      if neuroConfig.userProfile is not None:
        anatomistParameters += [ '-u', neuroConfig.userProfile ]
      mainThread=QtThreadCall()
      args = anatomistParameters
      super( Anatomist, self ).__singleton_init__( *args, **kwargs )
      self._reusableWindows = set()
      self._reusableWindowBlocks = set()

      if neuroConfig.anatomistImplementation != 'socket':
        a = anatomistModule.Anatomist( *args, **kwargs )
        if a.getControlWindow() is not None:
          a.getControlWindow().enableClose( False )
          mainThread.push( qt.QObject.connect, a.getControlWindow(), qt.SIGNAL("destroyed(QObject *)"), self.anatomist_closed )
        mainThread.push( reusablewinhook.installWindowHandler )

    def anatomist_closed(self):
      self._reusableWindows = set()
      self._reusableWindowBlocks = set()
      if neuroProcessesGUI:
        neuroProcessesGUI.close_viewers()

    ###############################################################################
    # Methods redefined to use Brainvisa log system.
    def log(self, message ):
      """
      This method is redefined to print logs in brainvisa log system.
      """
      self.lock.acquire()
      if self.communicationLogFile is None:
          return
      self.communicationLogFile.write( message+"<BR>" )
      self.communicationLogFile.flush()
      self.lock.release()

    def logCommand(self, command, **kwargs):
      if self.communicationLogFile is not None:
        if isinstance(command, str):
          logcmd = "<B>-->" + command + "</B><UL>"
          for ( name, value ) in kwargs.items():
              if value is not None:
                  logcmd += "<LI>" + name + " = " + str( value )
          logcmd += "</UL>"
          self.log( logcmd )
        else: # if the command is not a string it should an object Command from anatomist bindings
          cmdDesc=command.write()
          logcmd = "<B>-->" + command.name() + "</B><UL>"
          for ( name, value ) in cmdDesc.items():
            if value is not None:
              logcmd += "<LI>" + name + " = " + str( value )
          logcmd += "</UL>"
          self.log( logcmd )

    def logEvent(self, event, params):
      """
      Log an event received from anatomist application.

      @type event: string
      @param event: event's name
      @type params: string
      @param params: event's parameters
      """
      self.log("<B> &lt;-- " + event + "</B> : " + params)

    ###############################################################################
    # Methods redefined to use Brainvisa transformation manager (with database informations)
    # When a database object is loaded, associated referential and transformations are loaded

    def loadObject(self, fileref, objectName=None, restrict_object_types=None,
                   forceReload=False, loadReferential=True, duplicate=False,
                   hidden=False, loadTransformations=True):
      """
      Loads an object from a file (volume, mesh, graph, texture...)

      @type fileref: string or Diskitem
      @param fileref: name of the file that contains the object to load or a Diskitem representing this file.
      @type objectName: string
      @param objectName: object's name
      @type restrict_object_types: dictionary
      @param restrict_object_types: object -> accpepted types list. Ex: {'Volume' : ['S16', 'FLOAT']}
      @type forceReload: boolean
      @param forceReload: if True the object will be loaded even if it is already loaded in Anatomist. Otherwise, the already loaded one is returned.
      @type loadReferential: boolean
      @param loadReferential: if True, use brainvisa database informations to search referential and transformations associated to this object and load them.

      @rtype: AObject
      @return: the loaded object
      """
      if hasattr( fileref, "fullPath" ): # is it a diskitem ?
        file = fileref.fullPath()
        #if not forceReload:
          #object=self.getObject(file)
          #if object is not None: # object is already loaded
            #files = fileref.fullPaths()
            #for x in files:
              #if os.path.exists( x ):
                #if os.stat(x).st_mtime >= object.loadDate: # reload it if the file has been modified since last load
                  #self.reloadObjects([object])
                  #break
            #return object
        newObject=anatomistModule.Anatomist.loadObject(self, file, objectName, restrict_object_types, forceReload, duplicate, hidden)
        # search referential for this object
        if loadReferential:
          try:
            tm = registration.getTransformationManager()
            ref = tm.referential(fileref)
            if ref is not None :
              # the referential is loaded only if necessary : if the object has not the right referential assigned
              ruuid=str(ref.uuid())
              oruuid=newObject.referential.refUuid
              if (ruuid != oruuid):
                # create referential
                aref=self.createReferential(ref)

                ## search transformations for this referential
                #self.loadTransformations(aref)

                # assign referential to object
                newObject.assignReferential(aref)

              # search transformations for this referential
              if loadTransformations:
                self.loadTransformations(newObject.referential)

          except:
            neuroException.showException( afterError= \
              'Cannot load referential and transformations information with ' \
              'object "' + file + '"' )
      else:
        newObject=anatomistModule.Anatomist.loadObject(self,fileref, objectName, restrict_object_types, forceReload, duplicate, hidden)
      return newObject

    def createWindow(self, wintype, geometry=None, block=None,
      no_decoration=None, options=None, allowreuse=True):
      self.findReusableWindowBlock( block )
      if allowreuse:
        win = self.findReusableWindow( wintype, block=block )
        if win and geometry is not None:
          a.execute( 'WindowConfig', window=win, geometry=geometry )
      else:
        win = None
      if win is None:
        win = anatomistModule.Anatomist.createWindow( self, wintype,
          geometry=geometry, block=block, no_decoration=no_decoration,
          options=options )
      return win

    def createWindowsBlock(self, nbCols=2, nbRows=0, allowreuse=True):
      if nbRows:
        nbCols = 0
      if allowreuse:
        bw = self.findReusableWindowBlock()
        return self.AWindowsBlock( self, nbCols=nbCols, nbRows=nbRows,
          widgetproxy=bw )
      return anatomistModule.Anatomist.createWindowsBlock( self,
          nbCols=nbCols, nbRows=nbRows )

    def createReferential(self, fileref=None):
      """
      Creates a new referential using the informations in the file.

      @type fileref: string or Diskitem
      @param filename: name or diskitem of a file (minf file, extension .referential) containing  informations about the referential : its name and uuid

      @rtype: Referential
      @return: the newly created referential
      """
      if hasattr( fileref, "fullPath" ): # is it a diskitem ?
        ruuid=fileref.uuid()
        # if it is a known referential, nothing to load
        if ruuid == registration.talairachACPCReferentialId :
          newRef=self.centralRef
          #print("getCentralReferential", newRef)
        elif ruuid == registration.talairachMNIReferentialId:
          newRef=self.mniTemplateRef
          #print("getMniRef", newRef)
        # unknown referential
        else:
          #print("create referential", fileref.fullPath())
          newRef=anatomistModule.Anatomist.createReferential(self, fileref.fullPath())
          #print("created referential", newRef)
          newRef.diskitem=fileref
      else:
        newRef=anatomistModule.Anatomist.createReferential(self, fileref)
      return newRef

    def loadTransformations(self, referential):
      """
      Search and load transformations between this referential and spm referential.

      @type referential: Referential
      @param referential: the referential for which searching transformations
      """
      def _transformWith( self, ref1, ref2, forceLoadTransformation = True):
        tm = registration.getTransformationManager()
        if isinstance( ref1, self.Referential ):
          id1=None
          if (getattr(ref1, "diskitem", None)==None):
            id1=ref1.refUuid
          else:
            id1 = ref1.diskitem.uuid()
          srcr = ref1
        else:
          id1 = ref1

        if isinstance( ref2, self.Referential ):
          id2 = None
          if (getattr(ref2, "diskitem", None)==None):
            id2 = ref2.refUuid
          else:
            id2 = ref2.diskitem.uuid()
        else:
          id2 = ref2

        pth = tm.findPaths( id1, id2, extensive=False, maxLength=4 )

        try:
          p = next(pth)

          loadTrAndCreateRef = forceLoadTransformation
          try:
              p = next(pth)
              self.log(string.join('processTransformations warning: multiple transformations from', ref1, 'to', ref2))
              loadTrAndCreateRef = forceLoadTransformation
          except:
              loadTrAndCreateRef = True

          if loadTrAndCreateRef:
            if not isinstance( ref1, self.Referential ):
              srcrDiskItem = tm.referential(id1)
              srcr = self.createReferential(srcrDiskItem)
              ref1 = srcr
            lastref = id1
            for t in p:
                dstrid = t[ 'destination_referential' ]
                srcrid = t[ 'source_referential' ]

                if lastref == dstrid: # The transformation should be applied in reverse
                  wantedref = srcrid
                else:
                  wantedref = dstrid

                if wantedref != id2 \
                    or not isinstance( ref2, self.Referential ):
                  dstrDiskItem = tm.referential(wantedref)
                  dstr = self.createReferential(dstrDiskItem)
                  #print('new dst ref:', dstr.uuid())
                else:
                  dstr = ref2

                #print("load transformation", t, ":", srcr.uuid(), "->", dstr.uuid())
                if wantedref == dstrid:
                  self.loadTransformation( t.fullPath(), srcr, dstr )
                else:
                  self.loadTransformation( t.fullPath(), dstr, srcr )
                srcr = dstr
                lastref = wantedref

          return loadTrAndCreateRef# 0 -> no UNIQUE path, transformations not loaded

        except StopIteration:
          return 0 # no path

      #end _transformWith------------------------------------------------

      # try to find transformation between this referential and spm referential
      triedrefs = [self.mniTemplateRef, self.centralRef,
                   registration.globallyRegistredSPAMReferentialId]

      for r in triedrefs:
        x = _transformWith( self, referential, r )
        if x==1:
          return x

      #print("no path from/to [mni, central or spam], search for others (if no ambiguity : unique path only).")
      # try to find transformation between this referential and others
      allRefs=self.getReferentials()

      triedUuid=[]
      for tr in triedrefs:
        if isinstance( tr, self.Referential ):
          triedUuid.append(tr.refUuid)
        else:
          triedUuid.append(tr)

      toremove = []
      for r in allRefs:
        if(r.refUuid in triedUuid):
          toremove.append(r)

      for r in toremove :
        allRefs.remove(r)

      if referential in allRefs :
        allRefs.remove(referential)

      otherRefs = allRefs

      result = 0
      for r in otherRefs:
        x = _transformWith( self, referential, r, False)
        if x == 1: # seulement si il n y a pas ambiguite
          result = 1

      return result

    def __getattr__(self, name):
      """
      Called when trying to access to name attribute, which is not defined.
      Used to give a value to centralRef attribute first time it is accessed.
      """
      if name == "centralRef":
        tm = registration.getTransformationManager()
        cr = tm.referential( registration.talairachACPCReferentialId )
        anatomistModule.Anatomist.__getattr__(self, name)
        self.lock.acquire()
        self.centralRef.diskitem=cr
        self.lock.release()
        #print("central ref loaded", self.centralRef, self.centralRef.diskitem)
        return self.centralRef
      elif name == "mniTemplateRef":
        tm = registration.getTransformationManager()
        mnir = tm.referential( registration.talairachMNIReferentialId )
        anatomistModule.Anatomist.__getattr__(self, name)
        self.lock.acquire()
        self.mniTemplateRef.diskitem=mnir
        self.lock.release()
        #print("mni ref loaded", self.mniTemplateRef, self.mniTemplateRef.diskitem)
        return self.mniTemplateRef
      else:
        anatomistModule.Anatomist.__getattr__(self, name)

    def findReusableWindow( self, wintype = '3D', block=None ):
      self._reusableWindows = set( [ w for w in self._reusableWindows \
        if w ] )
      todel = set()
      try:
        for w in self._reusableWindows:
          try:
            if w.windowType == wintype and len( w.objects ) == 0 and \
              (block is None or ( w.block is not None \
                and w.block.internalWidget == block.internalWidget ) ):
              return w
          except: # window probably closed in the meantime
            todel.add( w )
      finally:
        if len( todel ) != 0:
          self._reusableWindows = set( [ w for w in self._reusableWindows \
            if w not in todel ] )
      return None

    def findReusableWindowBlock( self, block=None ):
      if neuroConfig.anatomistImplementation == 'socket':
        return None
      if block is not None and hasattr( block, 'internalWidget' ) \
        and block.internalWidget:
        return block.internalWidget
      self._reusableWindowBlocks = set( [ w for w in \
        self._reusableWindowBlocks if w ] )
      todel = set()
      try:
        for w in self._reusableWindowBlocks:
          if block is None:
            return w
          us = anatomistModule.cpp.CommandContext.defaultContext().unserial
          bid = us.id( w.widget )
          if bid >= 0:
            block.internalRep = bid
          else:
            if block.internalRep < 0:
              bid = us.makeID( w.widget )
              block.internalRep = bid
              us.registerPointer( w.widget, bid )
          block.setWidget( w.widget )
          return block.internalWidget
      finally:
        if len( todel ) != 0:
          self._reusableWindowBlocks = set( [ w for w in \
            self._reusableWindowBlocks if w not in todel ] )
      return None

    def setReusableWindow( self, win, state=True ):
      self._reusableWindows = set( [ w for w in self._reusableWindows \
        if w ] )
      if type( win ) not in ( types.ListType, types.TupleType ):
        win = [ win ]
      if state:
        for w in win:
          self._reusableWindows.add( w.getRef( 'WeakShared' ) )
      else:
        s = set( [ w.getInternalRep() for w in win ] )
        s2 = set()
        for w in self._reusableWindows:
          if w.getInternalRep() in s:
            s2.add( w )
        for w in s2:
          self._reusableWindows.remove( w )
      if neuroConfig.anatomistImplementation != 'socket':
        mainThread=QtThreadCall()
        for w in win:
          ac = w.findChild( reusablewinhook.ReusableWindowAction )
          if ac and ac.isChecked() != state:
            mainThread.push( ac.setChecked, state )

    def setReusableWindowBlock( self, win, state=True ):
      #self._reusableWindowBlocks = set( [ w for w in \
        #self._reusableWindowBlocks if w ] )
      if type( win ) not in ( types.ListType, types.TupleType ):
        win = [ win ]
      win2 = []
      for w in win:
        if isinstance( w, self.AWindowsBlock ):
          w = w.internalWidget
        win2.append( w )
      win = win2
      del win2
      if win is None:
        return
      from PyQt4 import QtCore
      if state:
        for w in win:
          wp = self.AWindowsBlock.findBlock( w )
          if wp is None:
            wp = self.AWindowsBlock( self )
            wp.setWidget( w )
            wp = wp.widgetProxy()
          self._reusableWindowBlocks.add( wp )
          wp.widget.destroyed.connect( self.removeReusableWindowBlock )
      else:
        s2 = set()
        for w in self._reusableWindowBlocks:
          for ws in win:
            if w == ws:
              s2.add( w )
        for w in s2:
          wp = self.AWindowsBlock.findBlock( w )
          if wp is not None:
            self._reusableWindowBlocks.remove( wp )
            wp.widget.destroyed.disconnect( self.removeReusableWindowBlock )
      mainThread=QtThreadCall()
      for w in win:
        ac = w.findChild( reusablewinhook.ReusableWindowBlockAction )
        if ac and ac.isChecked() != state:
          mainThread.push( ac.setChecked, state )

    def removeReusableWindowBlock( self, win ):
      self.setReusableWindowBlock( win, False )

    # util methods for brainvisa processes
    def viewObject(self, fileRef, wintype = "Axial", palette = None ): # AnatomistImageView
      """
      Loads the image in anatomist, opens it in a new window and assigns the image's referential to the window.

      @type fileRef: string or DiskItem
      @param fileRef: filename of the image to load.
      @type

      @rtype: dictionary
      @return: {"object" : the loaded object, "window" : the new window, "file" : the readed file}
      """
      if palette is not None:
        # if the palette has to be changed, load object with duplicate option : returned object will be a copy of original object, which palette will not be modified
        object = self.loadObject( fileRef, duplicate=True )
        object.setPalette(palette)
      else:
        object = self.loadObject( fileRef)
      window = self.createWindow( wintype )
      window.assignReferential(object.referential)
      window.addObjects( [object] )
      return {"object" : object, "window" : window, "file" : fileRef}

    def viewMesh(self, fileRef):
      """
      Loads a mesh and opens it in a 3D window. The window is assigned the object's referential.
      """
      return self.viewObject(fileRef, "3D")

    def viewBias(self, fileRef, forceReload=False, wintype="Coronal",
                 hanfile=None, parent=None):
      """
      Loads an image, opens it in a new window in the object's referential. A
      palette is assigned to the object (Rainbow2) in order to see the bias.

      Parameters
      ----------
      fileRef: string or ReadDiskItem
          file name for the bias corrected image
      forceReload: boolean
          if True, the image is reloaded if already in memory.
      wintype: string
          "Axial", "Coronal", "Sagittal", "3D" (or other)
      hanfile: string or ReadDiskItem
          optional file name for histogram analysis file. If present it will be
          used to set palette bounds.
      parent: QWidget or anatomist block
          parent widget or block
      """
      object = self.loadObject( fileRef, duplicate=True )
      object.setPalette( self.getPalette("Rainbow2") )
      if isinstance(parent, self.AWindowsBlock):
        window = self.createWindow(wintype, block=parent)
      else:
        window = self.createWindow(wintype)
      if isinstance(parent, qt.QWidget):
        mainThread = QtThreadCall()
        mainThread.push(window.getInternalRep().reparent, parent)
      window.assignReferential( object.referential)

      if hanfile is not None and (hasattr(hanfile, 'fullPath')
                                  or  os.path.exists(hanfile)):

        def load_histo_analysis(hanfile):
          '''parse histo analysis file (.han) to extract gray and white
          mean/std.
          Returns a tuple in the following shape:
          ( ( gray_mean, gray_stdev ), ( white_mean, white_stdev ) )
          '''
          import re
          r = re.compile('^.*mean:\s*(-?[0-9]+(\.[0-9]*)?)\s*sigma:\s'
                        '(-?[0-9]+(\.[0-9]*)?)\s*$')
          gmean, gsigma, wmean, wsigma = None, None, None, None
          for l in open(hanfile).xreadlines():
              l = l.strip()
              if l.startswith('gray:'):
                  m = r.match(l)
                  if m:
                      gmean = float(m.group(1))
                      gsigma = float(m.group(3))
              elif l.startswith('white:'):
                  m = r.match(l)
                  if m:
                      wmean = float(m.group(1))
                      wsigma = float(m.group(3))
          return [gmean, gsigma], [wmean, wsigma]

        if hasattr(hanfile, 'fullPath'):
          hanfile = hanfile.fullPath()
        try:
          grey, white = load_histo_analysis(hanfile)
          object.setPalette(minVal=max(grey[0] - grey[1] * 8, 0),
                            maxVal=white[0] + white[1] * 3,
                            absoluteMode=True)
        except:
          print('Warning: histogram could not be read:', hanfile)

      window.addObjects( [object] )
      return {"object" : object, "window" : window, "file" : fileRef}

    def viewMaskOnMRI(self, mriFile, maskFile, palette, mode, rate, wintype = "Axial" ):
      """
      Fusions an irm image with a mask. A palette is associated to the mask to highlight it in the fusion.
      Fusion method is Fusion2DMethod. Resulting image is opened in a new window.

      @type mriFile: Diskitem or string
      @param mriFile: file containing the mri image
      @type maskFile: Diskitem or string
      @param maskFile: file containing the mask to apply
      @type palette: APalette
      @param palette: palette to use for the mask
      @type mode: string
      @param mode: mix color mode (geometric, linear, replace, decal, blend, add or combine)
      @type rate: float
      @param rate: mix rate in linear mode
      @type wintype: string
      @param wintype: type of window to open
      """
      mri = self.loadObject( mriFile )
      duplicate=False
      if palette is not None:
        duplicate=True
      mask = self.loadObject( maskFile, duplicate=True)#forceReload=1 )
      mask.setPalette( palette )
      fusion = self.fusionObjects( [mri, mask], method='Fusion2DMethod' )
      fmode = mode
      if mode not in ( 'linear', 'geometric', 'linear_on_defined' ):
        self.execute( 'TexturingParams', objects=[fusion], mode=mode,
          texture_index=1, rate=rate )
        fmode = None
      self.execute("Fusion2DParams", object=fusion, mode=fmode, rate = rate,
                          reorder_objects = [ mri, mask ] )
      window = self.createWindow( wintype )
      window.assignReferential( mri.referential )
      window.addObjects( [fusion] )

      return {'mri' : mri, 'mask' : mask, 'fusion' : fusion, 'window' : window, 'mriFile' : mriFile, 'maskFile' : maskFile}

    def viewActivationsOnMRI( self, mriFile, fmriFile, transformation = None, both = 0,
              palette = None, mode = "geometric",
              invertTransformation = 0,
              block = None, wintype = "Axial" ):
      if palette is None:
        palette = self.getPalette("actif_ret")
      mri = self.loadObject( mriFile )
      fmri = self.loadObject( fmriFile, duplicate=True )
      fmri.setPalette( palette, maxVal = 1, minVal = 0 )

      window = self.createWindow( wintype, block=block )
      refMRI = self.createReferential()
      self.assignReferential(refMRI, [mri, window] )

      if both:
          window2 = self.createWindow( wintype )
          refFMRI = self.createReferential()
          self.assignReferential( refFMRI, [fmri, window2] )
          window2.addObjects( [fmri] )
      else:
          refFMRI = self.createReferential()
          fmri.assignReferential(refFMRI)
      if invertTransformation:
          ref1, ref2 = refMRI, refFMRI
      else:
          ref1, ref2 = refFMRI, refMRI
      if transformation is not None:
        if type( transformation ) in ( types.ListType, types.TupleType ):
          transformation = self.createTransformation( transformation, ref1, ref2 )
        else:
          transformation = self.loadTransformation(transformation.fullPath(), ref1, ref2)
      fusion = self.fusionObjects( [mri, fmri], method = 'Fusion2DMethod' )
      self.execute("Fusion2DParams", object=fusion, mode = mode, rate = 0.5,
                            reorder_objects = [ mri, fmri ] )
      window.addObjects( [fusion] )

      # Keep a reference on objects  In case of temporary file, it must not be
      # deleted while in Anatomist
      return {"mri" : mri, "fmri" : fmri, "fusion" : fusion, "window" : window, "refMRI" : refMRI, "refFMRI" : refFMRI, "transformation" : transformation, "mriFile" : mriFile, "fmriFile" : fmriFile}

    def viewTextureOnMesh( self, meshFile, textureFile, palette=None,
      interpolation=None ):
      """Load a mesh file and apply the texture with the palette"""
      mesh = self.loadObject( meshFile )
      if not mesh.getInternalRep():
        raise RuntimeError( 'Anatomist could not read file %s' \
          % meshFile.fullPath() )
      duplicate=False
      if palette is not None:
        duplicate=True
      tex = self.loadObject( textureFile, duplicate=duplicate)
      if not tex.getInternalRep():
        raise RuntimeError( 'Anatomist could not read file %s' \
          % textureFile.fullPath() )
      if palette:
        tex.setPalette( palette )
      # Fusion indexMESH with indexTEX
      fusion = self.fusionObjects( [mesh, tex],
        method = 'FusionTexSurfMethod' )
      if interpolation:
        self.execute("TexturingParams", objects=[tex], interpolation =
          interpolation )

      window = self.createWindow( "3D" )
      window.assignReferential( mesh.referential )
      window.addObjects( [fusion] )
      # Keep a reference on mesh. In case of temporary file, it must not be
      # deleted while in Anatomist
      return {"mesh" : mesh, "texture" : tex, "fusion" : fusion,
        "window" : window, "meshFile" : meshFile, "textureFile" : textureFile}

    def close( self ):
      # print('CLOSE !!!')
      if neuroConfig.anatomistImplementation != 'threaded':
        anatomistModule.Anatomist.close( self )
      else:
        #self.execute( 'DeleteAll' )
        #self.getControlWindow().close()
        reusablewinhook.uninstallWindowHandler()
        anatomistModule.Anatomist.close( self )
      print('anatomist closed.')

  # end of Anatomist class

  class AWindowChoice( neuroData.Choice ):
    '''
    A process parameter to choose an Anatomist window.
    This parameter is a choice between several anatomist windows. By default, if anatomist isn't started or if there's no opened windows, the choice offer the possibility to create any type of anatomist window.
    If anatomist is started, the set of opened window is added to the choices list.
    The list of choices is not updated automatically, to refresh the choices it is necessary to open a new instance of the process.
    '''

    def __init__( self, noSelectionLabel=None, aslist=False ):
      neuroData.Choice.__init__( self )
      self._init2( noSelectionLabel, aslist=aslist )

    def _init2( self, noSelectionLabel=None, aslist=False ):
      if noSelectionLabel is None:
        noSelectionLabel = '<'+_t_('None')+'>'
      self._initargs = ( noSelectionLabel, aslist )
      self.noSelectionLabel = noSelectionLabel
      self.aslist = aslist
      # initial choice : creating new windows
      self.selWindow = ( '<'+_t_('Selected windows in Anatomist')+'>',
        self.getSelectedWindows )
      self.newWindow = ( '<'+_t_('New window (3D)')+'>', self._newWindow )
      self.newWindowA = ( '<'+_t_('New window (Axial)')+'>',
                          lambda self=self: self._newWindow( 'Axial' ) )
      self.newWindowS = ( '<'+_t_('New window (Sagittal)')+'>',
                          lambda self=self: self._newWindow( 'Sagittal' ) )
      self.newWindowC = ( '<'+_t_('New window (Coronal)')+'>',
                          lambda self=self: self._newWindow( 'Coronal' ) )
      self.newWindowB = ( '<'+_t_('New window (Browser)')+'>',
                          lambda self=self: self._newWindow( 'Browser' ) )
      self.refreshChoices()

    def __getinitargs__( self ):
      """
      getinitargs, getstate, setstate are used by copy module.
      When a process is opened, its signature is copied. So if the signature contains a AWindowChoice, it is copied too. 
      If a shallow copy is done, the new AWindowChoice will contain reference from the source object and it is a source of problems. So these methods are redefined in order to make the shallow copy create a new distinct instance.
      With getinitargs, the constructor is called to create the new object. And because getstate and setstate do nothing, the source object is not copied, the two objects are distinct instances.
      """
      return self._initargs

    def __getstate__(self):
      dic = neuroData.Choice.__getstate__( self )
      dic[ 'values' ] = []
      return dic

    def __setstate__(self, state):
      neuroData.Choice.__setstate__( self, state )
      self._init2()

    def getSelectedWindows( self ):
      a = Anatomist( create=False )
      if a is not None:
        windows = a.getWindows()
        sels = [ w for w in windows if w.getInfos()[ 'selected' ] ]
        if self.aslist:
          return sels
        if len( sels ) == 1:
          return sels[0]
        else:
          return None
      if self.aslist:
        return []
      else:
        return None

    def refreshChoices( self, *args ):
      """
      Updates choice list. Adds to default choices curently opened anatomist windows.
      """
      # if anatomist is not started, this command will not start it.
      a = Anatomist( create=False )
      if a is not None:
        try:
          windows = a.getWindows()
          choices = [ self.selWindow, self.newWindow,
                      self.newWindowA, self.newWindowS, self.newWindowC,
                      self.newWindowB ] + \
            map( lambda w, self=self: \
                # (repr(w), lambda w=w: w), windows ) # label=repr(window), value=a lambda function that returns the window
                (repr(w), lambda wr=w.getRef("Weak"): wr), windows ) # label=repr(window), value=a lambda function that returns the window
                # before value was weakref.ref(w, self.refreshChoices) but it doesn't work with current anatomist api objects : the window object is not a permanant object, it is only created for the getWindows method and is destroyed at the end of refreshChoices, which calls the callback, which create a new window object (proxy for anatomist window)... -> infinite loop
          self.setChoices( *choices )
        except:
          # if it is impossible to get informations about anatomist windows, it may be already closed (close window event may occur after exit event...), so retrieve default choices.
          self.clearChoices()
      else:
        self.clearChoices()

    def clearChoices( self ):
        self.setChoices( self.selWindow,
                        self.newWindow,
                        self.newWindowA, self.newWindowS, self.newWindowC,
                        self.newWindowB )

    def _newWindow( self, type = "3D" ):
      """
      Creates a new Anatomist window of the given type.
      """
      win = Anatomist().createWindow( type )
      if self.aslist:
        return [ win ]
      return win


else: # if anatomist module is not available: empty classes
  class Anatomist:
    pass
  class AWindowChoice:
    pass

