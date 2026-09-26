import typing as t

import aws_cdk as cdk
from constructs import Construct

from common.constructs import Ec2Instance, public_vpc


class TrinoStack(cdk.Stack):
    """Single node Trino deployment.

    Port 8080 is intentionally not opened to the internet (no authentication is
    configured yet); reach the coordinator through an SSH tunnel.
    """

    def __init__(self, scope: Construct, id: str, **kwargs: t.Any) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = public_vpc(self)
        instance = Ec2Instance(
            self,
            "TrinoInstance",
            vpc=vpc,
            # 8 GiB RAM; Trino's JVM heap is sized from this (see trino_jvm_heap)
            instance_type=cdk.aws_ec2.InstanceType("t4g.large"),
            volume=cdk.aws_ec2.BlockDeviceVolume.ebs(30),
        )

        bucket = cdk.aws_s3.Bucket(
            self,
            "TrinoBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            bucket_key_enabled=True,
            encryption=cdk.aws_s3.BucketEncryption.S3_MANAGED,
        )
        bucket.grant_read_write(instance.role)

        # Iceberg catalog: table pointers live in the Glue Data Catalog, data and
        # metadata files in the bucket. Scoped to this account/region's catalog so
        # Trino can create and drop its own schemas.
        glue_arn = f"arn:aws:glue:{self.region}:{self.account}"
        instance.role.add_to_principal_policy(
            cdk.aws_iam.PolicyStatement(
                actions=[
                    "glue:GetDatabase",
                    "glue:GetDatabases",
                    "glue:CreateDatabase",
                    "glue:UpdateDatabase",
                    "glue:DeleteDatabase",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:CreateTable",
                    "glue:UpdateTable",
                    "glue:DeleteTable",
                ],
                resources=[
                    f"{glue_arn}:catalog",
                    f"{glue_arn}:database/*",
                    f"{glue_arn}:table/*/*",
                    # DeleteDatabase is also authorized against the database's UDFs
                    f"{glue_arn}:userDefinedFunction/*/*",
                ],
            )
        )

        cdk.CfnOutput(
            self,
            "KeyPairPrivateKeyParameterName",
            value=instance.key_pair_parameter_name,
        )
        cdk.CfnOutput(self, "InstancePublicIp", value=instance.public_ip)
        cdk.CfnOutput(self, "BucketName", value=bucket.bucket_name)
        cdk.CfnOutput(self, "Region", value=self.region)
