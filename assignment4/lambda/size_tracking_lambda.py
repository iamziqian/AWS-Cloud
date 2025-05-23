# lambda function calculate bucket size and number of objects and store in dynamodb
import boto3
import datetime
import json
import os

# Initialize the S3 and DynamoDB clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

def calculate_bucket_size_and_number_of_objects(bucket_name):
    try:
        total_size = 0
        total_objects = 0
        objects = s3_client.list_objects_v2(Bucket=bucket_name)

        for obj in objects.get('Contents', []):
            object_key = obj['Key']
            
            # Ignore objects with the "plot/" prefix
            if object_key.startswith("plot/"):
                print(f"Ignoring plot file: {object_key}")
                continue

            total_size += obj['Size']
            total_objects += 1
    
        print(f"Bucket size: {total_size}, Number of objects: {total_objects}")
        return total_size, total_objects
    except Exception as e:
        print(f"Error calculating bucket size and number of objects: {e}")
        return None, None

def store_bucket_size_and_number_of_objects_in_dynamodb(bucket_name, table_name):
    try:
        # calculation
        bucket_size, number_of_objects = calculate_bucket_size_and_number_of_objects(bucket_name)

        if bucket_size is None or number_of_objects is None:
            raise ValueError("Failed to calculate bucket size or number of objects")
        
        # current timestamp
        timestamp = str(datetime.datetime.now())

        # Log the data being written to DynamoDB
        print(f"Writing to DynamoDB: bucket_name={bucket_name}, timestamp={timestamp}, bucket_size={bucket_size}, number_of_objects={number_of_objects}")

        # store data in dynamodb
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'bucket_name': {'S': bucket_name},
                'timestamp': {'S': timestamp},
                'bucket_size': {'N': str(bucket_size)},
                'number_of_objects': {'N': str(number_of_objects)}
            }
        )
        print(f"Stored {bucket_name} size and number of objects in {table_name} successfully!")
    except Exception as e:
        print(f"Error storing {bucket_name} size and number of objects in {table_name}: {e}")

def lambda_handler(event, context):
    table_name = os.environ['TABLE_NAME'] 

    # Process each message from the SQS queue
    for record in event['Records']:
        try:
            # Parse the SQS message body
            message_body = json.loads(record['body'])
            print(f"Received SQS message: {message_body}")

            # Parse the 'Message' field from the SNS message
            sns_message = json.loads(message_body['Message'])

            # Extract S3 event details
            for s3_record in sns_message.get('Records', []):
                bucket_name = s3_record['s3']['bucket']['name']
                object_key = s3_record['s3']['object']['key']

                # Ignore objects with the "plot/" prefix, so plot will not trigger SQS event
                if object_key.startswith("plot/"):
                    print(f"Ignoring plot file: {object_key}")
                    continue

                print(f"Processing object: {object_key} in bucket: {bucket_name}")

                # Store bucket size and number of objects in DynamoDB
                store_bucket_size_and_number_of_objects_in_dynamodb(bucket_name, table_name)

        except Exception as e:
            print(f"Error processing SQS message: {e}")

    return {
        'statusCode': 200,
        'body': 'Bucket size and object count updated in DynamoDB.'
    }