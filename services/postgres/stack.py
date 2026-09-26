import typing as t

import aws_cdk as cdk
from constructs import Construct

from common.constructs import Ec2Instance, public_vpc


class PostgresStack(cdk.Stack):
    """Single-instance PostgreSQL stack."""

    def __init__(self, scope: Construct, id: str, **kwargs: t.Any) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = public_vpc(self)
        instance = Ec2Instance(
            self,
            "PostgresInstance",
            vpc=vpc,
            volume=cdk.aws_ec2.BlockDeviceVolume.ebs(20),
            public_ports=[22, 5432],
        )

        backup_bucket = cdk.aws_s3.Bucket(
            self,
            "PgBackupBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            lifecycle_rules=[cdk.aws_s3.LifecycleRule(expiration=cdk.Duration.days(30))],
        )
        instance.instance.add_to_role_policy(
            cdk.aws_iam.PolicyStatement(
                actions=["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
                resources=[backup_bucket.bucket_arn, f"{backup_bucket.bucket_arn}/*"],
            )
        )

        cdk.CfnOutput(self, "KeyPairPrivateKeyParameterName", value=instance.key_pair_parameter_name)
        cdk.CfnOutput(self, "InstancePublicIp", value=instance.public_ip)
        cdk.CfnOutput(self, "BackupBucketName", value=backup_bucket.bucket_name)
