## File Microservice - Python + Backblaze B2

A fully tested, production-ready file upload microservice built with **FastAPI**, **Celery**, **Redis**, **PostgreSQL**, and **Backblaze B2**.

Supports asynchronous file uploads, type and size validation, deduplication using file hashing, and cloud storage integration.

Backblaze B2 is cheaper than solutions such as S3 and GCS, and thus more reasonable for small-dev teams starting out on a project.

## Features

- ## Asynchronous file uploads with validation
- ## Metadata fields
- ## Retrieval endpoints with pagination and filtering
- ## Cloud storage using Backblaze B2
- ## Celery workers for async file upload processing
- ## Docker-Compose setup and ready
- ## 100% test coverage 

## API endpoints

| GET    | `/health`                    | Health check                     |
| POST   | `/upload`                    | Upload a new file                |
| GET    | `/files/{file_id}`           | Retrieve file metadata           |
| GET    | `/files`                     | List files with filters & pages  |
| DELETE | `/files/{file_id}`           | Delete file by ID                |
| GET    | `/files/{file_id}/download`  | Get public download link   

## Tests

All tests are located in [`tests/`](./tests). Please read the test_summary.md for further
specifications on what they cover.

## Setup

## Create your .env file


```env
# PostgreSQL
DATABASE_URL=your_url

# Redis
REDIS_URL=your_url

# Backblaze B2
B2_APPLICATION_KEY_ID=your-b2-key-id
B2_APPLICATION_KEY=your-b2-key
B2_BUCKET_NAME=your-b2-bucket

# Security
SECRET_KEY=your-super-secret-key
```

## Run with docker-compose

```docker-compose up --build```

## MIT license:
This project is licensed under the MIT License – free for personal and commercial use.

## Feedback

I would appreciate your feedback and suggestions!