#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import signal

from Qt import QtCore, QtWidgets
from Qt.QtCore import QTimer
from Qt.QtGui import QPalette, QColor

from NodeGraphQt import (
    NodeGraph,
    # PropertiesBinWidget,
    # NodesTreeWidget,
    # NodesPaletteWidget
)

from nodes import sample_nodes

from functools import partial

# {'graph': {'layout_direction': 0, 'acyclic': True, 'pipe_collision': False, 'pipe_slicing': True, 'pipe_style': 1, 'accept_connection_types': {}, 'reject_connection_types': {}}, 'nodes': {'0x1a588ca4c10': {'type_': 'nodes.sample.InputNode', 'icon': None, 'name': 'Input', 'color': (13, 18, 23, 255), 'border_color': (74, 84, 85, 255), 'text_color': (255, 255, 255, 180), 'disabled': False, 'selected': False, 'visible': True, 'width': 160, 'height': 60, 'pos': [-5.023858959254142, 256.21680692196236], 'layout_direction': 0, 'port_deletion_allowed': False, 'subgraph_session': {}}, '0x1a588ca4e80': {'type_': 'nodes.sample.UniNode', 'icon': None, 'name': 'Uni', 'color': (13, 18, 23, 255), 'border_color': (74, 84, 85, 255), 'text_color': (255, 255, 255, 180), 'disabled': False, 'selected': False, 'visible': True, 'width': 160, 'height': 60, 'pos': [277.31701455082987, 335.59377847817814], 'layout_direction': 0, 'port_deletion_allowed': False, 'subgraph_session': {}}}, 'connections': [{'out': ['0x1a588ca4c10', 'out'], 'in': ['0x1a588ca4e80', 'in']}]}
def verify_session(graph):
    print(graph.serialize_session())

def counter(graph):
    all_nodes = graph.all_nodes()
    # if len(all_nodes) > 0:
    #     for node in all_nodes:
    #         rgb = node.color()
    #         if rgb == (13, 18, 23):
    #             node.set_color(255, 0, 0)
    #         print(rgb)
    

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

    graph.register_nodes([
        sample_nodes.InputNode,
        sample_nodes.OutputNode,
        sample_nodes.UniNode,
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()

    t1 = QTimer()
    t1.setInterval(5 * 1000)  # msec
    t1.timeout.connect(partial(counter, graph))
    t1.start()

    app.exec_()
