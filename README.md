# AmazonProductAdvertising-APy
Simple interface for the Amazon Product Advertising API 

For API Request details, see the [AWS documentation.](http://docs.aws.amazon.com/AWSECommerceService/latest/DG/Welcome.html)

To use:

```python
# the credentials will be provided by Amazon when registering for the API.
amazon = AmazonAPI(AssociateTag="<YOUR-ASSOCIATE-TAG>",
                   AWSAccessKeyId="<YOUR-AWS-KEY-ID>",
                   AWSAccessKeySecret="<YOUR-AWS-KEY-SECRET>",

item_details = amazon.ItemLookup(ItemId='B123456789',
                                 ResponseGroup='ItemAttributes,OfferFull,Offers')

```
