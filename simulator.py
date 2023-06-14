#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
from nodes import SampleNode, NodeStatusEnum, PortTraitsEnum

from logging import getLogger

logger = getLogger(__name__)

class Simulator:

    def __init__(self) -> None:
        self.__scheduler = {}
        self.__results = {}

    def execute(self, node: SampleNode) -> NodeStatusEnum:
        for output in node.output_ports():
            traits = node.get_port_traits(output.name())
            if output.name() in node.io_mapping():
                value = self.__results[(node.name(), node.io_mapping()[output.name()])]
            else:
                if traits in PortTraitsEnum.DATA:
                    value = 100
                elif traits in PortTraitsEnum.OBJECT:
                    value = None
                else:
                    assert False, "Never reach here {}".format(traits)
            self.__results[(node.name(), output.name())] = value

        logger.info("execute %s", self.__results)
        return NodeStatusEnum.DONE

    def run(self, node: SampleNode) -> NodeStatusEnum:
        logger.info('run %s', node)
        self.__scheduler[node.name] = datetime.datetime.now()

        for input in node.input_ports():
            key = None
            for connected in input.connected_ports():
                key = (connected.node().name(), connected.name())
                break
            assert key in self.__results, key
            self.__results[(node.name(), input.name())] = self.__results[key]
        return NodeStatusEnum.RUNNING
    
    def get_status(self, node: SampleNode) -> NodeStatusEnum:
        logger.info('get_status %s', node)
        if node.name not in self.__scheduler:
            return NodeStatusEnum.ERROR
        start = self.__scheduler[node.name]
        now = datetime.datetime.now()
        if (now - start).total_seconds() > 10:
            del self.__scheduler[node.name]
            return self.execute(node)
        return NodeStatusEnum.RUNNING