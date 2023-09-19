#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import uuid
import datetime
import numpy

from NodeGraphQt.constants import NodePropWidgetEnum

from PySide2.QtGui import QImage
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')

from nodes.ofp_node import NodeStatusEnum, OFPNode, IONode, expand_input_tokens, traits_str
from nodes import entity
from nodes.node_widgets import DoubleSpinBoxWidget, LabelWidget #  PushButtonWidget


class BuiltinNode(OFPNode):

    def _execute(self, sim):
        raise NotImplementedError("Override this")

def input_node_base(base, items):
    assert all(entity.is_acceptable(traits, base) for traits in items.values())

    class _InputNodeBase(BuiltinNode, IONode):

        OUTPUT_PORT_NAME = "value"
        BASE_ENTITY_TYPE = base
        ENTITY_TYPES = dict(items, **{'': base})

        def __init__(self):
            super(_InputNodeBase, self).__init__()

            assert all(entity.is_acceptable(traits, self.BASE_ENTITY_TYPE) for traits in self.ENTITY_TYPES.values()), f"{self.BASE_ENTITY_TYPE} {self.ENTITY_TYPES}"

            self.add_combo_menu(self.OUTPUT_PORT_NAME, items=sorted(self.ENTITY_TYPES))
            self.add_output_w_traits(self.OUTPUT_PORT_NAME, base)

        def set_property(self, name, value, push_undo=True):
            # logger.info(f"set_property: {self}, {value} {push_undo}")
            if name == self.OUTPUT_PORT_NAME:
                traits = self.ENTITY_TYPES.get(value, self.BASE_ENTITY_TYPE)
                self.update_port_traits(self.get_output(self.OUTPUT_PORT_NAME), traits)
            super(_InputNodeBase, self).set_property(name, value, push_undo)

    return _InputNodeBase
    
class GroupNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Group"

    def __init__(self):
        super(GroupNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("in1", entity.Data)
        self.add_output_w_traits("value", entity.Spread[entity.Data], expression="Spread[in1]")

    def check(self):
        logger.debug("GroupNode: check")
        if not super(GroupNode, self).check():
            return False
        
        traits = self.get_input_port_traits('in1')
        for i in range(1, len(self.input_ports())):
            another_traits = self.get_input_port_traits(f'in{i+1}')
            if another_traits != traits:
                self.set_node_status(NodeStatusEnum.ERROR)
                self.message = f"Port [in{i+1}] has wrong traits [{traits_str(another_traits)}]. [{traits_str(traits)}] expected"
                return False
        return True

    def _execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        traits = input_tokens["in1"]["traits"]  # The first element
        return {"value": {"value": value, "traits": entity.Spread[traits]}}
    
    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n > nports:
            for i in range(nports, n):
                self.add_input_w_traits(f"in{i+1}", entity.Data)
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"in{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)

class AsArrayNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "AsArray"

    def __init__(self):
        super(AsArrayNode, self).__init__()

        self.add_input_w_traits("in1", entity.Spread[entity.Data], expand=True)
        self.add_output_w_traits("out1", entity.Array[entity.Data], expand=True, expression="first_arg(in1)")

    def _execute(self, input_tokens):
        # print(input_tokens["in1"]["traits"])
        # print(entity.first_arg(input_tokens["in1"]["traits"]))
        # print(entity.Array[entity.first_arg(input_tokens["in1"]["traits"])])
        traits = entity.Array[entity.first_arg(input_tokens["in1"]["traits"])]
        return {"out1": {"value": numpy.asarray(input_tokens["in1"]["value"]), "traits": traits}}

class GroupObjectNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "GroupObject"

    def __init__(self):
        super(GroupObjectNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("in1", entity.Object)
        self.add_output_w_traits("value", entity.Spread[entity.Object], expression="Spread[in1]")

    def check(self):
        if not super(GroupObjectNode, self).check():
            return False
        
        traits = self.get_input_port_traits('in1')
        for i in range(1, len(self.input_ports())):
            another_traits = self.get_input_port_traits(f'in{i+1}')
            if another_traits != traits:
                self.set_node_status(NodeStatusEnum.ERROR)
                self.message = f"Port [in{i+1}] has wrong traits [{traits_str(another_traits)}]. [{traits_str(traits)}] expected"
                return False
        return True
    
    def _execute(self, input_tokens):
        ninputs = int(self.get_property("ninputs"))
        value = [input_tokens[f"in{i+1}"]["value"] for i in range(ninputs)]
        traits = input_tokens["in1"]["traits"]  # The first element
        return {"value": {"value": value, "traits": entity.Spread[traits]}}
    
    def on_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len(self.input_ports())
        if n == nports:
            return
        elif n > nports:
            for i in range(nports, n):
                self.add_input_w_traits(f"in{i+1}", entity.Object)
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"in{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)
        self.check()

class IntegerNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Integer"

    def __init__(self):
        super(IntegerNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="value")
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.add_output_w_traits("value", entity.Integer)
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

        self.add_output_w_traits("value", entity.Float)
        # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
    def _execute(self, input_tokens):
        return {"value": {"value": float(self.get_property("value")), "traits": entity.Float}}

class LiquidClassNode(BuiltinNode):  # IONode

    __identifier__ = "builtins"

    NODE_NAME = "LiquidClass"

    def __init__(self):
        super(LiquidClassNode, self).__init__()

        items = ['Pure Water', 'Red Water', 'Blue Water']
        self.add_combo_menu("value", items=items)
        self.add_output_w_traits("value", entity.LiquidClass)
    
    def _execute(self, input_tokens):
        return {"value": {"value": self.get_property("value"), "traits": entity.LiquidClass}}

class FullNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Full"

    def __init__(self):
        super(FullNode, self).__init__()
        self.add_input_w_traits("size", entity.Integer, expand=True)
        self.add_input_w_traits("fill_value", entity.Real, optional=True, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Real], expand=True, expression="Array[fill_value]")

        self.set_default_value("fill_value", 0.0, entity.Float)

    def _execute(self, input_tokens):
        fill_value = input_tokens["fill_value"]["value"]
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.full(size, fill_value, dtype=type(fill_value)), "traits": entity.Array[input_tokens["fill_value"]["traits"]]}}

class RangeNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Range"

    def __init__(self):
        super(RangeNode, self).__init__()
        self.add_input_w_traits("start", entity.Real, optional=True, expand=True)
        self.add_input_w_traits("stop", entity.Real, expand=True)
        self.add_input_w_traits("step", entity.Real, optional=True, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Real], expand=True, expression="Array[upper(start, stop, step)]")

        self.set_default_value("start", 0, entity.Integer)
        self.set_default_value("step", 1, entity.Integer)
    
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
        self.add_input_w_traits("start", entity.Real, optional=True, expand=True)
        self.add_input_w_traits("stop", entity.Real, optional=True, expand=True)
        self.add_input_w_traits("num", entity.Integer, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Float], expand=True, expression="Array[Float]")

        self.set_default_value("start", 0, entity.Float)
        self.set_default_value("stop", 1, entity.Float)
        
    def _execute(self, input_tokens):
        start = input_tokens["start"]["value"]
        stop = input_tokens["stop"]["value"]
        num = input_tokens["num"]["value"]
        return {"value": {"value": numpy.linspace(start, stop, num, dtype=numpy.float64), "traits": entity.Array[entity.Float]}}

class RandomUniformNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "RandomUniform"

    def __init__(self):
        super(RandomUniformNode, self).__init__()
        self.add_input_w_traits("low", entity.Real | entity.Array[entity.Real], optional=True, expand=True)
        self.add_input_w_traits("high", entity.Real | entity.Array[entity.Real], optional=True, expand=True)
        self.add_input_w_traits("size", entity.Integer, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Float], expand=True, expression="Array[Float]")

        self.set_default_value("low", 0.0, entity.Float)
        self.set_default_value("high", 1.0, entity.Float)
        
    def _execute(self, input_tokens):
        low = input_tokens["high"]["value"]
        high = input_tokens["low"]["value"]
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.random.uniform(low, high, size), "traits": entity.Array[entity.Float]}}

class RepeatNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Repeat"

    def __init__(self):
        super(RepeatNode, self).__init__()
        self.add_input_w_traits("a", entity.Array, expand=True)
        self.add_input_w_traits("repeats", entity.Integer, expand=True)
        self.add_output_w_traits("value", entity.Array, expand=True, expression="a")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        repeats = input_tokens["repeats"]["value"]
        return {"value": {"value": numpy.repeat(a, repeats), "traits": input_tokens["a"]["traits"]}}

class TileNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Tile"

    def __init__(self):
        super(TileNode, self).__init__()
        self.add_input_w_traits("a", entity.Array, expand=True)
        self.add_input_w_traits("reps", entity.Integer, expand=True)
        self.add_output_w_traits("value", entity.Array, expand=True, expression="a")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        reps = input_tokens["reps"]["value"]
        return {"value": {"value": numpy.tile(a, reps), "traits": input_tokens["a"]["traits"]}}

class SliceNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Slice"

    def __init__(self):
        super(SliceNode, self).__init__()
        self.add_input_w_traits("a", entity.Array, expand=True)
        self.add_output_w_traits("value", entity.Array, expand=True, expression="a")

        self.add_input_w_traits("start", entity.Integer, optional=True, expand=True)
        self.add_input_w_traits("stop", entity.Integer, optional=True, expand=True)
        self.add_input_w_traits("step", entity.Integer, optional=True, expand=True)

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
        self.add_input_w_traits("a", entity.Array[entity.Real], expand=True)
        self.add_output_w_traits("value", entity.Real, expand=True, expression="first_arg(a)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": numpy.sum(a), "traits": entity.first_arg(input_tokens["a"]["traits"])}}

class LengthNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Length"

    def __init__(self):
        super(LengthNode, self).__init__()
        self.add_input_w_traits("a", entity.Array, expand=True)
        self.add_output_w_traits("value", entity.Integer, expand=True, expression="Integer")  # why an expression is needed here?
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": len(a), "traits": entity.Integer}}

class AddNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Add"

    def __init__(self):
        super(AddNode, self).__init__()
        self.add_input_w_traits("a", entity.Array[entity.Real] | entity.Real, expand=True)
        self.add_input_w_traits("b", entity.Array[entity.Real] | entity.Real, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Real] | entity.Real, expand=True, expression="upper(a, b)")
    
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
        self.add_input_w_traits("a", entity.Array | entity.Real, expand=True)
        self.add_input_w_traits("b", entity.Array | entity.Real, expand=True)
        self.add_output_w_traits("value", entity.Array | entity.Real, expand=True, expression="upper(a, b)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        traits = entity.upper(input_tokens["a"]["traits"], input_tokens["b"]["traits"])
        return {"value": {"value": a - b, "traits": traits}}

class MulNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Mul"

    def __init__(self):
        super(MulNode, self).__init__()
        self.add_input_w_traits("a", entity.Array | entity.Real, expand=True)
        self.add_input_w_traits("b", entity.Array | entity.Real, expand=True)
        self.add_output_w_traits("value", entity.Array | entity.Real, expand=True, expression="upper(a, b)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        b = input_tokens["b"]["value"]
        traits = entity.upper(input_tokens["a"]["traits"], input_tokens["b"]["traits"])
        return {"value": {"value": a * b, "traits": traits}}

class DisplayNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Display"

    def __init__(self):
        super(DisplayNode, self).__init__()
        self.add_input_w_traits("in1", entity.Data)
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

        self.add_input_w_traits("scale", entity.Float, optional=True)
        self.add_input_w_traits("x", entity.Array, expand=True)
        self.add_input_w_traits("y", entity.Array, expand=True)

        self.set_default_value("scale", 0.25, entity.Float)

    def execute(self, input_tokens):
        input_tokens = dict(self.default_value, **input_tokens)
        scale = input_tokens["scale"]["value"]

        fig = Figure(figsize=(8 * scale, 6 * scale))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        for _input_tokens in expand_input_tokens(input_tokens, self.default_value):
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

#         self.add_output_w_traits("value", entity.Integer)
#         # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
#     def _execute(self, input_tokens):
#         return {"value": {"value": 0, "traits": entity.Trigger}}

# import fluent.experiments

class InspectNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Inspect"

    def __init__(self):
        super(InspectNode, self).__init__()
        self.add_input_w_traits("in1", entity.Object)
        self.add_output_w_traits("out1", entity.Object, expression="in1")

        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        return {"out1": input_tokens["in1"].copy()}

# class SwitchNode(BuiltinNode):

#     __identifier__ = "builtins"

#     NODE_NAME = "SwtichNode"

#     def __init__(self):
#         super(SwitchNode, self).__init__()
#         # self.__doc = doc
#         traits = entity.Object  # ANY?
#         self.add_input_w_traits("in1", traits)
#         self.add_input_w_traits("cond1", entity.Data)
#         self.add_output_w_traits("out1", traits, expression="in1")
#         self.add_output_w_traits("out2", traits, expression="in1")
    
#     def _execute(self, input_tokens):
#         dst = "out1" if input_tokens["cond1"]["value"] else "out2"
#         return {dst: input_tokens["in1"]}
