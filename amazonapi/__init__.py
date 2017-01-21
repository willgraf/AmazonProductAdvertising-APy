#!/usr/bin/env
# -*- coding: utf-8 -*-
from amazonapi.productadvertising import *
from amazonapi.api import *
from amazonapi.exceptions import *
import logging


try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
