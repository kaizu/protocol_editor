#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import getLogger

from nodes import evaluate_traits, NodeStatusEnum
from nodes import ofp_node_base
from nodes import entity

from NodeGraphQt import GroupNode

logger = getLogger(__name__)


class ForEachNode(ofp_node_base(GroupNode)):

    __identifier__ = 'builtins'

    NODE_NAME = 'ForEach'

    def __init__(self):
        super(ForEachNode, self).__init__()

        self.set_color(50, 8, 25)

        self._add_input('in1', entity.Object)
        self._add_output('out1', entity.Object)
        self.set_io_mapping('out1', 'in1')
        print(f"in -> {self.get_port_traits('in1')}")
        print(f"out -> {self.get_port_traits('out1')}")