#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import getLogger

from nodes import evaluate_traits, NodeStatusEnum
from nodes import ofp_node_base
from nodes import entity

from NodeGraphQt import GroupNode

from NodeGraphQt.constants import NodePropWidgetEnum
from nodes.node_widgets import DoubleSpinBoxWidget


logger = getLogger(__name__)


class OFPGroupNode(ofp_node_base(GroupNode)):

    def __init__(self):
        super(OFPGroupNode, self).__init__()

        self.create_property('status', NodeStatusEnum.ERROR)
        # self.add_text_input('_status', tab='widgets')

    def update_color(self):
        logger.info("update_color %s", self)

        value = self.get_property('status')
        if value == NodeStatusEnum.READY.value:
            self.set_color(13, 18, 23)
        elif value == NodeStatusEnum.ERROR.value:
            self.set_color(63, 18, 23)
        elif value == NodeStatusEnum.WAITING.value:
            self.set_color(63, 68, 73)
        elif value == NodeStatusEnum.RUNNING.value:
            self.set_color(13, 18, 73)
        elif value == NodeStatusEnum.DONE.value:
            self.set_color(13, 68, 23)
        else:
            assert False, "Never reach here {}".format(value)
        
        # subgraph = self.get_sub_graph()
        # if subgraph is not None:
        #     for node in subgraph.all_nodes():
        #         # print(f"{self.name()}: {node.name()}")
        #         pass

        # self.set_property('_status', NodeStatusEnum(value).name, push_undo=False)

class ForEachNode(OFPGroupNode):

    __identifier__ = 'builtins'

    NODE_NAME = 'ForEach'

    def __init__(self):
        super(ForEachNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self._add_input("in1", entity.Object)
        self._add_output("out1", entity.Object)
        self.set_io_mapping("out1", "in1")

    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n > nports:
            for i in range(nports, n):
                self._add_input(f"in{i+1}", entity.Object)
                self._add_output(f"out{i+1}", entity.Object)
                self.set_io_mapping(f"out{i+1}", f"in{i+1}")
        elif n < nports:
            for i in range(nports, n, -1):
                port = self.get_input(f"in{i}")
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(f"in{i}")

                port = self.get_output(f"out{i}")
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_output(f"out{i}")
                self.delete_io_mapping(f"out{i}")