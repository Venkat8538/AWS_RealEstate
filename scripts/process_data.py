import boto3,pandas as pd
s3=boto3.client('s3')
df=pd.read_csv(s3.get_object(Bucket='house-price-mlops-dev-itzi2hgi',Key='data/raw/house_data.csv')['Body'])
df.to_csv('/tmp/out.csv',index=0)
s3.upload_file('/tmp/out.csv','house-price-mlops-dev-itzi2hgi','data/processed/data.csv')
print('✅ Data processed and saved to S3')