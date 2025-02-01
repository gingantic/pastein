import mimetypes
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import hashlib
from boto3.s3.transfer import TransferConfig
import logging

# NOTE: Alternative for vercel if have problem with access denied using django-storages
# Tested on Supabase S3
@deconstructible
class S3Boto3Storage(Storage):
    def __init__(self, 
                    access_key=None, 
                    secret_key=None, 
                    bucket_name=None, 
                    region_name=None, 
                    custom_domain=None, 
                    default_acl=None, 
                    querystring_auth=None, 
                    url_expire=None, 
                    location=None,
                    signature_version=None,
                    endpoint_url=None,
                    **kwargs):
        
        self.access_key = access_key if access_key is not None else getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_key = secret_key if secret_key is not None else getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        self.bucket_name = bucket_name if bucket_name is not None else getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
        self.region_name = region_name if region_name is not None else getattr(settings, 'AWS_REGION_NAME', None)
        self.custom_domain = custom_domain if custom_domain is not None else getattr(settings, 'AWS_CUSTOM_DOMAIN', None)
        self.default_acl = default_acl if default_acl is not None else getattr(settings, 'AWS_DEFAULT_ACL', None)
        self.querystring_auth = querystring_auth if querystring_auth is not None else getattr(settings, 'AWS_QUERYSTRING_AUTH', False)
        self.url_expire = url_expire if url_expire is not None else getattr(settings, 'AWS_URL_EXPIRE', 3600)
        self.location = location.strip('/') if location else getattr(settings, 'AWS_LOCATION', '').strip('/')
        self.signature_version = signature_version or getattr(settings, 'AWS_SIGNATURE_VERSION', 's3v4')
        self.endpoint_url = endpoint_url or getattr(settings, 'AWS_ENDPOINT_URL', None)

        # Initialize the S3 session and client
        self.session = boto3.session.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        )
        self.s3_client = self.session.client(
            's3',
            config=Config(
                signature_version=self.signature_version,
                retries={'max_attempts': 10, 'mode': 'standard'},
                s3={'use_accelerate_endpoint': False, 'payload_signing_enabled': True}
            ),
            endpoint_url=self.endpoint_url
        )

    def _full_path(self, name):
        return f"{self.location}/{name}".strip('/')

    def _open(self, name, mode='rb'):
        if mode != 'rb' and mode != 'r':
            raise ValueError("S3 files can only be opened in read-only mode")
        key_name = self._full_path(name)
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key_name)
            return ContentFile(obj['Body'].read(), name=name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File {name} does not exist") from e
            raise

    def calculate_checksum(self, file):
        hasher = hashlib.sha256()
        file.seek(0)  # Ensure reading from the start
        while chunk := file.read(8192):
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            hasher.update(chunk)
        file.seek(0)  # Reset pointer after reading
        return hasher.hexdigest()

    def _save(self, name, content):
        # If the file appears to be uploaded but the file is invalid, Try debug use this
        # boto3.set_stream_logger('', logging.DEBUG)

        key_name = self._full_path(name)
        content.file.seek(0)
        file_data = content.file.read()  # Read once and store

        if not file_data:
            raise ValueError("File data is empty")

        # print(f"Original File: {file_data[:100]}...")
        # original_checksum = self.calculate_checksum(content.file)

        content_type, _ = mimetypes.guess_type(name)
        content_type = content_type or 'application/octet-stream'

        print(f"Content Type: {content_type}")

        # Prepare ExtraArgs without ACL if it's None
        extra_args = {
            "ContentType": content_type,
        }
        if self.default_acl is not None:
            extra_args['ACL'] = self.default_acl  # Only add ACL if defined

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key_name,
            Body=file_data,
            **extra_args
        )

        # Download file and re-check checksum
        # downloaded = self.s3_client.get_object(Bucket=self.bucket_name, Key=key_name)['Body'].read()
        # uploaded_checksum = hashlib.sha256(downloaded).hexdigest()

        # print(f"Original: {original_checksum}, Uploaded: {uploaded_checksum}")
        # print(f"File Download: {downloaded[:100]}...")

        # if original_checksum != uploaded_checksum:
        #     print(f"File corruption detected! Original: {original_checksum}, Uploaded: {uploaded_checksum}")
        #     raise ValueError("Checksum not same")

        return name

    def delete(self, name):
        key_name = self._full_path(name)
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key_name)

    def exists(self, name):
        key_name = self._full_path(name)
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def listdir(self, path):
        path = self._full_path(path)
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=path)
        directories, files = set(), []

        if 'Contents' not in response:
            return [], []

        for obj in response.get('Contents', []):
            key = obj['Key']
            relative_path = key[len(path):].lstrip('/')
            if '/' in relative_path:
                directories.add(relative_path.split('/')[0])
            else:
                files.append(relative_path)

        return list(directories), files


    def size(self, name):
        key_name = self._full_path(name)
        try:
            obj = self.s3_client.head_object(Bucket=self.bucket_name, Key=key_name)
            return obj['ContentLength']
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File {name} does not exist") from e
            raise e

    def url(self, name):
        key_name = self._full_path(name)
        if self.custom_domain:
            return f"https://{self.custom_domain.rstrip('/')}/{key_name.lstrip('/')}"
        elif self.querystring_auth:
            params = {'Bucket': self.bucket_name, 'Key': key_name}
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=self.url_expire
            )
            return url
        else:
            region = self.s3_client.meta.region_name
            if region == 'us-east-1':
                base_url = f"https://{self.bucket_name}.s3.amazonaws.com"
            else:
                base_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
            return f"{base_url}/{key_name}"

    def get_available_name(self, name, max_length=None):
        name = self._full_path(name)
        return super().get_available_name(name, max_length)