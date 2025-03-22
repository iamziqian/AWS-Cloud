import os
import aws_cdk as cdk

from StorageStack import StorageStack
from ReplicatorStack import ReplicatorStack
from CleanerStack import CleanerStack

app = cdk.App()
storage_stack = StorageStack(app, "StorageStack", env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)

replicator_stack = ReplicatorStack(
    app, "ReplicatorStack",
    bucket_src_arn=storage_stack.bucket_src_arn,
    bucket_dst_arn=storage_stack.bucket_dst_arn,
    table=storage_stack.table,
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

cleaner_stack = CleanerStack(
    app, "CleanerStack",
    bucket_dst_arn=storage_stack.bucket_dst_arn,
    table=storage_stack.table,
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

app.synth()
