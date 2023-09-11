from logging import getLogger

logger = getLogger(__name__)

import numpy

from NodeGraphQt.constants import NodePropWidgetEnum

from PySide2.QtGui import QImage
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')

from nodes import SampleNode
from . import entity
from .node_widgets import DoubleSpinBoxWidget, LabelWidget, PushButtonWidget

class BuiltinNode(SampleNode):

    def execute(self, sim):
        raise NotImplementedError("Override this")

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
        self._add_output("value", entity.Group)
        # self.set_io_mapping("value", "in1")
    
    def execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        return {"value": {"value": value, "traits": entity.Group}}
    
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

class FloatNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Float"

    def __init__(self):
        super(FloatNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="value", decimals=1)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self._add_output("value", entity.Float)
        # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
    def execute(self, input_tokens):
        return {"value": {"value": float(self.get_property("value")), "traits": entity.Float}}

class FullNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Full"

    def __init__(self):
        super(FullNode, self).__init__()
        self._add_input("size", entity.Integer)
        self._add_input("fill_value", entity.Real, True)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        fill_value = input_tokens["fill_value"]["value"] if "fill_value" in input_tokens else 0
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.full(size, fill_value, dtype=numpy.float64), "traits": entity.Array}}

class RangeNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Range"

    def __init__(self):
        super(RangeNode, self).__init__()
        self._add_input("start", entity.Real, True)
        self._add_input("stop", entity.Real)
        self._add_input("step", entity.Real, True)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        start = input_tokens["start"]["value"] if "start" in input_tokens else 0
        stop = input_tokens["stop"]["value"]
        step = input_tokens["step"]["value"] if "step" in input_tokens else 1
        return {"value": {"value": numpy.arange(start, stop, step, dtype=numpy.float64), "traits": entity.Array}}

class LinspaceNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Linspace"

    def __init__(self):
        super(LinspaceNode, self).__init__()
        self._add_input("start", entity.Real, True)
        self._add_input("stop", entity.Real, True)
        self._add_input("num", entity.Integer)
        self._add_output("value", entity.Array)
    
    def execute(self, input_tokens):
        start = input_tokens["start"]["value"] if "start" in input_tokens else 0
        stop = input_tokens["stop"]["value"] if "stop" in input_tokens else 1
        num = input_tokens["num"]["value"]
        return {"value": {"value": numpy.linspace(start, stop, num, dtype=numpy.float64), "traits": entity.Array}}

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

class AsArray96Node(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "AsArray96"

    def __init__(self):
        super(AsArray96Node, self).__init__()
        self._add_input("a", entity.Array)
        self._add_output("value", entity.Array96)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        value = numpy.zeros(96, dtype=numpy.float64)
        n = min(len(a), len(value))
        value[: n] = a[: n]
        return {"value": {"value": value, "traits": entity.Array96}}

class ArrayViewNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "ArrayView"

    def __init__(self):
        super(ArrayViewNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_output("value", entity.Array)

        self._add_input("start", entity.Integer, True)
        self._add_input("stop", entity.Integer, True)
        self._add_input("step", entity.Integer, True)
    
    def execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        start = input_tokens["start"]["value"] if "start" in input_tokens else None
        stop = input_tokens["stop"]["value"] if "stop" in input_tokens else None
        step = input_tokens["step"]["value"] if "step" in input_tokens else None
        value = a[slice(start, stop, step)].copy()
        return {"value": {"value": value, "traits": entity.Array}}

class SumNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Sum"

    def __init__(self):
        super(SumNode, self).__init__()
        self._add_input("a", entity.Array)
        self._add_output("value", entity.Float)
    
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

        self._add_input("scale", entity.Float, optional=True)
        self._add_input("x", entity.Array)
        self._add_input("y", entity.Group)
        # self._add_input("y", entity.Group | entity.Array)
    
    def execute(self, input_tokens):
        scale = input_tokens["scale"]["value"] if "scale" in input_tokens else 0.25
        x = input_tokens["x"]["value"]
        y = input_tokens["y"]["value"] if issubclass(input_tokens["y"]["traits"], entity.Group) else [input_tokens["y"]["value"]]

        fig = Figure(figsize=(8 * scale, 6 * scale))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        for yi in y:
            ax.plot(x, yi, '.')
        fig.tight_layout()
        canvas.draw()
        
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        self.set_property("plot", img)
        return {}

# class TriggerNode(BuiltinNode):

#     __identifier__ = "builtins"

#     NODE_NAME = "Trigger"

#     def __init__(self):
#         super(TriggerNode, self).__init__()

#         widget = PushButtonWidget(self.view, name="value")
#         # self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
#         self.add_custom_widget(widget)

#         self._add_output("value", entity.Integer)
#         # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
#     def execute(self, input_tokens):
#         return {"value": {"value": 0, "traits": entity.Trigger}}

# import fluent.experiments

class DispenseLiquid96WellsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "DispenseLiquid96Wells"

    def __init__(self):
        super(DispenseLiquid96WellsNode, self).__init__()

        self._add_input("in1", entity.Plate96)
        self._add_output("out1", entity.Plate96)

        self._add_input("channel", entity.Integer, optional=True)
        self._add_input("volume", entity.Array96)
    
    def execute(self, input_tokens):
        data = input_tokens["volume"]["value"].astype(int)
        channel = input_tokens["channel"]["value"] if "channel" in input_tokens else 0
        params = {'data': data, 'channel': channel}
        logger.info(f"DispenseLiquid96WellsNode execute with {str(params)}")
        # _, opts = fluent.experiments.dispense_liquid_96wells(**params)
        return {"out1": input_tokens["in1"].copy()}

class ReadAbsorbance3ColorsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "ReadAbsorbance3Colors"

    def __init__(self):
        super(ReadAbsorbance3ColorsNode, self).__init__()

        self._add_input("in1", entity.Plate96)
        self._add_output("out1", entity.Plate96)

        self._add_output("value", entity.Group)
    
    def execute(self, input_tokens):
        params = {}
        logger.info(f"ReadAbsorbance3ColorsNode execute")
        # (data, ), opts = fluent.experiments.read_absorbance_3colors(**params)
        data = numpy.zeros((3, 96), dtype=numpy.float64)
        return {"out1": input_tokens["in1"].copy(), "value": {"value": data, "traits": entity.Group}}

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