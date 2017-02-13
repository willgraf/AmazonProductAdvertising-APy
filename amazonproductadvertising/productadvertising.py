#!/usr/bin/env
# -*- coding: utf-8 -*-

"""Python Product Advertising API"""

from base64 import b64encode
from hashlib import sha256

import time
import hmac
import logging

from urllib import urlencode
try:
    from urllib.parse import quote as quote
except ImportError:
    from urllib import quote as quote

import xmltodict
import requests

from amazonproductadvertising.exceptions import AmazonException


DOMAINS = {
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


LOGGER = logging.getLogger(__name__)


class ProductAdvertisingAPI(object):

    """
    Executes AmazonRequests.
    Contains functions for each of the main calls of the Amazon API.
    Required parameters are defined in the function, but users can
    customize their requests with Keyword Arguments.  It is required
    that the keyword name be that of the paramter in the API documentation.
    """

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs):
        if (AssociateTag is None) or (AWSAccessKeyId is None) or (AWSAccessKeySecret is None):
            raise ValueError('Your Amazon Credentials are required and cannot be None.')
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
        self.Region = kwargs.pop('Region', 'US')
        self.Version = kwargs.pop('Version', '2013-08-01')
        self.Service = kwargs.pop('Service', 'AWSECommerceService')
        self.ITEM_ID_MAX = 10
        self.retry_count = kwargs.pop('retry_count', 3)
        self.qps = kwargs.pop('qps', None)
        self.timeout = kwargs.pop('timeout', None)
        self._last_time = None
        if not isinstance(self.Region, str) or self.Region.upper() not in DOMAINS:
            raise ValueError('Your region is currently unsupported.')
        if self.qps:
            try:
                self.qps = float(self.qps)
            except:
                raise ValueError('qps (query per second) must be a number.')
        if not isinstance(self.retry_count, int):
            try:
                self.retry_count = int(self.retry_count)
            except:
                raise ValueError('retry_count must be an integer.')


    def _make_request(self, name, **kwargs):
        if self.qps is not None and self.qps > 0:
            if self._last_time is not None:
                wait_time = 1 / self.qps - (time.time() - self._last_time)
                if wait_time > 0:
                    LOGGER.warning('Waiting %s secs to send next Request.',
                                   round(wait_time, 3))
                    time.sleep(wait_time)
            self._last_time = time.time()

        request = AmazonRequest(self.AssociateTag, self.AWSAccessKeyId,
                                self.AWSAccessKeySecret, Operation=name,
                                Region=self.Region, Service=self.Service,
                                Version=self.Version, timeout=self.timeout,
                                retry_count=self.retry_count)

        return request.execute(**kwargs)

    def _check_valid_asin(self, asin):
        """
        Strings will be split by commas (,) and lists of strings are OK too
        """
        asin = self._parse_multiple_items(asin)
        bad_asins = [a for a in asin if len(a) != 10 or a[0].upper() != 'B']
        if len(bad_asins) > 0:
            raise ValueError('INVALID ASINS: "%s".  ASIN is 10 characters long'
                             ' and starts with a "B".' % ', '.join(bad_asins))

    def _check_valid_quantity(self, quantity):
        """
        Strings will be split by commas (,) and lists of strings are OK too
        Quantity must be positive, and less than 1000
        """
        quantity = self._parse_multiple_items(quantity)
        for quant in quantity:
            try:
                quant = int(quant)
                if quant < 0 or quant > 999:
                    raise TypeError
            except (TypeError, ValueError):
                raise ValueError('Invalid Quantity "%s": Quantity must be between'
                                 ' 0 and 999, inclusive.' % quant)

    def _handle_errors(self, request):
        """log request errors, raise if necessary"""
        if 'Errors' in request:
            errors = request['Errors']['Error']
            errors = [errors] if not isinstance(errors, list) else errors
            error_output = []
            for err in errors:
                err_message = err['Message']
                err_code = err['Code']
                LOGGER.error('%s  -  %s', err_code, err_message)
                error_output.append('%s  -  %s' % (err_code, err_message))
            if len(error_output) > 0:
                raise AmazonException(' , '.join(error_output))
        return self

    def _parse_multiple_items(self, data):
        """turn data from string to list"""
        if isinstance(data, str) and ',' in data:
            data = data.split(',')
        if not isinstance(data, list):
            data = [data]
        return data

    def ItemSearch(self, **kwargs):
        response = self._make_request('ItemSearch', **kwargs)
        self._handle_errors(response['Items']['Request'])
        return response

    def BrowseNodeLookup(self, BrowseNodeId=None, **kwargs):
        if BrowseNodeId is None:
            raise ValueError('BrowseNodeId must be a positive Integer.  For a'
                             ' list of valid IDs, please see: http://docs.aws'
                             '.amazon.com/AWSECommerceService/latest/DG/'
                             'localevalues.html')
        params = {
            'BrowseNodeId': BrowseNodeId
        }
        kwargs.update(params)
        response = self._make_request('BrowseNodeLookup', **kwargs)
        self._handle_errors(response['BrowseNodes']['Request'])
        return response

    def ItemLookup(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise ValueError('ItemId is required.')
        ItemId = self._parse_multiple_items(ItemId)
        self._check_valid_asin(ItemId)
        params = {
            'ItemId': ','.join(ItemId)
        }
        kwargs.update(params)
        response = self._make_request('ItemLookup', **kwargs)
        self._handle_errors(response['Items']['Request'])
        return response

    def SimilarityLookup(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise ValueError('ItemId is required.')
        ItemIdType = kwargs.pop('ItemIdType', 'ASIN')
        if ItemIdType == 'ASIN':
            self._check_valid_asin(ItemId)
        params = {
            'ItemId': ItemId,
            'ItemIdType': ItemIdType
        }
        kwargs.update(params)
        response = self._make_request('SimilarityLookup', **kwargs)
        self._handle_errors(response['Items']['Request'])
        return response

    def CartAdd(self, CartId=None, HMAC=None, **kwargs):
        if CartId is None:
            raise ValueError('CartId is required.')
        elif HMAC is None:
            raise ValueError('HMAC is required.')
        elif 'ASIN' not in kwargs and 'OfferListingId' not in kwargs and 'ItemId' not in kwargs:
            raise ValueError('Must provide a valid ASIN or OfferListingId to add.')

        item_type = 'OfferListingId' if 'OfferListingId' in kwargs else 'ASIN'

        items = self._parse_multiple_items(kwargs.pop(item_type, kwargs.pop('ItemId', [])))

        if item_type == 'ASIN':
            self._check_valid_asin(items)

        Quantity = self._parse_multiple_items(kwargs.pop('Quantity', '1'))
        self._check_valid_quantity(Quantity)
        Quantity = Quantity * len(items) if len(Quantity) == 1 else Quantity

        if len(Quantity) != len(items):
            raise AmazonException('Weird stuff with multiple items and '
                                  'their quantities is not matching up.')
        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        for i, zip_data in enumerate(zip(items, Quantity)):
            item, quantity = zip_data
            params.update({
                'Item.%d.%s' % (i, item_type): item,
                'Item.%d.Quantity' % i: quantity
            })
        kwargs.update(params)
        response = self._make_request('CartAdd', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response

    def CartClear(self, CartId=None, HMAC=None, **kwargs):
        if CartId is None:
            raise ValueError('CartId is required.')
        elif HMAC is None:
            raise ValueError('HMAC is required.')
        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        kwargs.update(params)
        response = self._make_request('CartClear', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response

    def CartCreate(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise ValueError('ItemId is required.')
        ItemIdType = kwargs.pop('ItemIdType', 'ASIN')

        if ItemIdType.upper() == 'ASIN':
            self._check_valid_asin(ItemId)

        ItemId = self._parse_multiple_items(ItemId)
        Quantity = self._parse_multiple_items(kwargs.pop('Quantity', '1'))
        Quantity = Quantity * len(ItemId) if len(Quantity) == 1 else Quantity

        self._check_valid_quantity(Quantity)
        if len(Quantity) != len(ItemId):
            raise AmazonException('Weird stuff with multiple items and '
                                  'their quantities is not matching up.')

        for i, zip_data in enumerate(zip(ItemId, Quantity)):
            item_id, quantity = zip_data
            params = {
                'Item.%d.%s' % (i, ItemIdType): item_id,
                'Item.%d.Quantity' % i: quantity
            }
            kwargs.update(params)
        response = self._make_request('CartCreate', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response

    def CartGet(self, CartId=None, CartItemId=None, HMAC=None, **kwargs):
        if CartId is None:
            raise ValueError('CartId is required.')
        elif CartItemId is None:
            raise ValueError('CartItemId is required.')
        elif HMAC is None:
            raise ValueError('HMAC is requred')

        params = {
            'CartId': CartId,
            'CartItemId': CartItemId,
            'HMAC': HMAC
        }
        kwargs.update(params)
        response = self._make_request('CartGet', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response

    def CartModify(self, CartId=None, CartItemId=None, HMAC=None, **kwargs):
        if CartId is None:
            raise ValueError('CartId is required.')
        elif CartItemId is None:
            raise ValueError('CartItemId is required.')
        elif HMAC is None:
            raise ValueError('HMAC is requred')

        CartItemId = self._parse_multiple_items(CartItemId)
        Quantity = self._parse_multiple_items(kwargs.pop('Quantity', '1'))
        Quantity = Quantity * len(CartItemId) if len(Quantity) == 1 else Quantity

        if len(Quantity) != len(CartItemId):
            raise AmazonException('Weird stuff with multiple items and '
                                  'their quantities is not matching up.')

        self._check_valid_quantity(Quantity)
        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        for i, zip_info in enumerate(zip(CartItemId, Quantity)):
            item, quantity = zip_info
            params.update({
                'Item.%d.CartItemId' % i: item,
                'Item.%d.Quantity' % i: quantity
            })
        kwargs.update(params)
        response = self._make_request('CartModify', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response


class AmazonRequest(object):

    """
    AmazonRequest class.. Initializes with Amazon API Credentials
    (KEY_ID, KEY_SECRET, ASSOCIATE TAG) as well as the
    API Operation Name, the target Region, the Service,
    and the Version.

    This class is created only by the ProductAdvertisingAPI.
    """

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret,
                 Operation, Region, Service, Version, timeout, retry_count):
        if Operation not in ['BrowseNodeLookup', 'ItemSearch', 'ItemLookup',
                             'SimilarityLookup', 'CartAdd', 'CartClear',
                             'CartCreate', 'CartGet', 'CartModify']:
            raise ValueError('Invalid Operation Name: "%s".  Please see the '
                             'documentation for details: http://docs.aws.'
                             'amazon.com/AWSECommerceService/latest/DG/CHAP_'
                             'OperationListAlphabetical.html' % Operation)
        self.AssociateTag = AssociateTag.encode('utf-8')
        self.AWSAccessKeySecret = AWSAccessKeySecret.encode('utf-8')
        self.AWSAccessKeyId = AWSAccessKeyId
        self.Operation = Operation
        self.Region = Region
        self.Service = Service
        self.Version = Version
        self.timeout = timeout
        self.retry_count = retry_count

    def _quote_params(self, params):
        """URL Encode Parameters"""
        key_values = []
        for key, val in params.iteritems():
            if not isinstance(key, str):
                key = str(key)
            if not isinstance(val, str):
                val = str(val)
            key_values.append((quote(key), quote(val)))
        key_values.sort()
        return '&'.join(['%s=%s' % (k, v) for k, v in key_values])

    def _signed_url(self, **kwargs):
        """Return Signed URL for Request"""
        params = {
            'Operation': self.Operation,
            'Service': self.Service,
            'Version': self.Version,
            'AssociateTag': self.AssociateTag.encode('utf-8'),
            'AWSAccessKeyId': self.AWSAccessKeyId,
            'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        params.update(kwargs)
        quoted_params = self._quote_params(params)
        server = DOMAINS[self.Region]

        msg = 'GET\n%s\n/onca/xml\n%s' % (server, quoted_params)

        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        signature = b64encode(hmac.new(self.AWSAccessKeySecret, msg, sha256).digest())
        return 'http://%s/onca/xml?%s&Signature=%s' % (server, quoted_params, quote(signature))

    def _handle_request_errors(self, response):
        """log errors, raise an AmazonException if a problem occurs"""
        if response.status_code != 200:
            err = xmltodict.parse(response.text)
            err_code = err[self.Operation + 'ErrorResponse']['Error']['Code']
            err_msg = err[self.Operation + 'ErrorResponse']['Error']['Message']
            LOGGER.debug(response.text)
            LOGGER.error('Amazon %sRequest STATUS %s: %s - %s',
                         self.Operation, response.status_code, err_code, err_msg)
            raise AmazonException('AmazonRequestError %s: %s - %s' % \
                                  (response.status_code, err_code, err_msg))

    def execute(self, **kwargs):
        """execute AmazonRequest, return response as JSON"""
        trying, try_num = True, 0
        while trying and try_num < self.retry_count:
            try:
                try_num += 1

                if 'headers' in kwargs:
                    headers = kwargs['headers']
                    del kwargs['headers']
                else:
                    headers = {}

                url = self._signed_url(**kwargs)
                response = requests.get(url, timeout=self.timeout, headers=headers)
                self._handle_request_errors(response)
                trying = False
            except (AmazonException, requests.exceptions.ConnectTimeout) as err:
                sleep_time = 3
                LOGGER.warning('Error encountered: %s.  Retrying in %s seconds...',
                               err, sleep_time)
                if try_num >= self.retry_count:
                    raise err
                time.sleep(sleep_time)

        return xmltodict.parse(response.text)[self.Operation + 'Response']


__all__ = ['ProductAdvertisingAPI']
