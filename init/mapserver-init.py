import boto3
import os

access_key = os.getenv("S3_MAPS_ACCESS_KEY")
secret_key = os.getenv("S3_MAPS_SECRET_KEY")

host = os.getenv("S3_MAPS_HOST")
bucket_name = os.getenv("S3_MAPS_BUCKET")

download_path = "/work-dir/"

s3_resource = boto3.resource('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, endpoint_url=host)
s3_client = s3_resource.meta.client
bucket=s3_resource.Bucket(bucket_name)


map_files = s3_client.list_objects(Bucket=bucket_name)["Contents"]
for map_file in map_files:
    bucket.download_file(map_file["Key"], download_path + map_file["Key"])
