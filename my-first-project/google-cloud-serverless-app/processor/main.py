import base64
import datetime
import json
import logging
import os
import re
from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize GCP clients lazily
storage_client = None
bq_client = None

def get_storage_client():
    global storage_client
    if storage_client is None:
        storage_client = storage.Client()
    return storage_client

def get_bq_client():
    global bq_client
    if bq_client is None:
        bq_client = bigquery.Client()
    return bq_client

@app.route("/", methods=["POST"])
def process_message():
    """Receives and processes Pub/Sub push messages."""
    envelope = request.get_json()
    if not envelope:
        msg = "no Pub/Sub message received"
        logger.error(msg)
        return f"Bad Request: {msg}", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        logger.error(msg)
        return f"Bad Request: {msg}", 400

    pubsub_message = envelope["message"]

    if "data" not in pubsub_message:
        msg = "message has no data field"
        logger.error(msg)
        return f"Bad Request: {msg}", 400

    # Decode the base64 Pub/Sub data payload
    try:
        data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        event_data = json.loads(data_str)
    except Exception as e:
        logger.error(f"Error decoding/parsing message data: {e}")
        return "Bad Request: data payload is not valid base64-encoded JSON", 400

    logger.info(f"Received event payload: {json.dumps(event_data)}")

    # GCS Notifications can be sent for multiple events. We are interested in file creations (OBJECT_FINALIZE)
    # However, sometimes we might receive other events. We'll extract properties assuming it's standard GCS notification.
    bucket_name = event_data.get("bucket")
    object_name = event_data.get("name")
    size = event_data.get("size", 0)
    content_type = event_data.get("contentType", "application/octet-stream")

    if not bucket_name or not object_name:
        # Ignore folder creations or deletions/other events that don't represent a file object
        logger.info("Event doesn't contain GCS bucket/object details (possibly directory creation or delete). Skipping.")
        return "OK", 200

    logger.info(f"Processing file gs://{bucket_name}/{object_name} (Size: {size} bytes, Content-Type: {content_type})")

    try:
        # 1. Processing and simulated OCR
        word_count = 0
        tags = []
        ocr_text_preview = ""

        # Check if the file is a text file
        is_text = object_name.endswith(".txt") or content_type.startswith("text/")

        if is_text:
            logger.info("Detected text file. Downloading contents to perform simulated OCR & metadata extraction...")
            try:
                s_client = get_storage_client()
                bucket = s_client.bucket(bucket_name)
                blob = bucket.blob(object_name)
                text_content = blob.download_as_text(encoding="utf-8")
                
                # Word count calculation
                words = re.findall(r"\b\w+\b", text_content)
                word_count = len(words)
                
                # Preview (up to 200 chars)
                ocr_text_preview = text_content[:200]
                
                # Tags: extract words > 5 chars, filter out standard stopwords roughly or just take unique ones
                # Let's find unique alphanumeric words of length > 5, convert to lowercase
                candidate_tags = [w.lower() for w in words if len(w) > 5 and w.isalnum()]
                # Deduplicate and sort by length or just unique set
                unique_tags = sorted(list(set(candidate_tags)))
                tags = unique_tags[:5]  # limit to top 5 tags
                if not tags:
                    tags = ["text-file", "parsed"]
            except Exception as download_err:
                logger.error(f"Failed to read file from GCS: {download_err}")
                raise download_err
        else:
            logger.info("Non-text file detected. Simulating OCR metadata generation...")
            # Simulate OCR word count and metadata for PDF/Images/etc.
            import random
            word_count = random.randint(150, 850)
            ocr_text_preview = f"Simulated OCR preview for file: {object_name} (Type: {content_type})."
            
            # Simulated tags based on content-type or filename suffix
            suffix = os.path.splitext(object_name)[1].replace(".", "").lower()
            tags = ["scanned", "ocr-simulated"]
            if suffix:
                tags.append(suffix)
            if "pdf" in content_type:
                tags.append("pdf-document")
            elif "image" in content_type:
                tags.append("image-source")

        # 2. BigQuery Streaming Ingestion
        project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        bq_dataset = os.environ.get("BQ_DATASET", "document_processing")
        bq_table = os.environ.get("BQ_TABLE", "metadata")
        
        if not project_id:
            # Try to get project ID from BigQuery client if not set in environment
            b_client = get_bq_client()
            project_id = b_client.project

        table_id = f"{project_id}.{bq_dataset}.{bq_table}"
        logger.info(f"Streaming metadata into BigQuery table: {table_id}")

        row = {
            "filename": object_name,
            "bucket": bucket_name,
            "size": int(size),
            "content_type": content_type,
            "word_count": int(word_count),
            "tags": tags,
            "ocr_text_preview": ocr_text_preview,
            "process_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        b_client = get_bq_client()
        errors = b_client.insert_rows_json(table_id, [row])

        if errors:
            logger.error(f"Failed to insert row into BigQuery: {errors}")
            raise RuntimeError(f"BigQuery insert errors: {errors}")

        logger.info("Successfully processed document and streamed metadata to BigQuery.")
        return "OK", 200

    except Exception as e:
        logger.exception(f"Error processing document: {e}")
        # Return HTTP 500 to signal Pub/Sub to retry the delivery
        return f"Internal Server Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
