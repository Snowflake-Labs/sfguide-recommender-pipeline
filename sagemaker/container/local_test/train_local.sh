#!/bin/sh

image=$1

mkdir -p test_dir/model
mkdir -p test_dir/output

rm test_dir/model/*
rm test_dir/output/*

docker run -v $(pwd)/test_dir:/opt/ml \
    -e AWS_ACCESS_KEY_ID=$(aws configure get default.aws_access_key_id) \
    -e AWS_SECRET_ACCESS_KEY=$(aws configure get default.aws_secret_access_key) \
    -e AWS_DEFAULT_REGION=us-east-1  --rm ${image} train
