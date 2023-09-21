#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import uuid
import datetime
import numpy

from NodeGraphQt.constants import NodePropWidgetEnum

from nodes import entity
from nodes.builtins import BuiltinNode, input_node_base

from nodes.control import experiments


class ServeNode(input_node_base(entity.Labware, {"Plate (96-well)": entity.Plate96, "Tube (5ml)": entity.Tube5})):

    __identifier__ = "builtins"

    NODE_NAME = "Serve"

    def _execute(self, input_tokens):
        assert len(input_tokens) == 0, input_tokens
        value = experiments.serve_plate_96wells()
        return {"value": value}

class StoreLabwareNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "StoreLabware"

    def __init__(self):
        super(StoreLabwareNode, self).__init__()

        self.add_text_input("where", "where", '')
        self.add_input_w_traits("in1", entity.Optional[entity.Labware], expand=True)

        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        where = self.get_property("where")
        if input_tokens["in1"]["value"] is not None:  #XXX:
            if where == "":
                experiments.dispose_labware(input_tokens["in1"])
            else:
                experiments.store_labware(input_tokens["in1"], where)
        return {}
    
class StoreArtifactsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "StoreArtifacts"

    def __init__(self):
        super(StoreArtifactsNode, self).__init__()

        self.add_text_input("where", "where")
        self.add_input_w_traits("in1", entity.Any[entity.Data])  #FIXME

        self.create_property("in1", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
    
    def _execute(self, input_tokens):
        assert "in1" in input_tokens
        self.set_property("in1", str(input_tokens["in1"]))
        experiments.save_artifacts(input_tokens["in1"], self.get_property("where"))
        return {}

class DispenseLiquid96WellsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "DispenseLiquid96Wells"

    def __init__(self):
        super(DispenseLiquid96WellsNode, self).__init__()

        self.add_input_w_traits("in1", entity.Optional[entity.Plate96], expand=True)
        self.add_output_w_traits("out1", entity.Optional[entity.Plate96], expand=True, expression="in1")
        self.add_input_w_traits("channel", entity.Integer | entity.LiquidClass, free=True, expand=True)
        self.add_input_w_traits("volume", entity.Array[entity.Real], expand=True)

        self.set_default_value("channel", 0, entity.Integer)

        self.__channels = {'Pure Water': 0, 'Red Water': 1, 'Blue Water': 2}
    
    def _execute(self, input_tokens):
        if input_tokens["in1"]["value"] is None:  #XXX:
            return {"out1": input_tokens["in1"].copy()}

        data = input_tokens["volume"]["value"].astype(int).resize(96)

        if input_tokens["channel"]["traits"] == entity.LiquidClass:
            channel = self.__channels[input_tokens["channel"]["value"]]
        else:
            assert input_tokens["channel"]["traits"] == entity.Integer
            channel = input_tokens["channel"]["value"]
        params = {'data': data, 'channel': channel}
        # logger.info(f"DispenseLiquid96WellsNode execute with {str(params)}")
        # _, opts = fluent.experiments.dispense_liquid_96wells(**params)
        experiments.dispense_liquid_96wells(input_tokens["in1"], data, channel)
        return {"out1": input_tokens["in1"].copy()}

class ReadAbsorbance3ColorsNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "ReadAbsorbance3Colors"

    def __init__(self):
        super(ReadAbsorbance3ColorsNode, self).__init__()

        self.add_input_w_traits("in1", entity.Optional[entity.Plate96], expand=True)
        self.add_output_w_traits("out1", entity.Optional[entity.Plate96], expand=True, expression="in1")
        self.add_output_w_traits("value", entity.Optional[entity.Spread[entity.Array[entity.Float]]], expand=True, expression="Spread[Array[Float]]")
    
    def _execute(self, input_tokens):
        # logger.info(f"ReadAbsorbance3ColorsNode execute")
        if input_tokens["in1"]["value"] is None:  #XXX:
            data = None
        else:
            # (data, ), opts = fluent.experiments.read_absorbance_3colors(**params)
            data = experiments.read_absorbance_3colors(input_tokens["in1"])
        return {"out1": input_tokens["in1"].copy(), "value": {"value": data, "traits": entity.Optional[entity.Spread[entity.Array[entity.Float]]]}}
