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


class ObjectFlowProgrammingNode(BaseNode):
    """
    A base node for object flow programming.
    """

    NODE_NAME = 'ObjectFlowProgramming'

    def __init__(self, qgraphics_item=None):
        super(ObjectFlowProgrammingNode, self).__init__(qgraphics_item)

    def add_data_input(self, name, multi_input=False):
        self.add_input(name, color=(180, 80, 0), multi_input=multi_input)

    def add_data_output(self, name, multi_output=True):
        self.add_output(name, color=(180, 80, 0), multi_output=multi_output)

    def add_object_input(self, name, multi_input=False):
        self.add_input(name, multi_input=multi_input, painter_func=draw_square_port)

    def add_object_output(self, name, multi_output=False):
        self.add_output(name, multi_output=multi_output, painter_func=draw_square_port)

class SaveArtifactsNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SaveArtifacts'

    def __init__(self):
        super(SaveArtifactsNode, self).__init__()

        # create node inputs.
        self.add_data_input('in', multi_input=True)

        # create QLineEdit text input widget.
        self.add_text_input('artifact_name', 'Name', 'name', tab='widgets')


class DiscardNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'Discard'

    def __init__(self):
        super(DiscardNode, self).__init__()

        # create node outputs.
        self.add_object_input('in', multi_input=True)


class SupplyLiquidNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyLiquid'

    def __init__(self):
        super(SupplyLiquidNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['Pure Water', 'Red', 'Blue', 'Yellow']
        self.add_combo_menu('liquid_type', 'Type', items=items)


class NumberInputNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'NumberInput'

    def __init__(self):
        super(NumberInputNode, self).__init__()

        # create node outputs.
        self.add_data_output('value')

        # create the QComboBox menu.
        items = ['Integer', 'Float']
        self.add_combo_menu('value_type', 'Type', items=items)

        # create QLineEdit text input widget.
        self.add_text_input('value', 'Value', '0', tab='widgets')


class SupplyContainerSingleNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyContainerSingle'

    def __init__(self):
        super(SupplyContainerSingleNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['1.5mL Tube', '300uL Well']
        self.add_combo_menu('container_type', 'Type', items=items)


class SupplyContainerArrayNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyContainerArray'

    def __init__(self):
        super(SupplyContainerArrayNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['1.5mL Tube', '300uL Well']
        self.add_combo_menu('container_type', 'Type', items=items)

        # create QLineEdit text input widget.
        self.add_text_input('array_size', 'Size', '96', tab='widgets')


class DispenseLiquidNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'DispenseLiquid'

    def __init__(self):
        super(DispenseLiquidNode, self).__init__()

        # create node inputs.
        self.add_data_input('quantity')
        self.add_object_input('from')
        self.add_object_input('to')

        # create node outputs.
        self.add_object_output('from')
        self.add_object_output('to')

        # create the QComboBox menu.
        items = ['uL', 'mL']
        self.add_combo_menu('unit', 'Unit', items=items)


class MeasureAbsorbanceNode(ObjectFlowProgrammingNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'MeasureAbsorbance'

    def __init__(self):
        super(MeasureAbsorbanceNode, self).__init__()

        # create node inputs.
        self.add_object_input('in')

        # create node outputs.
        self.add_object_output('out')
        self.add_data_output('absorbance')
