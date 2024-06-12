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

POSTS_DB_HOST = 'car-network-db.c5kgayasi5x2.us-east-1.rds.amazonaws.com'
POSTS_DB_USER = 'admin'
POSTS_DB_PASSWORD = 'FrostGaming1!'
POSTS_DB_NAME = 'post_db'

MEDIA_DB_HOST = 'car-network-db.c5kgayasi5x2.us-east-1.rds.amazonaws.com'
MEDIA_DB_USER = 'admin'
MEDIA_DB_PASSWORD = 'FrostGaming1!'
MEDIA_DB_NAME = 'media_metadata_db'

COMMENT_DB_NAME = 'comment_db'

DOMAIN_ENDPOINT = 'vpc-car-network-open-search-qkd46v7okrwchflkznxsldkx4y.aos.us-east-1.on.aws'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Sql

follower_id_sql = '''
SELECT follower_id FROM followers WHERE user_id = %s
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
    follower_ids = []
    
    try:
        logger.info("Fetching all follower ids")
        cursor.execute(follower_id_sql, (user_id))
        result = cursor.fetchall()
        
        for follow in result:
            follower_ids.append(follow[0])
        
        return follower_ids
        
        
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
    
    # Domain Info
    url = f"https://{DOMAIN_ENDPOINT}/posts/_search"
    headers = {"Content-Type": "application/json"}
    
    
    
    try:
        logger.info("Getting Follower IDs")
        follower_ids = get_follower_ids(user_id)
        logger.info(follower_ids)
        
        search_payload = {
          "query": {
            "bool": {
              "filter": [
                {
                  "terms": {
                    "user_id": follower_ids
                  }
                }
              ]
            }
          },
          "sort": [
            {
              "created_at": {
                "order": "desc"
              }
            }
          ]
        }
        
        response = requests.get(url, headers=headers, json=search_payload)
        logger.info("Search Response")
        search_results = response.json()
        logger.info(search_results)
        
        processed_results = process_search_results(search_results)
        
        return {
            'statusCode': 200,
            'body':json.dumps({"message": processed_results})
        }
        

    except Exception as e:
        logger.error(str(e))
        return {
            'statusCode': 500,
            'body':json.dumps({"error": str(e)})
        }
        
#  Helper Functions

def get_post_ids(posts):
    post_ids = []
    
    for post in posts:
        if post['_index'] == "posts":
            post_ids.append( post['_source']['id'] ) 
        
    return post_ids
    
def process_search_results(results):
    logger.info("Setting Variables")
    processed_results = defaultdict(list)
    posts = []
    tmp_posts = []
    
    try:
        logger.info("Separating Post IDs")
        post_ids = get_post_ids(results['hits']['hits'])
        
        if post_ids:
            logger.info("Getting comments for the posts")
            comments = get_comments_by_post_id(post_ids)
            
            logger.info("Getting Media Metadata for the posts")
            media_metadata = get_media_metadata_by_post_ids(post_ids)
            
            logger.info("Separating Users and Posts from results")
            for result in results['hits']['hits']:
                if result['_index'] == "posts":
                    tmp_posts.append( result['_source'] )
            
            posts = combine_posts_with_media(tmp_posts, comments, media_metadata)
        

        processed_results['posts'] = posts
        
        return processed_results
    except Exception as e:
        logger.info(str(e))
        raise e

def get_media_metadata_by_post_ids(post_ids):
    if not post_ids:
        return []
    
    connection = pymysql.connect(host=MEDIA_DB_HOST,
                                 user=MEDIA_DB_USER,
                                 password=MEDIA_DB_PASSWORD,
                                 database=MEDIA_DB_NAME)
    logger.info("Get metadata for media in post")
    post_id_tuple = tuple(post_ids)
    try:
        with connection.cursor() as cursor:
            sql = "select user_id, post_id, s3_key, url, size, type  from media_metadata where post_id in %s"
            cursor.execute(sql, (post_id_tuple,))
            results = cursor.fetchall()
            logger.info("media metadata")
            logger.info(results)
            media_list = []
            for media in results:
                media_dict = {
                    "user_id": media[0],
                    "post_id": media[1],
                    "s3_key": media[2],
                    "url" : media[3],
                    "size": media[4],
                    "type": media[5]
                }
                media_list.append(media_dict)
            logger.info("media list")
            logger.info(media_list)
        return media_list
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()
        
def get_comments_by_post_id(post_ids):
    if not post_ids:
        return []
    
    connection = pymysql.connect(host=MEDIA_DB_HOST,
                                 user=MEDIA_DB_USER,
                                 password=MEDIA_DB_PASSWORD,
                                 database=COMMENT_DB_NAME)
    logger.info("Get comments for posts")
    post_id_tuple = tuple(post_ids)
    logger.info("post id's")
    logger.info(post_id_tuple)
    try:
        with connection.cursor() as cursor:
            sql = "select id, user_id, post_id, content, created_at from comments where post_id in %s"
            cursor.execute(sql, (post_id_tuple,))
            results = cursor.fetchall()
            logger.info("post comments")
            logger.info(results)
            comment_dict = defaultdict(list)
            
            for comment in results:
                
                comment_object = {
                    "id":comment[0],
                    "post_id":comment[2],
                    "user_id":comment[1],
                    "content":comment[3],
                    "created_at":comment[4].strftime('%Y-%m-%d %H:%M:%S')
                }
                
                comment_dict[comment_object['post_id']].append(comment_object)
                
            logger.info("comment dictionary")
            logger.info(comment_dict)
        return comment_dict
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()
        
def combine_posts_with_media(posts, comments, media_metadata):
    logger.info("Combining media to the post")
    logger.info(media_metadata)
    media_dict = {}
    for media in media_metadata:
        post_id = media['post_id']
        if post_id not in media_dict:
            media_dict[post_id] = []
        media_dict[post_id].append(media)
    
    for post in posts:
        post['media_metadata'] = media_dict.get(post['id'], [])
        post['comments'] = comments.get(post['id'],[])
    
    return posts
