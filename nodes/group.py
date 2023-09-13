#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

from nodes import evaluate_traits, NodeStatusEnum
from nodes import entity

from NodeGraphQt import GroupNode

logger = getLogger(__name__)


class ForEachNode(GroupNode):

    __identifier__ = 'builtins'

    NODE_NAME = 'ForEach'

    def __init__(self):
        super(ForEachNode, self).__init__()

        self.set_color(50, 8, 25)

        self.add_input('in')
        self.add_output('out')