#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

import uuid
from collections import deque
from enum import IntEnum, auto

from Qt import QtGui, QtCore

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum
from NodeGraphQt.nodes.port_node import PortInputNode, PortOutputNode

from . import entity

logger = getLogger(__name__)


def draw_square_port(painter, rect, info):
    """
    Custom paint function for drawing a Square shaped port.

    Args:
        painter (QtGui.QPainter): painter object.
        rect (QtCore.QRectF): port rect used to describe parameters needed to draw.
        info (dict): information describing the ports current state.
            {
                'port_type': 'in',
                'color': (0, 0, 0),
                'border_color': (255, 255, 255),
                'multi_connection': False,
                'connected': False,
                'hovered': False,
            }
    """
    painter.save()

    # mouse over port color.
    if info['hovered']:
        color = QtGui.QColor(14, 45, 59)
        border_color = QtGui.QColor(136, 255, 35, 255)
    # port connected color.
    elif info['connected']:
        color = QtGui.QColor(195, 60, 60)
        border_color = QtGui.QColor(200, 130, 70)
    # default port color
    else:
        color = QtGui.QColor(*info['color'])
        border_color = QtGui.QColor(*info['border_color'])

    pen = QtGui.QPen(border_color, 1.8)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)

    painter.setPen(pen)
    painter.setBrush(color)
    painter.drawRect(rect)

    painter.restore()

def evaluate_traits(expression, inputs=None):
    inputs = inputs or {}
    params = entity.get_categories()
    # print(f"inputs -> {inputs}")
    # print(f"params -> {params}")
    locals = dict(inputs, **params)
    code = compile(expression, "<string>", "eval")
    is_static = all(name in params for name in code.co_names)
    assert all(name in locals for name in code.co_names)
    return eval(expression, {"__builtins__": {}}, locals), is_static

class NodeStatusEnum(IntEnum):
    READY = auto()
    ERROR = auto()
    WAITING = auto()
    RUNNING = auto()
    DONE = auto()

def ofp_node_base(cls):
    class _BasicNode(cls):

        def __init__(self, *args, **kwargs):
            super(_BasicNode, self).__init__(*args, **kwargs)

            self.__port_traits = {}
            self.__io_mapping = {}

        def is_optional_port(self, name):
            return self.__port_traits[name][1]

        def _add_input(self, name, traits, optional=False):
            assert not optional or entity.is_subclass_of(traits, entity.Data)
            if entity.is_subclass_of(traits, entity.Object):
                self.add_input(name, multi_input=False, painter_func=draw_square_port)
            elif entity.is_subclass_of(traits, entity.Data):
                self.add_input(name, color=(180, 80, 0), multi_input=False)
            else:
                assert False, 'Never reach here {}'.format(traits)
            self.__port_traits[name] = (traits, optional)

        def _add_output(self, name, traits):
            if entity.is_subclass_of(traits, entity.Object):
                self.add_output(name, multi_output=False, painter_func=draw_square_port)
            elif entity.is_subclass_of(traits, entity.Data):
                self.add_output(name, color=(180, 80, 0), multi_output=True)
            else:
                assert False, 'Never reach here {}'.format(traits)
            self.__port_traits[name] = (traits, False)

        def set_io_mapping(self, output_port_name, expression):
            assert output_port_name in self.outputs(), output_port_name
            # assert input_port_name in self.inputs(), input_port_name
            # input_traits = super(OFPNode, self).get_port_traits(input_port_name)
            # if not entity.is_subclass_of(input_traits, entity.Data):
            #     assert (
            #         output_port_name in self.__io_mapping
            #         or sum(1 for name in self.__io_mapping.values() if name == input_port_name) == 0
            #     ), "{} {} {}".format(output_port_name, input_port_name, input_traits)
            self._set_io_mapping(output_port_name, expression)

        def _set_io_mapping(self, output_port_name, expression):
            self.__io_mapping[output_port_name] = expression
        
        def has_io_mapping(self, name):
            return name in self.__io_mapping
        
        def delete_io_mapping(self, name):
            assert name in self.__io_mapping
            del self.__io_mapping[name]

        def io_mapping(self):
            return self.__io_mapping.copy()

        def _get_connected_traits(self, input_port):
            for connected in input_port.connected_ports():
                another = connected.node()
                if isinstance(another, PortInputNode):
                    parent_port = another.parent_port
                    another_traits = parent_port.node()._get_connected_traits(parent_port)
                    # print(f"{parent_port.node()} {another} {connected} {another_traits}")
                    return another_traits
                else:
                    return another.get_port_traits(connected.name())
            return self.__port_traits[input_port.name()][0]

        def get_port_traits(self, name):
            #XXX: This impl would be too slow. Use cache
            if name in self.__io_mapping:
                expression = self.__io_mapping[name]
                input_traits = {input.name(): self._get_connected_traits(input) for input in self.input_ports()}
                # print(f"{expression}: {input_traits}: {name}")
                port_traits = evaluate_traits(expression, input_traits)[0]
                return port_traits
            return self.__port_traits[name][0]
        
    return _BasicNode

class OFPNode(ofp_node_base(BaseNode)):

    def __init__(self):
        super(OFPNode, self).__init__()

        self.create_property('status', NodeStatusEnum.ERROR)

        self.__input_queue = deque()
        self.__output_queue = deque()

    def update_color(self):
        logger.info("update_color %s", self)

        value = self.get_node_status()
        if value == NodeStatusEnum.READY:
            self.set_color(13, 18, 23)
        elif value == NodeStatusEnum.ERROR:
            self.set_color(63, 18, 23)
        elif value == NodeStatusEnum.WAITING:
            self.set_color(63, 68, 73)
        elif value == NodeStatusEnum.RUNNING:
            self.set_color(13, 18, 73)
        elif value == NodeStatusEnum.DONE:
            self.set_color(13, 68, 23)
        else:
            assert False, "Never reach here {}".format(value)

    @property
    def output_queue(self):
        return self.__output_queue  # No longer protected
    
    def get_node_status(self):
        return NodeStatusEnum(self.get_property('status'))
    
    def set_node_status(self, newstatus):
        self.set_property('status', newstatus.value)
    
    def run(self, input_tokens):
        self.__input_queue.append(input_tokens.copy())
        if self.get_node_status() != NodeStatusEnum.RUNNING:
            self.set_node_status(NodeStatusEnum.RUNNING)

    def update_node_status(self):
        current_status = self.get_node_status()
        if current_status == NodeStatusEnum.RUNNING:
            assert len(self.__input_queue) > 0

            output_tokens = self.execute(self.__input_queue.popleft())
            # try:
            #     output_tokens = self.execute(self.__input_queue.popleft())
            # except:
            #     self.set_node_status(NodeStatusEnum.ERROR)

            self.__output_queue.append(output_tokens)

            if len(self.__input_queue) == 0:
                self.set_node_status(NodeStatusEnum.DONE)

    def execute(self, input_tokens):
        raise NotImplementedError()
        # assert all(input.name() in input_tokens for input in self.input_ports())
        # if all(self.has_property(output.name()) for output in self.output_ports()):
        #     #XXX: ast.literal_eval
        #     return {
        #         output.name(): {
        #             "value": eval(self.get_property(output.name()),{"__builtins__": None}, {}),
        #             "traits": self.get_port_traits(output.name())
        #         }
        #         for output in self.output_ports()}
        # else:
        #     raise NotImplementedError()

class ObjectOFPNode(OFPNode):

    def __init__(self):
        super(ObjectOFPNode, self).__init__()
        # self.add_text_input('station', tab='widgets')
        self.create_property('station', "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)

    def execute(self, input_tokens):
        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_port_traits(output.name())
            if output.name() in self.io_mapping():
                traits_str = self.io_mapping()[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                if entity.is_subclass_of(traits, entity.Data):
                    value = {'value': 100, 'traits': traits}
                elif entity.is_subclass_of(traits, entity.Object):
                    value = {'value': uuid.uuid4(), 'traits': traits}
                else:
                    assert False, "Never reach here {}".format(traits)
            output_tokens[output.name()] = value
        return output_tokens

class DataOFPNode(OFPNode):

    def __init__(self):
        super(DataOFPNode, self).__init__()
    
    def execute(self, input_tokens):
        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_port_traits(output.name())
            if output.name() in self.io_mapping():
                traits_str = self.io_mapping()[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                assert entity.is_subclass_of(traits, entity.Data)
                value = {'value': 100, 'traits': traits}
            output_tokens[output.name()] = value
        return output_tokens