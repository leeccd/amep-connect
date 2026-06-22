# Save-Script configuration variables
$Region = "us-central1"
$DatasetId = "document_processing"
$TableId = "metadata"
$TopicName = "gcs-upload-topic"
$SubscriptionName = "gcs-upload-cloudrun-sub"

# Retrieve current GCP Project ID
$ProjectId = (gcloud config get-value project 2>$null)

if (-not $ProjectId) {
    Write-Error "ERROR: No Google Cloud Project ID is configured in gcloud CLI."
    Write-Host "Please set your project using: gcloud config set project [PROJECT_ID]"
    exit 1
}

$BucketName = "${ProjectId}-documents"
$ServiceName = "doc-processor"

Write-Host "================================================================="
Write-Host "Configuring Serverless Document Processing Pipeline Infrastructure"
Write-Host "Project ID:        $ProjectId"
Write-Host "Region:            $Region"
Write-Host "Storage Bucket:    gs://$BucketName"
Write-Host "Pub/Sub Topic:     $TopicName"
Write-Host "Subscription:      $SubscriptionName"
Write-Host "BigQuery Dataset:  $DatasetId"
Write-Host "BigQuery Table:    $TableId"
Write-Host "Cloud Run Service: $ServiceName"
Write-Host "================================================================="

# 1. Enable Google Cloud APIs
Write-Host "Step 1: Enabling Google Cloud APIs..."
gcloud services enable `
    storage.googleapis.com `
    pubsub.googleapis.com `
    run.googleapis.com `
    bigquery.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com

# 2. Create Storage Bucket
Write-Host "Step 2: Checking storage bucket..."
$bucketExists = gcloud storage buckets describe gs://$BucketName 2>$null
if ($bucketExists) {
    Write-Host "Bucket gs://$BucketName already exists."
} else {
    Write-Host "Creating GCS Bucket gs://$BucketName..."
    gcloud storage buckets create gs://$BucketName --location=$Region
}

# 3. Create BigQuery Dataset and Table
Write-Host "Step 3: Creating BigQuery resources..."
$datasetExists = bq show $DatasetId 2>$null
if ($datasetExists) {
    Write-Host "Dataset $DatasetId already exists."
} else {
    Write-Host "Creating dataset $DatasetId..."
    bq --project_id=$ProjectId mk --location=$Region $DatasetId
}

$tableExists = bq show "$DatasetId.$TableId" 2>$null
if ($tableExists) {
    Write-Host "Table $DatasetId.$TableId already exists."
} else {
    Write-Host "Creating table $DatasetId.$TableId using schema.json..."
    bq --project_id=$ProjectId mk `
        --table `
        --schema schema.json `
        "$DatasetId.$TableId"
}

# 4. Build and Deploy Cloud Run service
Write-Host "Step 4: Building and deploying Cloud Run service..."
gcloud run deploy $ServiceName `
    --source ./processor `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars BQ_DATASET=$DatasetId,BQ_TABLE=$TableId `
    --quiet

# Retrieve the Cloud Run service URL
$ServiceUrl = (gcloud run services describe $ServiceName --region $Region --format="value(status.url)")
Write-Host "Service URL is: $ServiceUrl"

# 5. Create Pub/Sub Topic and set up permissions
Write-Host "Step 5: Setting up Pub/Sub Topic..."
$topicExists = gcloud pubsub topics describe $TopicName 2>$null
if ($topicExists) {
    Write-Host "Pub/Sub Topic $TopicName already exists."
} else {
    Write-Host "Creating Pub/Sub Topic $TopicName..."
    gcloud pubsub topics create $TopicName
}

# Grant Cloud Storage service agent permission to publish to our topic
$ProjectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)")
$GcsServiceAccount = "service-${ProjectNumber}@gs-project-accounts.iam.gserviceaccount.com"

Write-Host "Granting Pub/Sub Publisher role to GCS Service Account: $GcsServiceAccount"
gcloud pubsub topics add-iam-policy-binding $TopicName `
    --member="serviceAccount:${GcsServiceAccount}" `
    --role="roles/pubsub.publisher" `
    --quiet

# Create GCS notification configuration to fire when objects are finalized (created)
Write-Host "Setting up GCS Bucket notification triggers..."
$notifications = gcloud storage buckets notifications list gs://$BucketName --format="value(name)" 2>$null
if ($notifications) {
    Write-Host "Notifications already configured for gs://$BucketName."
} else {
    gcloud storage buckets notifications create gs://$BucketName `
        --topic=$TopicName `
        --event-types="OBJECT_FINALIZE"
}

# 6. Create Pub/Sub Subscription pointing to Cloud Run
Write-Host "Step 6: Creating Pub/Sub Push Subscription..."
$subExists = gcloud pubsub subscriptions describe $SubscriptionName 2>$null
if ($subExists) {
    Write-Host "Pub/Sub Subscription $SubscriptionName already exists."
} else {
    gcloud pubsub subscriptions create $SubscriptionName `
        --topic=$TopicName `
        --push-endpoint=$ServiceUrl `
        --ack-deadline=60
}

Write-Host "================================================================="
Write-Host "Pipeline configuration completed successfully!"
Write-Host "You can now upload files to gs://$BucketName to process them."
Write-Host "================================================================="
