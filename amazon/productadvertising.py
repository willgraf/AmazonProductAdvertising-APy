#!/usr/bin/env
# -*- coding: utf-8 -*-
import sys
_ver = sys.version_info

if _ver[0] == 2:
    from urllib import quote as quote
elif _ver[0] == 3:
    from urllib.parse import quote as quote

from base64 import b64encode
from hashlib import sha256
import time
import hmac
import logging

import xmltodict
import requests

from .exceptions import AmazonException


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


logger = logging.getLogger(__name__)


"""
Executes AmazonRequests.
Contains functions for each of the main calls of the Amazon API.
Required parameters are defined in the function, but users can
customize their requests with Keyword Arguments.  It is required
that the keyword name be that of the paramter in the API documentation.
"""


class ProductAdvertisingAPI(object):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret,
                 Region='US', Version='2013-08-01', qps=None, timeout=None):
        if (AssociateTag is None) or (AWSAccessKeyId is None) or (AWSAccessKeySecret is None):
            raise ValueError('Your Amazon Credentials are'
                             ' required and cannot be None.')
        if not isinstance(Region, str) or Region.upper() not in DOMAINS:
            raise ValueError('Your region is currently unsupported.')
        if qps:
            try:
                qps = float(qps)
            except:
                raise ValueError('qps (query per second) must be a number.')
        self.AssociateTag = AssociateTag
        self.AWSAccessKeyId = AWSAccessKeyId
        self.AWSAccessKeySecret = AWSAccessKeySecret
        self.Region = Region
        self.Version = Version
        self.timeout=timeout
        self.qps = qps
        self.Service = 'AWSECommerceService'
        self.ITEM_ID_MAX = 10
        self._last_time = None

    def _make_request(self, name, **kwargs):
        request = AmazonRequest(self.AssociateTag, self.AWSAccessKeyId,
                                self.AWSAccessKeySecret, Operation=name,
                                Region=self.Region, Service=self.Service,
                                Version=self.Version, timeout=self.timeout)

        if self.qps is not None and self.qps > 0:
            if self._last_time is not None:
                wait_time = 1 / self.qps - (time.time() - self._last_time)
                if wait_time > 0:
                    logger.warning('Waiting %s secs to send next Request.',
                                   round(wait_time, 3))
                    time.sleep(wait_time)
            self._last_time = time.time()
        return request.execute(**kwargs)

    def _check_valid_asin(self, asin):
        asin = asin.split(',') if ',' in asin else [asin]
        bad_asins = [a for a in asin if len(a) != 10 or a[0].upper() != 'B']
        if len(bad_asins) > 0:
            raise ValueError('INVALID ASIN: "%s".  ASIN is 10 characters long'
                             ' and starts with a "B".' % str(bad_asins))

    def _check_valid_quantity(self, quantity):
        try:
            quantity = int(quantity)
            if quantity < 0 or quantity > 999:
                raise TypeError
        except TypeError:
            raise ValueError('Invalid Quantity "%s": Quantity must be between'
                             ' 0 and 999, inclusive.' % str(quantity))

    def _handle_errors(self, request):
        if 'Errors' in request:
            errors = request['Errors']['Error']
            errors = [errors] if type(errors) is not list else errors
            for e in errors:
                err_message = e['Message']
                err_code = e['Code']
                logger.error('%s  -  %s' % (err_code, err_message))
                raise AmazonException('%s  -  %s' % (err_code, err_message))
        return self

    def _parse_multiple_items(self, data):
        if type(data) is str and ',' in data:
            data = data.split(',')
        if type(data) is not list:
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
            'ItemId': ItemId
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
        Quantity = '1' if 'Quantity' not in kwargs else kwargs['Quantity']
        self._check_valid_quantity(Quantity)

        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        items = kwargs[item_type]
        if ',' in items:
            items = items.split(',')
        else:
            items = [items]
        for item in items:
            i = {
                'Item.%d.%s' % (items.index(item), item_type): item,
                'Item.%d.Quantity' % items.index(item): Quantity
            }
            params.update(i)
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
        if 'ItemIdType' in kwargs:
            ItemIdType = kwargs['ItemIdType']
        else:
            ItemIdType = 'ASIN'
            self._check_valid_asin(ItemId)
        if ',' in ItemId:
            ItemId = ItemId.split(',')
        else:
            ItemId = [ItemId]
        if 'Quantity' in kwargs:
            Quantity = kwargs['Quantity']
            if type(Quantity) is str and ',' in Quantity:
                Quantity = Quantity.split(',')
            if type(Quantity) is list and len(Quantity) != len(ItemId):
                raise AmazonException('Weird stuff with multiple items and '
                                      'their quantities is not matching up.')
        else:
            Quantity = '1'
   
        for i in xrange(len(ItemId)):
            params = {
                'Item.%d.%s' % (i, ItemIdType): ItemId[i],
                'Item.%d.Quantity' % i: Quantity
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
        elif type(CartItemId) is str and ',' in CartItemId:
            CartItemId = CartItemId.split(',')
        if type(CartItemId) is not list:
            CartItemId = [CartItemId]
        Quantity = '1' if 'Quantity' not in kwargs else kwargs['Quantity']
        self._check_valid_quantity(Quantity)
        params = {
            'CartId': CartId,
            'HMAC': HMAC
        }
        for item in CartItemId:
            i = CartItemId.index(item)
            params.update({
                'Item.%d.CartItemId' % i: item,
                'Item.%d.Quantity' % i: Quantity[i]
            })
        kwargs.update(params)
        response = self._make_request('CartModify', **kwargs)
        self._handle_errors(response['Cart']['Request'])
        return response


"""
AmazonRequest class.. Initializes with Amazon API Credentials
(KEY_ID, KEY_SECRET, ASSOCIATE TAG) as well as the
API Operation Name, the target Region, the Service,
and the Version.

This class is created only by the ProductAdvertisingAPI.
"""


class AmazonRequest(object):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret,
                 Operation, Region, Service, Version, timeout):
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

    def _quote_params(self, params):
        key_values = []
        for k, v in params.iteritems():
            if type(k) is not str:
                k = str(k)
            if type(v) is not str:
                v = str(v)
            key_values.append((quote(k), quote(v)))
        key_values.sort()
        return '&'.join(['%s=%s' % (k, v) for k, v in key_values])

    def _timestamp(self):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    def _signed_url(self, **kwargs):
        params = {'Operation': self.Operation,
                  'Service': self.Service,
                  'Version': self.Version,
                  'AssociateTag': self.AssociateTag,
                  'AWSAccessKeyId': self.AWSAccessKeyId,
                  'Timestamp': self._timestamp()}

        params.update(kwargs)
        quoted_params = self._quote_params(params)
        server = DOMAINS[self.Region]

        msg = 'GET\n' + server + '\n' + '/onca/xml\n' + quoted_params

        if type(msg) is unicode:
            self.msg = msg.encode('utf-8')
        if type(self.AWSAccessKeySecret) is unicode:
            self.AWSAccessKeySecret = self.AWSAccessKeySecret.encode('utf-8')

        signature = b64encode(hmac.new(self.AWSAccessKeySecret, msg, sha256).digest())
        urlinputs = (server, quoted_params, quote(signature))
        return 'http://%s/onca/xml?%s&Signature=%s' % urlinputs

    def execute(self, **kwargs):
        trying, try_num = True, 0
        while trying and try_num < 3:
            try:
                try_num += 1
                response = requests.get(self._signed_url(**kwargs),
                                        timeout=self.timeout)
                trying = False
            except requests.exceptions.ConnectTimeout as e:
                logger.warning('Error encountered: %s.  Retrying...', e)
                time.sleep(3)
        status_code = response.status_code
        if status_code != 200:
            e = xmltodict.parse(response.text)
            eCode = e[self.Operation + 'ErrorResponse']['Error']['Code']
            eMsg = e[self.Operation + 'ErrorResponse']['Error']['Message']
            logger.debug(response.text)
            logger.error('Amazon %sRequest STATUS %s: %s - %s',
                         self.Operation, status_code, eCode, eMsg)
            raise AmazonException(
                'AmazonRequestError %s: %s - %s' % (status_code, eCode, eMsg))
        return xmltodict.parse(response.text)[self.Operation + 'Response']


__all__ = ['ProductAdvertisingAPI']
