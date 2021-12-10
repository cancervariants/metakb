"""Module for terminating MetaKB EB environment."""
import boto3
import json
import time
client = boto3.client('lambda')
servicecatalog = boto3.client('servicecatalog')
eb_env_name = "metakb-dev-env"
data = {"sc_provisioned_name": eb_env_name}
client.invoke(FunctionName='igm-inf-terminate-provisioned-product',
              Payload=json.dumps(data))
time.sleep(10)
provisioned_product =\
    servicecatalog.describe_provisioned_product(Name=eb_env_name)
eb_provisioned_product_Id = \
    provisioned_product['ProvisionedProductDetail']['Id']
product_status = servicecatalog.describe_provisioned_product(
    Id=eb_provisioned_product_Id)
eb_provisioned_product_status = \
    product_status['ProvisionedProductDetail']['Status']
while eb_provisioned_product_status == "UNDER_CHANGE":
    time.sleep(10)
    try:
        product_status = servicecatalog.describe_provisioned_product(
            Id=eb_provisioned_product_Id)
        eb_provisioned_product_status = \
            product_status['ProvisionedProductDetail']['Status']
    except:  # noqa: E722
        eb_provisioned_product_status = "PRODUCT NOT FOUND"
    print(eb_provisioned_product_status)
