#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

import copy
import functools
import signal
import inspect
import pathlib

from Qt import QtCore, QtWidgets
from Qt.QtCore import QTimer
from Qt.QtGui import QPalette, QColor

from NodeGraphQt import (
    NodeGraph,
    BaseNode,
    PropertiesBinWidget,
    # NodesTreeWidget,
    # NodesPaletteWidget
)
from NodeGraphQt.constants import NodePropWidgetEnum
from NodeGraphQt.nodes.port_node import PortInputNode, PortOutputNode

from ofpeditor.nodes.ofp_node import NodeStatusEnum, OFPNode, ObjectOFPNode, DataOFPNode, IONode, evaluate_traits
from ofpeditor.nodes.group import OFPGroupNode #, ForEachNode
from ofpeditor.nodes import entity, builtins, manipulate
from ofpeditor.simulator import Simulator

from ofpeditor.nodes.builtins import UnpackNode  #XXX

logger = getLogger(__name__)


def get_graph_id(graph):
    if graph.is_root:
        return id(graph)  #XXX
    return id(graph.node)  # SubGraph

def run_session(graph):
    logger.info(f"run_session {get_graph_id(graph)}")
    # print(f"run_session {get_graph_id(graph)}")
    
    for node in graph.all_nodes():
        logger.info('node {}'.format(node))
        if not isinstance(node, (OFPNode, OFPGroupNode)):
            logger.info('This is not an instance of OFPNode.')
            continue
            
        # node.set_node_status(NodeStatusEnum.ACTIVE)
        node.activate(force=True)

        # if isinstance(node, OFPGroupNode):
        #     subgraph = node.get_sub_graph()
        #     if subgraph is not None:
        #         #XXX
        #         run_session(subgraph)

def reset_session(graph):
    logger.info("reset_session")
    all_nodes = (node for node in graph.all_nodes() if isinstance(node, (OFPNode, OFPGroupNode)))
    for node in all_nodes:
        node.reset()
    verify_session(graph)

def verify_session(graph):
    logger.debug("verify_session")

    is_valid_graph = True

    for node in graph.all_nodes():
        if isinstance(node, (OFPNode, OFPGroupNode)):
            pass
        elif isinstance(node, PortInputNode):
            is_valid_graph = is_valid_graph and all(len(port.connected_ports()) > 0 for port in node.output_ports())
            continue
        elif isinstance(node, PortOutputNode):
            is_valid_graph = is_valid_graph and all(len(port.connected_ports()) > 0 for port in node.input_ports())
            continue
        else:
            continue

        is_valid_node = node.check()

        if is_valid_node and isinstance(node, OFPGroupNode):
            subgraph = node.get_sub_graph()
            if subgraph is not None:
                is_valid_subgraph = verify_session(subgraph)
                is_valid_node = is_valid_node and is_valid_subgraph
                if not is_valid_graph:
                    error_msg = "Invalid subgraph"
            else:
                error_msg = "No subgraph"
                is_valid_node = False

            if not is_valid_node:
                node.set_node_status(NodeStatusEnum.NOT_READY)
                node.message = error_msg

        if not is_valid_node:
            is_valid_graph = False

    # logger.info(graph.serialize_session())
    return is_valid_graph

loop_count = 0

def _main_loop(graph, sim):
    graph_id = get_graph_id(graph)
    all_nodes = [
        node for node in graph.all_nodes()
        if isinstance(node, (OFPNode, OFPGroupNode))
    ]
    if sim.num_tokens() == 0 and all(node.get_node_status() not in (NodeStatusEnum.ACTIVE, NodeStatusEnum.RUNNING, NodeStatusEnum.FINISHED) for node in all_nodes):
        return

    for node in all_nodes:
        node.update_node_status()

    for node in all_nodes:
        if node.get_node_status() == NodeStatusEnum.FINISHED:
            sim.fetch_token(node, graph_id)
            sim.transmit_token(node, graph_id)
            node.set_node_status(NodeStatusEnum.READY)  #XXX

    for node in all_nodes:
        if node.get_node_status() == NodeStatusEnum.READY:
            node.activate()

    for node in all_nodes:
        if (
            node.get_node_status() == NodeStatusEnum.ACTIVE
            and all(
                (node.is_free_port(input_port.name()) and len(input_port.connected_ports()) == 0)
                or sim.has_token((graph_id, node.name(), input_port.name()))
                for input_port in node.input_ports()
            )
        ):
            sim.run(node, graph_id)

def main_loop(graph):
    global loop_count
    loop_count += 1
    # logger.info(f"main_loop: loop_count={loop_count}, graph_id={get_graph_id(graph)}")

    _main_loop(graph, graph.simulator)

class MyModel:

    def __init__(self, doc):
        self.__property = {}

        self.__stations = doc.get('station', {})

    def set_property(self, name, value):
        assert value is True or value is False
        self.__property[name] = value

    def get_property(self, name):
        return self.__property.get(name, False)
    
    def has_property(self, name):
        return name in self.__property

    def list_stations(self):
        return list(self.__stations.keys())
    
    def allocate_station(self, node):
        if not isinstance(node, OFPNode):
            return ""
        class_name = node.__class__.__name__
        for key, value in self.__stations.items():
            if class_name in value and self.get_property(key):
                return key
        logger.info('allocate_station %s', class_name)
        return ""

def declare_node(name, doc):
    def base_node_class(doc):
        for _, traits_str in doc.get('input', {}).items():
            traits, _ = evaluate_traits(traits_str)
            if entity.is_object(traits):
                return ObjectOFPNode
        for _, traits_str in doc.get('output', {}).items():
            try:
                traits, _ = evaluate_traits(traits_str)
            except:
                pass  # io_mapping
            else:
                if entity.is_object(traits):
                    return ObjectOFPNode
        return DataOFPNode
    
    base_cls = base_node_class(doc)

    def __init__(self):
        base_cls.__init__(self)
        self.__doc = doc
        input_traits = {}
        params = entity.get_categories()
        for port_name, traits_str in doc.get('input', {}).items():
            traits, _ = evaluate_traits(traits_str)
            input_traits[port_name] = traits
            self.add_input_w_traits(port_name, traits)
        for port_name, traits_str in doc.get('output', {}).items():
            traits, is_static = evaluate_traits(traits_str, input_traits)
            self.add_output_w_traits(port_name, traits, expression=None if is_static else traits_str)
        for prop_name, value in doc.get('property', {}).items():
            assert not self.has_property(prop_name)
            self.create_property(prop_name, str(value), widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

    tab = doc.get("tab", "test")
    cls = type(name, (base_cls, ), {'__identifier__': f'nodes.{tab}', 'NODE_NAME': name, '__init__': __init__})
    return cls

class MyNodeGraph(NodeGraph):

    def __init__(self, simulator=None, doc=None):
        super(MyNodeGraph, self).__init__()

        self.node_created.connect(self._node_updated)
        self.nodes_deleted.connect(functools.partial(self._node_updated, deleted=True))
        self.port_connected.connect(self._pipe_updated)
        self.port_disconnected.connect(functools.partial(self._pipe_updated, disconnected=True))
        # self.port_connected.connect(self._updated)
        # self.port_disconnected.connect(self._updated)
        self.property_changed.connect(self._property_changed)

        self.simulator = simulator or Simulator()
        self.__mymodel = MyModel(doc.get('model', {}))

        # self.register_nodes([
        #     declare_node(key, value)
        #     for key, value in doc.get('node', {}).items()
        # ])

        for station in self.__mymodel.list_stations():
            self.set_property(station, True)

    def _pipe_updated(self, one, another, disconnected=False):
        logger.info(f"_pipe_updated {one} {another} {disconnected}")

        if isinstance(one.node(), UnpackNode):
            one.node().unpack_input_traits()
        if isinstance(another.node(), UnpackNode):
            another.node().unpack_input_traits()

        verify_session(self)

    def _node_updated(self, node, deleted=False):
        logger.info(f"_node_updated {node} {deleted}")
        if not deleted:
            if isinstance(node, GraphPropertyNode):
                # for name in node.property_names:
                #     if not self.__mymodel.has_property(name):
                #         self.set_property(name, True)
                node.update_property()
            elif isinstance(node, (OFPNode, OFPGroupNode)):
                node.update_color()
        verify_session(self)

    def _property_changed(self, node, name, value):
        logger.debug("property_changed %s %s %s", node, name, value)
        if isinstance(node, GraphPropertyNode) and self.__mymodel.has_property(name):
            self.set_property(name, value)
            verify_session(self)
        elif isinstance(node, IONode):
            verify_session(self)
            node.update_color()
        elif isinstance(node, (OFPNode, OFPGroupNode)) and name == "status":
            node.update_color()
            if value != NodeStatusEnum.FINISHED.value:
                self.simulator.reset_token(node, get_graph_id(self))  #XXX

    def set_property(self, name, value):
        self.__mymodel.set_property(name, value)

        for node in self.all_nodes():
            if isinstance(node, GraphPropertyNode):
                node.update_property(name)

    def get_property(self, name):
        return self.__mymodel.get_property(name)

    def allocate_station(self, node):
        return self.__mymodel.allocate_station(node)
    
    def expand_group_node(self, node):
        subgraph = super(MyNodeGraph, self).expand_group_node(node)
        if subgraph is None:
            return subgraph
        
        logger.info(f"Expand group node [{node.name()}]")

        subgraph.node_created.connect(self._node_created)
        subgraph.nodes_deleted.connect(self._updated)
        subgraph.port_connected.connect(self._updated)
        subgraph.port_disconnected.connect(self._updated)
        subgraph.property_changed.connect(self._property_changed)

        return subgraph

    def _register_builtin_nodes(self):
        pass  # do nothing
            
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
    import yaml 

    from logging import StreamHandler, Formatter, INFO
    handler = StreamHandler()
    handler.setLevel(INFO)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(INFO)
    
    getLogger('simulator').addHandler(handler)
    getLogger('simulator').setLevel(INFO)
    getLogger('nodes').addHandler(handler)
    getLogger('nodes').setLevel(INFO)
    
    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])

    app.setStyle("Fusion")
    mypalette = QPalette()
    # mypalette.setColor(QPalette.Text, QColor(192, 192, 192))
    mypalette.setColor(QPalette.Text, QColor(0, 0, 0))
    app.setPalette(mypalette)

    with open(pathlib.Path(__file__).parent / 'config.yaml') as f:
        doc = yaml.safe_load(f)

    # create graph controller.
    graph = MyNodeGraph(doc=doc)
    # graph.set_acyclic(False)

    # set up context menu for the node graph.

    import json, os
    context_menu_path = str(pathlib.Path(__file__).parent / 'hotkeys/hotkeys.json')
    with open(context_menu_path) as f:
        s = f.read()
        s = s.format(root=str(pathlib.Path(__file__).parent).replace(os.sep, '/'))
        data = json.loads(s)
    graph.set_context_menu("graph", data)
    # graph.set_context_menu_from_file(str(pathlib.Path(__file__).parent / 'hotkeys/hotkeys.json'))

    # graph.register_nodes([
    #     ConfigNode,
    #     ForEachNode,
    # ])

    for module in (builtins, manipulate):
        graph.register_nodes([
            nodecls
            for _, nodecls in inspect.getmembers(module, inspect.isclass)
            if issubclass(nodecls, builtins.BuiltinNode) and nodecls is not builtins.BuiltinNode
        ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()
    
    # graph.create_node("nodes.config.ConfigNode")
    
    # create a node properties bin widget.
    properties_bin = PropertiesBinWidget(node_graph=graph)
    properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # example show the node properties bin widget when a node is double clicked.
    def display_properties_bin(node):
        if not properties_bin.isVisible():
            properties_bin.show()

    # wire function to "node_double_clicked" signal.
    graph.node_double_clicked.connect(display_properties_bin)

    t1 = QTimer()
    # t1.setInterval(3 * 1000)  # msec
    t1.setInterval(0.5 * 1000)  # msec
    t1.timeout.connect(functools.partial(main_loop, graph))
    t1.start()

    app.exec_()
