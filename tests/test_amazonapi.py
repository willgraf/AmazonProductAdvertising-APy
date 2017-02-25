#!/usr/bin/env
# -*- coding: utf-8 -*-
import json
import pytest
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from paapy.api import Amazon, AmazonCart
from paapy.exceptions import AmazonException

# Setting up testing variables
with open('./config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

ASSOC_TAG = CONFIG['AssociateTag']
AWS_ID = CONFIG['AccessKeyId']
AWS_SECRET = CONFIG['AccessKeySecret']
QPS = CONFIG['QPS']

TEST_ASIN = 'B00JM5GW10'
TEST_ASIN_2 = 'B00WI0QCAM'
TEST_ASIN_3 = 'B018HB2QFU'
BAD_ASIN = 'ABC123'

AMAZON = Amazon(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=QPS, retry_count=0, Validate=True)
CART = AmazonCart(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=QPS, retry_count=0, Validate=True)

# Start Testing methods

class TestAmazon:

    # Amazon.lookup(ASIN) Tests

    def test_amazon_lookup_bad_response_group(self):
        with pytest.raises(AmazonException) as err:
            response = AMAZON.lookup(TEST_ASIN, ResponseGroup='badresponsegroup')
        assert 'ResponseGroup is invalid' in str(err)
        
    def test_amazon_lookup_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            AMAZON.lookup([TEST_ASIN, BAD_ASIN])
        assert 'INVALID ASIN' in str(err)

    def test_amazon_lookup_valid_input(self):
        response = AMAZON.lookup(TEST_ASIN)
        assert response is not None

    def test_amazon_lookup_valid_multi_input(self):
        response = AMAZON.lookup([TEST_ASIN, TEST_ASIN_2])
        assert response is not None


class TestAmazonCart:

    # AmazonCart.create(ItemId, Quantity) tests

    def test_amazon_cart_create_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_create_bad_quantity(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)

    def test_amazon_cart_create_one_item(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        cart_asin = CART.items[0]['ASIN']
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 1 and cart_asin == TEST_ASIN

    def test_amazon_cart_create_multi_item(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        asin_1 = CART.items[0]['ASIN']
        asin_2 = CART.items[1]['ASIN']
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 2 and asin_1 == TEST_ASIN and asin_2 == TEST_ASIN_2

    # AmazonCart.add(ItemId, Quantity) tests

    def test_amazon_cart_add_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=TEST_ASIN, Quantity=1)
            CART.add(ItemId=BAD_ASIN, Quantity=1)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_add_bad_quantity(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=TEST_ASIN, Quantity=1)
            CART.add(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)

    def test_amazon_cart_add_one_item(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=TEST_ASIN_2, Quantity=1)
        test_asins = set([item['ASIN'] for item in CART.items])
        val_asins = set([TEST_ASIN, TEST_ASIN_2])
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 2 and test_asins == val_asins

    def test_amazon_cart_add_multi_item(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=[TEST_ASIN_2, TEST_ASIN_3], Quantity=1)
        test_asins = set([item['ASIN'] for item in CART.items])
        val_asins = set([TEST_ASIN, TEST_ASIN_2, TEST_ASIN_3])
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 3 and test_asins == val_asins

    def test_amazon_cart_add_item_in_cart(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=TEST_ASIN, Quantity=1)
        items = {str(item['ASIN']): item['Quantity'] for item in CART.items}
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 1 and items.get(TEST_ASIN) == 2

    def test_amazon_cart_add_multi_item_one_exists(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        items = {str(item['ASIN']): item['Quantity'] for item in CART.items}
        assert CART.cart_id is not None and CART.hmac is not None and \
               items[TEST_ASIN] == 2 and items[TEST_ASIN_2] == 1 and len(CART.items) == 2

    # AmazonCart.clear() tests

    def test_amazon_cart_clear(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.clear()
        assert CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0

    # AmazonCart.get() tests

    def test_amazon_cart_get(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        cart_id = CART.cart_id
        cart_item_id = CART.items[0]['CartItemId']
        hmac = CART.hmac
        CART.create(ItemId=TEST_ASIN_2, Quantity=1)
        CART.get(CartId=cart_id, CartItemId=cart_item_id, HMAC=hmac)
        new_item_id = CART.items[0]['CartItemId']
        assert cart_id == CART.cart_id and cart_item_id == new_item_id and hmac == CART.hmac

    # AmazonCart.remove(ItemId) tests

    def test_amazon_cart_remove_one_of_many(self):
        CART.create(ItemId=TEST_ASIN, Quantity=3)
        CART.remove(ItemId=TEST_ASIN, Quantity=1)
        assert len(CART.items) == 1 and CART.items[0]['ASIN'] == TEST_ASIN and \
               CART.items[0]['Quantity'] == 2

    def test_amazon_cart_remove_some_of_many(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=[3, 2])
        CART.remove(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=[1, 1])
        assert len(CART.items) == 2 and CART.items[0]['ASIN'] == TEST_ASIN and \
               CART.items[0]['Quantity'] == 2 and CART.items[1]['ASIN'] == TEST_ASIN_2 and \
               CART.items[1]['Quantity'] == 1

    def test_amazon_cart_remove(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2])
        CART.remove(ItemId=TEST_ASIN_2)
        asin = [i['ASIN'] for i in CART.items]
        assert len(asin) == 1 and TEST_ASIN_2 not in asin

    def test_amazon_cart_remove_singleton(self):
        CART.create(ItemId=TEST_ASIN)
        CART.remove(ItemId=TEST_ASIN)
        assert CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0

    def test_amazon_cart_remove_multi(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2])
        CART.remove(ItemId=[TEST_ASIN, TEST_ASIN_2])
        assert CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0

    def test_amazon_cart_remove_not_in_cart(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.remove(ItemId=TEST_ASIN_2)
        assert CART.cart_id is not None and CART.hmac is not None and \
               len(CART.items) == 1 and CART.items[0]['ASIN'] == TEST_ASIN
