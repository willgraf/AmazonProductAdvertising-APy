#!/usr/bin/env
# -*- coding: utf-8 -*-
from amazon.productadvertising import *
from amazon.api import *
from amazon.exceptions import *
import logging


try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
