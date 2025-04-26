import json
import logging
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize CloudWatch Logs client
logs_client = boto3.client('logs')

def lambda_handler(event, context):
    """
    Lambda function to process S3 CreateObject and DeleteObject events from SQS messages.
    Logs the event details into the Lambda's default CloudWatch log group.
    """

    # Iterate through SQS messages
    for record in event.get('Records', []):
        try:
            # Parse the SQS message body
            message_body = json.loads(record['body'])
            print(f"Received SQS message: {message_body}")

            # Parse the 'Message' field
            sns_message = json.loads(message_body['Message'])

            # Extract S3 event details
            for s3_record in sns_message.get('Records', []):
                event_name = s3_record.get('eventName')
                object_key = s3_record.get('s3', {}).get('object', {}).get('key')

                # Ignore objects with the "plot/" prefix, so plot will not trigger SQS event
                if not object_key.startswith("plot/"):
                    if event_name.startswith("ObjectCreated"):
                        # Handle object creation
                        object_size = s3_record.get('s3', {}).get('object', {}).get('size', 0)
                        log_entry = {
                            "object_name": object_key,
                            "size_delta": object_size
                        }
                        print(f"Object created: {object_key}, Size: {object_size}")
                        logger.info(json.dumps(log_entry))

                    elif event_name.startswith("ObjectRemoved:Delete"):
                        # Handle object deletion
                        object_size = get_object_size_from_logs(object_key, context.log_group_name)
                        log_entry = {
                            "object_name": object_key,
                            "size_delta": -object_size
                        }
                        print(f"Object deleted: {object_key}, Size: {object_size}")
                        logger.info(json.dumps(log_entry))

        except Exception as e:
            logger.error("Error processing SQS message: %s", str(e))
            logger.exception(e)

    return {
        "statusCode": 200,
        "body": "S3 events processed successfully"
    }

def get_object_size_from_logs(object_key, log_group_name):
    """
    Query CloudWatch Logs to find the size of the object from its creation log.
    """
    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            filterPattern=f'"{object_key}"',
            limit=1
        )
        print(f"CloudWatch Logs response: {response}")

        log_data = response['events'][0]['message']
        print(f"Log data: {log_data}")

        start = log_data.find("'Message': '") + len("'Message': '")
        end = log_data.find("}', 'Timestamp':")
        message_json = log_data[start:end] + '}' 

        message_data = json.loads(message_json)

        size = message_data['Records'][0]['s3']['object']['size']

        return size

    except:
        logger.error("Error querying CloudWatch Logs")
        return 0