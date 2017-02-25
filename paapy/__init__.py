#!/usr/bin/env
# -*- coding: utf-8 -*-
from paapy.productadvertising import *
from paapy.api import *
from paapy.exceptions import *
import logging

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
