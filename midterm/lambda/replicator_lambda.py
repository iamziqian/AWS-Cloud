import os
import time
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

dst_bucket = os.environ['DEST_BUCKET']
table = dynamodb.Table(os.environ['DYNAMO_TABLE'])

def lambda_handler(event, context): # handle trigger from src bucket
    for record in event['Records']:
        event_name = record['eventName']
        src_bucket = record['s3']['bucket']['name']
        src_key = record['s3']['object']['key']
        
        if 'ObjectCreated:Put' in event_name:
            handle_put_event(src_bucket, src_key)
        elif 'ObjectRemoved:Delete' in event_name:
            handle_delete_event(src_key)

    return {
        'statusCode': 200,
        'body': 'Replication completed successfully'
    }

def handle_put_event(src_bucket, src_key):
    # create a copy of the object
    timestamp = int(time.time())
    dst_key = f"{src_key}-{timestamp}"

    s3.copy_object(
        CopySource={'Bucket': src_bucket, 'Key': src_key},
        Bucket=dst_bucket,
        Key=dst_key
    )

    # query existing copies in des bucket
    response = table.query(
        KeyConditionExpression='SrcObjName = :src',
        ExpressionAttributeValues={':src': src_key}
    )
    items = response.get('Items', [])

    # number of copies > 3, delete the oldest copy
    if len(items) > 3:
        oldest_item = sorted(items, key=lambda x: x['CreatedAtTimestamp'])[0]
        table.delete_item(Key={'SrcObjName': oldest_item['SrcObjName'], 'CreatedAtTimestamp': oldest_item['CreatedAtTimestamp']})
        s3.delete_object(Bucket=dst_bucket, Key=oldest_item['DstObjName'])

    # insert a new copy record into the dynamodb table
    table.put_item(Item={
        'SrcObjName': src_key,
        'CreatedAtTimestamp': timestamp,
        'DstObjName': dst_key,
        'IsDisowned': 0, #false - not disowned
        'DisownedAtTimestamp': None
    })

def handle_delete_event(src_key):
    # get the deleted copies
    response = table.query(
        KeyConditionExpression='SrcObjName = :src',
        ExpressionAttributeValues={':src': src_key}
    )
    items = response.get('Items', [])
    for item in items:
        # mark each deleted copies as disowned(1)
        table.update_item(
            Key={'SrcObjName': item['SrcObjName'], 'CreatedAtTimestamp': item['CreatedAtTimestamp']},
            UpdateExpression='SET IsDisowned = :disowned, DisownedAtTimestamp = :time',
            ExpressionAttributeValues={
                ':disowned': 1, #true - disowned
                ':time': int(time.time())
            }
        )
