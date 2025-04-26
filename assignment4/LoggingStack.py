from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_sqs as sqs,
    aws_iam as iam,
)
from constructs import Construct

class LoggingStack(Stack):
    def __init__(self, scope: Construct, id: str,
                logging_queue_arn: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Import the SQS queue using its ARN
        logging_queue = sqs.Queue.from_queue_arn(
            self,
            "LoggingQueue",
            logging_queue_arn
        )
        
        logging_lambda = _lambda.Function(
            self,
            "LoggingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="logging_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "QUEUE_URL": logging_queue.queue_url
            }
        )

        # grant permissions
        logging_queue.grant_consume_messages(logging_lambda)

        logging_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(logging_queue)
        )

        # grant permissions to read CloudWatch logs
        logging_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:FilterLogEvents",  # Allows filtering log events
                    "logs:GetLogEvents"     # Allows retrieving log events
                ],
                resources=["*"]
            )
        )

        # Expose the log group name
        self.logging_lambda_log_group_name = logging_lambda.log_group.log_group_name