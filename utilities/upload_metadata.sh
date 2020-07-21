#!/bin/bash

# Upload data to the MetaDataBucket to kick off calculations.

if (( $# != 1 )); then
  echo "Error: Please pass in the stack name as the script argument."
  exit 1
fi

STACK_NAME=${1}

METADATA_BUCKET=$(aws cloudformation describe-stack-resource --stack-name ${STACK_NAME} --logical-resource-id MetadataBucket --query "StackResourceDetail.PhysicalResourceId" --output text)

for file in $(ls metadata/*.json | awk -F'/' '{print $2}'); do
  echo "Uploading ${file} to s3://${METADATA_BUCKET}/${file}" && aws s3 cp metadata/${file} s3://${METADATA_BUCKET}/${file}
done