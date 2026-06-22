#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Retrieve current GCP Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No Google Cloud Project ID is configured in gcloud CLI."
    exit 1
fi

BUCKET_NAME="${PROJECT_ID}-documents"
DATASET_ID="document_processing"
TABLE_ID="metadata"

echo "================================================================="
echo "Cloud Integration Test for Document Processing Pipeline"
echo "Project: $PROJECT_ID"
echo "Bucket:  gs://$BUCKET_NAME"
echo "Table:   $PROJECT_ID.$DATASET_ID.$TABLE_ID"
echo "================================================================="

# Create sample files
echo "Creating local sample test files..."
cat <<EOF > sample_invoice.pdf
%PDF-1.4 Mock PDF Content for Invoicing Pipeline
EOF

cat <<EOF > sample_document.txt
Google Cloud Platform serverless computing allows developers to build and run applications
without thinking about servers. It handles provisioning, scaling, and managing infrastructure.
Our serverless document pipeline uses GCS, Pub/Sub, Cloud Run, and BigQuery.
EOF

echo "Uploading files to storage bucket gs://$BUCKET_NAME..."
gcloud storage cp sample_invoice.pdf gs://"$BUCKET_NAME"/sample_invoice.pdf
gcloud storage cp sample_document.txt gs://"$BUCKET_NAME"/sample_document.txt

echo "Files uploaded. Sleeping for 10 seconds to allow async processing to complete..."
sleep 10

echo "Querying BigQuery to verify metadata ingestion..."
bq query --nouse_legacy_sql "
SELECT 
  filename, 
  bucket, 
  size, 
  content_type, 
  word_count, 
  tags, 
  LEFT(ocr_text_preview, 50) as ocr_preview_short,
  process_timestamp
FROM 
  \`$PROJECT_ID.$DATASET_ID.$TABLE_ID\`
ORDER BY 
  process_timestamp DESC
LIMIT 5
"

# Clean up local temp files
rm -f sample_invoice.pdf sample_document.txt

echo "================================================================="
echo "Integration test run finished."
echo "If rows for sample_invoice.pdf and sample_document.txt are shown above, the pipeline works!"
echo "================================================================="
