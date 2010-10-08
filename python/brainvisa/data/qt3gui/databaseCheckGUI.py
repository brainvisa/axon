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

## TODO : 
# Pourvoir selectionner par selection multiple dans le listview les actions a cocher
# bouton inverser la selection au lieu de checkbox select all

# interface pour check database : plusieurs colonnes : fichier, type, action(s) (conversion, referentiel)
# possibilite de visualiser la donnee
# filtres pour modifier la vue

import neuroConfig 
from brainvisa.data.qt3gui.diskItemBrowser import DiskItemBrowser
import backwardCompatibleQt as qt
import qtui
import os
import neuroDiskItems, neuroHierarchy
from brainvisa.data.actions import Move, Remove, FileProcess, ImportData

ICON_SIZE=16

class ActionsWidget( qt.QDialog ):
  """
  A widget to present a list of file with suggested action associated. 
  Each action is (de)selectable. 
  The user can choose to run all actions now or later (= ok and cancel button of the dialog)
  """
  def __init__( self, processor, parent=None, uiFile='actions.ui'):
    qt.QDialog.__init__( self, parent, None ) # by default the dialog is not modal (doesn't block waiting user action)
    layout = qt.QVBoxLayout( self )
    layout.setAutoAdd( 1 )

    p = os.path.join( os.path.dirname( __file__ ), uiFile)  #os.path.join( neuroConfig.mainPath, 'actions.ui' )
    self.ui = qtui.QWidgetFactory.create(p, None, self)
    
    # change the instruction bar title
    self.titleLabel = self.ui.child('titleLabel')
    self.titleLabel.setText(_t_('Suggested actions on database files :'))
    
    # actions list
    self.actionsList=self.ui.child("actionsList")
    self.actionsList.setSorting(-1) # disable sort
    self.actionsList.setColumnText(0, _t_("File"))
    self.actionsList.setColumnText(1, _t_("Action"))
    self.tooltipsViewer=ActionToolTip(self.actionsList.viewport())
    
    #item=None
    directory=None
    for name, component in processor.components.items():
      if component.fileProcesses != []:
        directory=DirectoryWidget(name, self.actionsList, directory, "toolbox.png")
        #item=None
        item=self.addActions(directory, None, component.fileProcesses)
    item=self.addActions(self.actionsList, directory, processor.fileProcesses)
          
    # buttons to run actions
    self.runNowButton=self.ui.child("runNowButton")
    self.runNowButton.setText(_t_("Run now"))
    self.connect(self.runNowButton, qt.SIGNAL("clicked()"), self.runNow)#, qt.SLOT("done(1)")) #self.runActions)
    qt.QToolTip.add(self.runNowButton, _t_("Executes checked actions immediatly"))
    
    self.runLaterButton=self.ui.child("runLaterButton")
    self.runLaterButton.setText(_t_("Run later"))
    self.connect(self.runLaterButton, qt.SIGNAL("clicked()"), self.runLater)#self, qt.SLOT("done(2)"))
    qt.QToolTip.add(self.runLaterButton, _t_("Executes checked actions at the end of the pipeline. Does nothing outside of the pipeline."))
    
    # button to invert the state of selected check box item
    self.selectButton=self.ui.child("selectButton")
    self.selectButton.setText(_t_("Check/Uncheck selection"))
    self.connect(self.selectButton, qt.SIGNAL("clicked()"), self.invertSelection)
    qt.QToolTip.add(self.selectButton, _t_("Inverts the state of selected items"))
      
    #print "item added"
    self.resize(850,600)
  
  def runNow(self):
    self.done(1)
    
  def runLater(self):
    self.done(2)
    
  def invertSelection(self):
    it = qt.QListViewItemIterator(self.actionsList, qt.QListViewItemIterator.Selected)
    while it.current() :
      if isinstance(it.current(), qt.QCheckListItem):
        on=not it.current().isOn()
        it.current().setOn(on)
        it.current().model.selected=on
      it+=1
  
  def addActions(self, parent, after, actions):
    item=after
    if type(actions) is list:
      for action in actions:
        if isinstance(action, FileProcess):
          item=ActionWidget(action, parent, item)
        else: # it can be a map
          for key, value in action:
            item=DirectoryWidget(key, parent, item)
            self.addActions(item, None, value)
    else: # it is a map attribute -> map or list of FileProcess
      for key, value in actions.items():
        item=DirectoryWidget(key, parent, item)
        self.addActions(item, None, value)
    return item

###################################
class DirectoryWidget(qt.QListViewItem):
  defaultIcon="folder.png"
  
  def __init__(self, name, parent, after=None, icon=defaultIcon):
    qt.QListViewItem.__init__(self, parent, after, name)
    self.setOpen(True)
    image=qt.QImage(os.path.join(neuroConfig.iconPath, icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.setPixmap(0, pix)
    
###################################
class ActionWidget(qt.QCheckListItem):
  """
  Item in an ActionsList. 
  Shows a file with associated action.
  """
  
  def __init__(self, fileProcess, parent, after=None):
    self.model=fileProcess
    if after is None:
      qt.QCheckListItem.__init__(self, parent, fileProcess.filePattern(), qt.QCheckListItem.CheckBox)
    else:
      qt.QCheckListItem.__init__(self, parent, after, fileProcess.filePattern(), qt.QCheckListItem.CheckBox)
    if fileProcess.action is not None:
      icon=fileProcess.action.icon
      self.setText(1, unicode(fileProcess.action))
    else : # there's nothing to do because the file is correct
      icon="ok.png"
    image=qt.QImage(os.path.join(neuroConfig.iconPath, icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.setPixmap(1, pix)
    self.setOn(True)
  
  def stateChange(self, state):
    self.model.selected=state
  
  def setAction(self, action):
    self.model.action = action
    image=qt.QImage(os.path.join(neuroConfig.iconPath, action.icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.setPixmap(1, pix)
    self.setText(1, unicode(self.model.action))

###################################
class ActionToolTip(qt.QToolTip):
  """
  This class enables to show a tooltip when the mouse is on action icon.
  """
  def __init__(self, parent):
    qt.QToolTip.__init__(self, parent)

  def maybeTip(self, pos):
    """Called when the mouse stay at a point of this object's parent."""
    # this object is a child of the viewport, not directly of the listview otherwise this method isn't called when the mouse is on the list content.
    viewport=self.parentWidget()
    listview=viewport.parent()
    #cursorPos=w.toContentsPoint(pos)
    currentItem=listview.itemAt(pos) #item under the mouse cursor
    if (currentItem != None) and (getattr(currentItem, "model", None) != None) :
      rect=listview.itemRect(currentItem)
      
      # for each column, set a tooltip with the column's text : get column's content rect
      cRect=[]
      currentPos=rect.left()
      for c in range(listview.columns()):
        cRect.append(qt.QRect(currentPos, rect.top(), listview.columnWidth(c), rect.height()) ) # left, top, width, height
        currentPos=cRect[c].right()
      # for last column, set a tooltip for the action icon, so reduce size of the last rect
      actionTooltip=getattr(currentItem.model, "tooltip", None)
      if actionTooltip:
        iconRect=qt.QRect(cRect[-1].left(), rect.top(), ICON_SIZE, rect.height())
        cRect[-1].setLeft(iconRect.right())
      
      #set tooltips
      c=0
      for r in cRect:
        self.tip(r, currentItem.text(c))
        c+=1
      # set icon tootip
      if actionTooltip:
        self.tip(iconRect, currentItem.model.tooltip)
      
###################################
class UnknownFilesWidget( ActionsWidget ):
  """
  Widget that presents a list of unknown files and proposes 2 actions on these files : remove and move. 
  It is possible to choose the same action for each file with the buttons remove all and move all. 
  It is possible to change the action for a partcular file with context menu.
  For move action, default destination is the database directory.
  """
  def __init__( self, processor, parent=None):
    """
    @type processor: DBCleaner
    @param processor: the database cleaner that find unknown files in the database.
    """
    ActionsWidget.__init__(self, processor, parent)
    self.defaultDest=processor.dbDir
    self.database=processor.db
    # change the instruction bar title
    self.titleLabel.setText(_t_('Choose actions for unknown files in the database :'))
        
    # add buttons to change all actions remove all and move all
    # there is two frames action1 and action2 to enable to add some buttons. 
    # Else I cannot add a button to the widget at a right place, added button are always on existing buttons...
    self.removeAllButton=qt.QPushButton(_t_("Remove all"), self.ui.child("action1"))
    self.connect(self.removeAllButton, qt.SIGNAL("clicked()"), self.removeAll)
    self.moveAllButton=qt.QPushButton(_t_("Move all"), self.ui.child("action2"))
    self.connect(self.moveAllButton, qt.SIGNAL("clicked()"), self.moveAll)
    
    
    # add a right click menu to change action for a particular file
    self.popupMenu = qt.QPopupMenu()
    image=qt.QImage(os.path.join(neuroConfig.iconPath, Remove.icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.popupMenu.insertItem( qt.QIconSet(pix), "Remove",  self.menuRemoveEvent )
    image=qt.QImage(os.path.join(neuroConfig.iconPath, Move.icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.popupMenu.insertItem( qt.QIconSet(pix), "Move",  self.menuMoveEvent )
    image=qt.QImage(os.path.join(neuroConfig.iconPath, ImportData.icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.popupMenu.insertItem( qt.QIconSet(pix), "Import",  self.menuImportEvent )

    self.connect(self.actionsList, qt.SIGNAL( 'contextMenuRequested ( QListViewItem *, const QPoint &, int )'), self.openContextMenu)
  
  def openContextMenu(self):
    """
    Called on contextMenuRequested signal. It opens the popup menu at cursor position.
    """
    self.popupMenu.exec_loop(qt.QCursor.pos())
  
  def menuRemoveEvent(self):
    item=self.actionsList.selectedItem()
    if item:
      action=Remove(os.path.dirname(item.model.file))
      item.setAction(action) 
  
  def menuMoveEvent(self):
    item=self.actionsList.selectedItem()
    if item:
      # open a dialog to choose where to move
      dest=unicode(qt.QFileDialog.getExistingDirectory(self.defaultDest, self, "fileDialog", _t_("Choose a directory for destination : ") ))
      action=Move(dest)
      item.setAction(action)
  
  def menuImportEvent(self):
    """
    Called when user choose to import unidentified file in the database. 
    """
    item=self.actionsList.selectedItem()
    selectedType=None
    selectedFormat=None
    selectedAttributes={}
    if item:
      # if the current action associated to this item is already ImportData, get current parameter to initialize the diskItemBrowser
      if isinstance(item.model.action, ImportData) and item.model.action.dest:
        action=item.model.action
        defaultValue=action.dest
      else:
        action=ImportData(item.model.diskItem, None)
        defaultValue=item.model.diskItem
      selection = defaultValue.hierarchyAttributes()
      if defaultValue.type is None :
        selection[ '_type' ] = 'Any Type'
      else :
        selection[ '_type' ] = defaultValue.type.name
      if defaultValue.format is None :
        selection[ '_format' ] = None
      else :
        selection[ '_format' ] = defaultValue.format.name

      self.importDialog=DiskItemBrowser( self.database, self, write=True, selection=selection, required={'_type' : selection['_type'], '_format' : selection['_format']} )
      self.importDialog.setCaption( _t_( selection[ '_type' ] ) )
      self.importDialog.connect( self.importDialog, qt.PYSIGNAL( 'accept' ), lambda item=item, action=action: self.importDialogAccepted(item, action) )
      self.importDialog.show()

  def importDialogAccepted(self, item, action):
    values=self.importDialog.getValues()
    if len(values) > 0:
      action.dest=values[0]
      item.setAction(action)
    
  def removeAll(self):
    """
    Called when the user click on remove all button. Set action Remove on all unknown file.
    """
    it = qt.QListViewItemIterator(self.actionsList)
    while it.current() :
      action = Remove(os.path.dirname(it.current().model.file))
      it.current().setAction(action)
      it+=1
  
  def moveAll(self):
    """
    Called when the user click on move all button. Set action Move on all unknown file.
    """
    # open a dialog to choose where to move
    dest=unicode(qt.QFileDialog.getExistingDirectory(self.defaultDest, self, "fileDialog", _t_("Choose a directory for destination : ") ))
    it = qt.QListViewItemIterator(self.actionsList)
    while it.current() :
      action=Move(os.path.join(dest, os.path.basename(it.current().model.file)))
      it.current().setAction(action)
      it+=1

###################################
class CheckFilesWidget( ActionsWidget ):
  """
  Widget to present checked database files. 
  There are several columns to provide information about database items : filename, format, type, suggested action.
  If a file is correct, there is no action associated : an icon "ok" is displayed.
  This widget is based on check.ui qt designer file.
  The checked files are grouped by filters attributes : these attributes are displayed as directories in the listview. 
  """
  def __init__( self, processor, parent=None):
    """
    @type processor: DBChecker
    @param processor: the database checker that checks database files and can suggest actions if some files are incorrect.
    """
    super(CheckFilesWidget, self).__init__(processor, parent, "check.ui")
    # actions list
    self.actionsList.setColumnText(0, _t_("File"))
    self.actionsList.setColumnText(1, _t_("Type"))
    self.actionsList.setColumnText(2, _t_("Format"))
    self.actionsList.setColumnText(3, _t_("Action"))
  
  def addActions(self, parent, after, actions):
    """
    This method is redefined because, item are different from ActionsWidget items (more columns to fill)
    """
    item=after
    if type(actions) is list:
      for action in actions:
        if isinstance(action, FileProcess):
          item=CheckFileWidget(action, parent, item)
        else: # it can be a map
          for key, value in action:
            if key:
              item=DirectoryWidget(key, parent, item)
              self.addActions(item, None, value)
            else:
              item=self.addActions(parent, item, value)
    else: # it is a map attribute -> map or list of FileProcess
      for key, value in actions.items():
        if key:
          item=DirectoryWidget(key, parent, item)
          self.addActions(item, None, value)
        else:
          item=self.addActions(parent, item, value)
    return item

###################################
class CheckFileWidget(qt.QCheckListItem):
  """
  Item in an CheckFilesWidget. 
  For each checked file, show filename, type, format and associated action (or "ok" icon if there is no action).
  """
  def __init__(self, fileProcess, parent, after=None):
    self.model=fileProcess
    if after is None:
      qt.QCheckListItem.__init__(self, parent, os.path.basename(fileProcess.diskItem.name), qt.QCheckListItem.CheckBox)
    else:
      qt.QCheckListItem.__init__(self, parent, after, os.path.basename(fileProcess.diskItem.name), qt.QCheckListItem.CheckBox)
    self.setText(1, unicode(fileProcess.diskItem.type))
    self.setText(2, unicode(fileProcess.diskItem.format))
    if fileProcess.action is not None:
      icon=fileProcess.action.icon
      self.setText(3, unicode(fileProcess.action))
    else : # there's nothing to do because the file is correct
      icon="ok.png"
    image=qt.QImage(os.path.join(neuroConfig.iconPath, icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.setPixmap(3, pix)
    if fileProcess.selected:
      self.setOn(True) # the item is not selected
  
  def stateChange(self, state):
    self.model.selected=state
  
  def setAction(self, action):
    self.model.action = action
    image=qt.QImage(os.path.join(neuroConfig.iconPath, action.icon))
    pix=qt.QPixmap(image.smoothScale(ICON_SIZE, ICON_SIZE))
    self.setPixmap(3, pix)
    self.setText(3, unicode(self.model.action))
