#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import getLogger
logger = getLogger(__name__)

from NodeGraphQt import GroupNode
from NodeGraphQt.constants import NodePropWidgetEnum

from ofpeditor.nodes.ofp_node import evaluate_traits, NodeStatusEnum
from ofpeditor.nodes.ofp_node import ofp_node_base
from ofpeditor.nodes import entity
from ofpeditor.nodes.node_widgets import DoubleSpinBoxWidget


class OFPGroupNode(ofp_node_base(GroupNode)):

    def __init__(self):
        super(OFPGroupNode, self).__init__()

    def update_node_status(self):
        current_status = self.get_node_status()
        if current_status == NodeStatusEnum.ACTIVE:
            assert len(self._input_queue) > 0

            output_tokens = self.execute(self._input_queue.popleft())
            # try:
            #     output_tokens = self.execute(self._input_queue.popleft())
            # except:
            #     self.set_node_status(NodeStatusEnum.ERROR)

            self.output_queue.append(output_tokens)

            if len(self._input_queue) == 0:
                self.set_node_status(NodeStatusEnum.FINISHED)

    def run(self, input_tokens):
        super(OFPGroupNode, self).run(input_tokens)
    
    def execute(self, input_tokens):
        raise NotImplementedError()
    
class ForEachNode(OFPGroupNode):

    __identifier__ = 'builtins'

    NODE_NAME = 'ForEach'

    def __init__(self):
        super(ForEachNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("in1", entity.Data)
        self.add_output_w_traits("out1", entity.Data, expression="in1")

    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n > nports:
            for i in range(nports, n):
                self.add_input_w_traits(f"in{i+1}", entity.Data)
                self.add_output_w_traits(f"out{i+1}", entity.Data, expression=f"in{i+1}")
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

    def update_node_status(self):
        pass