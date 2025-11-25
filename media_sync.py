"""
Media File Sync Helper
Automatically configures storage backend based on environment
"""

import os
import sys
from pathlib import Path

def check_s3_configuration():
    """Check if S3 credentials are properly configured"""
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_STORAGE_BUCKET_NAME'
    ]
    
    return all(os.getenv(var) for var in required_vars)

def check_media_files():
    """Check if media files exist locally"""
    media_path = Path('media')
    if not media_path.exists():
        return 0
    
    file_count = sum(1 for _ in media_path.rglob('*') if _.is_file())
    return file_count

def diagnose_storage():
    """Diagnose current storage configuration"""
    print("=" * 60)
    print("📁 Media Storage Diagnostic")
    print("=" * 60)
    
    # Check environment
    use_s3 = os.getenv('USE_S3', 'False').lower() == 'true'
    has_s3_config = check_s3_configuration()
    local_files = check_media_files()
    
    print(f"\n📊 Configuration Status:")
    print(f"  USE_S3 setting: {use_s3}")
    print(f"  AWS credentials configured: {has_s3_config}")
    print(f"  Local media files: {local_files}")
    
    print(f"\n💾 Storage Backend:")
    if use_s3 and has_s3_config:
        print("  ✅ Using AWS S3 (Cloud storage)")
        print(f"     Bucket: {os.getenv('AWS_STORAGE_BUCKET_NAME')}")
        print(f"     Region: {os.getenv('AWS_S3_REGION_NAME', 'us-east-1')}")
    else:
        print("  ✅ Using Local Storage (/media folder)")
        print(f"     Files: {local_files}")
    
    print(f"\n🔧 Recommendations:")
    if not has_s3_config and use_s3:
        print("  ⚠️  USE_S3=True but AWS credentials not configured!")
        print("     Add credentials to .env file:")
        print("     - AWS_ACCESS_KEY_ID")
        print("     - AWS_SECRET_ACCESS_KEY")
        print("     - AWS_STORAGE_BUCKET_NAME")
    elif has_s3_config and not use_s3:
        print("  ℹ️  AWS credentials available but USE_S3=False")
        print("     Set USE_S3=True in .env to enable cloud storage")
    elif not has_s3_config and local_files > 0:
        print("  ✅ Local storage with files - all good!")
    elif not has_s3_config and local_files == 0:
        print("  ℹ️  No local files yet")
        print("     Upload files through the application")
    
    print("\n" + "=" * 60)

def pull_from_s3():
    """Pull media files from S3 to local machine"""
    import boto3
    from botocore.exceptions import NoCredentialsError
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        media_path = Path('media')
        media_path.mkdir(exist_ok=True)
        
        print(f"📥 Downloading media files from S3...")
        
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix='media/')
        
        if 'Contents' not in response:
            print("   No files found in S3")
            return
        
        downloaded = 0
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('/'):
                continue
            
            local_file = Path(key)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"   ⬇️  {key}")
            s3_client.download_file(bucket, key, str(local_file))
            downloaded += 1
        
        print(f"✅ Downloaded {downloaded} files")
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print("   Add to .env file:")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
    except Exception as e:
        print(f"❌ Error: {e}")

def push_to_s3():
    """Push local media files to S3"""
    import boto3
    from botocore.exceptions import NoCredentialsError
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        media_path = Path('media')
        
        if not media_path.exists():
            print("❌ No local media folder found")
            return
        
        print(f"📤 Uploading media files to S3...")
        
        uploaded = 0
        for file_path in media_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            s3_key = str(file_path)
            print(f"   ⬆️  {s3_key}")
            s3_client.upload_file(str(file_path), bucket, s3_key)
            uploaded += 1
        
        print(f"✅ Uploaded {uploaded} files")
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Default: diagnose
        diagnose_storage()
    else:
        command = sys.argv[1]
        
        if command == 'diagnose':
            diagnose_storage()
        elif command == 'pull':
            pull_from_s3()
        elif command == 'push':
            push_to_s3()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python manage.py shell < media_sync.py diagnose")
            print("  python media_sync.py diagnose  # Check configuration")
            print("  python media_sync.py pull      # Download from S3")
            print("  python media_sync.py push      # Upload to S3")
