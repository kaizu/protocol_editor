#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

import os
import copy
import itertools
import functools
import signal

from Qt import QtCore, QtWidgets
from Qt.QtCore import QTimer
from Qt.QtGui import QPalette, QColor

from NodeGraphQt import (
    NodeGraph,
    BaseNode,
    # PropertiesBinWidget,
    # NodesTreeWidget,
    # NodesPaletteWidget
)
from NodeGraphQt.constants import PortTypeEnum

from nodes import PortTraitsEnum, sample_nodes

logger = getLogger(__name__)


def verify_session(graph):
    all_nodes = (node for node in graph.all_nodes() if isinstance(node, sample_nodes.SampleNode))
    for node in all_nodes:
        is_valid = True

        station = graph.get_station(node)
        node.set_property("station", station, push_undo=False)

        if any(node.get_port_traits(port.name()) in PortTraitsEnum.OBJECT for port in itertools.chain(node.input_ports(), node.output_ports())):
            is_valid = is_valid and station != ""

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

        self.node_created.connect(self._node_created)
        self.nodes_deleted.connect(self.dump)
        self.port_connected.connect(self.dump)
        self.port_disconnected.connect(self.dump)
        self.property_changed.connect(self._property_changed)

        self.__property = dict()

    def dump(self, *args, **kwargs):
        logger.info("dump %s %s", args, kwargs)
        verify_session(self)

    def _node_created(self, node):
        if isinstance(node, GraphPropertyNode):
            for name in node.property_names:
                if name not in self.__property:
                    self.set_property(name, True)
            node.update_property()
        verify_session(self)

    def _property_changed(self, node, name, value):
        if isinstance(node, GraphPropertyNode) and name in self.__property:
            self.set_property(name, value)
        # logger.info(self.__property)
        verify_session(self)

    def set_property(self, name, value):
        assert value is True or value is False
        self.__property[name] = value

        #XXX: Send signal to GraphPropertyNode
        for node in self.all_nodes():
            if isinstance(node, GraphPropertyNode):
                node.update_property(name)

    def get_property(self, name):
        return self.__property.get(name, False)

    def get_station(self, node):
        if not isinstance(node, sample_nodes.SampleNode):
            return ""
        if (
            isinstance(node, sample_nodes.ObjectInputNode)
            or isinstance(node, sample_nodes.ObjectOutputNode)
        ):
            if self.get_property("station1"):
                return "station1"
        if isinstance(node, sample_nodes.ObjectUniNode):
            if self.get_property("station2"):
                return "station2"
            if self.get_property("station3"):
                return "station3"
        if isinstance(node, sample_nodes.ObjectBiNode):
            if self.get_property("station4"):
                return "station4"
            if self.get_property("station5"):
                return "station5"
        if isinstance(node, sample_nodes.MeasurementNode):
            if self.get_property("station2"):
                return "station2"
        return ""

class GraphPropertyNode(BaseNode):

    def __init__(self, *property_names):
        super(GraphPropertyNode, self).__init__()

        self.__property_names = property_names
        for name in self.__property_names:
            value = False  # self.graph.get_property(name)
            self.add_checkbox(name, "", name, value)

    def update_property(self, name=None):
        if name is None:
            for name in self.__property_names:
                value = self.graph.get_property(name)
                self.set_property(name, value)
        else:
            value = self.graph.get_property(name)
            self.set_property(name, value)

    @property
    def property_names(self):
        return copy.copy(self.__property_names)

class ConfigNode(GraphPropertyNode):
    """
    A config node class.
    """

    # unique node identifier.
    __identifier__ = 'nodes.config'

    # initial default node name.
    NODE_NAME = 'Config'

    def __init__(self):
        super(ConfigNode, self).__init__(*(f"station{i+1}" for i in range(5)))


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
        sample_nodes.DataOutputNode,
        sample_nodes.ObjectOutputNode,
        sample_nodes.DataUniNode,
        sample_nodes.ObjectUniNode,
        sample_nodes.ObjectBiNode,
        sample_nodes.MeasurementNode,
        ConfigNode,
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()
    
    graph.create_node("nodes.config.ConfigNode")
    
    # # create a node properties bin widget.
    # properties_bin = PropertiesBinWidget(node_graph=graph)
    # properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # # example show the node properties bin widget when a node is double clicked.
    # def display_properties_bin(node):
    #     if not properties_bin.isVisible():
    #         properties_bin.show()

    # # wire function to "node_double_clicked" signal.
    # graph.node_double_clicked.connect(display_properties_bin)
    
    # t1 = QTimer()
    # t1.setInterval(5 * 1000)  # msec
    # t1.timeout.connect(functools.partial(counter, graph))
    # t1.start()

    app.exec_()
