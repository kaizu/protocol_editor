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

class BasicNode(BaseNode):
    """
    A base node for object flow programming.
    """

    NODE_NAME = 'BasicNode'

    def __init__(self, qgraphics_item=None):
        super(BasicNode, self).__init__(qgraphics_item)

    def add_data_input(self, name, multi_input=False):
        self.add_input(name, color=(180, 80, 0), multi_input=multi_input)

    def add_data_output(self, name, multi_output=True):
        self.add_output(name, color=(180, 80, 0), multi_output=multi_output)

    def add_object_input(self, name, multi_input=False):
        self.add_input(name, multi_input=multi_input, painter_func=draw_square_port)

    def add_object_output(self, name, multi_output=False):
        self.add_output(name, multi_output=multi_output, painter_func=draw_square_port)
