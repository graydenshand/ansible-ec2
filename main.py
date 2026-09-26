import aws_cdk as cdk

from services.hello_world.stack import HelloWorldStack
from services.postgres.stack import PostgresStack
from services.postgres_ha.stack import PostgresHAStack
from services.trino.stack import TrinoStack

if __name__ == "__main__":
    app = cdk.App()
    HelloWorldStack(app, "HelloWorld")
    PostgresStack(app, "Postgres")
    PostgresHAStack(app, "PostgresHA")
    TrinoStack(app, "Trino")
    app.synth()
