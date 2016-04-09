#!/usr/bin/env
# -*- coding: utf-8 -*-
import json
import pytest
import sys, os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from amazon.productadvertising import ProductAdvertisingAPI
from amazon.exceptions import *

# Setting up testing variables
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)['Amazon']

ASSOC_TAG=config['AssociateTag']
AWS_ID=config['AccessKeyId']
AWS_SECRET=config['AccessKeySecret']

TEST_ASIN = 'B0080YHBR8'
TEST_ASIN_2 = 'B001E5ZWT4'
BAD_ASIN = 'ABC123'

API = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, AWS_SECRET, qps=.88)

cart = API.CartCreate(TEST_ASIN)['Cart']

TEST_HMAC = cart['HMAC']
TEST_CART = cart['CartId']

# Start Testing methods

class TestProductAdvertisingAPI:

	# Set up tests, testing valid parameters, and error checking functions.

	def test_empty_aws_key_id(self):
		with pytest.raises(ValueError) as err:
			api = ProductAdvertisingAPI(ASSOC_TAG, None, AWS_SECRET)
			api.CartCreate(TEST_ASIN)
		assert 'Amazon Credentials are required' in str(err)

	def test_bad_aws_key_id(self):
		with pytest.raises(AmazonException) as err:
			api = ProductAdvertisingAPI(ASSOC_TAG, 1, AWS_SECRET)
			api.CartCreate(TEST_ASIN)
		assert 'AmazonRequestError' in str(err)

	def test_empty_aws_key_secret(self):
		with pytest.raises(ValueError) as err:
			api = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, None)
			api.CartCreate(TEST_ASIN)
		assert 'Amazon Credentials are required' in str(err)

	# def test_bad_aws_key_secret(self):
	# 	with pytest.raises(AmazonException) as err:
	# 		api = ProductAdvertisingAPI(ASSOC_TAG, AWS_ID, 'SecretKey')
	# 		api.CartCreate(TEST_ASIN)
	# 	assert 'AmazonRequestError' in str(err)

	def test_empty_associate_tag(self):
		with pytest.raises(ValueError) as err:
			api = ProductAdvertisingAPI(None, AWS_ID, AWS_SECRET)
			api.CartCreate(TEST_ASIN)
		assert 'Amazon Credentials are required' in str(err)

	# def test_bad_associate_tag(self):
	# 	with pytest.raises(AmazonException) as err:
	# 		api = ProductAdvertisingAPI(
	# 			'dummy-associate-tag', AWS_ID, AWS_SECRET)
	# 		api.CartCreate(TEST_ASIN)
	# 	assert 'AmazonRequestError' in str(err)

	def test_invalid_qps(self):
		with pytest.raises(ValueError) as err:
			ProductAdvertisingAPI(
				ASSOC_TAG, AWS_ID, AWS_SECRET, qps='Invalid')
		assert 'QPS' in str(err).upper()

	def test_invalid_operation(self):
		with pytest.raises(ValueError) as err:
			API._make_request('InvalidName')
		assert 'INVALID OPERATION' in str(err).upper()

	def test_invalid_region(self):
		with pytest.raises(ValueError) as err:
			api = ProductAdvertisingAPI(
				ASSOC_TAG, AWS_ID, AWS_SECRET, Region=None)
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

	def test_CartAdd_empty_cart(self):
		with pytest.raises(ValueError) as err:
			API.CartAdd(ASIN=TEST_ASIN, HMAC=TEST_HMAC)
		assert 'CartId' in str(err)

	def test_CartAdd_empty_item(self):
		with pytest.raises(ValueError) as err:
			API.CartAdd(CartId=1, HMAC=TEST_HMAC)
		assert 'ASIN or OfferListingId' in str(err)

	def test_CartAdd_empty_hmac(self):
		with pytest.raises(AmazonException) as err:
			API.CartAdd(CartId=1, ASIN=TEST_ASIN)
		assert 'HMAC' in str(err)

	def test_CartAdd_bad_asin(self):
		with pytest.raises(ValueError) as err:
			API.CartAdd(CartId=1, ASIN=BAD_ASIN, HMAC=TEST_HMAC)
		assert 'INVALID ASIN' in str(err)

	def test_CartAdd_good_params(self):
		response = API.CartAdd(CartId=TEST_CART,
										  ASIN=TEST_ASIN_2,
										  HMAC=TEST_HMAC)
		req = response['Cart']['Request']
		item = str(req['CartAddRequest']['Items']['Item']['ASIN'])
		assert (req['IsValid'] == 'True') and (TEST_ASIN_2 == item)

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
		response = API.CartClear(CartId=TEST_CART, HMAC=TEST_HMAC)
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

	def test_CartCreate_good_params(self):
		response = API.CartCreate(TEST_ASIN)['Cart']['Request']
		item = str(response['CartCreateRequest']['Items']['Item']['ASIN'])
		assert response['IsValid'] == 'True' and TEST_ASIN == item

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
		response = API.CartGet(CartId=TEST_CART,
										  CartItemId=TEST_ASIN,
										  HMAC=TEST_HMAC)
		assert response['Cart']['Request']['IsValid'] == 'True'

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
			API.CartModify(CartId=TEST_CART,
									  CartItemId=TEST_ASIN)
		assert 'HMAC' in str(err)

	def test_CartModify_good_params(self):
		response = API.CartModify(CartId=TEST_CART,
										  	 CartItemId=TEST_ASIN,
										  	 HMAC=TEST_HMAC)
		assert response['Cart']['Request']['IsValid'] == 'True'
