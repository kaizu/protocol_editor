#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import numpy

from NodeGraphQt.constants import NodePropWidgetEnum

from PySide2.QtGui import QImage
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')

from ofpeditor.nodes.ofp_node import NodeStatusEnum, OFPNode, IONode, expand_input_tokens, traits_str
from ofpeditor.nodes import entity
from ofpeditor.nodes.node_widgets import DoubleSpinBoxWidget, LabelWidget, ValueStoreWidget


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
        
        def activate(self, force=False):
            if force:
                super(_InputNodeBase, self).activate(force=force)

    return _InputNodeBase
    
class GroupNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Group (Data)"

    def __init__(self):
        super(GroupNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("in1", entity.Any[entity.Data])
        self.add_output_w_traits("value", entity.Spread[entity.Any[entity.Data]], expression="Spread[in1]")

    def check(self):
        logger.debug("GroupNode: check")
        if not super(GroupNode, self).check():
            return False
        
        traits = self.get_input_port_traits('in1')
        for i in range(1, len(self.input_ports())):
            another_traits = self.get_input_port_traits(f'in{i+1}')
            if another_traits != traits:
                self.set_node_status(NodeStatusEnum.NOT_READY)
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
                self.add_input_w_traits(f"in{i+1}", entity.Any[entity.Data])
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"in{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)

class AsArrayNode(BuiltinNode):

    __identifier__ = "array"

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

    NODE_NAME = "Group (Object)"

    def __init__(self):
        super(GroupObjectNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="ninputs", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("in1", entity.Any[entity.Object])
        self.add_output_w_traits("value", entity.Spread[entity.Any[entity.Object]], expression="Spread[in1]")

    def check(self):
        if not super(GroupObjectNode, self).check():
            return False
        
        traits = self.get_input_port_traits('in1')
        for i in range(1, len(self.input_ports())):
            another_traits = self.get_input_port_traits(f'in{i+1}')
            if another_traits != traits:
                self.set_node_status(NodeStatusEnum.NOT_READY)
                self.message = f"Port [in{i+1}] has wrong traits [{traits_str(another_traits)}]. Port [in1] has [{traits_str(traits)}]"
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
                self.add_input_w_traits(f"in{i+1}", entity.Any[entity.Object])
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"in{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)
        self.check()

class IntegerNode(BuiltinNode):

    __identifier__ = "primitive"

    NODE_NAME = "Integer"

    def __init__(self):
        super(IntegerNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="value")
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.add_output_w_traits("value", entity.Integer)
        # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
    def _execute(self, input_tokens):
        return {"value": {"value": int(self.get_property("value")), "traits": entity.Integer}}

    # def activate(self, force=False):
    #     if force:
    #         super(IntegerNode, self).activate(force=force)

class FloatNode(BuiltinNode):

    __identifier__ = "primitive"

    NODE_NAME = "Float"

    def __init__(self):
        super(FloatNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, name="value", decimals=1)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.add_output_w_traits("value", entity.Float)
        # self.create_property("out1", "0", widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
    
    def _execute(self, input_tokens):
        return {"value": {"value": float(self.get_property("value")), "traits": entity.Float}}

    # def activate(self, force=False):
    #     if force:
    #         super(FloatNode, self).activate(force=force)

class LiquidClassNode(BuiltinNode):  # IONode

    __identifier__ = "primitive"

    NODE_NAME = "LiquidClass"

    def __init__(self):
        super(LiquidClassNode, self).__init__()

        items = ['Pure Water', 'Red Water', 'Blue Water']
        self.add_combo_menu("value", items=items)
        self.add_output_w_traits("value", entity.LiquidClass)
    
    def _execute(self, input_tokens):
        return {"value": {"value": self.get_property("value"), "traits": entity.LiquidClass}}
    
    def activate(self, force=False):
        if force:
            super(LiquidClassNode, self).activate(force=force)

class FullNode(BuiltinNode):

    __identifier__ = "array"

    NODE_NAME = "Full"

    def __init__(self):
        super(FullNode, self).__init__()
        self.add_input_w_traits("size", entity.Integer, expand=True)
        self.add_input_w_traits("fill_value", entity.Real, free=True, expand=True)
        self.add_output_w_traits("value", entity.Array[entity.Real], expand=True, expression="Array[fill_value]")

        self.set_default_value("fill_value", 0.0, entity.Float)

    def _execute(self, input_tokens):
        fill_value = input_tokens["fill_value"]["value"]
        size = input_tokens["size"]["value"]
        return {"value": {"value": numpy.full(size, fill_value, dtype=type(fill_value)), "traits": entity.Array[input_tokens["fill_value"]["traits"]]}}

class RangeNode(BuiltinNode):

    __identifier__ = "array"

    NODE_NAME = "Range"

    def __init__(self):
        super(RangeNode, self).__init__()
        self.add_input_w_traits("start", entity.Real, free=True, expand=True)
        self.add_input_w_traits("stop", entity.Real, expand=True)
        self.add_input_w_traits("step", entity.Real, free=True, expand=True)
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

    __identifier__ = "array"

    NODE_NAME = "Linspace"

    def __init__(self):
        super(LinspaceNode, self).__init__()
        self.add_input_w_traits("start", entity.Real, free=True, expand=True)
        self.add_input_w_traits("stop", entity.Real, free=True, expand=True)
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

    __identifier__ = "array"

    NODE_NAME = "RandomUniform"

    def __init__(self):
        super(RandomUniformNode, self).__init__()
        self.add_input_w_traits("low", entity.Real | entity.Array[entity.Real], free=True, expand=True)
        self.add_input_w_traits("high", entity.Real | entity.Array[entity.Real], free=True, expand=True)
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

    __identifier__ = "array"

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

    __identifier__ = "array"

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

    __identifier__ = "array"

    NODE_NAME = "Slice"

    def __init__(self):
        super(SliceNode, self).__init__()
        self.add_input_w_traits("a", entity.Array, expand=True)
        self.add_output_w_traits("value", entity.Array, expand=True, expression="a")

        self.add_input_w_traits("start", entity.Integer, free=True, expand=True)
        self.add_input_w_traits("stop", entity.Integer, free=True, expand=True)
        self.add_input_w_traits("step", entity.Integer, free=True, expand=True)

    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        start = input_tokens["start"]["value"] if "start" in input_tokens else None
        stop = input_tokens["stop"]["value"] if "stop" in input_tokens else None
        step = input_tokens["step"]["value"] if "step" in input_tokens else None
        value = a[slice(start, stop, step)].copy()
        return {"value": {"value": value, "traits": input_tokens["a"]["traits"]}}

class SumNode(BuiltinNode):

    __identifier__ = "array"

    NODE_NAME = "Sum"

    def __init__(self):
        super(SumNode, self).__init__()
        self.add_input_w_traits("a", entity.Array[entity.Real], expand=True)
        self.add_output_w_traits("value", entity.Real, expand=True, expression="first_arg(a)")
    
    def _execute(self, input_tokens):
        a = input_tokens["a"]["value"]
        return {"value": {"value": numpy.sum(a), "traits": entity.first_arg(input_tokens["a"]["traits"])}}

class LengthNode(BuiltinNode):

    __identifier__ = "array"

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

    __identifier__ = "inspect"

    NODE_NAME = "Display"

    def __init__(self):
        super(DisplayNode, self).__init__()
        self.add_input_w_traits("in1", entity.Any[entity.Data])
        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        # if self.is_optional():
        #     self.set_property("in1", str(input_tokens["in1"]))
        # else:
        #     self.set_property("in1", str({"in1": {"value": input_tokens["in1"]["value"], "traits": entity.first_arg(input_tokens["in1"]["traits"])}}))
        return {}

class ScatterNode(BuiltinNode):

    __identifier__ = "inspect"

    NODE_NAME = "Scatter"

    def __init__(self):
        super(ScatterNode, self).__init__()

        widget = LabelWidget(self.view, name="plot")
        self.add_custom_widget(widget)

        self.add_input_w_traits("scale", entity.Float, free=True)
        self.add_input_w_traits("x", entity.Array, expand=True)
        self.add_input_w_traits("y", entity.Array, expand=True)

        self.set_default_value("scale", 0.25, entity.Float)

    def execute(self, input_tokens):
        input_tokens = dict(self.default_value, **input_tokens)
        scale = input_tokens["scale"]["value"]

        fig = Figure(figsize=(8 * scale, 6 * scale))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        expandables = self.list_expandables({name: token["traits"] for name, token in input_tokens.items()})
        for _input_tokens in expand_input_tokens(input_tokens, expandables):
            x = _input_tokens["x"]["value"]
            y = _input_tokens["y"]["value"]
            ax.plot(x, y, '.')

        fig.tight_layout()
        canvas.draw()
        
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        self.get_widget("plot").set_image(img)
        return {}

class InspectNode(BuiltinNode):

    __identifier__ = "inspect"

    NODE_NAME = "Inspect"

    def __init__(self):
        super(InspectNode, self).__init__()
        self.add_input_w_traits("in1", entity.Any[entity.Object], optional=True)
        self.add_output_w_traits("out1", entity.Any[entity.Object], expression="in1", optional=True)

        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        if self.is_optional():
            self.set_property("in1", str(input_tokens["in1"]))
        else:
            self.set_property("in1", str({"in1": {"value": input_tokens["in1"]["value"], "traits": entity.first_arg(input_tokens["in1"]["traits"])}}))
        return {"out1": input_tokens["in1"].copy()}

class SwitchNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Swtitch"

    def __init__(self):
        super(SwitchNode, self).__init__()

        self.add_input_w_traits("in1", entity.Any[entity.Data])
        self.add_input_w_traits("in2", entity.Any[entity.Data])
        self.add_input_w_traits("cond", entity.Boolean, expand=True)  #TODO: entity.Array[entity.Boolean] -> Array[in1]
        self.add_output_w_traits("value", entity.Any[entity.Data], expand=True, expression="in1")

    def check(self):
        logger.debug("SwitchNode: check")
        if not super(SwitchNode, self).check():
            return False
        
        traits1 = self.get_input_port_traits('in1')
        traits2 = self.get_input_port_traits('in2')
        if traits1 != traits2:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = f"Port [in2] has wrong traits [{traits_str(traits2)}]. [{traits_str(traits1)}] expected"
            return False
        return True
    
    def _execute(self, input_tokens):
        cond = input_tokens["cond"]["value"]
        src = "in1" if cond else "in2"
        return {"value": input_tokens[src]}

class BooleanNode(BuiltinNode):

    __identifier__ = "logical"

    NODE_NAME = "Boolean"

    def __init__(self):
        super(BooleanNode, self).__init__()
        self.add_output_w_traits("out", entity.Boolean)

        self.add_checkbox("value", state=True)
    
    def _execute(self, input_tokens):
        value = self.get_property("value")
        return {"out": {"value": value, "traits": entity.Boolean}}

    # def activate(self, force=False):
    #     if force:
    #         super(BooleanNode, self).activate(force=force)

class LogicalNotNode(BuiltinNode):

    __identifier__ = "logical"

    NODE_NAME = "LogicalNot"

    def __init__(self):
        super(LogicalNotNode, self).__init__()
        self.add_input_w_traits("in1", entity.Boolean, expand=True)
        self.add_output_w_traits("out1", entity.Boolean, expand=True, expression="Boolean")
    
    def _execute(self, input_tokens):
        return {"out1": {"value": not input_tokens["in1"]["value"], "traits": entity.Boolean}}

class JustNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Just"

    def __init__(self):
        super(JustNode, self).__init__()

        self.add_input_w_traits("in1", entity.Object, expand=True, optional=True)
        self.add_output_w_traits("out1", entity.Optional[entity.Object], expand=True, expression="Optional[in1]")

    def _execute(self, input_tokens):
        # value = input_tokens["in1"]["value"]
        # traits = entity.Optional[input_tokens["in1"]["traits"]]
        # return {"out1": {"value": value, "traits": traits}}
        return {"out1": input_tokens["in1"].copy()}

class MergeNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Merge"

    def __init__(self):
        super(MergeNode, self).__init__()

        self.add_input_w_traits("in1", entity.Optional[entity.Object], expand=True)
        self.add_input_w_traits("in2", entity.Optional[entity.Object], expand=True)
        self.add_output_w_traits("out1", entity.Object, expand=True, expression="first_arg(in1)")

    def check(self):
        logger.debug("MergeNode: check")
        if not super(MergeNode, self).check():
            return False
        
        traits1 = self.get_input_port_traits('in1')
        traits2 = self.get_input_port_traits('in2')
        if traits1 != traits2:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = f"Port [in2] has wrong traits [{traits_str(traits2)}]. [{traits_str(traits1)}] expected"
            return False
        return True
    
    def _execute(self, input_tokens):
        value1 = input_tokens["in1"]["value"]
        value2 = input_tokens["in2"]["value"]
        traits = entity.first_arg(input_tokens["in1"]["traits"])

        if value1 is not None and value2 is None:
            value = value1
        elif value1 is None and value2 is not None:
            value = value2
        elif value1 is None and value2 is None:
            assert False, "Both value are None"
        else:
            # assert value1 is not None and value2 is not None
            assert False, f"Both value are not None: {value1} {value2}"

        return {"out1": {"value": value, "traits": traits}}

class BranchNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "Branch"

    def __init__(self):
        super(BranchNode, self).__init__()

        self.add_input_w_traits("in1", entity.Object, expand=True, optional=True)
        self.add_input_w_traits("cond", entity.Boolean, expand=True)
        self.add_output_w_traits("out1", entity.Optional[entity.Object], expand=True, expression="Optional[in1]")
        self.add_output_w_traits("out2", entity.Optional[entity.Object], expand=True, expression="Optional[in1]")

    def _execute(self, input_tokens):
        cond = input_tokens["cond"]["value"]
        value = input_tokens["in1"]["value"]
        # traits = entity.Optional[input_tokens["in1"]["traits"]]
        traits = input_tokens["in1"]["traits"]
        if cond:
            return {"out1": {"value": value, "traits": traits}, "out2": {"value": None, "traits": traits}}
        else:
            return {"out1": {"value": None, "traits": traits}, "out2": {"value": value, "traits": traits}}

class ClientNode(BuiltinNode):

    __identifier__ = "experimental"

    NODE_NAME = "Client (Object)"

    def __init__(self):
        super(ClientNode, self).__init__()

        self.add_text_input("address", "address", 'default')
        self.add_input_w_traits("in1", entity.Object, optional=True)
        self.add_output_w_traits("remote", entity.Object, optional=True, expression="in1", io=True)

        self.server = None

    def check(self):
        logger.debug("ClientNode: check")
        self.server = None

        if not super(ClientNode, self).check():
            return False
                
        if self.graph is None:
            self.message = ""
            return False

        for node in self.graph.all_nodes():
            if isinstance(node, ServerNode) and node.get_property("address") == self.get_property("address"):
                logger.info(f"{self} is connected to {node}.")
                self.server = node
                break
        else:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = f"No connection [{self.get_property('address')}]"
            return False
        return True

    def _execute(self, input_tokens):
        # return {"remote": {"value": input_tokens["in1"]["value"], "traits": entity.first_arg(input_tokens["in1"]["traits"])}}
        return {"remote": input_tokens["in1"].copy()}
    
    def process_token(self, output_token):
        if self.server is None:
            return None
        value = output_token["value"]
        traits = output_token["traits"]
        if entity.is_optional(traits):
            traits = entity.first_arg(traits)
            if value is None:
                return None
        return {"value": value, "traits": traits}

class ServerNode(BuiltinNode):

    __identifier__ = "experimental"

    NODE_NAME = "Server (Object)"

    def __init__(self):
        super(ServerNode, self).__init__()
        self.add_text_input("address", "address", 'default')
        self.add_input_w_traits("remote", entity.Object, io=True)
        self.add_output_w_traits("out1", entity.Object, expression="remote")

        self.clients = []

    def get_input_port_traits(self, name):
        assert name == "remote"
        if len(self.clients) > 0:
            traits = self.clients[0].get_output_port_traits(name)
            if entity.is_optional(traits):
                traits = entity.first_arg(traits)
            return traits
        return super(ServerNode, self).get_input_port_traits(name)

    def check(self):
        logger.debug("ServerNode: check")
        self.clients = []
        if not super(ServerNode, self).check():
            return False
        
        if self.graph is None:
            self.message = ""
            return False

        for node in self.graph.all_nodes():
            if isinstance(node, ClientNode) and node.get_property("address") == self.get_property("address"):
                self.clients.append(node)

        if len(self.clients) == 0:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = f"No connection [{self.get_property('address')}]"
            return False
        
        traits = (node.get_output_port_traits("remote") for node in self.clients)
        traits = set(x if not entity.is_optional(x) else entity.first_arg(x) for x in traits)  # strip
        if len(traits) != 1:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = f"Inconsistent types [{traits}]"
            return False

        return True

    def _execute(self, input_tokens):
        return {"out1": input_tokens["remote"]}

class PackNode(BuiltinNode):

    __identifier__ = "experimental"

    NODE_NAME = "Pack"

    def __init__(self):
        super(PackNode, self).__init__()

        widget = DoubleSpinBoxWidget(self.view, label="obj", name="ninputs1", minimum=1, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_ninputs1_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        widget = DoubleSpinBoxWidget(self.view, label="data", name="ninputs2", minimum=0, maximum=10)
        widget.get_custom_widget().valueChanged.connect(self.on_ninputs2_value_changed)
        self.add_custom_widget(widget, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("obj1", entity.Any[entity.Object])
        self.add_output_w_traits("value", entity.Any[entity.Object])

    def get_output_port_traits(self, name):
        assert name == "value"
        traits = entity.Struct[tuple(self.get_input_port_traits(port.name()) for port in self.input_ports())]
        # print(f"{traits}")
        return traits

    def _execute(self, input_tokens):
        value, traits = [], []
        for port in self.input_ports():
            value.append(input_tokens[port.name()]["value"])
            traits.append(input_tokens[port.name()]["traits"])
        return {"value": {"value": tuple(value), "traits": entity.Struct[tuple(traits)]}}
    
    def on_ninputs1_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len([port for port in self.input_ports() if port.name().startswith("obj")])
        if n > nports:
            for i in range(nports, n):
                self.add_input_w_traits(f"obj{i+1}", entity.Any[entity.Object])
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"obj{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)

    def on_ninputs2_value_changed(self, *args, **kwargs):
        n = int(args[0])
        nports = len([port for port in self.input_ports() if port.name().startswith("data")])
        if n > nports:
            for i in range(nports, n):
                self.add_input_w_traits(f"data{i+1}", entity.Any[entity.Data])
        elif n < nports:
            for i in range(nports, n, -1):
                name = f"data{i}"
                port = self.get_input(name)
                for another in port.connected_ports():
                    port.disconnect_from(another)
                self.delete_input(name)

class UnpackNode(BuiltinNode):

    __identifier__ = "experimental"

    NODE_NAME = "Unpack"

    def __init__(self):
        super(UnpackNode, self).__init__()

        widget = ValueStoreWidget(self.view, name="store", init=[], on_value_changed=self.on_value_changed)
        self.add_custom_widget(widget)
        
        self.set_port_deletion_allowed(True)

        self.add_input_w_traits("value", entity.Any[entity.Object])

    def on_value_changed(self, value, prev):
        #XXX: the custom widget set_value is former than port initialization in graph deserialize.
        # print(f"on_value_changed {value} {prev}")

        output_port_names = [port.name() for port in self.output_ports()]
        for name in output_port_names:
            port = self.get_output(name)
            for another in port.connected_ports():
                port.disconnect_from(another)
            self.delete_output(name)
        
        for i, is_object in enumerate(value):
            if is_object:
                self.add_output_w_traits(f"out{i+1}", entity.Any[entity.Object])
            else:
                self.add_output_w_traits(f"out{i+1}", entity.Any[entity.Data])
        
    def unpack_input_traits(self):
        traits = self.get_input_port_traits("value")
        # print(f"unpack_input_traits: {traits}")

        if not entity.is_acceptable(traits, entity._Struct):
            return
        
        if (
            len(traits.__args__) == len(self.output_ports())
            # and all(entity.is_object(x) == port.name().startswith("obj") for x, port in zip(traits.__args__, self.output_ports()))
        ):
            return

        value = []
        for i, output_port_traits in enumerate(traits.__args__):
            if entity.is_object(output_port_traits):
                value.append(True)
            elif entity.is_data(output_port_traits):
                value.append(False)
            else:
                assert False, f"Never reach here [{output_port_traits}]"

        self.set_property("store", value)
        self.check()

    def check(self):
        # print(f"check: {self._port_traits} {len(self.output_ports())}")

        if not super(UnpackNode, self).check():
            return False

        traits = self.get_input_port_traits("value")
        # print(f"check [{traits}]")
        # print(f"check [{len(traits.__args__)} == {len(self.output_ports())}]")

        is_valid = True
        if not entity.is_acceptable(traits, entity._Struct):
            error_msg = f"Wrong input type given [{traits}]. Struct is required"
            is_valid = False
        elif len(traits.__args__) != len(self.output_ports()):
            error_msg = f"The port number mismatches [{len(traits.__args__)} != {len(self.output_ports())}]"
            is_valid = False

        # for x, port in zip(traits.__args__, self.output_ports()):
        #     if entity.is_object(x) != port.name().startswith("obj"):
        #         self.msg = f"The port type mismatches [{port.name()}]"
        #         self.set_node_status(NodeStatusEnum.NOT_READY)
        #         return False

        if not is_valid:
            self.set_node_status(NodeStatusEnum.NOT_READY)
            self.message = error_msg
        elif self.get_node_status() == NodeStatusEnum.NOT_READY:
            self.set_node_status(NodeStatusEnum.READY)
            self.message = ''
        return is_valid

    def get_output_port_traits(self, name):
        traits = self.get_input_port_traits("value")
        # print(f"get_output_port_traits: {traits}")

        if entity.is_acceptable(traits, entity._Struct) and len(traits.__args__) == len(self.output_ports()):
            for output_port_traits, port in zip(traits.__args__, self.output_ports()):
                if port.name() == name:
                    return output_port_traits
        
        return super(UnpackNode, self).get_output_port_traits(name)

    def _execute(self, input_tokens):
        value = input_tokens["value"]["value"]
        traits = input_tokens["value"]["traits"]
        assert isinstance(value, tuple) and len(value) == len(traits.__args__)

        output_tokens = {}
        for i, (output_port_value, output_port_traits) in enumerate(zip(value, traits.__args__)):
            name = f"out{i+1}"
            output_tokens[name] = {"value": output_port_value, "traits": output_port_traits}
        return output_tokens