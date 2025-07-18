File upload testing:
    -> multiple file types
    -> file validation (100MB size)
    -> deduplication test
    -> form data

API endpoint tests:

    GET /health - Service health check
    POST /upload - File upload with validation
    GET /files/{id} - Retrieve file metadata
    GET /files - List files with pagination & filtering
    DELETE /files/{id} - File deletion
    GET /files/{id}/download - Download URL generation

Performance tests:

    -> concurrent uploads for five simultaneous files
    -> stress test with 10 rapid uploads after another
    -> pagination test

error handling:

    -> 400/413 for bad files
    -> 404 as usual
    -> edge: empty file, special chars in filename

system test:

    -> real postgresql tested
    -> testing live running Docker containers
    -> celery processing test
    -> file hash based duplicate detection