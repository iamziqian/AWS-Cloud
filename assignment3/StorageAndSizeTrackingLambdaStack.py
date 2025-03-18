# CDK stack include s3 bucket and dynamodb table
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_s3_notifications as s3_notifications,
)
from constructs import Construct

bucket_name = "violet-test-bucket-ziqianfu"
table_name = "S3-object-size-history"

class StorageAndSizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create s3 bucket: violet-test-bucket-ziqianfu
        self.bucket = s3.Bucket(
            self, 
            bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True)

        # create dynamodb table: S3-object-size-history: size info, timestamp, total number of objects, bucket name
        self.table = dynamodb.Table(
            self, 
            table_name,
            partition_key=dynamodb.Attribute(
                name="bucket_name", 
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", 
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            read_capacity=5,
            write_capacity=5
        )

        # create size tracking lambda
        size_tracking_lambda = _lambda.Function(
            self,
            "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="size_tracking_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": self.table.table_name
            }
        )

        # grant permissions
        self.bucket.grant_read(size_tracking_lambda)
        self.table.grant_write_data(size_tracking_lambda)

        # add s3 event notification to lambda
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3_notifications.LambdaDestination(size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_POST,
            s3_notifications.LambdaDestination(size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_RESTORE_COMPLETED,
            s3_notifications.LambdaDestination(size_tracking_lambda)
        )


