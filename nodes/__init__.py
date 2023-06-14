from enum import IntFlag, IntEnum, auto

from Qt import QtGui, QtCore
from NodeGraphQt import BaseNode


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

class PortTraitsEnum(IntFlag):
    DATA = auto()
    TUBE = auto()
    PLATE = auto()
    OBJECT = TUBE | PLATE

class BasicNode(BaseNode):
    """
    A base node for object flow programming.
    """

    NODE_NAME = 'BasicNode'

    def __init__(self, qgraphics_item=None):
        super(BasicNode, self).__init__(qgraphics_item)

        self.__port_traits = dict()

    def get_port_traits(self, name):
        return PortTraitsEnum(self.__port_traits[name])
    
    def _add_input(self, name, traits, multi=False):
        if traits in PortTraitsEnum.OBJECT:
            self.add_input(name, multi_input=multi, painter_func=draw_square_port)
        elif traits in PortTraitsEnum.DATA:
            self.add_input(name, color=(180, 80, 0), multi_input=multi)
        else:
            assert False, 'Never reach here {}'.format(traits)
        self.__port_traits[name] = traits.value

    def _add_output(self, name, traits, multi=False):
        if traits in PortTraitsEnum.OBJECT:
            self.add_output(name, multi_output=multi, painter_func=draw_square_port)
        elif traits in PortTraitsEnum.DATA:
            self.add_output(name, color=(180, 80, 0), multi_output=multi)
        else:
            assert False, 'Never reach here {}'.format(traits)
        self.__port_traits[name] = traits.value

    def add_data_input(self, name, multi_input=False):
        self._add_input(name, PortTraitsEnum.DATA, multi_input)

    def add_data_output(self, name, multi_output=True):
        self._add_output(name, PortTraitsEnum.DATA, multi_output)

    def add_object_input(self, name, multi_input=False):
        self._add_input(name, PortTraitsEnum.OBJECT, multi_input)

    def add_object_output(self, name, multi_output=False):
        self._add_output(name, PortTraitsEnum.OBJECT, multi_output)

class NodeStatusEnum(IntEnum):
    READY = auto()
    ERROR = auto()
    WAITING = auto()
    
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
        self.create_property('status', NodeStatusEnum.ERROR)
        self.add_text_input('station', tab='widgets')
        self.add_text_input('_status', tab='widgets')

    def update_color(self):
        value = self.get_property('status')
        if value == NodeStatusEnum.READY.value:
            self.set_color(13, 18, 23)
        elif value == NodeStatusEnum.ERROR.value:
            self.set_color(180, 18, 23)
        elif value == NodeStatusEnum.WAITING.value:
            self.set_color(63, 68, 73)
        else:
            assert False, "Never reach here {}".format(value)

        self.set_property('_status', NodeStatusEnum(value).name)