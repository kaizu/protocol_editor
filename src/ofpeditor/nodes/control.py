#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import numpy
import uuid
import datetime
import inspect

from ofpeditor.nodes import entity


class ServerBase:

    def serve_plate_96wells(self):
        raise NotImplementedError()

    def dispose_labware(self, obj):
        raise NotImplementedError()

    def save_artifacts(self, data, where):
        raise NotImplementedError()

    def store_labware(self, obj, where):
        raise NotImplementedError()

    def dispense_liquid_96wells(self, obj, data, channel):
        raise NotImplementedError()

    def read_absorbance_3colors(self, obj):
        raise NotImplementedError()

class DummyServer(ServerBase):

    def serve_plate_96wells(self):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        return dict(value={"id": uuid.uuid4(), "date": str(datetime.datetime.now())}, traits=entity.Plate96)

    def dispose_labware(self, obj):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        return
    
    def save_artifacts(self, data, where):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        return

    def store_labware(self, obj, where):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        return

    def dispense_liquid_96wells(self, obj, data, channel):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        assert obj["value"] is not None
        return

    def read_absorbance_3colors(self, obj):
        logger.info(f"{self.__class__.__name__}: {inspect.currentframe().f_code.co_name}: ")
        assert obj["value"] is not None
        data = [
            numpy.zeros(96, dtype=numpy.float64),
            numpy.zeros(96, dtype=numpy.float64),
            numpy.zeros(96, dtype=numpy.float64)
        ]
        return data

experiments = DummyServer()
