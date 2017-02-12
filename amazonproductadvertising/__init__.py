#!/usr/bin/env
# -*- coding: utf-8 -*-
from amazonproductadvertising.productadvertising import *
from amazonproductadvertising.api import *
from amazonproductadvertising.exceptions import *
import logging

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
