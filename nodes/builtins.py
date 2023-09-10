import numpy

from NodeGraphQt import NodeBaseWidget
from NodeGraphQt.constants import NodePropWidgetEnum


from PySide2.QtGui import QPixmap
import PySide2.QtWidgets

from PySide2.QtGui import QImage
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from nodes import SampleNode
from . import entity


class BuiltinNode(SampleNode):

    def execute(self, sim):
        raise NotImplementedError("Override this")

class DoubleSpinBoxWidget(NodeBaseWidget):

    def __init__(self, parent=None, name='', label='', minimum=-999, maximum=+999):
        super(DoubleSpinBoxWidget, self).__init__(parent, name, label)
        
        box = PySide2.QtWidgets.QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(0)
        self.set_custom_widget(box)

        # connect up the signals & slots.
        self.wire_signals()

    def wire_signals(self):
        widget = self.get_custom_widget()
        widget.valueChanged.connect(self.on_value_changed)

    @property
    def type_(self):
        return 'DoubleSpinBoxWidget'

    def get_value(self):
        """
        Returns the widgets current text.

        Returns:
            str: current text.
        """
        return self.get_custom_widget().value()

    def set_value(self, text=''):
        """
        Sets the widgets current text.

        Args:
            text (str): new text.
        """
        value = int(text)
        if value != self.get_value():
            self.get_custom_widget().setValue(value)
            self.on_value_changed()

class LabelWidget(NodeBaseWidget):

    def __init__(self, parent=None, name='', label=''):
        super(LabelWidget, self).__init__(parent, name, label)
        
        label = PySide2.QtWidgets.QLabel()
        pixmap = QPixmap('C:\\Users\\kaizu\\Documents\\Python Scripts\\protocol_editor\\nodes\\cat.jpg')
        label.setPixmap(pixmap)
        self.set_custom_widget(label)

        # connect up the signals & slots.
        # self.wire_signals()

    @property
    def type_(self):
        return 'LabelWidget'

    def get_value(self):
        """
        Returns the widgets current text.

        Returns:
            str: current text.
        """
        return self.get_custom_widget().pixmap().toImage()

    def set_value(self, img=''):
        """
        Sets the widgets current text.

        Args:
            text (str): new text.
        """
        pixmap = QPixmap(img)
        self.get_custom_widget().setPixmap(pixmap)
        self.on_value_changed()

# class MyNodeLineEdit(NodeBaseWidget):

#     def __init__(self, parent=None, name='', label='', text=''):
#         super(MyNodeLineEdit, self).__init__(parent, name, label)
#         bg_color = ViewerEnum.BACKGROUND_COLOR.value
#         text_color = tuple(map(lambda i, j: i - j, (255, 255, 255),
#                                bg_color))
#         style_dict = {
#             'QLabel': {
#                 'background': 'rgba({0},{1},{2},20)'.format(*bg_color),
#                 'border': '1px solid rgb({0},{1},{2})'
#                           .format(*ViewerEnum.GRID_COLOR.value),
#                 'border-radius': '3px',
#                 'color': 'rgba({0},{1},{2},150)'.format(*text_color),
#             }
#         }
#         stylesheet = ''
#         for css_class, css in style_dict.items():
#             style = '{} {{\n'.format(css_class)
#             for elm_name, elm_val in css.items():
#                 style += '  {}:{};\n'.format(elm_name, elm_val)
#             style += '}\n'
#             stylesheet += style
#         ledit = QtWidgets.QLabel()
#         ledit.setStyleSheet(stylesheet)
#         ledit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#         ledit.setFixedWidth(300)
#         ledit.setText(text)
#         self.set_custom_widget(ledit)
#         # self.widget().setMaximumWidth(300)

#     @property
#     def type_(self):
#         return 'MyLineEditNodeWidget'

#     def get_value(self):
#         """
#         Returns the widgets current text.

#         Returns:
#             str: current text.
#         """
#         return str(self.get_custom_widget().text())

#     def set_value(self, text=''):
#         """
#         Sets the widgets current text.

#         Args:
#             text (str): new text.
#         """
#         if text != self.get_value():
#             self.get_custom_widget().setText(text)
#             self.on_value_changed()

# class IONode(BuiltinNode):

#     __identifier__ = "builtins"

#     NODE_NAME = "IONode"

#     def __init__(self):
#         super(IONode, self).__init__()

#         widget = MyNodeLineEdit(self.view, name="mywidget", text="Saluton, \nMondo!")
#         self.add_custom_widget(widget, tab='widgets')
#         # self.add_text_input("mywidget", tab="widgets")
#         self._add_input("in1", PortTraitsEnum.DATA)

#     def execute(self, input_tokens):
#         value = input_tokens["in1"]
#         # value = input_tokens["in1"]["value"]
#         self.set_property("mywidget", str(value), push_undo=False)
#         return {}

class GroupNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Group"

    def __init__(self):
        super(GroupNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self._add_input("in1", entity.Data)
        self._add_output("value", entity.Data)
        # self.set_io_mapping("value", "in1")
    
    def execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        return {"value": {"value": value, "traits": entity.Data}}
    
    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n > nports:
            for i in range(nports, n):
                self._add_input(f"in{i+1}", entity.Data)
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"in{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)

class IntegerNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Integer"

    def __init__(self):
        super(IntegerNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="value")
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self._add_output("value", entity.Integer)
        # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
    def execute(self, input_tokens):
        return {"value": {"value": int(self.get_property("value")), "traits": entity.Integer}}

class FullNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Full"

    def __init__(self):
        super(FullNode, self).__init__()
        self._add_input("size", entity.Integer)
        self._add_input("fill_value", entity.Integer, True)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        fill_value = input_tokens["fill_value"]["value"] if "fill_value" in input_tokens else 0
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.full(size, fill_value), "traits": entity.Array}}

class RangeNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Range"

    def __init__(self):
        super(RangeNode, self).__init__()
        self._add_input("start", entity.Integer, True)
        self._add_input("stop", entity.Integer)
        self._add_input("step", entity.Integer, True)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        start = input_tokens["start"]["value"] if "start" in input_tokens else 0
        stop = input_tokens["stop"]["value"]
        step = input_tokens["step"]["value"] if "step" in input_tokens else 1
        return {"value": {"value": numpy.arange(start, stop, step), "traits": entity.Array}}

class RepeatNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Repeat"

    def __init__(self):
        super(RepeatNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_input("repeats", entity.Integer)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        repeats = input_tokens["repeats"]["value"]
        return {"value": {"value": numpy.repeat(a, repeats), "traits": entity.Array}}

class TileNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Tile"

    def __init__(self):
        super(TileNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_input("reps", entity.Integer)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        reps = input_tokens["reps"]["value"]
        return {"value": {"value": numpy.tile(a, reps), "traits": entity.Array}}

class SumNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Sum"

    def __init__(self):
        super(SumNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_output("value", entity.Integer)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": numpy.sum(a), "traits": entity.Integer}}

class LengthNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Length"

    def __init__(self):
        super(LengthNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_output("value", entity.Integer)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": len(a), "traits": entity.Integer}}

class AddNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Add"

    def __init__(self):
        super(AddNode, self).__init__()
        self._add_input("a", entity.Data)
        self._add_input("b", entity.Data)
        self._add_output("value", entity.Data)
        self.set_io_mapping("value", "a")
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        return {"value": {"value": a + b, "traits": input_tokens["a"]["traits"]}}

class SubNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Sub"

    def __init__(self):
        super(SubNode, self).__init__()
        self._add_input("a", entity.Data)
        self._add_input("b", entity.Data)
        self._add_output("value", entity.Data)
        self.set_io_mapping("value", "a")
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        return {"value": {"value": a - b, "traits": input_tokens["a"]["traits"]}}

class DisplayNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Display"

    def __init__(self):
        super(DisplayNode, self).__init__()
        self._add_input("in1", entity.Data)
        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        return {}

class ScatterNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Scatter"

    def __init__(self):
        super(ScatterNode, self).__init__()

        widget = LabelWidget(self.view, name="plot")
        self.add_custom_widget(widget)

        self._add_input("x", entity.Array)
        self._add_input("y", entity.Array)
    
    def execute(self, input_tokens):
        x = input_tokens["x"]["value"]
        y = input_tokens["y"]["value"]

        fig = Figure(figsize=(2, 1.5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot(x, y, 'k.')
        fig.tight_layout()
        canvas.draw()
        
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        self.set_property("plot", img)
        return {}
        
# class SwitchNode(BuiltinNode):

#     __identifier__ = "builtins"

#     NODE_NAME = "SwtichNode"

#     def __init__(self):
#         super(SwitchNode, self).__init__()
#         # self.__doc = doc
#         traits = entity.Object  # ANY?
#         self._add_input("in1", traits)
#         self._add_input("cond1", entity.Data)
#         self._add_output("out1", traits)
#         self._add_output("out2", traits)
#         self._set_io_mapping("out1", "in1")
#         self._set_io_mapping("out2", "in1")
    
#     def execute(self, input_tokens):
#         dst = "out1" if input_tokens["cond1"]["value"] else "out2"
#         return {dst: input_tokens["in1"]}