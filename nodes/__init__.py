#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

from enum import IntFlag, IntEnum, auto

from Qt import QtGui, QtCore, QtWidgets

from NodeGraphQt import BaseNode, NodeBaseWidget
from NodeGraphQt.constants import ViewerEnum

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

class BasicNode(BaseNode):
    """
    A base node for object flow programming.
    """

    NODE_NAME = 'BasicNode'

    def __init__(self, qgraphics_item=None):
        super(BasicNode, self).__init__(qgraphics_item)

        self.__port_traits = {}

    def get_port_traits(self, name):
        return self.__port_traits[name]
     
    def _add_input(self, name, traits):
        if entity.is_subclass_of(traits, entity.Object):
            self.add_input(name, multi_input=False, painter_func=draw_square_port)
        elif entity.is_subclass_of(traits, entity.Data):
            self.add_input(name, color=(180, 80, 0), multi_input=False)
        else:
            assert False, 'Never reach here {}'.format(traits)
        self.__port_traits[name] = traits

    def _add_output(self, name, traits):
        if entity.is_subclass_of(traits, entity.Object):
            self.add_output(name, multi_output=False, painter_func=draw_square_port)
        elif entity.is_subclass_of(traits, entity.Data):
            self.add_output(name, color=(180, 80, 0), multi_output=True)
        else:
            assert False, 'Never reach here {}'.format(traits)
        self.__port_traits[name] = traits

class NodeStatusEnum(IntEnum):
    READY = auto()
    ERROR = auto()
    WAITING = auto()
    RUNNING = auto()
    DONE = auto()
    
class SampleNode(BasicNode):
    """
    A node base class.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Sample'

    def __init__(self):
        super(SampleNode, self).__init__()

        self.__io_mapping = {}

        self.create_property('status', NodeStatusEnum.ERROR)
        self.add_text_input('_status', tab='widgets')

    def set_io_mapping(self, output_port_name, input_port_name):
        assert output_port_name in self.outputs(), output_port_name
        assert input_port_name in self.inputs(), input_port_name

        input_traits = super(SampleNode, self).get_port_traits(input_port_name)
        if not entity.is_subclass_of(input_traits, entity.Data):
            assert (
                output_port_name in self.__io_mapping
                or sum(1 for name in self.__io_mapping.values() if name == input_port_name) == 0
            ), "{} {} {}".format(output_port_name, input_port_name, input_traits)

        self._set_io_mapping(output_port_name, input_port_name)

    def _set_io_mapping(self, output_port_name, input_port_name):
        self.__io_mapping[output_port_name] = input_port_name
    
    def io_mapping(self):
        return self.__io_mapping.copy()

    def get_port_traits(self, name):
        #XXX: This impl would be too slow. Use cache
        if name in self.__io_mapping:
            input = self.get_input(self.__io_mapping[name])
            assert len(input.connected_ports()) <= 1
            for connected in input.connected_ports():
                another = connected.node()
                assert isinstance(another, SampleNode)
                return another.get_port_traits(connected.name())
        return super(SampleNode, self).get_port_traits(name)
    
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

        self.set_property('_status', NodeStatusEnum(value).name, push_undo=False)

class ObjectNode(SampleNode):

    def __init__(self):
        super(ObjectNode, self).__init__()
        self.add_text_input('station', tab='widgets')
        