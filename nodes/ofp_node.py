#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import uuid
from collections import deque
from enum import IntEnum, auto
import dataclasses

from Qt import QtGui, QtCore

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum
from NodeGraphQt.nodes.port_node import PortInputNode

from nodes import entity


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

def traits_str(traits):
    text = str(traits)
    text = text.replace('typing.', '').replace('nodes.entity.', '')
    return text

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
        assert False, f"Never reach here [{entity_type}]"

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
        # assert all(not entity.is_acceptable(token["traits"], entity.Object) for (name, token) in input_tokens.items() if name not in group_input_tokens), f"Object is not copyable [{input_tokens}]"
        for i in range(max_length):
            yield {
                name: (
                    dict(value=token["value"][i], traits=token["traits"].__args__[0])
                    if name in group_input_tokens
                    else dict(value=token["value"], traits=token["traits"])
                )
                for (name, token) in input_tokens.items()
            }

class IONode: pass

@dataclasses.dataclass
class PortTraits:
    traits: type = entity.Any
    optional: bool = False
    expand: bool = False

def trait_node_base(cls):
    class _TraitNodeBase(cls):

        def __init__(self, *args, **kwargs):
            super(_TraitNodeBase, self).__init__(*args, **kwargs)

            self.__port_traits = {}
            self.__io_mapping = {}
            self.__default_value = {}

            self.create_property("message", "", widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)

        def get_port_traits_def(self, name):
            if name in self.__port_traits:
                return self.__port_traits[name].traits
            return entity.Any

        def get_input_port_traits(self, name):
            input_port = self.get_input(name)

            for connected in input_port.connected_ports():
                another = connected.node()
                if isinstance(another, PortInputNode):
                    parent_port = another.parent_port
                    another_traits = parent_port.node().get_input_port_traits(parent_port)
                    logger.debug(f"get_input_port_traits: {parent_port.node()} {another} {connected} {another_traits}")
                    return another_traits
                else:
                    return another.get_output_port_traits(connected.name())
            else:
                if name in self.__default_value:
                    return self.__default_value[name]["traits"]
            return self.get_port_traits_def(name)

        def get_output_port_traits(self, name):
            #XXX: This impl would be too slow. Use cache
            if name in self.__io_mapping:
                expression = self.__io_mapping[name]
                input_traits = {input.name(): self.get_input_port_traits(input.name()) for input in self.input_ports()}
                # print(f"{expression}: {input_traits}: {name}")
                _input_traits = {name: unwrap_traits(traits) if self.is_expandable_port(name) else traits for name, traits in input_traits.items()}
                port_traits = evaluate_traits(expression, _input_traits)[0]
                return wrap_traits_if(port_traits, (input_traits[name] for name in self.expandable_ports if name in input_traits))
            return self.get_port_traits_def(name)

        def set_port_traits(self, port, port_traits):
            assert isinstance(port_traits, PortTraits)
            self.__port_traits[port.name()] = port_traits

            port_item = port.view
            conn_type = 'multi' if port_item.multi_connection else 'single'
            tooltip = '{}: ({})'.format(port_item.name, conn_type)
            if port_item._locked:
                tooltip += ' (L)'
            tooltip += f" [{traits_str(port_traits.traits)}]"
            port_item.setToolTip(tooltip)

        def update_port_traits(self, port, traits):
            assert issubclass(traits, entity.Entity)
            params = dataclasses.asdict(self.__port_traits[port.name()])
            params["traits"] = traits
            port_traits = PortTraits(**params)
            self.set_port_traits(port, port_traits)

        def is_optional_port(self, name):
            return self.__port_traits[name].optional

        def is_expandable_port(self, name):
            return self.__port_traits[name].expand
        
        @property
        def expandable_ports(self):
            for name, port_traits in self.__port_traits.items():
                if port_traits.expand:
                    yield name

        def add_input(self, name='input', multi_input=False, display_name=True, color=None, locked=False, painter_func=None):
            traits = self.get_port_traits_def(name)
            if entity.is_acceptable(traits, entity.Object):
                multi_input = False
                painter_func = painter_func or draw_square_port
            elif entity.is_acceptable(traits, entity.Data):
                multi_input = True
                color = color or (180, 80, 0)
            return super(_TraitNodeBase, self).add_input(name, multi_input, display_name, color, locked, painter_func)

        def add_output(self, name='input', multi_output=False, display_name=True, color=None, locked=False, painter_func=None):
            traits = self.get_port_traits_def(name)
            if entity.is_acceptable(traits, entity.Object):
                multi_output = False
                painter_func = painter_func or draw_square_port
            elif entity.is_acceptable(traits, entity.Data):
                multi_output = True
                color = color or (180, 80, 0)
            return super(_TraitNodeBase, self).add_output(name, multi_output, display_name, color, locked, painter_func)

        def delete_input(self, name):
            if name in self.__port_traits:
                del self.__port_traits[name]
            if name in self.__default_value:
                del self.__default_value[name]
            super(_TraitNodeBase, self).delete_input(name)
        
        def delete_output(self, name):
            if name in self.__port_traits:
                del self.__port_traits[name]
            if name in self.__io_mapping:
                del self.__io_mapping[name]
            super(_TraitNodeBase, self).delete_output(name)

        def set_default_value(self, name, value, traits):
            assert name in self.__port_traits
            assert self.__port_traits[name].optional  # check if it's optional
            assert entity.is_acceptable(traits, self.__port_traits[name].traits)
            self.__default_value[name] = dict(value=value, traits=traits)

        @property
        def default_value(self):
            return self.__default_value.copy()

        @property
        def io_mapping(self):
            return self.__io_mapping.copy()
        
        @property
        def message(self):
            return self.get_proprety('message')

        @message.setter
        def message(self, text):
            self.set_property('message', text, push_undo=False)

            node_item = self.view    
            tooltip = 'node: {}'.format(node_item.name)
            if len(text) > 0:
                tooltip += f' Message: "{text}"'
            node_item.setToolTip(tooltip)

        def add_input_w_traits(self, name, traits, *, optional=False, expand=False):
            if expand:
                traits = traits | wrap_traits(traits)

            assert not optional or entity.is_acceptable(traits, entity.Data)
            assert entity.is_acceptable(traits, entity.Data) or entity.is_acceptable(traits, entity.Object)

            port_traits = PortTraits(traits=traits, optional=optional, expand=expand)
            self.__port_traits[name] = port_traits  # required
            self.add_input(name)
            self.set_port_traits(self.get_input(name), port_traits)

        def add_output_w_traits(self, name, traits, *, expand=False, expression=None):
            if expand:
                traits = traits | wrap_traits(traits)

            assert entity.is_acceptable(traits, entity.Data) or entity.is_acceptable(traits, entity.Object)

            if expression is not None:
                self.__io_mapping[name] = expression

            port_traits = PortTraits(traits=traits, optional=False, expand=expand)
            self.__port_traits[name] = port_traits  # required
            self.add_output(name)
            self.set_port_traits(self.get_output(name), port_traits)

        def check(self):
            is_valid = True

            # if isinstance(node, ObjectOFPNode):
            #     station = graph.allocate_station(node)
            #     node.set_property("station", station, push_undo=False)
            #     is_valid = is_valid and station != ""

            for port in self.input_ports():
                port_traits = self.get_input_port_traits(port.name())
                connected_ports = port.connected_ports()

                if len(connected_ports) == 0 and not self.is_optional_port(port.name()):
                    is_valid = False
                    error_msg = f"Port [{port.name()}] is disconnected"
                    break

                for another_port in connected_ports:
                    another = another_port.node()

                    if isinstance(another, PortInputNode):
                        parent_port = another.parent_port
                        another_traits = parent_port.node().get_input_port_traits(parent_port.name())
                    else:
                        # assert isinstance(another, (OFPNode, OFPGroupNode))
                        another_traits = another.get_output_port_traits(another_port.name())
                    
                    if not entity.is_acceptable(another_traits, port_traits):
                        logger.info("%s %s %s; %s %s %s", self.NODE_NAME, port.type_(), port_traits, another.NODE_NAME, another_port.type_(), another_traits)
                        is_valid = False
                        error_msg = f"Port [{port.name()}] traits mismatches. [{traits_str(port_traits)}] expected. [{traits_str(another_traits)}] given"
                        break

            for port in self.output_ports():
                port_traits = self.get_output_port_traits(port.name())

                connected_ports = port.connected_ports()
                if len(connected_ports) == 0 and not entity.is_acceptable(port_traits, entity.Data):
                    is_valid = False
                    error_msg = f"Port [{port.name()}] is disconnected"
                    break

                # for another_port in connected_ports:
                #     another = another_port.node()

                #     if isinstance(another, PortOutputNode):
                #         parent_port = another.parent_port
                #         another_traits = parent_port.node().get_output_port_traits(parent_port.name())
                #     else:
                #         # assert isinstance(another, (OFPNode, OFPGroupNode))
                #         another_traits = another.get_inport_traits(another_port.name())
                    
                #     if not entity.is_acceptable(port_traits, another_traits):
                #         logger.info("%s %s %s; %s %s %s", self.NODE_NAME, port.type_(), port_traits, another.NODE_NAME, another_port.type_(), another_traits)
                #         is_valid = False
                #         error_msg = f"Port [{port.name()}] traits mismatches. [{traits_str(port_traits)}] expected. [{traits_str(another_traits)}] given"
                #         break

            if not is_valid:
                self.set_node_status(NodeStatusEnum.ERROR)
                self.message = error_msg
            elif self.get_node_status() == NodeStatusEnum.ERROR:
                self.set_node_status(NodeStatusEnum.READY)
                self.message = ''
            return is_valid
            
        def _execute(self, input_tokens):  #XXX: rename this
            raise NotImplementedError()
        
        def execute(self, input_tokens):
            input_tokens = dict(self.__default_value, **input_tokens)

            if not any(entity.is_acceptable(input_tokens[name]["traits"], entity._Spread) for name in self.expandable_ports if name in input_tokens):
                # no expansion
                return self._execute(input_tokens)
            else:
                # results = [
                #     self._execute(_input_tokens)
                #     for _input_tokens in expand_input_tokens(input_tokens)
                # ]

                loop_items = [
                    name
                    for name, token in input_tokens.items()
                    if entity.is_acceptable(token["traits"], entity.Object) and not entity.is_acceptable(token["traits"], entity._Spread)
                ]
                # assert all(name in self.__io_mapping and self.__io_mapping[name] in input_tokens for name in loop_items)
                results = []
                # updates = {}
                for _input_tokens in expand_input_tokens(input_tokens):
                    # _input_tokens.update(updates)
                    output_tokens = self._execute(_input_tokens)
                    results.append(output_tokens)
                    # updates = {self.__io_mapping[name]: token for name, token in output_tokens.items() if name in loop_items}

                return {
                    output_port.name(): {
                        "value": [result[output_port.name()]["value"] for result in results],
                        "traits": wrap_traits(results[0][output_port.name()]["traits"])
                    } if output_port.name() not in loop_items else {
                        "value": results[-1][output_port.name()]["value"],
                        "traits": results[0][output_port.name()]["traits"]
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
            logger.debug("update_color %s", self)

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
            logger.debug(f"set_node_status {repr(newstatus)}")
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
        io_mapping = self.io_mapping

        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_output_port_traits(output.name())
            if output.name() in io_mapping:
                traits_str = io_mapping[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                if entity.is_acceptable(traits, entity.Data):
                    value = {'value': 100, 'traits': traits}
                elif entity.is_acceptable(traits, entity.Object):
                    value = {'value': {"id": uuid.uuid4()}, 'traits': traits}
                else:
                    assert False, "Never reach here {}".format(traits)
            output_tokens[output.name()] = value
        return output_tokens

class DataOFPNode(OFPNode):

    def __init__(self):
        super(DataOFPNode, self).__init__()
    
    def _execute(self, input_tokens):
        io_mapping = self.io_mapping

        output_tokens = {}
        for output in self.output_ports():
            traits = self.get_output_port_traits(output.name())
            if output.name() in io_mapping:
                traits_str = io_mapping[output.name()]
                if traits_str in input_tokens:
                    value = input_tokens[traits_str]
                else:
                    raise NotImplementedError(f"No default behavior for traits [{traits_str}]")
            else:
                assert entity.is_acceptable(traits, entity.Data)
                value = {'value': 100, 'traits': traits}
            output_tokens[output.name()] = value
        return output_tokens