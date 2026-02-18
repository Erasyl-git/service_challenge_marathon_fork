import boto3
import os
import botocore
from pathlib import Path

from dotenv import load_dotenv
from botocore.client import Config

from utils.cache import CacheData


class S3Service:

    cache = CacheData()

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parent.parent
        load_dotenv(BASE_DIR / ".env")
        
        self.s3: boto3 = boto3.client(
            service_name="s3",
            endpoint_url=os.getenv("ENDPOINT_URL"),
            region_name=os.getenv("REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=Config(signature_version=os.getenv("SIGNATURE_VERSION"))
        )


    def upload_file(self, dirname: str, media_name: str, content) -> None:

        self.s3.upload_fileobj(
            Fileobj=content,    
            Bucket=os.getenv("AWS_BUCKET_NAME"),
            Key=f"{dirname}/{media_name}",
            ExtraArgs={
                'ContentType': 'image/jpeg',
                'ContentDisposition': 'inline'
            }
        )

        self.cache.delete_cache_source_data(f"{dirname}/{media_name}")


    def upload_video(self, dirname: str, media_name: str, content) -> None:

        self.s3.upload_fileobj( 
            Fileobj=content,
            Bucket=os.getenv("AWS_BUCKET_NAME"),
            Key=f"{dirname}/{media_name}",
            ExtraArgs={
                'ContentType': 'video/mp4',
                'ContentDisposition': 'inline'
            }
        )
        self.cache.delete_cache_source_data(f"{dirname}/{media_name}")

    
    def get_presigned_url(self, key: str) -> str:
        
        get_cache_data = self.cache.get_cache_source_data(key)

        if get_cache_data is not None:

            url = get_cache_data["url"]
            print("cache\n", url)
            return url

        url = self.s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": os.getenv("AWS_BUCKET_NAME"),
                "Key": key
            },
            ExpiresIn=3600,
        )

        data = {
            "url": url
        }

        self.cache.set_cache_source_data(key, data)

        print(url)
        return url
    

    def delete_file(self, dirname: str, filename: str) -> bool:
        key = f"{dirname}/{filename}"
        bucket = os.getenv("AWS_BUCKET_NAME")

        try:
            self.s3.delete_object(Bucket=bucket, Key=key)
            self.cache.delete_cache_source_data(key)
            return True
        except self.s3.exceptions.NoSuchKey:
            return False
        except botocore.exceptions.ClientError as e:
            return False
        except Exception as e:
            return False


