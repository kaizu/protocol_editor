#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import itertools
import uuid

from nodes import SampleNode, BuiltinNode, ObjectNode, NodeStatusEnum, PortTraitsEnum

from logging import getLogger

logger = getLogger(__name__)


class Simulator:

    def __init__(self) -> None:
        self.__scheduler = {}
        self.__results = {}
        self.__tokens = {}

    def _execute(self, node: SampleNode, input_tokens: dict[str, object]) -> list[dict[tuple[str, str], object]]:
        if isinstance(node, BuiltinNode):
            output_tokens = node.execute(input_tokens)
        else:
            output_tokens = {}
            for output in node.output_ports():
                traits = node.get_port_traits(output.name())
                if output.name() in node.io_mapping():
                    value = input_tokens[node.io_mapping()[output.name()]]
                else:
                    if traits in PortTraitsEnum.DATA:
                        value = {'value': 100, 'traits': traits}
                    elif traits in PortTraitsEnum.OBJECT:
                        value = {'value': uuid.uuid4(), 'traits': traits}
                    else:
                        assert False, "Never reach here {}".format(traits)
                output_tokens[output.name()] = value
        return output_tokens

    def execute(self, node: SampleNode) -> NodeStatusEnum:
        new_status = NodeStatusEnum.DONE

        input_tokens = {input.name(): self.__results[(node.name(), input.name())] for input in node.input_ports()}
        output_tokens = self._execute(node, input_tokens)

        output_tokens = {(node.name(), key): value for key, value in output_tokens.items()}
        for key, value in output_tokens.items():
            self.__results[key] = value
            self.__tokens[key] = value

        logger.debug("execute %s", self.__results)
        return new_status

    def run(self, node: SampleNode) -> NodeStatusEnum:
        logger.info('run %s', node)
        self.__scheduler[node.name] = datetime.datetime.now()

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
    
    def get_status(self, node: SampleNode) -> NodeStatusEnum:
        logger.info('get_status %s', node)
        if node.name not in self.__scheduler:
            return NodeStatusEnum.ERROR
        start = self.__scheduler[node.name]
        now = datetime.datetime.now()
        duration = 10 if isinstance(node, ObjectNode) else 0
        if (now - start).total_seconds() >= duration:
            del self.__scheduler[node.name]
            return self.execute(node)
        return NodeStatusEnum.RUNNING

    def transmit_token(self, node: SampleNode) -> NodeStatusEnum:
        logger.info('transmit_token %s', node)
        for output in node.output_ports():
            key = (node.name(), output.name())
            if not key in self.__tokens:
                continue
            value = self.__tokens[key]
            send = False
            for connected in output.connected_ports():
                if connected.node().get_property('status') == NodeStatusEnum.WAITING.value:
                    send = True
                    new_key = (connected.node().name(), connected.name())
                    self.__results[new_key] = value
                    self.__tokens[new_key] = value
            if send:
                del self.__tokens[key]

    def reset_token(self, node: SampleNode):
        for port in itertools.chain(node.input_ports(), node.output_ports()):
            key = (node.name(), port.name())
            if key in self.__tokens:
                del self.__tokens[key]

    def has_token(self, key) -> bool:
        return key in self.__tokens
