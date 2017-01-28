#!/usr/bin/env
# -*- coding: utf-8 -*-
import time
import logging

from productadvertising import ProductAdvertisingAPI


logger = logging.getLogger(__name__)


"""
ProductAdvertisingAPI Wrapper.  Primary Interface for the API.
Makes API requests and filters the response into a human readable,
and developer friendly, format.
"""


class Amazon(ProductAdvertisingAPI):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs):
        super(Amazon, self).__init__(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs)
        # self.cart = AmazonCart(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret)
        self.ITEM_LOOKUP_MAX = 10

    # def __getattr__(self, a):
    #     if str(a)[0] = str(a)[0].upper():
    #         raise AttributeError
    #     else:
    #         return object.__getattr__(self, a)

    def _build_query(self, array, curr_index):
        query = ''
        for i in xrange(self.ITEM_LOOKUP_MAX):
            try:
                item = array[curr_index + i]
            except IndexError:
                break
            query += str(item)
            more_room = (i + 1) < self.ITEM_LOOKUP_MAX
            last = array.index(item) >= len(array) - 1
            query = query + ',' if more_room and not last else query
        return query

    def lookup(self, ItemId, **kwargs):
        if isinstance(ItemId, str):
            ItemId = ItemId.split(',') if ',' in ItemId else ItemId
        ItemId = ItemId if isinstance(ItemId, list) else [ItemId]
        items = []
        for i in xrange(0, len(ItemId), self.ITEM_LOOKUP_MAX):
            response = self.ItemLookup(
                ItemId=self._build_query(ItemId, i),
                ResponseGroup='ItemAttributes,Offers,Images,Large',
                **kwargs
            )
            xml = response['Items']['Item']
            xml = [xml] if not isinstance(xml, list) else xml
            items.extend(xml)
        return items



"""
Amazon Cart.
Class to perform the Amazon Cart calls.  Each class represents an Amazon Cart
with a unique CartId and can be filled with items of type ASIN or OfferListingId.
Each of its Items has a unique CartItemId as well.
"""


class AmazonCart(ProductAdvertisingAPI):

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs):
        super(AmazonCart, self).__init__(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret)
        self.id = kwargs.pop('CartId')
        self.hmac = kwargs.pop('HMAC')
        self.url = kwargs.pop('URL')
        self.items = []
        if self.id is None:
            self.id, self.hmac = self.new()

    # def __getattr__(self, a):
    #     if str(a)[0] == str(a)[0].upper():
    #         raise AttributeError
    #     else:
    #         return object.__getattr__(self, a)

    def new(self, **kwargs):
        response = super(AmazonCart, self).CartCreate(**kwargs)
        cartid = response['Cart']['CartId']
        hmac = response['Cart']['HMAC']
        return cartid, hmac


    def add(self, ItemId, Quantity='1', **kwargs):
        response = super(AmazonCart, self).CartAdd(ItemId=ItemId,
                                                   Quantity=Quantity,
                                                   **kwargs)
        self.items.append(AmazonItem(ItemId, Quantity))


"""
Amazon Item.
Class to hold and access Amazon Item Information.
"""


class AmazonItem(object):
    
    def __init__(self, ItemId, Quantity='1'):
        self.id = ItemId
        self.quantity = Quantity

