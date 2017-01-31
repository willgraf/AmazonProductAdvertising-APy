#!/usr/bin/env
# -*- coding: utf-8 -*-

"""Classes to wrap the Product Advertising API"""

import logging

from amazon.productadvertising import ProductAdvertisingAPI


LOGGER = logging.getLogger(__name__)


class Amazon(ProductAdvertisingAPI):

    """
    ProductAdvertisingAPI Wrapper.  Primary Interface for the API.
    Makes API requests and filters the response into a human readable,
    and developer friendly, format.
    """

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs):
        super(Amazon, self).__init__(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs)
        # self.cart = AmazonCart(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret)
        self.item_lookup_max = 10

    def lookup(self, ItemId, **kwargs):
        """
        lookup a list of items from ItemId, if trying to lookup multiple
        ItemId, lookup will execute requests in batches of 10.
        """
        if isinstance(ItemId, str):
            ItemId = ItemId.split(',') if ',' in ItemId else ItemId
        ItemId = ItemId if isinstance(ItemId, list) else [ItemId]
        items = []
        for i in xrange(0, len(ItemId), self.item_lookup_max):
            response = self.ItemLookup(
                ItemId=','.join(ItemId[i : i + self.item_lookup_max]),
                ResponseGroup='ItemAttributes,Offers,Images,Large',
                **kwargs
            )
            xml = response['Items']['Item']
            xml = [xml] if not isinstance(xml, list) else xml
            items.extend(xml)
        return items


class AmazonCart(ProductAdvertisingAPI):

    """
    Amazon Cart.
    Class to perform the Amazon Cart calls.  Each class represents an Amazon Cart
    with a unique CartId and can be filled with items of type ASIN or OfferListingId.
    Each of its Items has a unique CartItemId as well.
    """

    def __init__(self, AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs):
        super(AmazonCart, self).__init__(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret)
        self.cart_id = kwargs.pop('CartId')
        self.hmac = kwargs.pop('HMAC')
        self.url = kwargs.pop('URL')
        self.items = []
        if self.cart_id is None:
            self.cart_id, self.hmac = self.new()

    def new(self, **kwargs):
        """returns new AmazonCart"""
        response = super(AmazonCart, self).CartCreate(**kwargs)
        cartid = response['Cart']['CartId']
        hmac = response['Cart']['HMAC']
        return cartid, hmac


    def add(self, ItemId, Quantity='1', **kwargs):
        """adds item to cart"""
        super(AmazonCart, self).CartAdd(ItemId=ItemId, Quantity=Quantity, **kwargs)
        self.items.append(AmazonItem(ItemId, Quantity))


class AmazonItem(object):

    """
    Amazon Item.
    Class to hold and access Amazon Item Information.
    """

    def __init__(self, ItemId, Quantity='1'):
        self.item_id = ItemId
        self.quantity = Quantity
