#!/usr/bin/python
# -*- coding: utf-8 -*-
import itertools

from nodes.ofp_node import OFPNode, NodeStatusEnum

from logging import getLogger

logger = getLogger(__name__)


class Simulator:

    def __init__(self) -> None:
        self.__results = {}
        self.__tokens = {}

    def run(self, node: OFPNode, graph_id: int) -> None:
        logger.info('run %s', node)

        input_tokens = {
            input.name(): self.__results[(graph_id, node.name(), input.name())]
            for input in node.input_ports()
            if (graph_id, node.name(), input.name()) in self.__results  # For optional inputs
        }
        node.run(input_tokens)

    def fetch_token(self, node: OFPNode, graph_id: int) -> None:
        logger.info('fetch_token %s', node)

        # This token_store doesn't support multiple tokens at a single port
        assert len(node.output_queue) <= 1
        while len(node.output_queue) > 0:
            output_tokens = node.output_queue.popleft()
            output_tokens = {(graph_id, node.name(), key): value for key, value in output_tokens.items()}
            for key, value in output_tokens.items():
                self.__results[key] = value
                self.__tokens[key] = value

    def transmit_token(self, node: OFPNode, graph_id: int) -> None:
        logger.info('transmit_token %s', node)

        # Transmit a token
        for output in node.output_ports():
            key = (graph_id, node.name(), output.name())
            if not key in self.__tokens:
                continue
            value = self.__tokens[key]
            send = False
            for connected in output.connected_ports():
                if connected.node().get_node_status() == NodeStatusEnum.WAITING:
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
