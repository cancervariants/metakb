"""Module for deploying MetaKB EB environment."""
import boto3
import time
elasticbeanstalk = boto3.client('elasticbeanstalk')
servicecatalog = boto3.client('servicecatalog')
terminate_time = 12
eb_app_name = "metakb"
eb_env_name = "metakb-staging-env"
sc_product_id = "prod-m4b65t5jgmcm4"
print(f'Launching new Service Catalog Product for staging environment: '
      f'{eb_app_name}')
sc_product_artifacts =\
    servicecatalog.list_provisioning_artifacts(ProductId=sc_product_id)
for artifact in sc_product_artifacts['ProvisioningArtifactDetails']:
    if artifact['Active']:
        provisioning_artifact_id = artifact['Id']
try:
    eb_provisioned_product = servicecatalog.provision_product(
        ProductId=sc_product_id,
        ProvisioningArtifactId=provisioning_artifact_id,
        ProvisionedProductName=eb_env_name,
        ProvisioningParameters=[
            {
                'Key': 'Env',
                'Value': eb_app_name
            },
            {
                'Key': 'EnvType',
                'Value': 'staging'
            },
            {
                'Key': 'TerminateTime',
                'Value': str(terminate_time)
            }
        ])
    eb_provisioned_product_Id = \
        eb_provisioned_product['RecordDetail']['ProvisionedProductId']
    product_status = servicecatalog.describe_provisioned_product(
        Id=eb_provisioned_product_Id)
    eb_provisioned_product_status =\
        product_status['ProvisionedProductDetail']['Status']
    while eb_provisioned_product_status == "UNDER_CHANGE":
        time.sleep(10)
        product_status = servicecatalog.describe_provisioned_product(
            Id=eb_provisioned_product_Id)
        eb_provisioned_product_status = \
            product_status['ProvisionedProductDetail']['Status']
        print(eb_provisioned_product_status)
except:  # noqa: E722
    print("The EB environment is already running...")
