from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
)
from constructs import Construct

class ReplicatorStack(Stack):
    def __init__(self, scope: Construct, id: str,
                bucket_src_arn: str,
                bucket_dst_arn: str,
                table: dynamodb.Table, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get S3 bucket objects from ARN
        src_bucket = s3.Bucket.from_bucket_arn(self, "ImportedBucketSrc", bucket_src_arn)
        dst_bucket = s3.Bucket.from_bucket_arn(self, "ImportedBucketDst", bucket_dst_arn)

        # create replicator lambda
        replicator_lambda = _lambda.Function(
            self,
            "ReplicatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="replicator_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "SRC_BUCKET": src_bucket.bucket_name,
                "DEST_BUCKET": dst_bucket.bucket_name,
                "DYNAMO_TABLE": table.table_name,
            }
        )

        # grant permissions
        src_bucket.grant_read(replicator_lambda)
        dst_bucket.grant_read_write(replicator_lambda)
        table.grant_read_write_data(replicator_lambda)
       
        # Add S3 event notification to trigger Lambda function: put and delete
        src_bucket.add_event_notification(s3.EventType.OBJECT_CREATED_PUT, s3_notifications.LambdaDestination(replicator_lambda))

        src_bucket.add_event_notification(s3.EventType.OBJECT_REMOVED_DELETE, s3_notifications.LambdaDestination(replicator_lambda))
