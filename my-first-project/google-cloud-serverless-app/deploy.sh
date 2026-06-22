#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Default configurations
REGION="us-central1"
DATASET_ID="document_processing"
TABLE_ID="metadata"
TOPIC_NAME="gcs-upload-topic"
SUBSCRIPTION_NAME="gcs-upload-cloudrun-sub"

# Retrieve current GCP Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No Google Cloud Project ID is configured in gcloud CLI."
    echo "Please set your project using: gcloud config set project [PROJECT_ID]"
    exit 1
fi

BUCKET_NAME="${PROJECT_ID}-documents"
SERVICE_NAME="doc-processor"

echo "================================================================="
echo "Configuring Serverless Document Processing Pipeline Infrastructure"
echo "Project ID:        $PROJECT_ID"
echo "Region:            $REGION"
echo "Storage Bucket:    gs://$BUCKET_NAME"
echo "Pub/Sub Topic:     $TOPIC_NAME"
echo "Subscription:      $SUBSCRIPTION_NAME"
echo "BigQuery Dataset:  $DATASET_ID"
echo "BigQuery Table:    $TABLE_ID"
echo "Cloud Run Service: $SERVICE_NAME"
echo "================================================================="

# 1. Enable Google Cloud APIs
echo "Step 1: Enabling Google Cloud APIs..."
gcloud services enable \
    storage.googleapis.com \
    pubsub.googleapis.com \
    run.googleapis.com \
    bigquery.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

# 2. Create Storage Bucket
echo "Step 2: Checking storage bucket..."
if gcloud storage buckets describe gs://"$BUCKET_NAME" >/dev/null 2>&1; then
    echo "Bucket gs://$BUCKET_NAME already exists."
else
    echo "Creating GCS Bucket gs://$BUCKET_NAME..."
    gcloud storage buckets create gs://"$BUCKET_NAME" --location="$REGION"
fi

# 3. Create BigQuery Dataset and Table
echo "Step 3: Creating BigQuery resources..."
if bq show "$DATASET_ID" >/dev/null 2>&1; then
    echo "Dataset $DATASET_ID already exists."
else
    echo "Creating dataset $DATASET_ID..."
    bq --project_id="$PROJECT_ID" mk --location="$REGION" "$DATASET_ID"
fi

if bq show "$DATASET_ID.$TABLE_ID" >/dev/null 2>&1; then
    echo "Table $DATASET_ID.$TABLE_ID already exists."
else
    echo "Creating table $DATASET_ID.$TABLE_ID using schema.json..."
    bq --project_id="$PROJECT_ID" mk \
        --table \
        --schema schema.json \
        "$DATASET_ID.$TABLE_ID"
fi

# 4. Build and Deploy Cloud Run service
echo "Step 4: Building and deploying Cloud Run service..."
gcloud run deploy "$SERVICE_NAME" \
    --source ./processor \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars BQ_DATASET="$DATASET_ID",BQ_TABLE="$TABLE_ID" \
    --quiet

# Retrieve the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
echo "Service URL is: $SERVICE_URL"

# 5. Create Pub/Sub Topic and set up permissions
echo "Step 5: Setting up Pub/Sub Topic..."
if gcloud pubsub topics describe "$TOPIC_NAME" >/dev/null 2>&1; then
    echo "Pub/Sub Topic $TOPIC_NAME already exists."
else
    echo "Creating Pub/Sub Topic $TOPIC_NAME..."
    gcloud pubsub topics create "$TOPIC_NAME"
fi

# Grant Cloud Storage service agent permission to publish to our topic
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
GCS_SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"

echo "Granting Pub/Sub Publisher role to GCS Service Account: $GCS_SERVICE_ACCOUNT"
gcloud pubsub topics add-iam-policy-binding "$TOPIC_NAME" \
    --member="serviceAccount:${GCS_SERVICE_ACCOUNT}" \
    --role="roles/pubsub.publisher" \
    --quiet

# Create GCS notification configuration to fire when objects are finalized (created)
echo "Setting up GCS Bucket notification triggers..."
NOTIFICATIONS_LIST=$(gcloud storage buckets notifications list gs://"$BUCKET_NAME" --format="value(name)" 2>/dev/null || true)
if [ -n "$NOTIFICATIONS_LIST" ]; then
    echo "Notifications already configured for gs://$BUCKET_NAME."
else
    gcloud storage buckets notifications create gs://"$BUCKET_NAME" \
        --topic="$TOPIC_NAME" \
        --event-types="OBJECT_FINALIZE"
fi

# 6. Create Pub/Sub Subscription pointing to Cloud Run
echo "Step 6: Creating Pub/Sub Push Subscription..."
if gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" >/dev/null 2>&1; then
    echo "Pub/Sub Subscription $SUBSCRIPTION_NAME already exists."
else
    gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" \
        --topic="$TOPIC_NAME" \
        --push-endpoint="$SERVICE_URL" \
        --ack-deadline=60
fi

echo "================================================================="
echo "Pipeline configuration completed successfully!"
echo "You can now upload files to gs://$BUCKET_NAME to process them."
echo "================================================================="
