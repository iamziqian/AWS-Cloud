from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class CleanerStack(Stack):
    def __init__(self, scope: Construct, id: str,
                bucket_dst_arn: str,
                table: dynamodb.Table, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get S3 bucket objects from ARN
        dst_bucket = s3.Bucket.from_bucket_arn(self, "ImportedBucketDst", bucket_dst_arn)

        # create cleaner lambda
        cleaner_lambda = _lambda.Function(
            self,
            "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="cleaner_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "DEST_BUCKET": dst_bucket.bucket_name,
                "DYNAMO_TABLE": table.table_name,
            }
        )

        # grant permissions
        dst_bucket.grant_delete(cleaner_lambda)
        table.grant_read_write_data(cleaner_lambda)
       
        # create an EventBridge Rule to trigger every 1 minute
        event_rule = events.Rule(
            self, "CleanerRule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            description="Trigger Cleaner Lambda every 1 minute"
        )

        # add the Lambda as the rule's target
        event_rule.add_target(targets.LambdaFunction(cleaner_lambda))
