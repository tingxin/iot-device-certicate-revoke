import json
import urllib.parse
import boto3
import OpenSSL
from datetime import datetime

## 需要修改
dynamodb_crl_series_number_trace = 'crl_series_number_trace'
list_device_lambda_arn = 'arn:aws-cn:lambda:cn-northwest-1:027040934161:function:list_iot_core_devices'
#########

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

def handler(event, context):

    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        
        crl_object = OpenSSL.crypto.load_crl(OpenSSL.crypto.FILETYPE_ASN1, content)
 
        revoked_objects = crl_object.get_revoked()
         
        # 输出吊销列表里面的证书序列号

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        index = 0
        items_to_update = list()
       
        for rvk in revoked_objects:
            series_number = rvk.get_serial().decode()
            print("Serial:", series_number)
            item = {
                'PutRequest': {
                    'Item': {
                        'series_number': {'S': series_number},
                        'update_time': {'S': current_time}
                    }
                }
            }
            if index < 100:
                items_to_update.append(item)
                index +=1
            else:
                para = {
                    dynamodb_crl_series_number_trace:items_to_update
                }

                response = dynamodb.batch_write_item(RequestItems=para)
                print(response)
                index = 0
                items_to_update = list()

            if len(items_to_update) > 0:
                para = {
                    dynamodb_crl_series_number_trace:items_to_update
                }
                response = dynamodb.batch_write_item(RequestItems=para)
                print(response)
            

        print(f'succcess save crl list to dynamodb {dynamodb_crl_series_number_trace}')

        input_data = {
            "trace": dynamodb_crl_series_number_trace
        }
        response = lambda_client.invoke(
            FunctionName=list_device_lambda_arn,
            InvocationType='RequestResponse',  # 同步触发方式
            Payload=json.dumps(input_data)  # 将输入数据转换为 JSON 字符串
        )
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

