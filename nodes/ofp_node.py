#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

import uuid
from collections import deque
from enum import IntEnum, auto

from Qt import QtGui, QtCore

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum
from NodeGraphQt.nodes.port_node import PortInputNode, PortOutputNode

from nodes import entity

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

def wrap_traits_if(original_type, entity_types):
    if any(entity.is_acceptable(entity_type, entity._Spread) for entity_type in entity_types):
        return wrap_traits(original_type)
    return original_type

def wrap_traits(entity_type):
    if entity.is_acceptable(entity_type, entity.Object):
        return entity.ObjectGroup[entity_type]
    elif entity.is_acceptable(entity_type, entity.Data):
        return entity.Group[entity_type]
    else:
        assert False, "Never reach here."

def unwrap_traits(entity_type):
    if entity.is_acceptable(entity_type, entity._Spread):
        return entity_type.__args__[0]
    return entity_type

def evaluate_traits(expression, inputs=None):
    inputs = inputs or {}
    params = entity.get_categories()
    # print(f"inputs -> {inputs}")
    # print(f"params -> {params}")
    locals = dict(inputs, **params)
    # locals.update({"wrap": wrap_traits_if, "unwrap": unwrap_traits})
    locals.update({"upper": entity.upper, "first_arg": entity.first_arg})
    code = compile(expression, "<string>", "eval")
    is_static = all(name in params for name in code.co_names)
    assert all(name in locals for name in code.co_names)
    return eval(expression, {"__builtins__": {}}, locals), is_static

class NodeStatusEnum(IntEnum):
    READY = auto()
    ERROR = auto()
    WAITING = auto()
    RUNNING = auto()
    DONE = auto()

def expand_input_tokens(input_tokens, defaults=None):
    defaults = defaults or {}
    input_tokens = dict(defaults, **input_tokens)
    group_input_tokens = {
        name: token for (name, token) in input_tokens.items()
        if entity.is_acceptable(token["traits"], entity._Spread)
    }
    assert all(token["traits"] not in (entity.Group, entity.ObjectGroup) for token in input_tokens.values()), f"Group cannot be bare [{input_tokens}]"

    if len(group_input_tokens) == 0:
        yield input_tokens
    else:
        max_length = max(len(token["value"]) for token in group_input_tokens.values())
        assert all(not entity.is_acceptable(token["traits"], entity.Object) for (name, token) in input_tokens.items() if name not in group_input_tokens), f"Object is not copyable [{input_tokens}]"
        for i in range(max_length):
            yield {
                name: (
                    dict(value=token["value"][i], traits=token["traits"].__args__[0])
                    if name in group_input_tokens
                    else dict(value=token["value"], traits=token["traits"])
                )
                for (name, token) in input_tokens.items()
            }

def trait_node_base(cls):
    class _TraitNodeBase(cls):

        def __init__(self, *args, **kwargs):
            super(_TraitNodeBase, self).__init__(*args, **kwargs)

            self.__port_traits = {}
            self.__io_mapping = {}
            self.__default_value = {}
            self.__expandables = []

        def is_optional_port(self, name):
            return self.__port_traits[name][1]

        def set_default_value(self, name, value, traits):
            assert name in self.__port_traits
            assert self.__port_traits[name][1]  # check if it's optional
            assert entity.is_acceptable(traits, self.__port_traits[name][0])
            self.__default_value[name] = dict(value=value, traits=traits)

        def get_default_value(self, name=None):
            if name is None:
                return self.__default_value  # not protected
            return self.__defalt_value.get(name, None)
        
        def _add_input(self, name, traits, *, optional=False, expand=False):
            if expand:
                traits = traits | wrap_traits(traits)
                self.__expandables.append(name)

            assert not optional or entity.is_subclass_of(traits, entity.Data)
            if entity.is_subclass_of(traits, entity.Object):
                self.add_input(name, multi_input=False, painter_func=draw_square_port)
            elif entity.is_subclass_of(traits, entity.Data):
                self.add_input(name, color=(180, 80, 0), multi_input=False)
            else:
                assert False, 'Never reach here {}'.format(traits)
            self.__port_traits[name] = (traits, optional)

        def _add_output(self, name, traits, *, expand=False):
            if expand:
                traits = traits | wrap_traits(traits)
                self.__expandables.append(name)

            if entity.is_subclass_of(traits, entity.Object):
                self.add_output(name, multi_output=False, painter_func=draw_square_port)
            elif entity.is_subclass_of(traits, entity.Data):
                self.add_output(name, color=(180, 80, 0), multi_output=True)
            else:
                assert False, 'Never reach here {}'.format(traits)
            self.__port_traits[name] = (traits, False)
        
        def delete_input(self, name):
            if name in self.__port_traits:
                del self.__port_traits[name]
            if name in self.__default_value:
                del self.__default_value[name]
            if name in self.__expandables:
                self.__expandables.remove(name)
            super(_TraitNodeBase, self).delete_input(name)
        
        def delete_output(self, name):
            if name in self.__port_traits:
                del self.__port_traits[name]
            if name in self.__io_mapping:
                del self.__io_mapping[name]
            if name in self.__expandables:
                self.__expandables.remove(name)
            super(_TraitNodeBase, self).delete_output(name)

        def set_io_mapping(self, output_port_name, expression):
            assert output_port_name in self.outputs(), output_port_name
            # assert input_port_name in self.inputs(), input_port_name
            # input_traits = super(OFPNode, self).get_port_traits(input_port_name)
            # if not entity.is_subclass_of(input_traits, entity.Data):
            #     assert (
            #         output_port_name in self.__io_mapping
            #         or sum(1 for name in self.__io_mapping.values() if name == input_port_name) == 0
            #     ), "{} {} {}".format(output_port_name, input_port_name, input_traits)
            self._set_io_mapping(output_port_name, expression)

        def _set_io_mapping(self, output_port_name, expression):
            self.__io_mapping[output_port_name] = expression
        
        def has_io_mapping(self, name):
            return name in self.__io_mapping
        
        def delete_io_mapping(self, name):
            assert name in self.__io_mapping
            del self.__io_mapping[name]

        def io_mapping(self):
            return self.__io_mapping.copy()

        def _get_connected_traits(self, input_port):
            for connected in input_port.connected_ports():
                another = connected.node()
                if isinstance(another, PortInputNode):
                    parent_port = another.parent_port
                    another_traits = parent_port.node()._get_connected_traits(parent_port)
                    # print(f"{parent_port.node()} {another} {connected} {another_traits}")
                    return another_traits
                else:
                    return another.get_port_traits(connected.name())
            else:
                if input_port.name() in self.__default_value:
                    return self.__default_value[input_port.name()]["traits"]
            return self.__port_traits[input_port.name()][0]
        
        def get_port_traits(self, name):
            #XXX: This impl would be too slow. Use cache
            if name in self.__io_mapping:
                expression = self.__io_mapping[name]
                input_traits = {input.name(): self._get_connected_traits(input) for input in self.input_ports()}
                # print(f"{expression}: {input_traits}: {name}")
                _input_traits = {name: unwrap_traits(traits) if name in self.__expandables else traits for name, traits in input_traits.items()}
                port_traits = evaluate_traits(expression, _input_traits)[0]
                return wrap_traits_if(port_traits, (input_traits[name] for name in self.__expandables if name in input_traits))
            return self.__port_traits[name][0]
        
        def _execute(self, input_tokens):  #XXX: rename this
            raise NotImplementedError()
        
        def execute(self, input_tokens):
            input_tokens = dict(self.__default_value, **input_tokens)

            if not any(entity.is_acceptable(input_tokens[name]["traits"], entity._Spread) for name in self.__expandables if name in input_tokens):
                # no expansion
                return self._execute(input_tokens)
            else:
                results = [
                    self._execute(_input_tokens)
                    for _input_tokens in expand_input_tokens(input_tokens)
                ]
                return {
                    output_port.name(): {
                        "value": [result[output_port.name()]["value"] for result in results],
                        "traits": wrap_traits(results[0][output_port.name()]["traits"])
                    }
                    for output_port in self.output_ports()
                }

    return _TraitNodeBase

def ofp_node_base(cls):
    class _OFPNodeBase(trait_node_base(cls)):
        def __init__(self):
            super(_OFPNodeBase, self).__init__()

            self.create_property('status', NodeStatusEnum.ERROR)

            self._input_queue = deque()
            self.output_queue = deque()

        def update_color(self):
            logger.info("update_color %s", self)

            value = self.get_node_status()
            if value == NodeStatusEnum.READY:
                self.set_color(13, 18, 23)
            elif value == NodeStatusEnum.ERROR:
                self.set_color(63, 18, 23)
            elif value == NodeStatusEnum.WAITING:
                self.set_color(63, 68, 73)
            elif value == NodeStatusEnum.RUNNING:
                self.set_color(13, 18, 73)
            elif value == NodeStatusEnum.DONE:
                self.set_color(13, 68, 23)
            else:
                assert False, "Never reach here {}".format(value)

        def get_node_status(self):
            return NodeStatusEnum(self.get_property('status'))
        
        def set_node_status(self, newstatus):
            logger.info(f"set_node_status {repr(newstatus)}")
            self.set_property('status', newstatus.value, push_undo=False)
        
        def run(self, input_tokens):
            self._input_queue.append(input_tokens.copy())
            if self.get_node_status() != NodeStatusEnum.RUNNING:
                self.set_node_status(NodeStatusEnum.RUNNING)
        
        def reset(self):
            self._input_queue.clear()
            self.output_queue.clear()

        def update_node_status(self):
            pass

        def _execute(self, input_tokens):
            raise NotImplementedError()
        
    return _OFPNodeBase

class OFPNode(ofp_node_base(BaseNode)):

    def __init__(self):
        super(OFPNode, self).__init__()

    def update_node_status(self):
        current_status = self.get_node_status()
        if current_status == NodeStatusEnum.RUNNING:
            assert len(self._input_queue) > 0

            output_tokens = self.execute(self._input_queue.popleft())
            # try:
            #     output_tokens = self.execute(self._input_queue.popleft())
            # except:
            #     self.set_node_status(NodeStatusEnum.ERROR)

            self.output_queue.append(output_tokens)

            if len(self._input_queue) == 0:
                self.set_node_status(NodeStatusEnum.DONE)

class ObjectOFPNode(OFPNode):

    def __init__(self):
        super(ObjectOFPNode, self).__init__()
        # self.add_text_input('station', tab='widgets')
        self.create_property('station', "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)

    def _execute(self, input_tokens):
        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_port_traits(output.name())
            if output.name() in self.io_mapping():
                traits_str = self.io_mapping()[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                if entity.is_subclass_of(traits, entity.Data):
                    value = {'value': 100, 'traits': traits}
                elif entity.is_subclass_of(traits, entity.Object):
                    value = {'value': uuid.uuid4(), 'traits': traits}
                else:
                    assert False, "Never reach here {}".format(traits)
            output_tokens[output.name()] = value
        return output_tokens

class DataOFPNode(OFPNode):

    def __init__(self):
        super(DataOFPNode, self).__init__()
    
    def _execute(self, input_tokens):
        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_port_traits(output.name())
            if output.name() in self.io_mapping():
                traits_str = self.io_mapping()[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                assert entity.is_subclass_of(traits, entity.Data)
                value = {'value': 100, 'traits': traits}
            output_tokens[output.name()] = value
        return output_tokens