#!/usr/bin/env
# -*- coding: utf-8 -*-
from amazonapi.productadvertising import *
import logging


try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
