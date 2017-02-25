#!/usr/bin/env
# -*- coding: utf-8 -*-

"""
Classes to wrap the Product Advertising API
Each Amazon Cart stays alive for ~30 days. To retrieve a cart and its contents,
the CartId, HMAC, and AssociateTag are needed.
CartId is returned in Response from CartCreate.
AssociateTag is required along with AWSAccessKeyId and AWSAccessKeySecret
"""

from collections import OrderedDict
import logging
import json, pdb

from amazonproductadvertising.productadvertising import ProductAdvertisingAPI
from amazonproductadvertising.exceptions import CartException, AmazonException


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

        resp_group = kwargs.pop('ResponseGroup', 'ItemAttributes,OfferFull,Offers,Images,Large')

        items = []
        for i in xrange(0, len(ItemId), self.item_lookup_max):
            response = self.ItemLookup(ItemId=','.join(ItemId[i : i + self.item_lookup_max]),
                                       ResponseGroup=resp_group, **kwargs)
            try:
                xml = response['Items']['Item']
            except KeyError:
                xml = []
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
        super(AmazonCart, self).__init__(AssociateTag, AWSAccessKeyId, AWSAccessKeySecret, **kwargs)
        item_id = kwargs.get('ItemId', kwargs.get('ASIN'))
        quantity = kwargs.get('Quantity', '1')
        self.cart_id = kwargs.get('CartId')
        self.hmac = kwargs.get('HMAC')
        self.url = kwargs.get('URL')
        self.items = kwargs.get('CartItems', [])
        self.subtotal = kwargs.get('SubTotal', 0.0)
        if not self.cart_id and item_id:
            self.create(ItemId=item_id, Quantity=quantity)

    @property
    def response(self):
        """
        print the response, for debugging purposes
        """
        if self._response:
            print(json.dumps(self._response, indent=4))

    def _update(self, response):
        """update instance properties from response"""
        # Update most important properties
        try:
            self.cart_id = response['Cart']['CartId']
            self.hmac = response['Cart']['HMAC']
        except KeyError as err:
            raise CartException('%s not in Cart Response!' % err)
        # Get URL and SubTotal
        try:
            self.url = response['Cart'].get('PurchaseURL', self.url)
            subtotal = response['Cart'].get('SubTotal', {}).get('Amount', self.subtotal)
            self.subtotal = int(subtotal) / 100.0
        except (ValueError, TypeError):
            LOGGER.warn('Error parsing subtotal for response')
        # update items; Create (and Get?) returns CartItems
        # otherwise it will change the Quantity values in self.items
        request = response['Cart']['Request']
        if 'CartClearRequest' in request:
            self.items = []
        elif 'CartCreateRequest' in request:
            self.items = self._parse_cart_items(response)
        elif 'CartAddRequest' in request:
            self.items = self._parse_cart_items(response)
        elif 'CartModifyRequest' in request:
            self.items = self._parse_modified_items(response)
        elif 'CartGetRequest' in request:
            self.items = self._parse_cart_items(response)
        else:
            raise CartException('Unknown Request Type!' % str(request))

        return self

    def _parse_modified_items(self, response):
        """
        CartModify does not return CartItems, must make relative update
        """
        # cart_items = self._parse_cart_items(response)
        mod_items = response['Cart']['Request']['CartModifyRequest']['Items']['Item']
        if mod_items is None:
            items = []
        elif isinstance(mod_items, OrderedDict):
            items = [dict(mod_items)]
        else:
            items = [dict(ord_dict) for ord_dict in mod_items]

        mod_ids = {i['CartItemId']: i['Quantity'] for i in items}
        parsed_items = []
        for item in self.items:
            try:
                if item['CartItemId'] not in mod_ids:
                    parsed_items.append(item)
                else:
                    quantity = int(mod_ids[item['CartItemId']])
                    if quantity > 0:
                        parsed_items.append({
                            'ASIN': item['ASIN'],
                            'CartItemId': item['CartItemId'],
                            'Title': item['Title'],
                            'Quantity': quantity,
                            'Price': int(item['Price'])
                        })
            except (KeyError, IndexError):
                LOGGER.error('Error parsing item: %s', item)

        return parsed_items

    def _parse_cart_items(self, response):
        """
        If CartItems in response, parses them into regular dicts
        and returns them as a list.
        """
        new_items = response['Cart'].get('CartItems', {}).get('CartItem')

        if new_items is None:
            items = []
        elif isinstance(new_items, OrderedDict):
            items = [dict(new_items)]
        else:
            items = [dict(ord_dict) for ord_dict in new_items]

        parsed_items = []
        for item in items:
            try:
                parsed_items.append({
                    'ASIN': item['ASIN'],
                    'CartItemId': item['CartItemId'],
                    'Title': item['Title'],
                    'Quantity': int(item['Quantity']),
                    'Price': int(item['Price']['Amount']) / 100.0
                })
            except (KeyError, IndexError):
                LOGGER.error('Error parsing item: %s', item)

        return parsed_items

    def create(self, ItemId=None, **kwargs):
        """
        udpates instance attributes to refelct the status the newly created cart
        returns new AmazonCart
        """
        item_id = kwargs.get('ASIN', ItemId)
        quantity = kwargs.get('Quantity', '1')
        response = super(AmazonCart, self).CartCreate(ItemId=item_id, Quantity=quantity)
        self._update(response)
        return self

    def clear(self, **kwargs): # Bad Info Combination? -> AssociateTag + CartId + HMAC
        """
        Clears the contents of the Cart
        """
        if not self.cart_id or not self.hmac:
            LOGGER.error('Clearing Cart before it has been initialized.  Please create one first')
            return self

        response = super(AmazonCart, self).CartClear(CartId=self.cart_id, HMAC=self.hmac, **kwargs)
        self._update(response)
        return self

    def get(self, CartId, CartItemId, HMAC, **kwargs):
        """
        Fetch a remote AmazonCart.  AmazonCarts will stay alive
        for ~30 days after being abandoned.
        Perhaps can save this as a field in the db for easier fulfillment.
        """
        response = super(AmazonCart, self).CartGet(CartId=CartId, HMAC=HMAC,
                                                   CartItemId=CartItemId, **kwargs)
        self._update(response)
        return self

    def remove(self, ItemId, **kwargs):
        """
        remove ItemId from Cart.
        Is really just a modify call with Quantity=0
        """
        ItemId = self._parse_multiple_items(ItemId)
        Quantity = self._parse_multiple_items(kwargs.pop('Quantity', 0))
        if len(Quantity) == 1:
            Quantity = Quantity * len(ItemId)

        item_ref = {item['ASIN']: item['Quantity'] for item in self.items}
        rem_items, rem_quantity = [], []
        for item_id, quantity in zip(ItemId, Quantity):
            # sku already in cart, so just want to update itemQuantity -= Quantity
            if item_id in item_ref:
                rem_items.append(item_id)
                if quantity > 0:
                    rem_quantity.append(max(int(item_ref[item_id] - int(quantity)), 0))
                else:
                    rem_quantity.append(quantity)

        self.modify(ItemId=rem_items, Quantity=rem_quantity)
        return self

    def modify(self, ItemId, Quantity, **kwargs):
        """
        CartModify can change the Quantity of items existing in the cart,
        or move items to "SaveForLater".  Cannot add new items to the cart.
        If Quantity is not given, it defaults to 0 (remove the item)
        """
        asin_lookup = {item['ASIN']: item for item in self.items}
        cartitem_lookup = {item['CartItemId']: item for item in self.items}
        ItemId = self._parse_multiple_items(ItemId)

        # classify the itemId, ASIN vs CartItemId
        cart_item_ids = {}
        for i in ItemId:
            if i in asin_lookup:
                cart_item_ids[asin_lookup[i]['CartItemId']] = asin_lookup[i]['Quantity']
            elif i in cartitem_lookup:
                cart_item_ids[i] = cartitem_lookup[i]['Quantity']
            else:
                LOGGER.warn('%s is not a valid ASIN or CartItemId in the Cart. Ignoring.', i)

        if len(cart_item_ids) > 0:
            if not isinstance(Quantity, list):
                Quantity = [Quantity] * len(cart_item_ids)
            
            response = super(AmazonCart, self).CartModify(CartId=self.cart_id, HMAC=self.hmac,
                                                          CartItemId=cart_item_ids.keys(),
                                                          Quantity=Quantity, **kwargs)

            self._update(response)
        else:
            LOGGER.warn('Could not find any ItemId in Cart Items.')

        return self

    def add(self, ItemId=None, **kwargs): # Missing Quantity??
        """
        adds item to cart
        ItemId may be a list of ASINs (or OfferListingType, if specified as ItemIdType)
        or it may be a string of ASINs joined by commas (,).
        Quantity must either be a similar list, or if Quantity is a single value,
        that value will be applied to all items.

        If ItemId already in the Cart, will use CartModify to add to the quantity
        If ItemId not in the Cart, will use CartAdd to add the item
        """
        ItemId = kwargs.get('ASIN', ItemId)
        if ItemId is None:
            raise ValueError('Include your ASIN/OfferListingId in '
                             'kwargs as either ItemId or ASIN')

        ItemId = self._parse_multiple_items(ItemId)
        Quantity = self._parse_multiple_items(kwargs.pop('Quantity', 1))
        if len(Quantity) == 1:
            Quantity *= len(ItemId)
        self._check_valid_quantity(Quantity)

        if not self.cart_id:
            self.create(ItemId=ItemId, Quantity=Quantity)

        new_items, new_quantity = [], []
        update_items, update_quantity = [], []
        item_ref = {item['ASIN']: item for item in self.items}

        for item_id, quantity in zip(ItemId, Quantity):
            # sku already in cart, so just want to update itemQuantity += Quantity
            if item_id in item_ref:
                update_items.append(item_id)
                update_quantity.append(int(quantity) + int(item_ref[item_id]['Quantity']))
            else:
                new_items.append(item_id)
                new_quantity.append(quantity)

        if len(update_items) > 0:# updates are having trouble
            self.modify(ItemId=update_items, Quantity=update_quantity, **kwargs)

        if len(new_items) > 0:
            response = super(AmazonCart, self).CartAdd(
                CartId=self.cart_id, HMAC=self.hmac, ItemId=new_items,
                Quantity=new_quantity, **kwargs)

            self._update(response)

        return self
