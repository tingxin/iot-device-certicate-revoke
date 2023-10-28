import boto3
import OpenSSL

## 需要修改
dynamodb_crl_series_number_trace = 'crl_series_number_trace'

def handler(event, context):
    iot = boto3.client('iot')
    dynamodb = boto3.client('dynamodb')

    for record in event['Records']:
        if 'body' not in record:
            continue
        thing_name = record['body']

        response = iot.list_thing_principals(thingName=thing_name)
        certificates = response['principals']

        for certificate_arn in certificates:
            print(f"设备 {thing_name} 关联的证书ARN: {certificate_arn}")
            # 从证书ARN中提取证书ID
            certificate_id = certificate_arn.split('/')[-1]
            # 获取证书信息
            certificate_response = iot.describe_certificate(certificateId=certificate_id)
            certificate = certificate_response['certificateDescription']

            # 解析 PEM 证书数据
            cert_data = certificate['certificatePem']
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)

            serial_number = cert.get_serial_number()
            print(f'{certificate_id}:{serial_number}')

            rp = dynamodb.get_item(TableName=dynamodb_crl_series_number_trace,
                Key={
                    'series_number': {'S':serial_number}
                }
            if 'Item' not in rp:
                continue

            response = iot.update_certificate(
                certificateId=certificate_id,
                newStatus='REVOKED'
            )
            print(response)

            
    
