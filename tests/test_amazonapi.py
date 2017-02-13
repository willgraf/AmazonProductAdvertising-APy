#!/usr/bin/env
# -*- coding: utf-8 -*-
import json
import pytest
import sys, os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from amazonproductadvertising.api import Amazon, AmazonCart
from amazonproductadvertising.exceptions import AmazonException

# Setting up testing variables
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)['Amazon']
    ASSOC_TAG = config['AssociateTag']
    AWS_ID = config['AccessKeyId']
    AWS_SECRET = config['AccessKeySecret']
    del config

TEST_ASIN = 'B00JM5GW10'
TEST_ASIN_2 = 'B00WI0QCAM'
TEST_ASIN_3 = 'B018HB2QFU'
BAD_ASIN = 'ABC123'

AMAZON = Amazon(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=2, retry_count=1)
CART = AmazonCart(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=2, retry_count=1)

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
        assert (CART.cart_id is not None and CART.hmac is not None and
                len(CART.items) == 1 and cart_asin == TEST_ASIN)

    def test_amazon_cart_create_multi_item(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        cart_asin_1 = CART.items[0]['ASIN']
        cart_asin_2 = CART.items[1]['ASIN']
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 2 and
                cart_asin_1 == TEST_ASIN and cart_asin_2 == TEST_ASIN_2)

    # AmazonCart.add(ItemId, Quantity) tests

    def test_amazon_cart_add_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_add_bad_quantity(self):
        with pytest.raises(ValueError) as err:
            CART.create(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)

    def test_amazon_cart_add_one_item(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=TEST_ASIN_2, Quantity=1)
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 2)

    def test_amazon_cart_add_multi_item(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=[TEST_ASIN_2, TEST_ASIN_3], Quantity=1)
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 3)

    def test_amazon_cart_add_multi_item_one_exists(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.add(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        items = {item['ASIN']: item['Quantity'] for item in CART.items}
        assert (CART.cart_id is not None and CART.hmac is not None and
                len(CART.items) == 2 and items[TEST_ASIN] == 2 and items[TEST_ASIN_2] == 1)

    # AmazonCart.remove(asin, asin2) tests

    def test_amazon_cart_remove_one_not_in_cart(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.remove(ItemId=TEST_ASIN_2)
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 1
                and CART.items[0]['ASIN'] == TEST_ASIN)

    def test_amazon_cart_remove_only_one_in_cart(self):
        CART.create(ItemId=[TEST_ASIN], Quantity=1)
        CART.remove(ItemId=TEST_ASIN)
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0)

    def test_amazon_cart_remove_one_in_multi_cart(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        CART.remove(ItemId=TEST_ASIN)
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 1
                and CART.items[0]['ASIN'] == TEST_ASIN_2)

    def test_amazon_cart_remove_many_in_cart(self):
        CART.create(ItemId=[TEST_ASIN, TEST_ASIN_2], Quantity=1)
        CART.remove(ItemId=[TEST_ASIN, TEST_ASIN_2])
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0)

    def test_amazon_cart_remove_many_singleton_cart(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.remove(ItemId=[TEST_ASIN, TEST_ASIN_2])
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0)

    # AmazonCart.clear() tests

    def test_amazon_cart_clear(self):
        CART.create(ItemId=TEST_ASIN, Quantity=1)
        CART.clear()
        assert (CART.cart_id is not None and CART.hmac is not None and len(CART.items) == 0)

