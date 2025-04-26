import os
import aws_cdk as cdk

from StorageStack import StorageStack
from PlottingStack import PlottingStack
from DriverStack import DriverStack
from FanoutStack import FanoutStack
from SizeTrackingStack import SizeTrackingStack
from LoggingStack import LoggingStack
from MonitoringAndCleanStack import MonitoringAndCleanStack


app = cdk.App()

storage_stack = StorageStack(app, "StorageStack", env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

plotting_stack = PlottingStack(app, "PlottingStack", 
                           table_arn=storage_stack.table_arn,
                           test_bucket_arn=storage_stack.test_bucket_arn,
                           env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

driver_stack = DriverStack(app, "DriverStack", 
                           test_bucket_arn=storage_stack.test_bucket_arn,
                           api_endpoint=plotting_stack.api_endpoint,
                           api_arn=plotting_stack.api_arn,
                           env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

fanout_stack = FanoutStack(app, "FanoutStack",
                           test_bucket_arn=storage_stack.test_bucket_arn,
                           env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

size_tracking_stack = SizeTrackingStack(app, "SizeTrackingStack",
                           table_arn=storage_stack.table_arn,
                           test_bucket_arn=storage_stack.test_bucket_arn,
                           size_tracking_queue_arn=fanout_stack.size_tracking_queue_arn,
                           env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

logging_stack = LoggingStack(app, "LoggingStack",
                            logging_queue_arn=fanout_stack.logging_queue_arn,
                            env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

monitoring_clean_stack = MonitoringAndCleanStack(app, "MonitoringAndCleanStack",
                                   test_bucket_arn=storage_stack.test_bucket_arn,
                                   log_group_name=logging_stack.logging_lambda_log_group_name,
                                   env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()