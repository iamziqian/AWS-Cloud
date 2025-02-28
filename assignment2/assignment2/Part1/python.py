import boto3
import datetime

#initalize s3 and dynamodb clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

def create_s3_bucket(bucket_name, region='us-west-1'):
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name, 
                CreateBucketConfiguration=location
            )
        print(f"{bucket_name} has been created successfully!")
    except Exception as e:
        print(f"Error creating {bucket_name}: {e}")


# create dynamodb table: bucket_name, timestamp, bucket_size, number of objects
def create_dynamodb_table(table_name):
    try:
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'bucket_name', # partition key
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',   # sort key
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'bucket_name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"{table_name} has been created successfully!")
    except Exception as e:
        print(f"Error creating {table_name}: {e}")

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

        # current timestamp
        timestamp = str(datetime.datetime.now())

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

def main():
    bucket_name = 'violet-test-bucket-ziqianfu-part1'
    create_s3_bucket(bucket_name)

    table_name = 'S3-object-size-history-part1'
    create_dynamodb_table(table_name)

    store_bucket_size_and_number_of_objects_in_dynamodb(bucket_name, table_name)

if __name__ == "__main__":
    main()