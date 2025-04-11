from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions
)
from constructs import Construct

class MonitoringAndCleanStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 test_bucket_arn: str,
                 log_group_name: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

         # Get S3 bucket objects from ARN
        test_bucket = s3.Bucket.from_bucket_arn(self, "ImportedTestBucket", test_bucket_arn)

        # create cleaner lambda
        cleaner_lambda = _lambda.Function(
            self,
            "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="cleaner_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TEST_BUCKET": test_bucket.bucket_name,
            }
        )

        # grant permissions
        test_bucket.grant_read(cleaner_lambda)
        test_bucket.grant_delete(cleaner_lambda)
        
        # Create a CloudWatch metric filter
        logs.MetricFilter(
            self,
            "TotalObjectSizeMetricFilter",
            log_group=logs.LogGroup.from_log_group_name(self, "LogGroup", log_group_name),
            filter_pattern=logs.FilterPattern.exists("$.size_delta"),
            metric_namespace="Assignment4App",
            metric_name="TotalObjectSize",
            metric_value="$.size_delta"
        )

        # Create a metric: SUM reflects the actual total bucket size instead of the delta per minute
        total_object_size_metric = cloudwatch.Metric(
            namespace="Assignment4App",
            metric_name="TotalObjectSize", 
            statistic="Sum",
            period=Duration.minutes(1),
        )

        # Create an alarm
        size_alarm = cloudwatch.Alarm(
            self,
            "TotalObjectSizeAlarm",
            metric=total_object_size_metric,
            threshold=20,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )

        cleaner_lambda.add_permission(
            "AllowAlarmInvocation",
            principal=iam.ServicePrincipal("cloudwatch.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=size_alarm.alarm_arn,
        )

        size_alarm.add_alarm_action(cloudwatch_actions.LambdaAction(cleaner_lambda))