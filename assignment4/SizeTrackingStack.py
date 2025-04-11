from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_event_sources,
    aws_sqs as sqs,
)
from constructs import Construct

class SizeTrackingStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 table_arn: str,
                 test_bucket_arn: str,
                 size_tracking_queue_arn: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Import the SQS queue using its ARN
        size_tracking_queue = sqs.Queue.from_queue_arn(
            self,
            "SizeTrackingQueue",
            size_tracking_queue_arn
        )

        # Import the DynamoDB table using its ARN
        table = dynamodb.Table.from_table_arn(
            self,
            "SizeTrackingTable",
            table_arn
        )

        # Get S3 bucket objects from ARN
        bucket = s3.Bucket.from_bucket_arn(
            self,
            "ImportedTestBucket",
            test_bucket_arn
        )
        
        # Define the Lambda function
        tracking_lambda = _lambda.Function(
            self,
            "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="size_tracking_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "QUEUE_URL": size_tracking_queue.queue_url
            }
        )

        # grant permissions
        table.grant_write_data(tracking_lambda)
        bucket.grant_read(tracking_lambda)
        size_tracking_queue.grant_consume_messages(tracking_lambda)

        # add SQS event source
        tracking_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(size_tracking_queue)
        )