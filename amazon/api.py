#!/usr/bin/env
# -*- coding: utf-8 -*-
from base64 import b64encode
from hashlib import sha256
from urllib import quote
import time
import hmac
import logging

import xmltodict
import requests


SERVICE_DOMAINS = {
    'CA': 'webservices.amazon.ca',
    'CN': 'webservices.amazon.cn',
    'DE': 'webservices.amazon.de',
    'ES': 'webservices.amazon.es',
    'FR': 'webservices.amazon.fr',
    'IN': 'webservices.amazon.in',
    'IT': 'webservices.amazon.it',
    'JP': 'webservices.amazon.co.jp',
    'UK': 'webservices.amazon.co.uk',
    'US': 'webservices.amazon.com',
    'BR': 'webservices.amazon.com.br',
    'MX': 'webservices.amazon.com.mx'
}

VALID_NAMES = [
    'BrowseNodeLookup',
    'ItemSearch',
    'ItemLookup',
    'SimilarityLookup',
    'CartAdd',
    'CartClear',
    'CartCreate',
    'CartGet',
    'CartModify'
]

logger = logging.getLogger(__name__)


"""
ProductAdvertisingAPI.
Contains functions for each of the main calls of the Amazon API.
Required parameters are defined in the function, but users can
customize their requests with Keyword Arguments.  It is required
that the keyword name be that of the paramter in the API documentation.
"""


class ProductAdvertisingAPI(object):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret,
                 Region='US', Service='AWSECommerceService',
                 Version='2013-08-01', QPS=None, timeout=None):
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
        self.Region = Region
        self.Service = Service
        self.Version = Version
        self.timeout=timeout
        self.QPS = QPS
        self.ITEM_LOOKUP_MAX = 10
        self._last_time = None

    def _build_request(self, name):
        if name not in VALID_NAMES:
            raise AmazonException(
                'Invalid Operation: "%s".  ' +
                'Please see the documentation for details: %s' % 
                (name, 'http://docs.aws.amazon.com/AWSECommerceService' +
                       '/latest/DG/CHAP_OperationListAlphabetical.html'
                )
            )
        if self.QPS is not None and self.QPS > 0:
            if self._last_time is not None:
                wait_time = 1 / self.QPS - (time.time() - self._last_time)
                print wait_time
                if wait_time > 0:
                    logger.error(
                        'Waiting %s seconds to send next API Request.',
                        wait_time
                    )
                    time.sleep(wait_time)
            self._last_time = time.time()
        return AmazonRequest(
            self.AssociateTag,
            self.AWSAccessKeyId,
            self.AWSAccessKeySecret,
            Operation=name, Region=self.Region,
            Service=self.Service, Version=self.Version,
            timeout=self.timeout
        )

    def _check_valid_asin(self, asin):
        bad_asins = []
        if ',' in asin:
            asins = asin.split(',')
        else:
            asins = [asin]
        for a in asins:
            valid = len(a) == 10 and a[0].upper() == 'B'
            if not valid:
                bad_asins.append(a)
        if len(bad_asins) > 1:
            raise AmazonException(
                'Invalid ASIN(s) "%s" provided.'
                '  Asins must be 10 characters long and start with a "B".'
                '  Please review your ItemID.' % str(bad_asins)
            )

    def _check_valid_quantity(self, quantity):
        try:
            quantity = int(quantity)
            if quantity < 0 or quantity > 999:
                quantity = int(None)
        except TypeError:
            raise AmazonException(
                'Quantity "%s" must be'
                ' between 0 and 999, inclusive.' % str(quantity)
            )

    def ItemSearch(self, SearchIndex=None, **kwargs):
        if SearchIndex is None:
            raise SearchException(
                'SearchIndex must provided.'
                '  For a list of valid values, please see:'
                ' http://docs.aws.amazon.com/AWSECommerceService'
                '/latest/DG/localevalues.html'
            )
        params = {
            'SearchIndex': SearchIndex
        }
        kwargs.update(params)
        return self._build_request('ItemSearch').execute(**kwargs)

    def BrowseNodeLookup(self, BrowseNodeId=None, **kwargs):
        try:
            BrowseNodeId = int(BrowseNodeId)
        except:
            raise LookupException(
                'BrowseNodeId must be a positive Integer.'
                '  For a list of valid IDs, please see:'
                ' http://docs.aws.amazon.com/AWSECommerceService'
                '/latest/DG/localevalues.html'
            )
        params = {
            'BrowseNodeId': BrowseNodeId
        }
        kwargs.update(params)
        return self._build_request('BrowseNodeLookup').execute(**kwargs)

    def ItemLookup(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise LookupException('ItemId is required.')
        self._check_valid_asin(ItemId)
        params = {
            'ItemId': ItemId
        }
        kwargs.update(params)
        return self._build_request('ItemLookup').execute(**kwargs)

    def SimilarityLookup(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise LookupException('ItemId is required.')
        self._check_valid_asin(ItemId)

        params = {
            'ItemId': ItemId
        }
        kwargs.update(params)
        return self._build_request('SimilarityLookup').execute(**kwargs)

    def CartAdd(self, ASIN=None, CartId=None, Quantity='1', **kwargs):
        if ASIN is None or CartId is None:
            raise CartException('ASIN and CartId are required.')
        self._check_valid_asin(ASIN)
        self._check_valid_quantity(Quantity)

        params = {
            'CartId': CartId,
            'Item.1.ASIN': ASIN,
            'Item.1.Quantity': Quantity
        }
        kwargs.update(params)
        return self._build_request('CartAdd').execute(**kwargs)

    def CartClear(self, CartId=None, **kwargs):
        if CartId is None:
            raise CartException('CartId is required.')
        self._check_valid_asin(ItemId)
        params = {
            'CartId': CartId
        }
        kwargs.update(params)
        return self._build_request('CartClear').execute(**kwargs)

    def CartCreate(self, ItemId=None, Quantity='1'):
        if ItemId is None:
            raise CartException('ItemId is required.')
        self._check_valid_asin(ItemId)
        self._check_valid_quantity(Quantity)
        params = {
            'Item.1.ASIN': ItemId,
            'Item.1.Quantity': Quantity
        }
        kwargs.update(params)
        return self._build_request('CartCreate').execute(**kwargs)

    def CartGet(self, CartId=None, CartItemId=None, **kwargs):
        if CartId is None or CartItemId is None:
            raise CartException('CartId and CartItemId are required.')
        params = {
            'CartId': CartId,
            'CartItemId': CartItemId
        }
        kwargs.update(params)
        return self._build_request('CartGet').execute(**kwargs)

    def CartModify(self, CartId=None, CartItemId=None, Quantity='1', **kwargs):
        if CartId is None or CartItemId is None:
            raise CartException('CartId and CartItemId are required.')
        self._check_valid_quantity(Quantity)
        params = {
            'CartId': CartId,
            'Item.1.CartItemId': CartItemId,
            'Item.1.Quantity': Quantity
        }
        kwargs.update(params)
        return self._build_request('CartModify').execute(**kwargs)


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


"""
Base Class. Initializes with Amazon API Credentials
(KEY_ID, KEY_SECRET, ASSOCIATE TAG) as well as the
API Operation Name, the target Region, the Service,
and the Version.

This class should not be used directly.
Use ProductAdvertising to create AmazonRequests.
"""


class AmazonRequest(object):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret,
                 Operation, Region, Service, Version, timeout):
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
        self.Operation = Operation
        self.Region = Region
        self.Service = Service
        self.Version = Version
        self.timeout = timeout

    def _quote_params(self, params):
        key_values = [(quote(k), quote(v)) for k, v in params.iteritems()]
        key_values.sort()
        return '&'.join(['%s=%s' % (k, v) for k, v in key_values])

    def _signed_url(self, **kwargs):
        params = {
            'Operation': self.Operation,
            'Service': self.Service,
            'Version': self.Version,
            'AssociateTag': self.AssociateTag,
            'AWSAccessKeyId': self.AWSAccessKeyId,
            'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        params.update(kwargs)

        quoted_params = self._quote_params(params)
        server = SERVICE_DOMAINS[self.Region]

        msg = 'GET\n' + server + '\n' + '/onca/xml\n' + quoted_params

        if type(msg) is unicode:
            self.msg = msg.encode('utf-8')
        if type(self.AWSAccessKeySecret) is unicode:
            self.AWSAccessKeySecret = self.AWSAccessKeySecret.encode('utf-8')

        signature = quote(
            b64encode(hmac.new(self.AWSAccessKeySecret, msg, sha256).digest())
        )
        return 'http://%s/onca/xml?%s&Signature=%s' % (
            server, quoted_params, signature
        )

    def _parse_xml(self, xml):
        pass

    def execute(self, **kwargs):
        trying, try_num = True, 0
        while trying and try_num < 3:
            try:
                try_num += 1
                response = requests.get(
                    self._signed_url(**kwargs), timeout=self.timeout
                )
                trying = False
            except requests.ConnecTimeout as e:
                logger.warning('Error encountered: %s.  Retrying...', e)
                time.sleep(1)

        if response.status_code != 200:
            raise AmazonException(
                'AmazonRequest encountered an Execution Error.'
                ' Status: %s %s.' % (response.status_code, response.reason)
            )
        response = xmltodict.parse(response.text)[self.Operation + 'Response']
        logger.debug(response)
        return response


__all__ = ['ProductAdvertising', 'AmazonException']
