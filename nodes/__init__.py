#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

from enum import IntEnum, auto

from Qt import QtGui, QtCore

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum

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

        def execute(self, input_tokens):
            raise NotImplementedError()
        
        def set_io_mapping(self, output_port_name, expression):
            assert output_port_name in self.outputs(), output_port_name
            # assert input_port_name in self.inputs(), input_port_name
            # input_traits = super(SampleNode, self).get_port_traits(input_port_name)
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
        
        def io_mapping(self):
            return self.__io_mapping.copy()

        def __get_connected_traits(self, input_port):
            for connected in input_port.connected_ports():
                another = connected.node()
                return another.get_port_traits(connected.name())
            return self.__port_traits[input_port.name()][0]

        def get_port_traits(self, name):
            #XXX: This impl would be too slow. Use cache
            if name in self.__io_mapping:
                expression = self.__io_mapping[name]
                input_traits = {input.name(): self.__get_connected_traits(input) for input in self.input_ports()}
                # print(f"{expression}: {input_traits}: {name}")
                port_traits = evaluate_traits(expression, input_traits)[0]
                return port_traits
            return self.__port_traits[name][0]
    return _BasicNode

class SampleNode(ofp_node_base(BaseNode)):
    """
    A node base class.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Sample'

    def __init__(self):
        super(SampleNode, self).__init__()

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

        # self.set_property('_status', NodeStatusEnum(value).name, push_undo=False)

    def execute(self, input_tokens):
        assert all(input.name() in input_tokens for input in self.input_ports())
        if all(self.has_property(output.name()) for output in self.output_ports()):
            #XXX: ast.literal_eval
            return {
                output.name(): {
                    "value": eval(self.get_property(output.name()),{"__builtins__": None}, {}),
                    "traits": self.get_port_traits(output.name())
                }
                for output in self.output_ports()}
        else:
            raise NotImplementedError()

class ObjectNode(SampleNode):

    def __init__(self):
        super(ObjectNode, self).__init__()
        # self.add_text_input('station', tab='widgets')
        self.create_property('station', "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        