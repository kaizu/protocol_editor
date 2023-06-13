#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

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
from NodeGraphQt.constants import PortTypeEnum

from nodes import sample_nodes

import itertools
import functools

logger = getLogger(__name__)


def verify_session(graph):
    all_nodes = graph.all_nodes()
    for node in all_nodes:
        is_valid = True
        for port in itertools.chain(
            node.input_ports(), node.output_ports()
        ):
            connected_ports = port.connected_ports()
            if len(connected_ports) == 0:
                is_valid = False
                break

            port_traits = node.get_port_traits(port.name())
            for another_port in connected_ports:
                another_traits = another_port.node().get_port_traits(another_port.name())
                if (
                    (port.type_() == PortTypeEnum.IN.value and another_traits not in port_traits)
                    or (port.type_() == PortTypeEnum.OUT.value and port_traits not in another_traits)
                ):
                    is_valid = False
                    break

        if is_valid:
            node.set_color(13, 18, 23)
        else:
            node.set_color(180, 18, 23)

    # logger.info(graph.serialize_session())

def counter(graph):
    all_nodes = graph.all_nodes()
    # if len(all_nodes) > 0:
    #     for node in all_nodes:
    #         rgb = node.color()
    #         if rgb == (13, 18, 23):
    #             node.set_color(255, 0, 0)
    #         print(rgb)
    
class MyNodeGraph(NodeGraph):

    def __init__(self):
        super(MyNodeGraph, self).__init__()

        self.node_created.connect(self.dump)
        self.nodes_deleted.connect(self.dump)
        self.port_connected.connect(self.dump)
        self.port_disconnected.connect(self.dump)

    def dump(self, *args, **kwargs):
        logger.info("dump %s %s", args, kwargs)
        verify_session(self)


if __name__ == '__main__':
    from logging import StreamHandler, Formatter, INFO
    handler = StreamHandler()
    handler.setLevel(INFO)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(INFO)
    
    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])

    app.setStyle("Fusion")
    mypalette = QPalette()
    mypalette.setColor(QPalette.Text, QColor(192, 192, 192))
    app.setPalette(mypalette)

    # create graph controller.
    graph = MyNodeGraph()

    # set up context menu for the node graph.
    graph.set_context_menu_from_file('hotkeys/hotkeys.json')

    graph.register_nodes([
        sample_nodes.DataInputNode,
        sample_nodes.ObjectInputNode,
        sample_nodes.ObjectOutputNode,
        sample_nodes.UniNode,
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()

    # t1 = QTimer()
    # t1.setInterval(5 * 1000)  # msec
    # t1.timeout.connect(functools.partial(counter, graph))
    # t1.start()

    app.exec_()
