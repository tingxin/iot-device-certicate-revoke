import json
import boto3

### 需要修改
sqs_url = "https://sqs.cn-northwest-1.amazonaws.com.cn/027040934161/iotcore"
##########

def lambda_handler(event, context):
    client = boto3.client('iot')
    sqs = boto3.client('sqs')
    
    try:
        response = client.list_things()
        while True:
            things = response['things']
            for thing in things:
                thing_name =  thing['thingName']
                resp = sqs.send_message(
                        QueueUrl=sqs_url,
                        MessageBody=thing_name,
                        DelaySeconds=0
                    )
                print(resp)

            if 'nextToken' not in response:
                break

            token = response['nextToken']
            response = client.list_things(nextToken=token)

    except Exception as e:
        print(f'Error list iot things due to \n{e}')
        raise e
        

