#!/bin/bash

# Upload data to the InputBucket.  These objects will be used by the Lambda calculator.

if (( $# != 1 )); then
  echo "Error: Please pass in the stack name as the script argument."
  exit 1
fi

STACK_NAME=${1}

INPUT_BUCKET=$(aws cloudformation describe-stack-resource --stack-name ${STACK_NAME} --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)

for file in $(ls raw_data/* | awk -F'/' '{print $2}'); do
  echo "Uploading ${file} to s3://${INPUT_BUCKET}/${file}" && aws s3 cp raw_data/${file} s3://${INPUT_BUCKET}/${file}
done