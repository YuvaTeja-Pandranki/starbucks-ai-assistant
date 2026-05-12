FROM public.ecr.aws/lambda/python:3.11

COPY requirements-lambda.txt .
RUN pip install -r requirements-lambda.txt --target /var/task

COPY backend/ /var/task/backend/
COPY data/ /var/task/data/
COPY lambda_handler.py /var/task/
COPY .env.example /var/task/.env

CMD ["lambda_handler.handler"]
