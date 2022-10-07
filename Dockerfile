FROM python:3.10.7-alpine3.16
RUN apk update \
    apk add \
        build-base \
        libffi-dev \
        openssl-dev \
        python3-dev
RUN pip install --upgrade pip
# Copy application files
COPY ./app /app
# Install application dependencies
RUN pip install -r /app/requirements.txt
# Set working directory
WORKDIR /app
ENV PYTHONBUFFERED 1
# Run application
CMD ["python", "app.py"]