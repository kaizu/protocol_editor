#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import itertools
import uuid

from nodes import OFPNode, ObjectNode, NodeStatusEnum
import nodes.entity as entity
from nodes.builtins import BuiltinNode

from logging import getLogger

logger = getLogger(__name__)


class Simulator:

    def __init__(self) -> None:
        self.__scheduler = {}
        self.__results = {}
        self.__tokens = {}

    def _execute(self, node: OFPNode, input_tokens: dict[str, object]) -> list[dict[tuple[str, str], object]]:
        try:
            output_tokens = node.execute(input_tokens)
        except NotImplementedError as err:
            assert not isinstance(node, BuiltinNode)
            output_tokens = {}
            for output in node.output_ports():
                traits = node.get_port_traits(output.name())
                if output.name() in node.io_mapping():
                    traits_str = node.io_mapping()[output.name()]
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

    def execute(self, node: OFPNode, graph_id: int) -> NodeStatusEnum:
        new_status = NodeStatusEnum.DONE

        input_tokens = {
            input.name(): self.__results[(graph_id, node.name(), input.name())]
            for input in node.input_ports()
            if (graph_id, node.name(), input.name()) in self.__results  # For optional inputs
        }
        output_tokens = self._execute(node, input_tokens)

        output_tokens = {(graph_id, node.name(), key): value for key, value in output_tokens.items()}
        for key, value in output_tokens.items():
            self.__results[key] = value
            self.__tokens[key] = value

        logger.debug("execute %s", self.__results)
        return new_status

    def run(self, node: OFPNode, graph_id: int) -> NodeStatusEnum:
        logger.info('run %s', node)
        self.__scheduler[(node.name, graph_id)] = datetime.datetime.now()

        # for input in node.input_ports():
        #     key = None
        #     for connected in input.connected_ports():
        #         key = (connected.node().name(), connected.name())
        #         break
        #     assert key in self.__results, key
        #     assert key in self.__tokens, key
        #     self.__results[(node.name(), input.name())] = self.__results[key]
        #     traits = node.get_port_traits(input.name())
        #     if traits in PortTraitsEnum.OBJECT:
        #         del self.__tokens[key]
        return NodeStatusEnum.RUNNING
    
    def get_status(self, node: OFPNode, graph_id: int) -> NodeStatusEnum:
        logger.info('get_status %s', node)
        if (node.name, graph_id) not in self.__scheduler:
            return NodeStatusEnum.ERROR
        start = self.__scheduler[(node.name, graph_id)]
        now = datetime.datetime.now()
        duration = 10 if isinstance(node, ObjectNode) else 0
        if (now - start).total_seconds() >= duration:
            del self.__scheduler[(node.name, graph_id)]
            return self.execute(node, graph_id)
        return NodeStatusEnum.RUNNING

    def transmit_token(self, node: OFPNode, graph_id: int) -> NodeStatusEnum:
        logger.info('transmit_token %s', node)
        for output in node.output_ports():
            key = (graph_id, node.name(), output.name())
            if not key in self.__tokens:
                continue
            value = self.__tokens[key]
            send = False
            for connected in output.connected_ports():
                if connected.node().get_property('status') == NodeStatusEnum.WAITING.value:
                    send = True
                    new_key = (graph_id, connected.node().name(), connected.name())
                    self.__results[new_key] = value
                    self.__tokens[new_key] = value
            if send:
                del self.__tokens[key]

    def reset_token(self, node: OFPNode, graph_id: int):
        for port in itertools.chain(node.input_ports(), node.output_ports()):
            key = (graph_id, node.name(), port.name())
            if key in self.__tokens:
                del self.__tokens[key]

    def has_token(self, key) -> bool:
        return key in self.__tokens
