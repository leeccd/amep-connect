import base64
import json
import requests
import sys

LOCAL_URL = "http://localhost:8080"

def create_mock_pubsub_payload(bucket, name, size, content_type):
    """Creates a mock Pub/Sub envelope simulating a GCS OBJECT_FINALIZE event."""
    gcs_event = {
        "kind": "storage#object",
        "id": f"{bucket}/{name}/12345",
        "selfLink": f"https://www.googleapis.com/storage/v1/b/{bucket}/o/{name}",
        "name": name,
        "bucket": bucket,
        "generation": "12345",
        "metageneration": "1",
        "contentType": content_type,
        "timeCreated": "2026-06-15T12:00:00.000Z",
        "updated": "2026-06-15T12:00:00.000Z",
        "storageClass": "STANDARD",
        "size": str(size),
        "md5Hash": "abcdef123456",
        "mediaLink": f"https://www.googleapis.com/download/storage/v1/b/{bucket}/o/{name}?alt=media",
        "crc32c": "xyz123",
        "etag": "etagval"
    }
    
    # Encode the GCS event to base64 as Pub/Sub does
    event_bytes = json.dumps(gcs_event).encode("utf-8")
    base64_data = base64.b64encode(event_bytes).decode("utf-8")
    
    return {
        "message": {
            "data": base64_data,
            "messageId": "99999999999",
            "publishTime": "2026-06-15T12:00:01.000Z"
        },
        "subscription": "projects/mock-project/subscriptions/mock-sub"
    }

def test_payload(payload, description):
    print(f"\n--- Testing: {description} ---")
    try:
        response = requests.post(LOCAL_URL, json=payload, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed. Is the local Flask server running at http://localhost:8080?")
        return False

def main():
    print("Sending mock Pub/Sub requests to local service...")
    
    # 1. Test non-text file trigger (should trigger mock OCR and not access GCS download)
    pdf_payload = create_mock_pubsub_payload(
        bucket="my-mock-bucket",
        name="invoice.pdf",
        size=154320,
        content_type="application/pdf"
    )
    pdf_success = test_payload(pdf_payload, "Non-Text File (PDF) Simulated Ingestion")
    
    # 2. Test text file trigger (note: this might fail if GCS download fails,
    # unless GCS_PROJECT environment is configured and GCS file actually exists)
    txt_payload = create_mock_pubsub_payload(
        bucket="my-mock-bucket",
        name="notes.txt",
        size=45,
        content_type="text/plain"
    )
    print("\n* Note: Text files will trigger downloading from GCS. If the bucket/file doesn't exist on GCS, the Flask service should throw an error and return HTTP 500.")
    txt_success = test_payload(txt_payload, "Text File (TXT) Ingestion")

    if pdf_success:
        print("\nLocal simulation tests completed successfully (PDF simulation worked)!")
        sys.exit(0)
    else:
        print("\nSome tests failed. Verify your local service status.")
        sys.exit(1)

if __name__ == "__main__":
    main()
