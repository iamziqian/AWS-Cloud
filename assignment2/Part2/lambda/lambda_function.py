# lambda function calculate bucket size and number of objects and store in dynamodb
import boto3
import datetime
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
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    event_type = event['Records'][0]['eventName']
    
    table_name = os.environ['TABLE_NAME'] 
    
    # Handle ObjectCreated, ObjectRemoved, and ObjectUpdate (overwrite) events
    if event_type.startswith("ObjectCreated"):
        print(f"Object created or updated in bucket: {bucket_name}")
    elif event_type.startswith("ObjectRemoved"):
        print(f"Object deleted in bucket: {bucket_name}")
    
    # store bucket size and number of objects in dynamodb
    store_bucket_size_and_number_of_objects_in_dynamodb(bucket_name, table_name)
    
    return {
        'statusCode': 200,
        'body': 'Bucket size and object count updated in DynamoDB.'
    }