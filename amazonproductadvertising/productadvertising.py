#!/usr/bin/env
# -*- coding: utf-8 -*-

"""Python Product Advertising API"""

from base64 import b64encode
from hashlib import sha256

import time
import hmac
import logging

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
            raise ValueError('Your Amazon Credentials are'
                             ' required and cannot be None.')
        Region = kwargs.get('Region', 'US')
        qps = kwargs.get('qps', None)
        retry_count = kwargs.get('retry_count', 3)
        Version = kwargs.get('Version', '2013-08-01')
        Service = kwargs.get('Service', 'AWSECommerceService')
        if not isinstance(Region, str) or Region.upper() not in DOMAINS:
            raise ValueError('Your region is currently unsupported.')
        if qps:
            try:
                qps = float(qps)
            except:
                raise ValueError('qps (query per second) must be a number.')
        if not isinstance(retry_count, int):
            try:
                retry_count = int(retry_count)
            except:
                raise ValueError('retry_count must be an integer.')
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
        self.Region = Region
        self.Version = Version
        self.Service = Service
        self.ITEM_ID_MAX = 10
        self.retry_count = kwargs.get('retry_count', 3)
        self.qps = qps
        self.timeout = kwargs.get('timeout', None)
        self._last_time = None


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
        asin = asin.split(',') if ',' in asin else [asin]
        bad_asins = [a for a in asin if len(a) != 10 or a[0].upper() != 'B']
        if len(bad_asins) > 0:
            raise ValueError('INVALID ASIN: "%s".  ASIN is 10 characters long'
                             ' and starts with a "B".' % str(bad_asins))

    def _check_valid_quantity(self, quantity):
        if not isinstance(quantity, list):
            if isinstance(quantity, str):
                quantity = quantity.split(',')
            else:
                quantity = [quantity]
        for quant in quantity:
            try:
                quant = int(quant)
                if quant < 0 or quant > 999:
                    raise TypeError
            except (TypeError, ValueError):
                raise ValueError('Invalid Quantity "%s": Quantity must be between'
                                 ' 0 and 999, inclusive.' % str(quant))

    def _handle_errors(self, request):
        if 'Errors' in request:
            errors = request['Errors']['Error']
            errors = [errors] if not isinstance(errors, list) else errors
            for err in errors:
                err_message = err['Message']
                err_code = err['Code']
                LOGGER.error('%s  -  %s', err_code, err_message)
                raise AmazonException('%s  -  %s' % (err_code, err_message))
        return self

    def _parse_multiple_items(self, data):
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
        elif isinstance(ItemId, list):
            ItemId = ','.join(ItemId)
        self._check_valid_asin(ItemId)
        params = {
            'ItemId': ItemId
        }
        kwargs.update(params)
        response = self._make_request('ItemLookup', **kwargs)
        self._handle_errors(response['Items']['Request'])
        return response

    def SimilarityLookup(self, ItemId=None, **kwargs):
        if ItemId is None:
            raise ValueError('ItemId is required.')
        if 'ItemIdType' in kwargs:
            ItemIdType = kwargs['ItemIdType']
        else:
            ItemIdType = 'ASIN'
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
        elif 'ASIN' not in kwargs and 'OfferListingId' not in kwargs:
            raise ValueError('Must provide a valid ASIN'
                             ' or OfferListingId to add.')

        if 'OfferListingId' in kwargs:
            item_type = 'OfferListingId'
        else:
            item_type = 'ASIN'
            self._check_valid_asin(kwargs[item_type])
        Quantity = kwargs.get('Quantity', '1')
        self._check_valid_quantity(Quantity)

        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        items = kwargs[item_type]
        items = items.split(',') if ',' in items else [items]
        for item in items:
            params.update({
                'Item.%d.%s' % (items.index(item), item_type): item,
                'Item.%d.Quantity' % items.index(item): Quantity
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
        ItemIdType = kwargs.get('ItemIdType', 'ASIN')

        if ItemIdType.upper() == 'ASIN':
            self._check_valid_asin(ItemId)

        Quantity = kwargs.get('Quantity', '1')
        if isinstance(Quantity, str) and ',' in Quantity:
            Quantity = Quantity.split(',')
        if isinstance(Quantity, list) and len(Quantity) != len(ItemId):
            raise AmazonException('Weird stuff with multiple items and '
                                  'their quantities is not matching up.')
        elif not isinstance(Quantity, list):
            Quantity = [Quantity] * len(ItemId)

        self._check_valid_quantity(Quantity)
        ItemId = ItemId.split(',') if ',' in ItemId else [ItemId]
        for i, item_id in enumerate(ItemId):
            params = {
                'Item.%d.%s' % (i, ItemIdType): item_id,
                'Item.%d.Quantity' % i: Quantity[i]
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
        elif isinstance(CartItemId, str) and ',' in CartItemId:
            CartItemId = CartItemId.split(',')
        if not isinstance(CartItemId, list):
            CartItemId = [CartItemId]
        Quantity = kwargs.get('Quantity', '1')
        self._check_valid_quantity(Quantity)
        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        for i, item in enumerate(CartItemId):
            params.update({
                'Item.%d.CartItemId' % i: item,
                'Item.%d.Quantity' % i: Quantity[i]
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
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
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
            'AssociateTag': self.AssociateTag,
            'AWSAccessKeyId': self.AWSAccessKeyId,
            'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        params.update(kwargs)
        quoted_params = self._quote_params(params)
        server = DOMAINS[self.Region]

        msg = 'GET\n' + server + '\n' + '/onca/xml\n' + quoted_params

        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')
        if isinstance(self.AWSAccessKeySecret, unicode):
            self.AWSAccessKeySecret = self.AWSAccessKeySecret.encode('utf-8')

        signature = b64encode(hmac.new(self.AWSAccessKeySecret, msg, sha256).digest())
        urlinputs = (server, quoted_params, quote(signature))
        return 'http://%s/onca/xml?%s&Signature=%s' % urlinputs

    def _handle_request_errors(self, response):
        status_code = response.status_code
        if status_code != 200:
            err = xmltodict.parse(response.text)
            err_code = err[self.Operation + 'ErrorResponse']['Error']['Code']
            err_msg = err[self.Operation + 'ErrorResponse']['Error']['Message']
            LOGGER.debug(response.text)
            LOGGER.error('Amazon %sRequest STATUS %s: %s - %s',
                         self.Operation, status_code, err_code, err_msg)
            raise AmazonException('AmazonRequestError %s: %s - %s' % \
                                  (status_code, err_code, err_msg))

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

                response = requests.get(self._signed_url(**kwargs),
                                        timeout=self.timeout,
                                        headers=headers)
                self._handle_request_errors(response)
                trying = False
            except (AmazonException, requests.exceptions.ConnectTimeout) as err:
                LOGGER.warning('Error encountered: %s.  Retrying...', err)
                if try_num >= self.retry_count:
                    raise err
                time.sleep(3)
        return xmltodict.parse(response.text)[self.Operation + 'Response']


__all__ = ['ProductAdvertisingAPI']
