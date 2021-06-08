
## Model Training, Deployment and Inference Using External Functions

#### Create the External Functions within Snowflake. 

We will create three External Functions: first one for training and bulk prediction, second for deploying the model and third for invoking the model.

1. Create `train_and_get_recommendations` external function:

    ```sql
    create or replace external function train_and_get_recommendations(input_table_name varchar, output_table_name varchar)
        returns variant
        api_integration = snf_recommender_api_integration
        as '<TRAIN_ENDPOINT_URL>';
    ```
    
    Fill in the `TRAIN_ENDPOINT_URL` from the serverless output as shown below:

    ![Train endpoint](./images/train_endpoint.png)

2. Similarly, create the `deploy_model` and `invoke_model` by filling in the corresponding endpoint URLs from the Serverless output:

    ```sql
    create or replace external function deploy_model(model_name varchar, model_url varchar)
    returns variant
    api_integration = snf_recommender_api_integration
    as '<DEPLOY_ENDPOINT_URL>';
    ```

    ```sql
    create or replace external function invoke_model(model_name varchar, user_id varchar, item_id varchar)
    returns variant
    api_integration = snf_recommender_api_integration
    as '<INVOKE_ENDPOINT_URL>';
    ```

3. Grant usage on the newly created External Functions to `sysadmin` role:

    ```sql
    grant usage on function train_and_get_recommendations(varchar, varchar) to role sysadmin;
    grant usage on function deploy_model(varchar, varchar) to role sysadmin;
    grant usage on function invoke_model(varchar, varchar, varchar) to role sysadmin;
    ```

#### Testing it out

Now that our Snowflake External Functions are deployed and the right persmissions are in place, its time to test the functions and see how we can trigger training and deployment of models right from Snowflake.

1. In the Snowflake UI, switch over to using the `sysadmin` role:

    `use role sysadmin;`

2. Review the newly created External Functions:

    `show external functions;`

3. Trigger SageMaker training and bulk predictions and get top 10 ratings for each user in our target table. 

    ```sql
    create or replace table MOVIELENS.PUBLIC.user_movie_recommendations like MOVIELENS.PUBLIC.user_movie_recommendations_local_test;

    select train_and_get_recommendations('MOVIELENS.PUBLIC.ratings_train_data','MOVIELENS.PUBLIC.user_movie_recommendations');
    ```

    The first parameter is the input table name that contains the training data. Second parameter specifies the output table name where the top 10 predictions for each user are to be stored.

4. To check the status of the training, check the `Training Jobs` section of the SageMaker console:

    ![SageMaker Training Jobs](./images/sagemaker_training.png)

    Note: the training will take about 5-10 mins to complete.

5. Our training code not only trained a new model using the SVD algorithm but also performed bulk prediciton and calculated the top 10 movie recommendations for each user. To the view the top 10 recommendations, run:

    ```sql
    select * from user_movie_recommendations limit 10;
    ```

6. When a user pulls up details for a movie, how do we get the predicted rating for this user/movie pair? We will have to use a real-time prediction endpoint for that. We can create this endpoint by using the model artifact produced by the training step above. 

    Switch to the SageMaker console and click on the training job name to view details. Scroll downd to find and copy the value of the model artifact.

    ![S3 Model Artifact](./images/model_artifact.png)


7. Copy the S3 model artifact path from the previous step into the SQL below and run it to deploy the model as an API.

    ```sql
    select deploy_model('movielens-model-v1', '<S3_MODEL_ARTIFACT>');
    ```

8. Check the `Endpoints` tab within the SageMaker console to view the status of the endpoint.

    Note: deploying an endpoint might take 5-15 mins.

9. While the endpoint in deploying, lets create some dummy data to test out the inference API:

    ```sql
    -- create a table to hold pairs of users and movies where we DO NOT have a rating
    create or replace table no_ratings (USERID float, MOVIEID float); 
    insert into no_ratings (USERID, MOVIEID) values
        ('1', '610'),
        ('10', '313'),
        ('10', '297'),
        ('5', '18'),
        ('5', '19');
    ```

    Wait for the endpoint to get into "In Service" status.

10. Now we can call the deployed model using our `invoke_model` External Functions right from any SQL query like this:

    ```sql
    --real-time prediction for an individual movie for a particular user
    select nr.USERID, nr.MOVIEID, m.title, invoke_model('movielens-model-v1', nr.USERID, nr.MOVIEID) as rating_prediction 
    from no_ratings nr, movies m
    where nr.movieid = m.movieid;
    ```

### Extra Credit: Automating the ML Pipeline

We will leave it as an exercise to automate this ML workflow. As new users and movies are added, the ML training, bulk prediction and model deployment can be automated. 

*Hint*: You can use [Continuous Data Pipelines](https://docs.snowflake.com/en/user-guide/data-pipelines.html) in Snowflake to automate `Tasks` which can call the External Functions we created above.

## Conclusion

Congratulations - you've built a lot of stuff in a short time! We started by ingesting data in lab 1 and then building a custom training and inference docker image for SageMaker in lab 2. In lab 3, we deployed a Serverless app to connect Snowflake and SageMaker using AWS Lambda and API Gateway. Finally, we tested to see how we can trigger SageMaker training, deployment and do inference using Snowflake External Functions.

