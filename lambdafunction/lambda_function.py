import json
import boto3
import pymysql
import logging
from collections import defaultdict
import requests

# Constants

DOMAIN_ENDPOINT = 'vpc-car-network-open-search-qkd46v7okrwchflkznxsldkx4y.aos.us-east-1.on.aws'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            pass
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method Not Allowed'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    



