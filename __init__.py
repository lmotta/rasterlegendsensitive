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
import os.path

from PyQt4.QtGui import ( QAction, QIcon )
from PyQt4.QtCore import ( Qt, pyqtSlot )

from rasterlegendsensitive import DockWidgetRasterLegendSensitive

def classFactory(iface):
  return RasterLegendSensitivePlugin( iface )

class RasterLegendSensitivePlugin:

  def __init__(self, iface):

    self.iface = iface
    self.name = u"Raster legend &sensitive"
    self.dock = None

  def initGui(self):
    msg = "Raster legend sensitive"
    icon = QIcon( os.path.join( os.path.dirname(__file__), 'rasterlegendsensitive.svg' ) )
    self.action = QAction( icon, msg, self.iface.mainWindow() )
    self.action.setObjectName("RasterLegendSensitive")
    self.action.setWhatsThis( msg )
    self.action.setStatusTip( msg )
    self.action.setCheckable( True )
    self.action.triggered.connect( self.run )

    self.iface.addRasterToolBarIcon( self.action )
    self.iface.addPluginToRasterMenu( self.name, self.action )

    self.dock = DockWidgetRasterLegendSensitive( self.iface )
    self.iface.addDockWidget( Qt.LeftDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeRasterToolBarIcon( self.action )
    self.iface.removePluginRasterMenu( self.name, self.action )

    self.dock.close()
    del self.dock
    self.dock = None

    del self.action

  @pyqtSlot()
  def run(self):
    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
    self.dock.visibility( visible )
