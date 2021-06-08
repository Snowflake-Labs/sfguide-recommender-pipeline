import json
import datetime
import time
import boto3
import os


def train_and_generate_recommendations(event, context):

    # 200 is the HTTP status code for "ok".
    status_code = 200

    try:
        # From the input parameter named "event", get the body, which contains
        # the input rows.
        event_body = event["body"]

        # Convert the input from a JSON string into a JSON object.
        payload = json.loads(event_body)
        # This is basically an array of arrays. The inner array contains the
        # row number, and a value for each parameter passed to the function.
        rows = payload["data"]

        # For each input row in the JSON object...
        for row in rows:
            # Read the input row number (the output row number will be the same).
            row_number = row[0]

            # Read the first input parameter's value. For example, this can be a
            # numeric value or a string, or it can be a compound value such as
            # a JSON structure.
            _input_table_name = row[1]
            _output_table_name = row[2]


        # start the SageMaker training job
        client = boto3.client('sagemaker')

        bucket = os.environ['s3_bucket'] 
        prefix = "training-job-" + time.strftime("%Y%m%d%H%M%S")

        s3_output_location = 's3://{}/'.format(bucket)

        print(s3_output_location)

        training_job_name = prefix
        TRAINING_IMAGE_ECR_PATH = os.environ['training_image_ecr_path']
        SAGEMAKER_ROLE_ARN = os.environ['sagemaker_role_arn']
        

        response = client.create_training_job(
            TrainingJobName=training_job_name,
            HyperParameters=dict(input_table_name=_input_table_name, output_table_name=_output_table_name, region=os.environ['region']),
            AlgorithmSpecification={
                'TrainingImage': TRAINING_IMAGE_ECR_PATH,
                'TrainingInputMode': 'File'
            },
            RoleArn=SAGEMAKER_ROLE_ARN,         
            OutputDataConfig={
                'S3OutputPath': s3_output_location
            },
            ResourceConfig={
                'InstanceType': 'ml.m5.xlarge',
                'InstanceCount': 1,
                'VolumeSizeInGB': 10
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 10000
            }
        )

        training_job_arn = response['TrainingJobArn']
        print(training_job_arn)

        array_of_rows_to_return = []
        # Put the returned row number and the returned value into an array.
        row_to_return = [0, training_job_arn]

        # ... and add that array to the main array.
        array_of_rows_to_return.append(row_to_return)

        json_compatible_string_to_return = json.dumps({"data" : array_of_rows_to_return})

    except Exception as err:
        # 400 implies some type of error.
        status_code = 400
        # Tell caller what this function could not handle.
        print(err)
        json_compatible_string_to_return = str(err)

    # Return the return value and HTTP status code.
    return {
        'statusCode': status_code,
        'body': json_compatible_string_to_return
    }


def deploy_model(event, context):

    # 200 is the HTTP status code for "ok".
    status_code = 200

    try:
        # From the input parameter named "event", get the body, which contains
        # the input rows.
        event_body = event["body"]

        # Convert the input from a JSON string into a JSON object.
        payload = json.loads(event_body)
        # This is basically an array of arrays. The inner array contains the
        # row number, and a value for each parameter passed to the function.
        rows = payload["data"]

        # For each input row in the JSON object...
        for row in rows:
            # Read the input row number (the output row number will be the same).
            row_number = row[0]

            # Read the first input parameter's value. 
            model_name = row[1]
            model_data_url = row[2]
        

        # start the SageMaker training job
        client = boto3.client('sagemaker')

        ECR_PATH = os.environ['training_image_ecr_path'] 
        SAGEMAKER_ROLE_ARN = os.environ['sagemaker_role_arn']

        response = client.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': ECR_PATH,
                'ModelDataUrl': model_data_url
            },
            ExecutionRoleArn=SAGEMAKER_ROLE_ARN
        )

        print(response)
        print("now trying to create endpoint config...")

        response = client.create_endpoint_config(
            EndpointConfigName=model_name,
            ProductionVariants=[
                {
                    'VariantName': 'variant-1',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.t2.medium'
                }
            ]
        )

        print(response)
        print("now trying to create the endpoint...")

        response = client.create_endpoint(
            EndpointName=model_name,
            EndpointConfigName=model_name
        )

        endpoint_arn = response['EndpointArn']
        print(endpoint_arn)

        array_of_rows_to_return = []
        # Put the returned row number and the returned value into an array.
        row_to_return = [0, endpoint_arn]

        # ... and add that array to the main array.
        array_of_rows_to_return.append(row_to_return)

        json_compatible_string_to_return = json.dumps({"data" : array_of_rows_to_return})

    except Exception as err:
        # 400 implies some type of error.
        status_code = 400
        # Tell caller what this function could not handle.
        print(err)
        json_compatible_string_to_return = str(err)

    # Return the return value and HTTP status code.
    return {
        'statusCode': status_code,
        'body': json_compatible_string_to_return
    }


# function that performs real-time prediction
def invoke_model(event, context):

    # 200 is the HTTP status code for "ok".
    status_code = 200

    try:
        # From the input parameter named "event", get the body, which contains
        # the input rows.
        event_body = event["body"]

        # Convert the input from a JSON string into a JSON object.
        payload = json.loads(event_body)
        # This is basically an array of arrays. The inner array contains the
        # row number, and a value for each parameter passed to the function.
        rows = payload["data"]

        # For each input row in the JSON object...
        body = ""
        for row in rows:
            model_name = row[1]
            # extract and transform the user_ids and item_ids posted to csv
            body = body + row[2] + "," + row[3] + "\n"
        
        # invoke the SageMaker endpoint
        client = boto3.client('sagemaker-runtime')
        response = client.invoke_endpoint(
            EndpointName=model_name,
            Body=body.encode('utf-8'),
            ContentType='text/csv'
        )

        predictions = response["Body"].read().decode('utf-8') 

        i = 0
        array_of_rows_to_return = []
        for prediction in iter(predictions.splitlines()):
            # Put the returned row number and the returned value into an array.
            row_to_return = [i, prediction]
            # ... and add that array to the main array.
            array_of_rows_to_return.append(row_to_return)
            i = i + 1

        json_compatible_string_to_return = json.dumps({"data" : array_of_rows_to_return})

    except Exception as err:
        # 400 implies some type of error.
        status_code = 400
        # Tell caller what this function could not handle.
        print(err)
        json_compatible_string_to_return = str(err)

    # Return the return value and HTTP status code.
    return {
        'statusCode': status_code,
        'body': json_compatible_string_to_return
    }