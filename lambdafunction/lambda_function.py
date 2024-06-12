import json
import boto3
import pymysql
import logging
from collections import defaultdict
import requests

# Constants
db_host = 'car-network-db.c5kgayasi5x2.us-east-1.rds.amazonaws.com'
db_user = 'admin'
db_password = 'FrostGaming1!'
db_name = 'user_db'
DOMAIN_ENDPOINT = 'vpc-car-network-open-search-qkd46v7okrwchflkznxsldkx4y.aos.us-east-1.on.aws'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Sql

follower_id_sql = '''
SELECT * FROM FOLLOWERS WHERE user_id = %s
'''


def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            return generate_feed(event)
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
        
        
def get_follower_ids(user_id):
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    cursor = conn.cursor()
    try:
        logger.info("Fetching all follower ids")
        cursor.execute(follower_id_sql, (user_id))
        results = cursor.fetchall()
        logger.info("Follower IDs")
        logger.info(results)
        
        return results
        
        
    except Exception as e:
        logger.error(str(e))
        return {
            'statusCode': 500,
            'body':json.dumps({'message':str(e)})
        }
    
def generate_feed(event):
    logger.info("Generating Feed")
    query_parameters = event['queryStringParameters']
    
    user_id = query_parameters.get('user_id')

    logger.info("query parameters")
    logger.info(query_parameters)
    
    follower_ids = get_follower_ids(user_id)
    
    try:
        pass
    except Exception as e:
        logger.erro(str(e))

