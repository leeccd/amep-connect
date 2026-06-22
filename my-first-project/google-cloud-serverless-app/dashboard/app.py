import os
import datetime
from flask import Flask, render_code_template, render_template, request, jsonify
from google.cloud import bigquery

app = Flask(__name__)

# Mock data for preview/fallback if BigQuery credentials are not configured
MOCK_DOCUMENTS = [
    {
        "filename": "q4_financial_report.pdf",
        "bucket": "my-first-project-documents",
        "size": 2453000,
        "content_type": "application/pdf",
        "word_count": 1420,
        "tags": ["finance", "report", "q4", "scanned"],
        "ocr_text_preview": "Q4 Financial Status. Profit increased by 15% year-over-year. Operating costs are stable...",
        "process_timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
    },
    {
        "filename": "pipeline_requirements.txt",
        "bucket": "my-first-project-documents",
        "size": 425,
        "content_type": "text/plain",
        "word_count": 87,
        "tags": ["pipeline", "requirements", "txt", "serverless"],
        "ocr_text_preview": "GCP Cloud Run service with trigger on storage upload events. Auto scale to zero enabled.",
        "process_timestamp": (datetime.datetime.now() - datetime.timedelta(hours=5)).isoformat()
    },
    {
        "filename": "contract_draft.docx",
        "bucket": "my-first-project-documents",
        "size": 45100,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "word_count": 680,
        "tags": ["legal", "contract", "draft"],
        "ocr_text_preview": "This Agreement is entered into by and between the parties hereto as of the effective date...",
        "process_timestamp": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    },
    {
        "filename": "receipt_costco.jpg",
        "bucket": "my-first-project-documents",
        "size": 1850000,
        "content_type": "image/jpeg",
        "word_count": 310,
        "tags": ["receipt", "expense", "costco"],
        "ocr_text_preview": "COSTCO WHOLESALE #421. Member 11192837. 06/12/2026. MILK $3.29. BREAD $2.49. TOTAL $5.78.",
        "process_timestamp": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat()
    }
]

def get_bigquery_data(selected_tag=None):
    """Retrieves document metadata from BigQuery, falling back to mock data on error/lack of auth."""
    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.environ.get("BQ_DATASET", "document_processing")
    table_id = os.environ.get("BQ_TABLE", "metadata")
    
    # If not authenticated or configured, immediately return mock data
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not project_id:
        print("GOOGLE_APPLICATION_CREDENTIALS or project variables not set. Running in MOCK Mode.")
        return filter_mock_data(selected_tag), True

    try:
        client = bigquery.Client()
        full_table_path = f"{client.project}.{dataset_id}.{table_id}"
        
        query = f"""
            SELECT 
                filename, 
                bucket, 
                size, 
                content_type, 
                word_count, 
                tags, 
                ocr_text_preview, 
                process_timestamp 
            FROM `{full_table_path}`
        """
        
        query_params = []
        if selected_tag:
            query += " WHERE EXISTS(SELECT 1 FROM UNNEST(tags) as t WHERE t = @tag)"
            query_params.append(bigquery.ScalarQueryParameter("tag", "STRING", selected_tag))
            
        query += " ORDER BY process_timestamp DESC LIMIT 100"
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        documents = []
        for row in results:
            documents.append({
                "filename": row.filename,
                "bucket": row.bucket,
                "size": row.size,
                "content_type": row.content_type,
                "word_count": row.word_count,
                "tags": list(row.tags) if row.tags else [],
                "ocr_text_preview": row.ocr_text_preview or "",
                "process_timestamp": row.process_timestamp.isoformat() if row.process_timestamp else ""
            })
        return documents, False
        
    except Exception as e:
        print(f"BigQuery Query failed: {e}. Falling back to simulated Mock Data.")
        return filter_mock_data(selected_tag), True

def get_unique_tags():
    """Fetches unique tags for filtering options."""
    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.environ.get("BQ_DATASET", "document_processing")
    table_id = os.environ.get("BQ_TABLE", "metadata")
    
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not project_id:
        # Get unique tags from mock data
        all_tags = set()
        for doc in MOCK_DOCUMENTS:
            all_tags.update(doc["tags"])
        return sorted(list(all_tags))
        
    try:
        client = bigquery.Client()
        full_table_path = f"{client.project}.{dataset_id}.{table_id}"
        query = f"SELECT DISTINCT tag FROM `{full_table_path}`, UNNEST(tags) as tag ORDER BY tag"
        query_job = client.query(query)
        results = query_job.result()
        return [row.tag for row in results if row.tag]
    except Exception:
        # Mock tags fallback
        all_tags = set()
        for doc in MOCK_DOCUMENTS:
            all_tags.update(doc["tags"])
        return sorted(list(all_tags))

def filter_mock_data(selected_tag):
    if not selected_tag:
        return MOCK_DOCUMENTS
    return [doc for doc in MOCK_DOCUMENTS if selected_tag in doc["tags"]]

@app.route("/")
def index():
    selected_tag = request.args.get("tag", "")
    documents, is_mock = get_bigquery_data(selected_tag)
    unique_tags = get_unique_tags()
    
    # Calculate stats
    total_docs = len(documents)
    avg_words = int(sum(doc["word_count"] for doc in documents) / total_docs) if total_docs > 0 else 0
    
    return render_template(
        "index.html", 
        documents=documents, 
        unique_tags=unique_tags, 
        selected_tag=selected_tag,
        is_mock=is_mock,
        total_docs=total_docs,
        avg_words=avg_words
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8085))
    app.run(host="0.0.0.0", port=port, debug=True)
