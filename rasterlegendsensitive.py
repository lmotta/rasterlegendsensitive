# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Raster legend sensitive
Description          : Change the legend of raster(need have palette) by extent of map and show/hide each item in legend.
Date                 : February, 2016
copyright            : (C) 2016 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import ( QObject, pyqtSignal, pyqtSlot, Qt, QThread )
from PyQt4.QtGui import ( 
     QTreeView, QGridLayout, QDockWidget, QWidget, QCheckBox,
     QStandardItemModel, QStandardItem,
     QFont, QPixmap, QIcon,
     QMessageBox, QApplication
)

from qgis.core  import QgsRasterTransparency, QgsMapLayerRegistry, QgsMapLayer
from qgis.gui  import QgsMessageBar

class TreeLegend(QObject):

  toggledLegend = pyqtSignal(  list )
  descriptionLegend = pyqtSignal(  str )
  
  def __init__(self, treeView):
    def init():
      self.setHeader()
      self.tree.setModel( self.model )
      self.headerView.setMovable( False )
      self.headerView.setClickable( True )
      self.tree.setSelectionMode(0) # no selection

    super(TreeLegend, self).__init__()
    self.tree = treeView
    #
    self.hasConnect = self.layer = self.legendItems = None
    self.visibleItems = []
    self.model = QStandardItemModel( 0, 1 )
    self.headerView = self.tree.header()
    #
    init()
    self._connect()

  def __del__(self):
    if self.hasConnect:
      self._connect( False )
    self.model.clear()
    self.layer.legendChanged.disconnect( self.updateLegendItems )

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': self.tree.clicked, 'slot': self.toggleItem },
      { 'signal': self.headerView.sectionClicked, 'slot': self.toggleHeader },
      { 'signal': self.headerView.sectionDoubleClicked, 'slot': self.emitDescription }
    ]
    if isConnect:
      self.hasConnect = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnect = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def setHeader(self, data=None):
    if data is None:
      self.model.clear()
      nameHeader = 'Select Raster Layer(Palette)'
      font = QFont()
      font.setStrikeOut( False )
      headerModel = QStandardItem( nameHeader )
      headerModel.setData( font, Qt.FontRole )
      tip = "Raster with Palette(Single Band)"
      headerModel.setData( tip, Qt.ToolTipRole )
      self.model.setHorizontalHeaderItem( 0, headerModel )
    else:
      headerModel = self.model.horizontalHeaderItem( 0 )
      label = "%s" % data[ 'name' ]
      formatMgs = "Layer: %s\nSource: %s\nNumber Class: %d\nWidth: %d\nHeight: %d\nRes.X: %f\nRes.Y: %f\n\n* Double click copy to Clipboard"
      dataMsg = ( data['name'], data[ 'source' ], data ['num_class' ], data['width'], data['height'], data['resX'], data['resY'] ) 
      tip = formatMgs % dataMsg
      headerModel.setData( data, Qt.UserRole )
      headerModel.setData( label, Qt.DisplayRole )
      headerModel.setData( tip, Qt.ToolTipRole )
    
  def setLayer(self, layer):
    self.legendItems = layer.legendSymbologyItems()
    total = len( self.legendItems )
    self.visibleItems = [ True for x in range( total ) ]
    data = { 
      'name':layer.name(), 'source': layer.source(), 'num_class': total,
      'width': layer.width(), 'height': layer.height(), 'resX': layer.rasterUnitsPerPixelX(), 'resY': layer.rasterUnitsPerPixelY()
    }
    self.setHeader( data )
    #
    if not self.layer is None:
      self.layer.legendChanged.disconnect( self.updateLegendItems )
    layer.legendChanged.connect( self.updateLegendItems )
    self.layer = layer

  def setLegend(self, values):
    def setHeader():
      headerModel = self.model.horizontalHeaderItem( 0 )
      data = headerModel.data( Qt.UserRole )
      data['num_class'] = len( values )
      self.setHeader( data )

    def createItem( item ):
      ( pixel, total ) = item
      ( legend, color ) = self.legendItems[ pixel ]
      name = "[%d] %s" % ( pixel, legend )
      tip = "Value pixel: %d\nTotal pixels: %d\nClass name: %s" % ( pixel, total, legend )
      pix = QPixmap( 16, 16 )
      pix.fill( color )
      font.setStrikeOut( not self.visibleItems[ pixel ] )
      #
      itemModel = QStandardItem( QIcon( pix ), name )
      itemModel.setEditable( False )
      itemModel.setData( font, Qt.FontRole )
      itemModel.setData( tip, Qt.ToolTipRole )
      itemModel.setData( item, Qt.UserRole )
      #
      return itemModel

    setHeader()
    self.model.removeRows( 0, self.model.rowCount() )
    #
    font = QFont()
    for item in values:
      self.model.appendRow( createItem( item ) )

  def setEnabled(self, isEnable=True):
    self._connect( isEnable )
    self.tree.setEnabled( isEnable )

  def getLayerName(self):
    headerModel = self.model.horizontalHeaderItem( 0 )
    return headerModel.data( Qt.UserRole )[ 'name']

  @pyqtSlot()
  def updateLegendItems(self):
    self.legendItems = self.layer.legendSymbologyItems()
    # Refresh legend
    rows = self.model.rowCount()
    row = 0
    while row < rows:
      index = self.model.index( row, 0 )
      ( pixel, total ) = self.model.data( index, Qt.UserRole )
      ( legend, color ) = self.legendItems[ pixel ]
      pix = QPixmap( 16, 16 )
      pix.fill( color )
      self.model.setData( index, QIcon( pix ), Qt.DecorationRole )
      row += 1

  @pyqtSlot('QModelIndex')
  def toggleItem(self, index):
    font = index.data( Qt.FontRole )
    strike = not font.strikeOut()
    font.setStrikeOut( strike )
    self.model.setData( index, font, Qt.FontRole )
    #
    ( pixel, total ) = index.data( Qt.UserRole )
    visible = not strike
    self.visibleItems[ pixel ] = visible
    #
    self.toggledLegend.emit( self.visibleItems )

  @pyqtSlot(int)
  def toggleHeader(self, logical):
    rowCount = self.model.rowCount()
    if rowCount == 0:
      return

    header = self.model.horizontalHeaderItem( 0 )
    font = header.data( Qt.FontRole )
    strike = not font.strikeOut()
    font.setStrikeOut( strike )
    header.setData( font, Qt.FontRole )
    #
    items = []
    row = 0
    while row < self.model.rowCount():
      index = self.model.index( row, 0 )
      self.model.setData( index, font, Qt.FontRole )
      items.append( index.data( Qt.UserRole ) )
      row += 1

    visible = not strike
    for item in items:
      ( pixel, total ) = item
      self.visibleItems[ pixel ] = visible
    #
    self.toggledLegend.emit( self.visibleItems )

  @pyqtSlot(int)
  def emitDescription(self):
    def getDescription():
      data = self.model.horizontalHeaderItem( 0 ).data( Qt.UserRole )
      formatMgs = "Layer: %s\nSource: %s\nNumber Class: %d\nWidth: %d\nHeight: %d\nRes.X: %f\nRes.Y: %f"
      dataMsg = ( data['name'], data[ 'source' ], data ['num_class' ], data['width'], data['height'], data['resX'], data['resY'] ) 
      descHeader  = formatMgs % dataMsg
      #
      descItems = [ "Value pixel;Total pixels;Class name" ]
      rows = self.model.rowCount()
      row = 0
      while row < rows:
        index = self.model.index( row, 0 )
        ( pixel, total ) = self.model.data( index, Qt.UserRole )
        ( legend, color ) = self.legendItems[ pixel ]
        descItems.append( "%d;%d;%s" % ( pixel, total, legend ) )
        row += 1

      return "%s\n\n%s" % ( descHeader, '\n'.join( descItems ) )

    if self.model.rowCount() > 0:
      self.descriptionLegend.emit( getDescription() )

class WorkerRasterLegendSensitive(QObject):

  finished = pyqtSignal(list)
  messageStatus = pyqtSignal( str )

  def __init__(self):
    super(WorkerRasterLegendSensitive, self).__init__()
    self.isKilled = None
    self.readBlock = self.extent = self.widthRead = self.heightRead = None
    self.legendAll = None

  def setLegendReadBlock(self, layer):
    self.readBlock = layer.dataProvider().block
    self.legendAll = map( lambda x: x[0], layer.legendSymbologyItems() )

  def setProcessImage(self, extent, widthRead, heightRead):
    ( self.extent, self.widthRead, self.heightRead ) = ( extent, widthRead, heightRead )
    self.isKilled = False

  @pyqtSlot()
  def run(self):
    self.messageStatus.emit( "Reading image..." )

    keysLegend = range( len(self.legendAll) )
    # pixels_values = { float'idClass': ZERO ...} *** block.value return 'float'
    pixels_values = dict( ( float(x),0 ) for x in keysLegend )
    del keysLegend[:]
    data = self.readBlock(  1, self.extent, self.widthRead, self.heightRead )
    h = 0
    stepStatus = 10.0
    showStatus = stepStatus
    value = 0.0
    while h < self.heightRead:
      w = 0
      #
      if self.isKilled:
        pixels_values.clear()
        del data
        self.finished.emit( [] )
        return
      #
      perc = 100.0 * float(h+1) / self.heightRead
      if perc >= showStatus:
        msg = "Calculating legend... %d %%" % int(perc)
        self.messageStatus.emit( msg )
        showStatus += stepStatus
      #
      while w < self.widthRead:
        pixels_values[ data.value(h,w) ] += 1
        w += 1
      h += 1
    del data
    
    values = [ ( int(k), v ) for k,v in pixels_values.items() if v > 0 ]
    pixels_values.clear()
    #
    self.finished.emit( values )

class RasterLegendSensitive(QObject):
  def __init__(self, iface, treeView):
    super(RasterLegendSensitive, self).__init__()
    self.tree = TreeLegend( treeView )
    #
    self.layer = self.worker = self.thread = self.transparencyLayer = None
    self.valuesFullExtent = self.hasConnect = self.hasConnectTree = None
    self.iface = iface
    self.legend = iface.legendInterface()
    self.canvas = iface.mapCanvas()
    self.msgBar = iface.messageBar()
    self.nameModulus = "RasterLegendSensitive"
    #
    self.initThread()
    self._connect()
    self._connectTree()

  def __del__(self):
    del self.tree
    self.finishThread()
    if not self.hasConnect:
      self._connect( False )
    if not self.layer is None:
      self.transparencyLayer.setTransparentSingleValuePixelList( [] )

  def initThread(self):
    self.thread = QThread( self )
    self.thread.setObjectName( self.nameModulus )
    self.worker = WorkerRasterLegendSensitive()
    self.worker.moveToThread( self.thread )
    self._connectWorker()

  def finishThread(self):
    self._connectWorker( False )
    self.worker.deleteLater()
    self.thread.wait()
    self.thread.deleteLater()
    self.thread = self.worker = None

  def _connectWorker(self, isConnect = True):
    ss = [
      { 'signal': self.thread.started, 'slot': self.worker.run },
      { 'signal': self.worker.finished, 'slot': self.finishedWorker },
      { 'signal': self.worker.messageStatus, 'slot': self.messageStatusWorker }
    ]
    if isConnect:
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': self.legend.currentLayerChanged, 'slot': self.selectLayer },
      { 'signal': QgsMapLayerRegistry.instance().layerWillBeRemoved, 'slot': self.unselectLayer },
      { 'signal': self.canvas.extentsChanged, 'slot': self.changeSensitiveLegend }
    ]
    if isConnect:
      self.hasConnect = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnect = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _connectTree(self, isConnect = True):
    ss = [
      { 'signal': self.tree.toggledLegend, 'slot': self.setTransparenceLayer },
      { 'signal': self.tree.descriptionLegend, 'slot': self.sendClipboard }
    ]
    if isConnect:
      self.hasConnectTree = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnectTree = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def setEnabled(self, isEnabled=True):
    self._connect( isEnabled )
    self._connectTree( isEnabled )
    self.tree.setEnabled( isEnabled )
    #
    if isEnabled:
      if self.layer is None:
        self.selectLayer( self.iface.activeLayer() )
        if not self.layer is None:
          self.changeSensitiveLegend()
      else:
        layers = self.legend.layers()
        if not self.layer in layers:
          if len( layers ) > 0:
            self.unselectLayer( self.layer.id() )
          else:
            self.unselectLayer()
        else:
          self.changeSensitiveLegend()

  @pyqtSlot(list)
  def finishedWorker(self, values):
    self.thread.quit()
    self.msgBar.popWidget()
    if not self.worker.isKilled: 
      if len( values ) > 0: # Never Happing...
        self.tree.setLegend( values )
        if self.valuesFullExtent is None:
          self.valuesFullExtent = values
    else: # When PAN/ZOOM/...
      self.thread.wait()
      self.changeSensitiveLegend()

  @pyqtSlot( str )
  def messageStatusWorker(self, msg):
    self.msgBar.popWidget()
    self.msgBar.pushMessage( self.nameModulus, msg, QgsMessageBar.INFO )

  @pyqtSlot( list )
  def setTransparenceLayer(self, visibleItems ):
    def refreshLayer():
      if  hasattr( self.layer, "setCacheImage" ):
        self.layer.setCacheImage(None) # Refresh
      else:
        self.layer.triggerRepaint()

    def setTransparence(value, visible):
      t = QgsRasterTransparency.TransparentSingleValuePixel()
      t.min = t.max = value
      percent = 100.0 if not visible else 0.0
      t.percentTransparent = percent

      return t

    valuesTransparent = []
    item = 0
    for visible in visibleItems:
      valuesTransparent.append( setTransparence( item, visible ) )
      item += 1
    self.transparencyLayer.setTransparentSingleValuePixelList( valuesTransparent )
    refreshLayer()
    del valuesTransparent[:]

  @pyqtSlot( str )
  def sendClipboard(self, description):

    mapSettings = self.canvas.mapSettings()
    crsCanvas = mapSettings.destinationCrs()
    extentCanvas = self.canvas.extent()
    extentLayer = self.layer.extent()
    
    if self.layer.crs() != crsCanvas:
      extentCanvas = mapSettings.mapToLayerCoordinates( self.layer, extentCanvas )

    if extentCanvas == extentLayer or extentCanvas.contains( extentLayer):
      msg = "Calculate for all extent of layer '%s'\n\n%s" % ( self.layer.name(), description )
    else:
      msg = "Calculate for subset of layer '%s' (extend: %s)\n\n%s" % ( self.layer.name(), extentCanvas.toString(), description )
    clip = QApplication.clipboard()
    clip.setText( msg )
    self.msgBar.pushMessage( self.nameModulus, "Copy to Clipboard", QgsMessageBar.INFO, 5)

  @pyqtSlot( 'QgsMapLayer' )
  def selectLayer(self, layer):
    def setValuesFullExtent():
      if not self.valuesFullExtent is None:
        del self.valuesFullExtent[:]
        self.valuesFullExtent = None

    if self.layer == layer or self.thread.isRunning():
      return

    if not layer is None and layer.type() ==  QgsMapLayer.RasterLayer:
      legendItems = layer.legendSymbologyItems()
      total = len( legendItems )
      if total > 0: # Had a classification
        self.msgBar.pushMessage( self.nameModulus, "Starting legend...", QgsMessageBar.INFO)
        self.worker.setLegendReadBlock( layer )
        self.tree.setLayer( layer )
        setValuesFullExtent()
        ( self.layer, self.transparencyLayer ) = ( layer, layer.renderer().rasterTransparency() )
        self.changeSensitiveLegend()
        self.msgBar.popWidget()

  @pyqtSlot( str )
  def unselectLayer(self, idLayer=None):
    if idLayer is None or ( not self.layer is None and self.layer.id() == idLayer ):
      if self.thread.isRunning():
        self.worker.isKilled = True
      msg = "Layer '%s' was removed" % self.tree.getLayerName()
      self.msgBar.pushMessage( self.nameModulus, msg, QgsMessageBar.WARNING, 5)
      self.layer = None
      self.tree.setHeader()
      self.tree.layer = None

  @pyqtSlot()
  def changeSensitiveLegend(self):
    if self.layer is None:
      return

    if self.thread.isRunning():
      self.worker.isKilled = True
      return

    mapSettings = self.canvas.mapSettings()
    crsCanvas = mapSettings.destinationCrs()
    extentCanvas = self.canvas.extent()
    
    extentLayer = self.layer.extent()
    resX = self.layer.rasterUnitsPerPixelX() 
    resY = self.layer.rasterUnitsPerPixelY()
    
    if self.layer.crs() != crsCanvas:
      extentCanvas = mapSettings.mapToLayerCoordinates( self.layer, extentCanvas )

    if not extentCanvas.intersects( extentLayer ):
      self.msgBar.popWidget()
      self.msgBar.pushMessage( self.nameModulus, "View not intersects Raster '%s'" % self.layer.name, QgsMessageBar.WARNING, 5)
      self.tree.setLegend( [] )
      return
    
    if extentCanvas == extentLayer or extentCanvas.contains( extentLayer):
      if not self.valuesFullExtent is None:
        self.tree.setLegend( self.valuesFullExtent )
        return
      extent = extentLayer
      delta = 0
    else:
      extent = extentCanvas.intersect( extentLayer )
      delta = 1

    widthRead  = int( extent.width()  / resX ) + delta
    heightRead = int( extent.height() / resY ) + delta

    self.worker.setProcessImage( extent, widthRead, heightRead )
    self.thread.start()
    #self.worker.run() # DEBUG

class DockWidgetRasterLegendSensitive(QDockWidget):

  def __init__(self, iface):

    def setupUi():
      self.setObjectName( "rasterlegendasensitive_dockwidget" )
      wgt = QWidget( self )
      wgt.setAttribute(Qt.WA_DeleteOnClose)
      #
      gridLayout = QGridLayout( wgt )
      gridLayout.setContentsMargins( 0, 0, gridLayout.verticalSpacing(), gridLayout.verticalSpacing() )
      #
      ( iniY, iniX, spanY, spanX ) = ( 0, 0, 1, 1 )
      self.ckEnabled = QCheckBox( "Enabled", wgt )
      gridLayout.addWidget( self.ckEnabled, iniY, iniX, spanY, spanX )
      #
      self.tree = QTreeView( wgt )
      iniY += 1
      spanX = 2
      gridLayout.addWidget( self.tree, iniY, iniX, spanY, spanX )
      #
      wgt.setLayout( gridLayout )
      self.setWidget( wgt )

    super( DockWidgetRasterLegendSensitive, self ).__init__( "Raster Legend Sensitive", iface.mainWindow() )
    #
    self.tree = self.ckEnabled = None
    setupUi()
    self.rls = RasterLegendSensitive( iface, self.tree )
    #
    self.ckEnabled.stateChanged.connect( self.enabled )
    self.rlsEnabled = True
    self.ckEnabled.setCheckState( Qt.Unchecked )
    self.enabled( Qt.Unchecked )

  def __del__(self):
    del self.rls

  @pyqtSlot( int )
  def enabled(self, state):
    enabled = True if state == Qt.Checked else False
    if not self.rlsEnabled == enabled:
      self.rls.setEnabled( enabled )
      self.rlsEnabled = enabled
  
  def visibility( self, visible ):
    if not visible:
      self.ckEnabled.setCheckState( Qt.Unchecked )
