from google.cloud import storage

import sys

# Authenticate with Google Cloud using the service account key file
key = sys.argv[1]
storage_client = storage.Client.from_service_account_json(key)

# List Cloud Storage Buckets to validate the communication
buckets = list(storage_client.list_buckets())
print(buckets)