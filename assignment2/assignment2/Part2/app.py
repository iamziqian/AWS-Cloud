import aws_cdk as cdk
from s3_size_tracking_stack import S3SizeTrackingStack
from S3_object_size_history_plotting_stack import S3ObjectSizeHistoryPlottingStack

app = cdk.App()
s3_size_tracking_stack = S3SizeTrackingStack(app, "S3SizeTrackingStack")
s3_object_size_history_plotting_stack = S3ObjectSizeHistoryPlottingStack(app, "S3ObjectSizeHistoryPlottingStack", s3_size_tracking_stack)
app.synth()