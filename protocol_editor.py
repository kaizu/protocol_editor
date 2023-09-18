#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

import copy
import itertools
import functools
import signal
import inspect

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
from NodeGraphQt.constants import PortTypeEnum, NodePropWidgetEnum
from NodeGraphQt.nodes.port_node import PortInputNode, PortOutputNode

from nodes.ofp_node import NodeStatusEnum, OFPNode, ObjectOFPNode, DataOFPNode, IONode, evaluate_traits, traits_str
from nodes.group import OFPGroupNode, ForEachNode
import nodes.entity as entity
import nodes.builtins
from simulator import Simulator

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
        if node.get_node_status() != NodeStatusEnum.READY:
            logger.info(f'Status is not READY. {node.get_node_status()}')
            continue
            
        node.set_node_status(NodeStatusEnum.WAITING)

        # if isinstance(node, OFPGroupNode):
        #     subgraph = node.get_sub_graph()
        #     if subgraph is not None:
        #         #XXX
        #         run_session(subgraph)

def reset_session(graph):
    logger.info("reset_session")
    all_nodes = (node for node in graph.all_nodes() if isinstance(node, (OFPNode, OFPGroupNode)))
    for node in all_nodes:
        # if node.get_node_status() in (NodeStatusEnum.DONE, NodeStatusEnum.WAITING):
        #     node.set_node_status(NodeStatusEnum.READY)
        if node.get_node_status() in (NodeStatusEnum.DONE, NodeStatusEnum.WAITING, NodeStatusEnum.RUNNING):
            node.reset()
            node.set_node_status(NodeStatusEnum.READY)

def verify_session(graph):
    logger.info("verify_session")

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

        is_valid_node = True
        error_msg = ""  # error message

        # if isinstance(node, ObjectOFPNode):
        #     station = graph.allocate_station(node)
        #     node.set_property("station", station, push_undo=False)
        #     is_valid_node = is_valid_node and station != ""

        for port in itertools.chain(
            node.input_ports(), node.output_ports()
        ):
            port_traits = node.get_port_traits(port.name())

            connected_ports = port.connected_ports()
            if len(connected_ports) == 0:
                if node.is_optional_port(port.name()):
                    pass
                elif port.type_() == PortTypeEnum.OUT.value and entity.is_acceptable(port_traits, entity.Data):
                    pass
                else:
                    is_valid_node = False
                    error_msg = f"Port [{port.name()}] is disconnected"
                    break

            for another_port in connected_ports:
                another = another_port.node()

                if isinstance(another, PortInputNode):
                    parent_port = another.parent_port
                    another_traits = parent_port.node()._get_connected_traits(parent_port)
                elif isinstance(another, PortOutputNode):
                    parent_port = another.parent_port
                    another_traits = parent_port.node().get_port_traits(parent_port.name())
                else:
                    assert isinstance(another, (OFPNode, OFPGroupNode))
                    another_traits = another.get_port_traits(another_port.name())
                
                if (
                   (port.type_() == PortTypeEnum.IN.value and not entity.is_acceptable(another_traits, port_traits))
                    or (port.type_() == PortTypeEnum.OUT.value and not entity.is_acceptable(port_traits, another_traits))
                ):
                    logger.info("%s %s %s; %s %s %s", node.NODE_NAME, port.type_(), port_traits, another.NODE_NAME, another_port.type_(), another_traits)
                    is_valid_node = False
                    error_msg = f"Port [{port.name()}] traits mismatches. [{traits_str(port_traits)}] expected. [{traits_str(another_traits)}] given"
                    break

        if isinstance(node, OFPGroupNode):
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
            node.set_node_status(NodeStatusEnum.ERROR)
            node.message = error_msg
            is_valid_graph = False
        elif node.get_node_status() == NodeStatusEnum.ERROR:
            node.set_node_status(NodeStatusEnum.READY)
            node.message = ''

    # logger.info(graph.serialize_session())
    return is_valid_graph

loop_count = 0

def _main_loop(graph, sim):
    graph_id = get_graph_id(graph)
    all_nodes = [
        node for node in graph.all_nodes()
        if isinstance(node, (OFPNode, OFPGroupNode))
    ]

    for node in all_nodes:
        node.update_node_status()
    
    for node in all_nodes:
        if node.get_node_status() == NodeStatusEnum.DONE:
            sim.fetch_token(node, graph_id)
            sim.transmit_token(node, graph_id)

    for node in all_nodes:
        if (
            node.get_node_status() == NodeStatusEnum.WAITING
            and all(
                (node.is_optional_port(input_port.name()) and len(input_port.connected_ports()) == 0)
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
            if entity.is_acceptable(traits, entity.Object):
                return ObjectOFPNode
        for _, traits_str in doc.get('output', {}).items():
            try:
                traits, _ = evaluate_traits(traits_str)
            except:
                pass  # io_mapping
            else:
                if entity.is_acceptable(traits, entity.Object):
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
            self._add_input(port_name, traits)
        for port_name, traits_str in doc.get('output', {}).items():
            traits, is_static = evaluate_traits(traits_str, input_traits)
            self._add_output(port_name, traits, expression=None if is_static else traits_str)
        for prop_name, value in doc.get('property', {}).items():
            assert not self.has_property(prop_name)
            self.create_property(prop_name, str(value), widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

    tab = doc.get("tab", "test")
    cls = type(name, (base_cls, ), {'__identifier__': f'nodes.{tab}', 'NODE_NAME': name, '__init__': __init__})
    return cls

class MyNodeGraph(NodeGraph):

    def __init__(self, simulator=None, doc=None):
        super(MyNodeGraph, self).__init__()

        self.node_created.connect(self._node_created)
        self.nodes_deleted.connect(self._updated)
        self.port_connected.connect(self._updated)
        self.port_disconnected.connect(self._updated)
        self.property_changed.connect(self._property_changed)

        self.simulator = simulator or Simulator()
        self.__mymodel = MyModel(doc.get('model', {}))

        self.register_nodes([
            declare_node(key, value)
            for key, value in doc.get('node', {}).items()
        ])

        for station in self.__mymodel.list_stations():
            self.set_property(station, True)

    def _updated(self, *args, **kwargs):
        logger.info("updated %s %s", args, kwargs)
        verify_session(self)

    def _node_created(self, node):
        logger.info("node_created %s", node)
        if isinstance(node, GraphPropertyNode):
            # for name in node.property_names:
            #     if not self.__mymodel.has_property(name):
            #         self.set_property(name, True)
            node.update_property()
        elif isinstance(node, (OFPNode, OFPGroupNode)):
            node.update_color()
        verify_session(self)

    def _property_changed(self, node, name, value):
        logger.info("property_changed %s %s %s", node, name, value)
        if isinstance(node, GraphPropertyNode) and self.__mymodel.has_property(name):
            self.set_property(name, value)
            verify_session(self)
        elif isinstance(node, IONode):
            verify_session(self)
            node.update_color()
        elif isinstance(node, (OFPNode, OFPGroupNode)) and name == "status":
            node.update_color()
            if value != NodeStatusEnum.DONE.value:
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
    mypalette.setColor(QPalette.Text, QColor(192, 192, 192))
    app.setPalette(mypalette)

    with open('./config.yaml') as f:
        doc = yaml.safe_load(f)

    # create graph controller.
    graph = MyNodeGraph(doc=doc)
    # graph.set_acyclic(False)

    # set up context menu for the node graph.
    graph.set_context_menu_from_file('hotkeys/hotkeys.json')

    graph.register_nodes([
        ConfigNode,
        ForEachNode,
    ])

    graph.register_nodes([
        nodecls
        for _, nodecls in inspect.getmembers(nodes.builtins, inspect.isclass)
        if issubclass(nodecls, nodes.builtins.BuiltinNode) and nodecls is not nodes.builtins.BuiltinNode
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
