#!/usr/bin/env
# -*- coding: utf-8 -*-
import json
import pytest
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from paapy.productadvertising import ProductAdvertisingAPI
from paapy.exceptions import AmazonException

# Setting up testing variables
try:
    with open('./config.json', 'r') as config_file:
        CONFIG = json.load(config_file)
        ASSOC_TAG = CONFIG['AssociateTag']
        AWS_ID = CONFIG['AccessKeyId']
        AWS_SECRET = CONFIG['AccessKeySecret']
        QPS = CONFIG['QPS']
        del CONFIG
except:
    raise Exception('No Configuration file loaded, cannot test without amazon creds.')

TEST_ASIN = 'B00JM5GW10'
TEST_ASIN_2 = 'B00WI0QCAM'
TEST_ASIN_3 = 'B018HB2QFU'
BAD_ASIN = 'ABC123'

API = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=QPS, retry_count=0, Validate=True)

CART = API.CartCreate(TEST_ASIN)['Cart']

TEST_HMAC = CART['URLEncodedHMAC']
# TEST_URL_HMAC = cart['URLEncodedHMAC']
TEST_CART = CART['CartId']

def get_test_hmac_cartid(asin, quantity=1):
    cart = API.CartCreate(asin, Quantity=quantity)['Cart']
    return cart['HMAC'], cart['CartId']

# Start Testing methods

class TestProductAdvertisingAPI:

    # Set up tests, testing valid parameters, and error checking functions.

    def test_empty_aws_key_id(self):
        with pytest.raises(ValueError) as err:
            api = ProductAdvertisingAPI(ASSOC_TAG, None, AWS_SECRET,
                                        retry_count=0, qps=QPS)
            api.CartCreate(TEST_ASIN)
        assert 'Amazon Credentials are required' in str(err)

    def test_bad_aws_key_id(self):
        with pytest.raises(AmazonException) as err:
            api = ProductAdvertisingAPI(ASSOC_TAG, 1, AWS_SECRET,
                                        retry_count=0, qps=QPS)
            api.CartCreate(TEST_ASIN)
        assert 'AmazonRequestError' in str(err)

    def test_empty_aws_key_secret(self):
        with pytest.raises(ValueError) as err:
            api = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, None,
                                        retry_count=0, qps=QPS)
            api.CartCreate(TEST_ASIN)
        assert 'Amazon Credentials are required' in str(err)

    def test_bad_aws_key_secret(self):
        with pytest.raises(AmazonException) as err:
            api = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, 'SecretKey',
                                        retry_count=0, qps=QPS)
            api.CartCreate(TEST_ASIN)
        assert 'AmazonRequestError' in str(err)

    def test_empty_associate_tag(self):
        with pytest.raises(ValueError) as err:
            api = ProductAdvertisingAPI(None, AWS_ID, AWS_SECRET,
                                        retry_count=0, qps=QPS)
            api.CartCreate(TEST_ASIN)
        assert 'Amazon Credentials are required' in str(err)

    # def test_bad_associate_tag(self):
    #     with pytest.raises(AmazonException) as err:
    #         hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
    #         api = ProductAdvertisingAPI('ASSOC_TAG', AWS_ID, AWS_SECRET, retry_count=0, qps=QPS)
    #         api.CartAdd(CartId=cart_id, ASIN=TEST_ASIN_2, HMAC=hmac)
    #     assert 'AssociateTag' in str(err)

    def test_invalid_qps(self):
        with pytest.raises(ValueError) as err:
            ProductAdvertisingAPI(
                ASSOC_TAG, AWS_ID, AWS_SECRET, qps='Invalid', retry_count=0)
        assert 'QPS' in str(err).upper()

    def test_invalid_retry_count(self):
        with pytest.raises(ValueError) as err:
            ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, AWS_SECRET, retry_count='Invalid', qps=QPS)
        assert 'retry_count must be an integer.' in str(err)

    def test_invalid_operation(self):
        with pytest.raises(ValueError) as err:
            API._make_request('InvalidName')
        assert 'INVALID OPERATION' in str(err).upper()

    def test_invalid_region(self):
        with pytest.raises(ValueError) as err:
            api = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, AWS_SECRET, Region=None, qps=QPS)
        assert 'REGION' in str(err).upper()

    def test_invalid_asin(self):
        with pytest.raises(ValueError) as err:
            API._check_valid_asin('1234ABCDE')
        assert 'INVALID ASIN' in str(err)

    def test_valid_quantity_low(self):
        with pytest.raises(ValueError) as err:
            API._check_valid_quantity(-1)
        assert 'INVALID QUANTITY' in str(err).upper()

    def test_valid_quantity_high(self):
        with pytest.raises(ValueError) as err:
            API._check_valid_quantity(10000)
        assert 'INVALID QUANTITY' in str(err).upper()

    def test_valid_quantity_NaN(self):
        with pytest.raises(ValueError) as err:
            API._check_valid_quantity(None)
        assert 'INVALID QUANTITY' in str(err).upper()

    # API Call tests

    # Browse Node Lookup.  Requires a BrowseNodeId

    def test_BrowseNodeLookup_empty_params(self):
        with pytest.raises(ValueError) as err:
            API.BrowseNodeLookup()
        assert 'BrowseNodeId' in str(err)

    def test_BrowseNodeLookup_bad_params(self):
        invalid_node_id = -1
        with pytest.raises(AmazonException) as err:
            API.BrowseNodeLookup(invalid_node_id)
        assert 'InvalidParameter' in str(err)

    def test_BrowseNodeLookup_good_params(self):
        valid_node_id = 1000
        response = API.BrowseNodeLookup(valid_node_id)
        assert response['BrowseNodes']['Request']['IsValid'] == 'True'

    # ItemSearch.  Requires one of many keyword arguments.

    def test_ItemSearch_empty_params(self):
        with pytest.raises(AmazonException) as err:
            API.ItemSearch()
        assert 'AWS.MinimumParameterRequirement' in str(err)

    def test_ItemSearch_bad_params(self):
        invalid_param = 'Electronics'
        with pytest.raises(AmazonException) as err:
            API.ItemSearch(InvalidName=invalid_param)
        assert 'AWS.MinimumParameterRequirement' in str(err)

    def test_ItemSearch_good_params(self):
        response = API.ItemSearch(Manufacturer='Apple')
        assert response['Items']['Request']['IsValid'] == 'True'

    # Item Lookup.  Requires ASIN.

    def test_ItemLookup_empty_params(self):
        with pytest.raises(ValueError) as err:
            API.ItemLookup()
        assert 'ItemId' in str(err)

    def test_ItemLookup_bad_params(self):
        with pytest.raises(ValueError) as err:
            API.ItemLookup(BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_ItemLookup_good_params(self):
        response = API.ItemLookup(TEST_ASIN)
        assert response['Items']['Request']['IsValid'] == 'True'

    # Similarity Lookup.  Requires ASIN

    def test_SimilarityLookup_empty_params(self):
        with pytest.raises(ValueError) as err:
            API.SimilarityLookup()
        assert 'ItemId' in str(err)

    def test_SimilarityLookup_bad_params(self):
        with pytest.raises(ValueError) as err:
            API.SimilarityLookup(BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_SimilarityLookup_good_params(self):
        response = API.SimilarityLookup(TEST_ASIN)
        assert response['Items']['Request']['IsValid'] == 'True'

    # Cart Add.  Takes CartId, CartItemId, and HMAC.

    def test_CartAdd_empty_cart_id(self):
        with pytest.raises(ValueError) as err:
            API.CartAdd(ASIN=TEST_ASIN, HMAC=TEST_HMAC)
        assert 'CartId' in str(err)

    def test_CartAdd_empty_item_id(self):
        with pytest.raises(ValueError) as err:
            API.CartAdd(CartId=1, HMAC=TEST_HMAC)
        assert 'ASIN or OfferListingId' in str(err)

    def test_CartAdd_empty_hmac(self):
        with pytest.raises(ValueError) as err:
            API.CartAdd(CartId=1, ASIN=TEST_ASIN)
        assert 'HMAC' in str(err)

    def test_CartAdd_bad_asin(self):
        with pytest.raises(ValueError) as err:
            API.CartAdd(CartId=1, ASIN=BAD_ASIN, HMAC=TEST_HMAC)
        assert 'INVALID ASIN' in str(err)

    def test_CartAdd_good_params_one_item(self):
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
        response = API.CartAdd(CartId=cart_id, ASIN=TEST_ASIN_2, HMAC=hmac)
        req = response['Cart']['Request']
        items = response['Cart']['CartItems']['CartItem']
        asins = [item['ASIN'] for item in items]
        assert req['IsValid'] == 'True' and set(asins) == set([TEST_ASIN, TEST_ASIN_2])

    def test_CartAdd_good_params_multi_item(self):
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
        response = API.CartAdd(CartId=cart_id, ASIN=[TEST_ASIN_3, TEST_ASIN_2], HMAC=hmac)
        req = response['Cart']['Request']
        cart_items = response['Cart']['CartItems']['CartItem']
        item1 = str(cart_items[0]['ASIN'])
        item2 = str(cart_items[1]['ASIN'])
        assert req['IsValid'] == 'True' and TEST_ASIN_2 == item2 and TEST_ASIN_3 == item1

    def test_CartAdd_good_params_multi_item_diff(self):
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
        response = API.CartAdd(CartId=cart_id, HMAC=hmac,
                               ASIN=[TEST_ASIN_3, TEST_ASIN_2],
                               Quantity=[3, 2])
        req = response['Cart']['Request']
        cart_items = response['Cart']['CartItems']['CartItem']
        item1 = str(cart_items[0]['ASIN'])
        item2 = str(cart_items[1]['ASIN'])
        item3 = str(cart_items[2]['ASIN'])
        quant1 = int(cart_items[0]['Quantity'])
        quant2 = int(cart_items[1]['Quantity'])
        quant3 = int(cart_items[2]['Quantity'])
        assert req['IsValid'] == 'True' and TEST_ASIN_2 == item2 and TEST_ASIN_3 == item1 and \
               item3 == TEST_ASIN and quant1 == 3 and quant2 == 2 and quant3 == 1

    # Cart Clear.  Takes CartId, and HMAC.

    def test_CartClear_empty_cart(self):
        with pytest.raises(ValueError) as err:
            API.CartClear(HMAC=TEST_HMAC)
        assert 'CartId' in str(err)

    def test_CartClear_empty_hmac(self):
        with pytest.raises(ValueError) as err:
            API.CartClear(CartId=TEST_CART)
        assert 'HMAC' in str(err)

    def test_CartClear_good_params(self):
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
        response = API.CartClear(CartId=cart_id, HMAC=hmac)
        clear = 'Items' not in response['Cart']['Request']['CartClearRequest']
        assert clear and response['Cart']['Request']['IsValid'] == 'True'

    # Cart Create.  Returns CartId, CartItemId, and HMAC for other methods.

    def test_CartCreate_empty_item(self):
        with pytest.raises(ValueError) as err:
            API.CartCreate()
        assert 'ItemId' in str(err)

    def test_CartCreate_bad_item(self):
        with pytest.raises(ValueError) as err:
            API.CartCreate(BAD_ASIN)
        assert 'INVALID ASIN' in str(err)

    def test_CartCreate_good_one_item(self):
        response = API.CartCreate(TEST_ASIN)
        item = str(response['Cart']['CartItems']['CartItem']['ASIN'])
        assert response['Cart']['Request']['IsValid'] == 'True' and TEST_ASIN == item

    def test_CartCreate_good_multi_item(self):
        response = API.CartCreate([TEST_ASIN, TEST_ASIN_2])
        items = response['Cart']['CartItems']['CartItem']
        asins = [item['ASIN'] for item in items]
        assert response['Cart']['Request']['IsValid'] == 'True' and \
               asins == [TEST_ASIN, TEST_ASIN_2]

    def test_CartCreate_good_multi_item_diff_quants(self):
        diff_quants = [1, 2]
        response = API.CartCreate([TEST_ASIN, TEST_ASIN_2], Quantity=diff_quants)
        items = response['Cart']['CartItems']['CartItem']
        asins = [item['ASIN'] for item in items]
        quants = [int(item['Quantity']) for item in items]
        assert response['Cart']['Request']['IsValid'] == 'True' and \
               asins == [TEST_ASIN, TEST_ASIN_2] and quants == diff_quants

    # Cart Get.  Takes CartId, CartItemId, and HMAC.

    def test_CartGet_empty_cart(self):
        with pytest.raises(ValueError) as err:
            API.CartGet(CartItemId=TEST_ASIN, HMAC=TEST_HMAC)
        assert 'CartId' in str(err)

    def test_CartGet_empty_item(self):
        with pytest.raises(ValueError) as err:
            API.CartGet(CartId=TEST_CART, HMAC=TEST_HMAC)
        assert 'CartItemId' in str(err)

    def test_CartGet_empty_hmac(self):
        with pytest.raises(ValueError) as err:
            API.CartGet(CartId=TEST_CART, CartItemId=TEST_ASIN)
        assert 'HMAC' in str(err)

    def test_CartGet_good_params(self):
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN)
        response = API.CartGet(CartId=cart_id, CartItemId=TEST_ASIN, HMAC=hmac)
        valid_req = response['Cart']['Request']['IsValid']
        cart_id_req = response['Cart']['CartId']
        hmac_req = response['Cart']['HMAC']
        asin = response['Cart']['CartItems']['CartItem']['ASIN']
        assert valid_req == 'True' and cart_id_req == cart_id and \
               hmac_req == hmac and asin == TEST_ASIN

    # Cart Modify.  Takes CartId, CartItemId, and HMAC.

    def test_CartModify_empty_cart(self):
        with pytest.raises(ValueError) as err:
            API.CartModify(CartItemId=TEST_ASIN, HMAC=TEST_HMAC)
        assert 'CartId' in str(err)

    def test_CartModify_empty_item(self):
        with pytest.raises(ValueError) as err:
            API.CartModify(CartId=TEST_CART, HMAC=TEST_HMAC)
        assert 'CartItemId' in str(err)

    def test_CartModify_empty_hmac(self):
        with pytest.raises(ValueError) as err:
            API.CartModify(CartId=TEST_CART, CartItemId=TEST_ASIN)
        assert 'HMAC' in str(err)

    def test_CartModify_good_params_rm(self):
        new_quant = 0
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN, quantity=1)
        response = API.CartModify(CartId=cart_id, HMAC=hmac,
                                  CartItemId=TEST_ASIN, Quantity=new_quant)
        quant = int(response['Cart']['Request']['CartModifyRequest']['Items']['Item']['Quantity'])
        assert response['Cart']['Request']['IsValid'] == 'True' and quant == 0

    def test_CartModify_good_params_one_item(self):
        new_quant = 5
        hmac, cart_id = get_test_hmac_cartid(TEST_ASIN, quantity=1)
        response = API.CartModify(CartId=cart_id, HMAC=hmac,
                                  CartItemId=TEST_ASIN, Quantity=new_quant)
        quant = int(response['Cart']['Request']['CartModifyRequest']['Items']['Item']['Quantity'])
        assert response['Cart']['Request']['IsValid'] == 'True' and quant == 5

    def test_CartModify_good_params_multi_items(self):
        new_quants = [2, 4]
        hmac, cart_id = get_test_hmac_cartid([TEST_ASIN, TEST_ASIN_2], quantity=1)
        response = API.CartModify(CartId=cart_id, CartItemId=[TEST_ASIN, TEST_ASIN_2],
                                  Quantity=new_quants, HMAC=hmac)
        mod_items = response['Cart']['Request']['CartModifyRequest']['Items']['Item']
        quant1 = int(mod_items[0]['Quantity'])
        quant2 = int(mod_items[1]['Quantity'])
        assert response['Cart']['Request']['IsValid'] == 'True' and \
               quant1 == new_quants[0] and quant2 == new_quants[1]
