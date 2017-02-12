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

TEST_ASIN = 'B0080YHBR8'
TEST_ASIN_2 = 'B000CSS8UE'
BAD_ASIN = 'ABC123'

AMAZON = Amazon(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=.88, retry_count=1)
CART = AmazonCart(ASSOC_TAG, AWS_ID, AWS_SECRET, TEST_ASIN, qps=.88, retry_count=1)


# Start Testing methods

class TestAmazon:

    def test_amazon_lookup_bad_response_group(self):
        with pytest.raises(AmazonException) as err:
            response = AMAZON.lookup(TEST_ASIN, ResponseGroup='badresponsegroup')
        assert 'ResponseGroup is invalid' in str(err)
        
    def test_amazon_lookup_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            AMAZON.lookup([TEST_ASIN, BAD_ASIN])
        assert 'INVALID ASIN' in str(err)


class TestAmazonCart:

    def test_amazon_cart_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            AmazonCart(ASSOC_TAG, AWS_ID, AWS_SECRET, BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_new_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            CART.new(ItemId=BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_new_bad_quantity(self):
        with pytest.raises(ValueError) as err:
            CART.new(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)

    def test_amazon_cart_add_bad_item_id(self):
        with pytest.raises(ValueError) as err:
            CART.new(ItemId=BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_amazon_cart_add_bad_quantity(self):
        with pytest.raises(ValueError) as err:
            CART.new(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)

    def test_amazon_cart_clear(self):
        with pytest.raises(ValueError) as err:
            CART.new(ItemId=TEST_ASIN, Quantity='badquantity')
        assert 'Invalid Quantity' in str(err)


