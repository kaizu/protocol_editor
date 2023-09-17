from logging import getLogger

logger = getLogger(__name__)

import uuid
import numpy

from NodeGraphQt.constants import NodePropWidgetEnum

from PySide2.QtGui import QImage
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')

from nodes.ofp_node import OFPNode, IONode, expand_input_tokens
from nodes import entity
from nodes.node_widgets import DoubleSpinBoxWidget, LabelWidget, PushButtonWidget


class BuiltinNode(OFPNode):

    def _execute(self, sim):
        raise NotImplementedError("Override this")

def input_node_base(base, items):
    assert all(entity.is_acceptable(traits, base) for traits in items.values())

    class _InputNodeBase(BuiltinNode, IONode):

        BASE_ENTITY_TYPE = base
        ENTITY_TYPES = dict(items, **{'': base})

        def __init__(self):
            super(_InputNodeBase, self).__init__()

            self.add_combo_menu("value", items=sorted(self.ENTITY_TYPES))
            self._add_output("value", base)

        def set_property(self, name, value, push_undo=True):
            logger.info(f"set_property: {self}, {value} {push_undo}")
            if name == "value":
                traits = self.ENTITY_TYPES.get(value, self.BASE_ENTITY_TYPE)
                self._set_port_traits("value", traits, self._get_port_traits("value")[1])
            # print(self.get_port_traits("value"))
            super(_InputNodeBase, self).set_property(name, value, push_undo)

    return _InputNodeBase

class ServeNode(input_node_base(entity.Labware, {"Plate (96-well)": entity.Plate96, "Tube (5ml)": entity.Tube5})):

    __identifier__ = "builtins"

    NODE_NAME = "Serve"

    def _execute(self, input_tokens):
        assert len(input_tokens) == 0, input_tokens
        traits = self.get_port_traits("value")  # an output port
        assert entity.is_acceptable(traits, entity.Object), traits
        value = {'value': uuid.uuid4(), 'traits': traits}
        return {"value": value}

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
        self._add_output("value", entity.Group[entity.Data])
        self.set_io_mapping("value", "Group[in1]")

    def _execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        traits = input_tokens["in1"]["traits"]  # The first element
        return {"value": {"value": value, "traits": entity.Group[traits]}}
    
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

class ObjectGroupNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "ObjectGroup"

    def __init__(self):
        super(ObjectGroupNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self._add_input("in1", entity.Object)
        self._add_output("value", entity.ObjectGroup[entity.Object])
        self.set_io_mapping("value", "ObjectGroup[in1]")

    def _execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        traits = input_tokens["in1"]["traits"]  # The first element
        return {"value": {"value": value, "traits": entity.ObjectGroup[traits]}}
    
    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n > nports:
            for i in range(nports, n):
                self._add_input(f"in{i+1}", entity.Object)
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
    
    def _execute(self, input_tokens):
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
    
    def _execute(self, input_tokens):
        return {"value": {"value": float(self.get_property("value")), "traits": entity.Float}}
    
class FullNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Full"

    def __init__(self):
        super(FullNode, self).__init__()
        self._add_input("size", entity.Integer, expand=True)
        self._add_input("fill_value", entity.Real, optional=True, expand=True)
        self._add_output("value", entity.Array[entity.Real], expand=True)

        self.set_default_value("fill_value", 0.0, entity.Float)
        self.set_io_mapping("value", "Array[fill_value]")

    def _execute(self, input_tokens):
        fill_value = input_tokens["fill_value"]["value"]
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.full(size, fill_value, dtype=type(fill_value)), "traits": entity.Array[input_tokens["fill_value"]["traits"]]}}

class RangeNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Range"

    def __init__(self):
        super(RangeNode, self).__init__()
        self._add_input("start", entity.Real, optional=True, expand=True)
        self._add_input("stop", entity.Real, expand=True)
        self._add_input("step", entity.Real, optional=True, expand=True)
        self._add_output("value", entity.Array[entity.Real], expand=True)

        self.set_default_value("start", 0, entity.Integer)
        self.set_default_value("step", 1, entity.Integer)
        self.set_io_mapping("value", "Array[upper(start, stop, step)]")  #FIXME
    
    def _execute(self, input_tokens):
        start = input_tokens["start"]["value"]
        stop = input_tokens["stop"]["value"]
        step = input_tokens["step"]["value"]
        traits = entity.upper(input_tokens["start"]["traits"], input_tokens["stop"]["traits"], input_tokens["step"]["traits"])
        return {"value": {"value": numpy.arange(start, stop, step), "traits": entity.Array[traits]}}

class LinspaceNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Linspace"

    def __init__(self):
        super(LinspaceNode, self).__init__()
        self._add_input("start", entity.Real, optional=True, expand=True)
        self._add_input("stop", entity.Real, optional=True, expand=True)
        self._add_input("num", entity.Integer, expand=True)
        self._add_output("value", entity.Array[entity.Float], expand=True)

        self.set_default_value("start", 0, entity.Float)
        self.set_default_value("stop", 1, entity.Float)
        self.set_io_mapping("value", "Array[Float]")
        
    def _execute(self, input_tokens):
        start = input_tokens["start"]["value"]
        stop = input_tokens["stop"]["value"]
        num = input_tokens["num"]["value"]
        return {"value": {"value": numpy.linspace(start, stop, num, dtype=numpy.float64), "traits": entity.Array[entity.Float]}}

class RepeatNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Repeat"

    def __init__(self):
        super(RepeatNode, self).__init__()
        self._add_input("a", entity.Array, expand=True)
        self._add_input("repeats", entity.Integer, expand=True)
        self._add_output("value", entity.Array, expand=True)
        self.set_io_mapping("value", "a")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        repeats = input_tokens["repeats"]["value"]
        return {"value": {"value": numpy.repeat(a, repeats), "traits": input_tokens["a"]["traits"]}}

class TileNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Tile"

    def __init__(self):
        super(TileNode, self).__init__()
        self._add_input("a", entity.Array, expand=True)
        self._add_input("reps", entity.Integer, expand=True)
        self._add_output("value", entity.Array, expand=True)
        self.set_io_mapping("value", "a")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        reps = input_tokens["reps"]["value"]
        return {"value": {"value": numpy.tile(a, reps), "traits": input_tokens["a"]["traits"]}}

class SliceNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Slice"

    def __init__(self):
        super(SliceNode, self).__init__()
        self._add_input("a", entity.Array, expand=True)
        self._add_output("value", entity.Array, expand=True)
        self.set_io_mapping("value", "a")

        self._add_input("start", entity.Integer, optional=True, expand=True)
        self._add_input("stop", entity.Integer, optional=True, expand=True)
        self._add_input("step", entity.Integer, optional=True, expand=True)

    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        start = input_tokens["start"]["value"] if "start" in input_tokens else None
        stop = input_tokens["stop"]["value"] if "stop" in input_tokens else None
        step = input_tokens["step"]["value"] if "step" in input_tokens else None
        value = a[slice(start, stop, step)].copy()
        return {"value": {"value": value, "traits": input_tokens["a"]["traits"]}}

class SumNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Sum"

    def __init__(self):
        super(SumNode, self).__init__()
        self._add_input("a", entity.Array[entity.Real], expand=True)
        self._add_output("value", entity.Real, expand=True)
        self.set_io_mapping("value", "first_arg(a)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": numpy.sum(a), "traits": entity.first_arg(input_tokens["a"]["traits"])}}

class LengthNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Length"

    def __init__(self):
        super(LengthNode, self).__init__()
        self._add_input("a", entity.Array, expand=True)
        self._add_output("value", entity.Integer, expand=True)
        self.set_io_mapping("value", "Integer")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": len(a), "traits": entity.Integer}}

class AddNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Add"

    def __init__(self):
        super(AddNode, self).__init__()
        self._add_input("a", entity.Array[entity.Real] | entity.Real, expand=True)
        self._add_input("b", entity.Array[entity.Real] | entity.Real, expand=True)
        self._add_output("value", entity.Array[entity.Real] | entity.Real, expand=True)
        self.set_io_mapping("value", "upper(a, b)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        traits = entity.upper(input_tokens["a"]["traits"], input_tokens["b"]["traits"])
        return {"value": {"value": a + b, "traits": traits}}

class SubNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Sub"

    def __init__(self):
        super(SubNode, self).__init__()
        self._add_input("a", entity.Array | entity.Real, expand=True)
        self._add_input("b", entity.Array | entity.Real, expand=True)
        self._add_output("value", entity.Array | entity.Real, expand=True)
        self.set_io_mapping("value", "upper(a, b)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        traits = entity.upper(input_tokens["a"]["traits"], input_tokens["b"]["traits"])
        return {"value": {"value": a + b, "traits": traits}}

class DisplayNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Display"

    def __init__(self):
        super(DisplayNode, self).__init__()
        self._add_input("in1", entity.Data)
        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
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
        self._add_input("x", entity.Array, expand=True)
        self._add_input("y", entity.Array, expand=True)

        self.set_default_value("scale", 0.25, entity.Float)

    def execute(self, input_tokens):
        input_tokens = dict(self.get_default_value(), **input_tokens)
        scale = input_tokens["scale"]["value"]

        fig = Figure(figsize=(8 * scale, 6 * scale))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        for _input_tokens in expand_input_tokens(input_tokens, self.get_default_value()):
            x = _input_tokens["x"]["value"]
            y = _input_tokens["y"]["value"]
            ax.plot(x, y, '.')

        fig.tight_layout()
        canvas.draw()
        
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        self.get_widget("plot").set_image(img)
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
    
#     def _execute(self, input_tokens):
#         return {"value": {"value": 0, "traits": entity.Trigger}}

# import fluent.experiments

class InspectNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Inspect"

    def __init__(self):
        super(InspectNode, self).__init__()
        self._add_input("in1", entity.Object)
        self._add_output("out1", entity.Object)
        self.set_io_mapping("out1", "in1")

        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        return {"out1": input_tokens["in1"].copy()}

class DispenseLiquid96WellsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "DispenseLiquid96Wells"

    def __init__(self):
        super(DispenseLiquid96WellsNode, self).__init__()

        self._add_input("in1", entity.Plate96, expand=True)
        self._add_output("out1", entity.Plate96, expand=True)
        self._add_input("channel", entity.Integer, optional=True, expand=True)
        self._add_input("volume", entity.Array[entity.Real], expand=True)
        self.set_io_mapping("out1", "in1")

        self.set_default_value("channel", 0, entity.Integer)
    
    def _execute(self, input_tokens):
        data = input_tokens["volume"]["value"].astype(int).resize(96)
        channel = input_tokens["channel"]["value"]
        params = {'data': data, 'channel': channel}
        logger.info(f"DispenseLiquid96WellsNode execute with {str(params)}")
        # _, opts = fluent.experiments.dispense_liquid_96wells(**params)
        return {"out1": input_tokens["in1"].copy()}

class ReadAbsorbance3ColorsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "ReadAbsorbance3Colors"

    def __init__(self):
        super(ReadAbsorbance3ColorsNode, self).__init__()

        self._add_input("in1", entity.Plate96, expand=True)
        self._add_output("out1", entity.Plate96, expand=True)
        self._add_output("value", entity.Group[entity.Array[entity.Float]], expand=True)

        self.set_io_mapping("out1", "in1")
    
    def _execute(self, input_tokens):
        params = {}
        logger.info(f"ReadAbsorbance3ColorsNode execute")
        # (data, ), opts = fluent.experiments.read_absorbance_3colors(**params)
        data = numpy.zeros((3, 96), dtype=numpy.float64)
        return {"out1": input_tokens["in1"].copy(), "value": {"value": data, "traits": entity.Group[entity.Array[entity.Float]]}}

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
    
#     def _execute(self, input_tokens):
#         dst = "out1" if input_tokens["cond1"]["value"] else "out2"
#         return {dst: input_tokens["in1"]}
