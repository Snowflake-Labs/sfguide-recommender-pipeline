FROM python:3.7

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install boto3 numpy scikit-surprise snowflake-connector-python[pandas] flask gevent gunicorn 

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY recommendation_engine /opt/program
WORKDIR /opt/program

