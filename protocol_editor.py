#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

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

from nodes import PortTraitsEnum, PortTraitsDict, NodeStatusEnum, SampleNode, ObjectNode
from nodes.builtins import SwitchNode
from simulator import Simulator

import pprint
pp = pprint.PrettyPrinter(indent=4)

logger = getLogger(__name__)


def run_session(graph):
    logger.info("run_session")
    graph._run()

def reset_session(graph):
    logger.info("reset_session")
    all_nodes = (node for node in graph.all_nodes() if isinstance(node, SampleNode))
    for node in all_nodes:
        if node.get_property('status') in (NodeStatusEnum.DONE.value, NodeStatusEnum.WAITING.value):
            node.set_property('status', NodeStatusEnum.READY.value)

def verify_session(graph):
    logger.info("verify_session")
    all_nodes = (node for node in graph.all_nodes() if isinstance(node, SampleNode))
    for node in all_nodes:
        is_valid = True

        if isinstance(node, ObjectNode):
            station = graph.allocate_station(node)
            node.set_property("station", station, push_undo=False)
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
                    logger.info("%s %s %s", port.type_(), port_traits, another_traits)
                    is_valid = False
                    break

        if not is_valid:
            node.set_property('status', NodeStatusEnum.ERROR.value, push_undo=False)
        elif node.get_property('status') == NodeStatusEnum.ERROR.value:
            node.set_property('status', NodeStatusEnum.READY.value, push_undo=False)

    # logger.info(graph.serialize_session())

loop_count = 0

def counter(graph):
    global loop_count
    loop_count += 1

    sim = graph.simulator
    all_nodes = [
        node for node in graph.all_nodes()
        if isinstance(node, SampleNode)
    ]
    running = [node for node in all_nodes if node.get_property('status') == NodeStatusEnum.RUNNING.value]
    waiting = [node for node in all_nodes if node.get_property('status') == NodeStatusEnum.WAITING.value]

    for node in running:
        new_status = sim.get_status(node)  # execute when done
        logger.info("counter %s", new_status)
        node.set_property('status', new_status.value)
    
    for node in all_nodes:
        if node.get_property('status') == NodeStatusEnum.DONE.value:
            sim.transmit_token(node)

    for node in waiting:
        if all(sim.has_token((node.name(), input_port.name())) for input_port in node.input_ports()):
            node.set_property('status', sim.run(node).value)

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
        if not isinstance(node, SampleNode):
            return ""
        class_name = node.__class__.__name__
        for key, value in self.__stations.items():
            if class_name in value and self.get_property(key):
                return key
        logger.info('allocate_station %s', class_name)
        return ""

def declare_node(name, doc):
    def base_node_class(doc):
        params = PortTraitsDict.copy()#{t.name: t for t in PortTraitsEnum}
        pp.pprint(params)
        for _, traits_str in doc.get('input', {}).items():
            pp.pprint(traits_str)
            pp.pprint(type(PortTraitsEnum))
            pp.pprint(list(PortTraitsEnum))
            traits = eval(traits_str, {}, params)
            if traits in PortTraitsEnum.OBJECT:
                return ObjectNode
        for _, traits_str in doc.get('output', {}).items():
            try:
                traits = eval(traits_str, {}, params)
            except:
                pass  # io_mapping
            else:
                if traits in PortTraitsEnum.OBJECT:
                    return ObjectNode
        return SampleNode
    
    base_cls = base_node_class(doc)

    def __init__(self):
        base_cls.__init__(self)
        self.__doc = doc
        input_traits = {}
        params = {t.name: t for t in PortTraitsEnum}
        for port_name, traits_str in doc.get('input', {}).items():
            traits = eval(traits_str, {}, params)
            input_traits[port_name] = traits
            self._add_input(port_name, traits)
        for port_name, traits_str in doc.get('output', {}).items():
            if traits_str in input_traits:
                traits = input_traits[traits_str]
                self._add_output(port_name, traits)
                self.set_io_mapping(port_name, traits_str)
            else:
                traits = eval(traits_str, {}, params)
                self._add_output(port_name, traits)

    cls = type(name, (base_cls, ), {'__identifier__': 'nodes.test', 'NODE_NAME': name, '__init__': __init__})
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
        elif isinstance(node, SampleNode):
            node.update_color()
        verify_session(self)

    def _property_changed(self, node, name, value):
        logger.info("property_changed %s %s %s", node, name, value)
        if isinstance(node, GraphPropertyNode) and self.__mymodel.has_property(name):
            self.set_property(name, value)
            verify_session(self)
        elif isinstance(node, SampleNode) and name == "status":
            node.update_color()
            if value != NodeStatusEnum.DONE.value:
                self.simulator.reset_token(node)

    def set_property(self, name, value):
        self.__mymodel.set_property(name, value)

        for node in self.all_nodes():
            if isinstance(node, GraphPropertyNode):
                node.update_property(name)

    def get_property(self, name):
        return self.__mymodel.get_property(name)

    def allocate_station(self, node):
        return self.__mymodel.allocate_station(node)
    
    def _run(self):
        session = {}

        for node in self.all_nodes():
            logger.info('node {}'.format(node))
            if not isinstance(node, SampleNode):
                logger.info('This is not an instance of SampleNode.')
                continue
            if node.get_property('status') != NodeStatusEnum.READY.value:
                logger.info('Status is not READY. {}'.format(node.get_property('status')))
                continue
            
            node.set_property('status', NodeStatusEnum.WAITING.value, push_undo=False)

            dependencies = []
            for port in node.input_ports():
                assert len(port.connected_ports()) <= 1
                for another_port in port.connected_ports():
                    dependencies.append(another_port.node().NODE_NAME)
            session[node.NODE_NAME] = dependencies

        logger.info(session)

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
        SwitchNode,
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)

    splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)  # 水平分割を作成
    new_widget = QtWidgets.QWidget()  # 新しいウィジェットを作成

    splitter.addWidget(new_widget)  # 新しいウィジェットを分割器に追加
    splitter.addWidget(graph_widget)  # 既存のウィジェットを分割器に追加

    splitter.show()  # 分割器（とその中のウィジェット）を表示

    #graph_widget.show()
    
    # graph.create_node("nodes.config.ConfigNode")
    
    # # create a node properties bin widget.
    # properties_bin = PropertiesBinWidget(node_graph=graph)
    # properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # # example show the node properties bin widget when a node is double clicked.
    # def display_properties_bin(node):
    #     if not properties_bin.isVisible():
    #         properties_bin.show()

    # # wire function to "node_double_clicked" signal.
    # graph.node_double_clicked.connect(display_properties_bin)
    
    t1 = QTimer()
    t1.setInterval(3 * 1000)  # msec
    t1.timeout.connect(functools.partial(counter, graph))
    t1.start()

    app.exec_()
