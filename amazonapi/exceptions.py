#!/usr/bin/env
# -*- coding: utf-8 -*-


"""
Exceptions:
Specific exceptions for common issues.
"""


class AmazonException(Exception):
    pass

class SearchException(AmazonException):
    pass

class LookupException(AmazonException):
    pass

class CartException(AmazonException):
    pass

class InvalidASIN(AmazonException):
    pass
