from datetime import datetime 
import json
import os
import sys
import time
import urllib.parse

from aws_lambda_powertools import Logger
import boto3
import redis


logger = Logger()

redis_host = os.getenv('REDIS_HOST')
redis_port = os.getenv('REDIS_PORT')

input_bucket = os.getenv('INPUT_BUCKET')

output_bucket = os.getenv('OUTPUT_BUCKET')

aws_region = os.environ['AWS_REGION']

s3 = boto3.client('s3', region_name=aws_region)

r = redis.Redis(host=redis_host, port=redis_port, db=0)


def load_data(bucket, key):
    '''Take in a bucket and key and return data from either Elasticache or S3.  If there is a cache
    miss then the value loaded from S3 and stored to Elasticache.  Write timing data to logs in seconds.

    Parameters
    ----------
    bucket: string, required
        Bucket where object is stored
    
    key: string, required
        Key name of object
    
    Returns
    -------
    data: string
        Value stored in key (returned from Elasticache or S3)
    '''
    try:
        start_redis_get = datetime.now()
        result = r.get(f'{bucket}:{key}')
        end_redis_get = datetime.now()
        delta_seconds_redis_get = (end_redis_get - start_redis_get).total_seconds()
    except Exception as e:
        logger.error(f'Error getting {bucket}:{key} from {redis_host}: {str(e)}')
        raise()


    if result is None:
        # Get data from S3
        try:
            start_s3_get = datetime.now()
            result = s3.get_object(Bucket=bucket,Key=key)['Body'].read().decode('utf-8')
            end_s3_get = datetime.now()
            delta_seconds_s3_get = (end_s3_get - start_s3_get).total_seconds()
        except Exception as e:
            logger.error(f'Error getting s3://{bucket}/{key}: {str(e)}')
            raise()

        # Store data in Redis
        logger.info(f'Caching data at {bucket}:{key}')
        start_redis_set = datetime.now()
        r.set(f'{bucket}:{key}', str(result))
        end_redis_set = datetime.now()
        delta_seconds_redis_set = (end_redis_set - start_redis_set).total_seconds()
        logger.info({
                "redis_object": f'{bucket}:{key}',
                "cache_hit": False,
                "s3_object": f's3://{bucket}/{key}',
                "s3_download_time": delta_seconds_s3_get,
                "redis_set_time": delta_seconds_redis_set
        })
    else:
        logger.info({
            "redis_object": f'{bucket}:{key}',
            "redis_get_time": delta_seconds_redis_get,
            "cache_hit": True
        })

    return result


def write_data(data, bucket, key):
    '''Take in a data and write it to s3://bucket/key

    Parameters
    ----------
    data: string, required
        Data to persist to S3

    bucket: string, required
        Bucket where object is stored
    
    key: string, required
        Key name of object
    
    Returns
    -------
    result: string
        Result of S3 operation
    '''

    # Write data to S3
    try:
        start_s3_put = datetime.now()
        result = s3.put_object(
            Body=data,
            Bucket=bucket, 
            Key=key)
        end_s3_put = datetime.now()
        delta_seconds_s3_put = (end_s3_put - start_s3_put).total_seconds()
        logger.info({
                "s3_object": f's3://{bucket}/{key}',
                "s3_upload_time": delta_seconds_s3_put
        })
    except Exception as e:
        logger.error(f'Error writing data to s3://{bucket}/{key}: {str(e)}')
        raise()


    return result


@logger.inject_lambda_context
def handler(event, context):
    # Determine the contents of the metadata file
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        metadata_contents = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        json_contents = json.loads(metadata_contents)
    except Exception as e:
        logger.error(f'Could not get metadata from s3://{bucket}/{key}: {str(e)}')
        raise

    # Extract infiles from the metadata file
    infiles = json_contents['infiles']
    logger.info({
        "infiles": infiles
    })

    # Initialize the responses for load_data
    responses = []

    for infile in infiles:
        data = load_data(input_bucket, infile)
        result = write_data(data, output_bucket, infile)
