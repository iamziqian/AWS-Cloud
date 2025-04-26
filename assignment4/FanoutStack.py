from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_s3_notifications as s3n,
    aws_sns_subscriptions as sns_subscriptions,
    Duration,
)
from constructs import Construct

class FanoutStack(Stack):
    def __init__(self, scope: Construct, id: str,
                test_bucket_arn: str, 
                **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

       # create SNS topic
        topic = sns.Topic(
            self,
            "FanoutTopic",
            display_name="Fanout Topic"
        )

        # create SQS queues
        size_tracking_queue = sqs.Queue(
            self,
            "SizeTrackingQueue",
            visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(4)
        )

        logging_queue = sqs.Queue(
            self,
            "LoggingQueue",
            visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(4)
        )

        # Expose the SQS queue ARNs
        self.size_tracking_queue_arn = size_tracking_queue.queue_arn
        self.logging_queue_arn = logging_queue.queue_arn

        # subscribe SQS queues to SNS topic
        topic.add_subscription(sns_subscriptions.SqsSubscription(size_tracking_queue))
        topic.add_subscription(sns_subscriptions.SqsSubscription(logging_queue))

        # get S3 bucket objects from ARN
        test_bucket = s3.Bucket.from_bucket_arn(self, "ImportedTestBucket", test_bucket_arn)

        # add s3 event notification to trigger SNS topic
        test_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SnsDestination(topic)
        )
        test_bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.SnsDestination(topic)
        )
