# redis-s3-lambda-example

The purpose of this project is to highlight how to use Amazon Elasticache (Redis) as a cache for S3.  The compute used in this example is AWS Lambda.  A AWS Lambda function will read data from either Elasticache or an input S3 bucket and write the output to another S3 bucket.  

The simple example uses data stored in *metadata* files to determine the objects to download.  The raw data stored used for the transfers is stored in the *InputBucket*.

A single-node Elasticache Redis host is created in the same subnet that is associated with the VPC-enabled Lambda Function.

# Dependencies

* [AWS CLI](https://aws.amazon.com/cli/)

* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

* [Docker Desktop](https://docs.docker.com/engine/install/)

# Deployment

## Build the resources

```bash
sam build --use-container
```

## Deploy the resources

For the first deployment, please run the following command and save the generated configuration file *samconfig.toml*.  Please use **redis-s3-lambda-example** for the stack name.  

```bash
sam deploy --guided
```

Subsequent deployments can use the simplified `sam deploy`.  The command will use the generated configuration file *samconfig.toml*.

## Create and copy input files to the InputBucket

The raw data used for the transfers are stored in S3.  The files will first need to be created in the *raw_data* directory.  Once they are created, they can be uploaded to the *InputBucket*.  The *utilities/upload_raw.sh* script will determine the *InputBucket* resource by querying the CloudFormation stack and upload the files in the *raw_data* directory to the bucket.  

### Create files in the raw_directory

The *metadata* files reference files *file1*, *file2*, and *file3*.  The first step in the process is to create the files locally.

#### Mac OS X

```bash
for num in 1 2 3; do
    echo "Creating 10m file at raw_data/file${num}" && mkfile 10m raw_data/file${num}
done
```

#### Linux

```bash
for num in 1 2 3; do
    echo "Creating 10m file at raw_data/file${num}" && dd if=/dev/zero of=raw_data/file${num} bs=10240000 count=1
done
```

### Upload files to the InputBucket

Once the raw files are created, they will need to be uploaded to the InputBucket created in the CloudFormation stack *redis-s3-lambda-example*.

```bash
bash utilities/upload_raw.sh redis-s3-lambda-example
```

# Testing the application

Copy operations are started by uploading metadata files to the *MetadataBucket* S3 bucket.  The *utilities/upload_metadata.sh* script will determine the *MetadataBucket* resource by querying the CloudFormation stack and uploading JSON files in the *metadata* directory to the bucket.  Uploading data will, in turn, trigger the Lambda function execution.

```bash
bash utilities/upload_metadata.sh redis-s3-lambda-example
```

