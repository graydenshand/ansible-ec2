import typing as t

import aws_cdk as cdk
from constructs import Construct


class Ec2Instance(Construct):
    """A high level EC2 instance construct."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: cdk.aws_ec2.IVpc,
        instance_type: cdk.aws_ec2.InstanceType = cdk.aws_ec2.InstanceType("t4g.micro"),
        volume: cdk.aws_ec2.BlockDeviceVolume | None = None,
        public_ports: t.Iterable[int] | None = None,
        key_pair: cdk.aws_ec2.IKeyPair | None = None,
        vpc_subnets: cdk.aws_ec2.SubnetSelection | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if key_pair is None:
            self.key_pair = cdk.aws_ec2.KeyPair(
                self,
                "KeyPair",
                type=cdk.aws_ec2.KeyPairType.ED25519,
                format=cdk.aws_ec2.KeyPairFormat.PEM,
            )
        else:
            self.key_pair = key_pair

        block_devices = []
        if volume is not None:
            block_devices.append(
                cdk.aws_ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=volume,
                )
            )

        instance_kwargs: dict[str, t.Any] = dict(
            instance_type=instance_type,
            machine_image=cdk.aws_ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=cdk.aws_ec2.AmazonLinuxCpuType.ARM_64
            ),
            vpc=vpc,
            key_pair=self.key_pair,
            block_devices=block_devices,
        )
        if vpc_subnets is not None:
            instance_kwargs["vpc_subnets"] = vpc_subnets

        self.instance = cdk.aws_ec2.Instance(self, "Ec2Instance", **instance_kwargs)

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(5432), "Allow PostgreSQL access from anywhere"
        )

        self.instance.connections.allow_from_any_ipv4(
            cdk.aws_ec2.Port.tcp(22), "Allow SSH access from anywhere"
        )

        self.key_pair_parameter_name = self.key_pair.private_key.parameter_name
        self.public_ip = self.instance.instance_public_ip
        self.private_ip = self.instance.instance_private_ip


class PostgresHACluster(Construct):
    """Two-node Postgres HA cluster with Patroni + DynamoDB."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: cdk.aws_ec2.IVpc,
        volume: cdk.aws_ec2.BlockDeviceVolume | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        shared_key_pair = cdk.aws_ec2.KeyPair(
            self,
            "KeyPair",
            type=cdk.aws_ec2.KeyPairType.ED25519,
            format=cdk.aws_ec2.KeyPairFormat.PEM,
        )

        self.patroni_table = cdk.aws_dynamodb.Table(
            self,
            "PatroniTable",
            partition_key=cdk.aws_dynamodb.Attribute(
                name="id", type=cdk.aws_dynamodb.AttributeType.STRING
            ),
            sort_key=cdk.aws_dynamodb.Attribute(
                name="key", type=cdk.aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=cdk.aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.backup_bucket = cdk.aws_s3.Bucket(
            self,
            "PgBackupBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            lifecycle_rules=[cdk.aws_s3.LifecycleRule(expiration=cdk.Duration.days(30))],
        )

        azs = vpc.availability_zones

        self.node1 = Ec2Instance(
            self,
            "Node1",
            vpc=vpc,
            volume=volume,
            key_pair=shared_key_pair,
            vpc_subnets=cdk.aws_ec2.SubnetSelection(availability_zones=[azs[0]]),
        )

        self.node2 = Ec2Instance(
            self,
            "Node2",
            vpc=vpc,
            volume=volume,
            key_pair=shared_key_pair,
            vpc_subnets=cdk.aws_ec2.SubnetSelection(availability_zones=[azs[1]]),
        )

        # Allow Patroni REST API between nodes
        self.node1.instance.connections.allow_from(
            self.node2.instance.connections,
            cdk.aws_ec2.Port.tcp(8008),
            "Patroni REST API from node2",
        )
        self.node2.instance.connections.allow_from(
            self.node1.instance.connections,
            cdk.aws_ec2.Port.tcp(8008),
            "Patroni REST API from node1",
        )

        # Allow replication traffic between nodes
        self.node1.instance.connections.allow_from(
            self.node2.instance.connections,
            cdk.aws_ec2.Port.tcp(5432),
            "PostgreSQL replication from node2",
        )
        self.node2.instance.connections.allow_from(
            self.node1.instance.connections,
            cdk.aws_ec2.Port.tcp(5432),
            "PostgreSQL replication from node1",
        )

        dynamo_actions = [
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:DeleteItem",
            "dynamodb:Query",
            "dynamodb:Scan",
        ]
        dynamo_policy = cdk.aws_iam.PolicyStatement(
            actions=dynamo_actions,
            resources=[self.patroni_table.table_arn],
        )
        s3_policy = cdk.aws_iam.PolicyStatement(
            actions=["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
            resources=[self.backup_bucket.bucket_arn, f"{self.backup_bucket.bucket_arn}/*"],
        )

        for node in (self.node1, self.node2):
            node.instance.add_to_role_policy(dynamo_policy)
            node.instance.add_to_role_policy(s3_policy)

        self.key_pair_parameter_name = shared_key_pair.private_key.parameter_name

        # NLB: port 5432 → primary (health check /master), port 5433 → replica (health check /replica)
        nlb = cdk.aws_elasticloadbalancingv2.NetworkLoadBalancer(
            self, "NLB", vpc=vpc, internet_facing=True
        )

        instances = [self.node1.instance, self.node2.instance]

        for port, path, tg_id, listener_id in [
            (5432, "/master", "PrimaryTG", "PrimaryListener"),
            (5433, "/replica", "ReplicaTG", "ReplicaListener"),
        ]:
            tg = cdk.aws_elasticloadbalancingv2.NetworkTargetGroup(
                self,
                tg_id,
                vpc=vpc,
                port=5432,
                protocol=cdk.aws_elasticloadbalancingv2.Protocol.TCP,
                targets=[
                    cdk.aws_elasticloadbalancingv2_targets.InstanceTarget(inst, 5432)
                    for inst in instances
                ],
                health_check=cdk.aws_elasticloadbalancingv2.HealthCheck(
                    protocol=cdk.aws_elasticloadbalancingv2.Protocol.HTTP,
                    port="8008",
                    path=path,
                    healthy_http_codes="200",
                ),
            )
            nlb.add_listener(listener_id, port=port, default_target_groups=[tg])

        # Allow NLB health checks (port 8008) from within the VPC
        for node in (self.node1, self.node2):
            node.instance.connections.allow_from(
                cdk.aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
                cdk.aws_ec2.Port.tcp(8008),
                "Patroni REST API health checks from NLB",
            )

        self.nlb_dns_name = nlb.load_balancer_dns_name


def _public_vpc(scope: Construct) -> cdk.aws_ec2.Vpc:
    vpc = cdk.aws_ec2.Vpc(
        scope,
        "VPC",
        max_azs=2,
        nat_gateways=0,
        subnet_configuration=[
            cdk.aws_ec2.SubnetConfiguration(
                name="Public", subnet_type=cdk.aws_ec2.SubnetType.PUBLIC
            )
        ],
    )
    vpc.add_gateway_endpoint("S3Endpoint", service=cdk.aws_ec2.GatewayVpcEndpointAwsService.S3)
    vpc.add_gateway_endpoint(
        "DynamoEndpoint", service=cdk.aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
    )
    return vpc


class PostgresStack(cdk.Stack):
    """Single-instance PostgreSQL stack."""

    def __init__(self, scope: Construct, id: str, **kwargs: t.Any) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = _public_vpc(self)
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


class PostgresHAStack(cdk.Stack):
    """Two-node HA PostgreSQL stack with Patroni + DynamoDB."""

    def __init__(self, scope: Construct, id: str, **kwargs: t.Any) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = _public_vpc(self)
        cluster = PostgresHACluster(
            self,
            "PostgresHACluster",
            vpc=vpc,
            volume=cdk.aws_ec2.BlockDeviceVolume.ebs(20),
        )

        cdk.CfnOutput(self, "Node1PublicIp", value=cluster.node1.public_ip)
        cdk.CfnOutput(self, "Node2PublicIp", value=cluster.node2.public_ip)
        cdk.CfnOutput(self, "Node1PrivateIp", value=cluster.node1.private_ip)
        cdk.CfnOutput(self, "Node2PrivateIp", value=cluster.node2.private_ip)
        cdk.CfnOutput(self, "KeyPairPrivateKeyParameterName", value=cluster.key_pair_parameter_name)
        cdk.CfnOutput(self, "BackupBucketName", value=cluster.backup_bucket.bucket_name)
        cdk.CfnOutput(self, "PatroniTableName", value=cluster.patroni_table.table_name)
        cdk.CfnOutput(self, "PrimaryEndpoint", value=f"{cluster.nlb_dns_name}:5432")
        cdk.CfnOutput(self, "ReplicaEndpoint", value=f"{cluster.nlb_dns_name}:5433")


if __name__ == "__main__":
    app = cdk.App()
    PostgresStack(app, "PostgresStack")
    PostgresHAStack(app, "PostgresHAStack")
    app.synth()
