#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import signal

from Qt import QtCore, QtWidgets
from Qt.QtGui import QPalette, QColor

from NodeGraphQt import (
    NodeGraph,
    PropertiesBinWidget,
    NodesTreeWidget,
    NodesPaletteWidget
)

# import example nodes from the "example_nodes" package
from nodes import ofp_nodes, slab_nodes

if __name__ == '__main__':
    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])

    app.setStyle("Fusion")
    mypalette = QPalette()
    mypalette.setColor(QPalette.Text, QColor(192, 192, 192))
    app.setPalette(mypalette)

    # create graph controller.
    graph = NodeGraph()

    # set up context menu for the node graph.
    graph.set_context_menu_from_file('hotkeys/hotkeys.json')

    # registered example nodes.
    graph.register_nodes([
        ofp_nodes.SupplyContainerSingleNode,
        ofp_nodes.SupplyContainerArrayNode,
        ofp_nodes.SupplyLiquidNode,
        ofp_nodes.DispenseLiquidNode,
        ofp_nodes.DiscardNode,
        ofp_nodes.SaveArtifactsNode,
        ofp_nodes.MeasureAbsorbanceNode,
        ofp_nodes.NumberInputNode,
        slab_nodes.SLabNode,
        slab_nodes.TransporterNode,
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()

    app.exec_()
