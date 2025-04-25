from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import os
import sys
import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import shutil
import subprocess
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("docuscraper-api")

# Create directories
os.makedirs("logs", exist_ok=True)
os.makedirs("data/downloads", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="DocuScraper API",
    description="API for searching, downloading, and classifying document files from the web",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DocumentClass(BaseModel):
    id: str
    name: str
    category: str
    file_types: List[str]

class DocumentClassesResponse(BaseModel):
    company: List[DocumentClass]
    individual: List[DocumentClass]

class DocumentSearchRequest(BaseModel):
    doc_class: str = Field(..., description="Document class ID to search for")
    query: Optional[str] = Field(None, description="Additional search query to refine results")
    limit: int = Field(5, description="Maximum number of documents to download")
    file_types: Optional[List[str]] = Field(None, description="Specific file types to download")

class DocumentSearchResponse(BaseModel):
    job_id: str
    doc_class: str
    status: str
    start_time: str
    estimated_completion: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    doc_class: str
    start_time: str
    completed: Optional[bool] = None
    documents_found: Optional[int] = None
    documents_downloaded: Optional[int] = None
    error: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    doc_class: str
    title: str
    file_type: str
    file_size: int
    download_url: str
    timestamp: str

class ReportRequest(BaseModel):
    doc_class: Optional[str] = Field(None, description="Document class to filter by, or None for all")
    output_format: str = Field("excel", description="Report format: excel or pdf")

class ReportResponse(BaseModel):
    report_id: str
    doc_class: Optional[str]
    document_count: int
    download_url: str
    timestamp: str

# In-memory storage for scraping jobs
active_jobs = {}
completed_jobs = {}
downloaded_documents = {}

# Document class definitions - normally would be in a separate module
DOCUMENT_CLASSES = {
    "company": {
        "commercial_register": {
            "name": "Commercial Register",
            "category": "company",
            "file_types": [".pdf", ".doc", ".docx"]
        },
        "articles_of_association": {
            "name": "Articles of Association",
            "category": "company",
            "file_types": [".pdf", ".doc", ".docx"]
        },
        "incorporation": {
            "name": "Certificate of Incorporation",
            "category": "company",
            "file_types": [".pdf", ".doc", ".docx"]
        }
    },
    "individual": {
        "passport": {
            "name": "Passport",
            "category": "individual",
            "file_types": [".pdf", ".jpg", ".png"]
        },
        "id": {
            "name": "ID",
            "category": "individual",
            "file_types": [".pdf", ".jpg", ".png"]
        },
        "utility_bill": {
            "name": "Utility Bill",
            "category": "individual",
            "file_types": [".pdf", ".doc", ".docx"]
        }
    }
}

def get_document_classes_by_category(category):
    """Get document classes by category"""
    if category in DOCUMENT_CLASSES:
        return DOCUMENT_CLASSES[category]
    return {}

def get_all_document_classes():
    """Get all document classes"""
    all_classes = {}
    for category, classes in DOCUMENT_CLASSES.items():
        all_classes.update(classes)
    return all_classes

# Routes
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    logger.info("Root endpoint accessed")
    return {
        "name": "DocuScraper API",
        "version": "1.0.0",
        "description": "API for searching, downloading, and classifying document files from the web",
        "documentation": "/docs"
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(active_jobs),
        "completed_jobs": len(completed_jobs),
        "documents_count": len(downloaded_documents)
    }

@app.get("/document/classes", response_model=DocumentClassesResponse, tags=["Documents"])
async def get_document_classes():
    """Get all available document classes"""
    logger.info("Document classes endpoint accessed")
    
    # Get document classes by category
    company_classes = get_document_classes_by_category("company")
    individual_classes = get_document_classes_by_category("individual")
    
    # Format response
    response = {
        "company": [
            {
                "id": class_id,
                "name": class_info["name"],
                "category": class_info["category"],
                "file_types": class_info["file_types"]
            }
            for class_id, class_info in company_classes.items()
        ],
        "individual": [
            {
                "id": class_id,
                "name": class_info["name"],
                "category": class_info["category"],
                "file_types": class_info["file_types"]
            }
            for class_id, class_info in individual_classes.items()
        ]
    }
    
    return response

async def run_document_search(job_id, doc_class, limit, file_types=None, query=None):
    """Background task to run document search and download"""
    try:
        # Update job status
        active_jobs[job_id]["status"] = "searching"
        
        # Create output directory for this job
        output_dir = f"data/downloads/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare search command
        cmd = [
            "python", "document_scraper.py",
            "--output-dir", output_dir,
            "--max-downloads", str(limit),
            "--doc-class", doc_class
        ]
        
        if file_types:
            cmd.extend(["--file-types", ",".join(file_types)])
            
        if query:
            cmd.extend(["--query", query])
        
        # Run the document scraper as a subprocess
        logger.info(f"Starting document search job {job_id}: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        # Update job status based on result
        if process.returncode == 0:
            # Job completed successfully
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["completed"] = True
            
            # Scan output directory for downloaded files
            downloaded_files = []
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.lower().endswith(tuple([".pdf", ".doc", ".docx", ".jpg", ".png"])):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        _, file_ext = os.path.splitext(file)
                        
                        # Generate a unique ID for this document
                        doc_id = str(uuid.uuid4())
                        
                        # Create document metadata
                        document = {
                            "id": doc_id,
                            "doc_class": doc_class,
                            "title": file,
                            "file_path": file_path,
                            "file_type": file_ext.lower(),
                            "file_size": file_size,
                            "timestamp": datetime.now().isoformat(),
                            "download_url": f"/document/download/{doc_id}"
                        }
                        
                        downloaded_files.append(document)
                        downloaded_documents[doc_id] = document
            
            # Update job with document info
            active_jobs[job_id]["documents_found"] = len(downloaded_files)
            active_jobs[job_id]["documents_downloaded"] = len(downloaded_files)
            
            # Move job to completed jobs
            completed_jobs[job_id] = active_jobs[job_id]
            del active_jobs[job_id]
            
            logger.info(f"Job {job_id} completed. Downloaded {len(downloaded_files)} documents.")
        else:
            # Job failed
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["completed"] = True
            active_jobs[job_id]["error"] = stderr
            
            # Move job to completed jobs
            completed_jobs[job_id] = active_jobs[job_id]
            del active_jobs[job_id]
            
            logger.error(f"Job {job_id} failed: {stderr}")
    except Exception as e:
        logger.error(f"Error in document search job {job_id}: {str(e)}")
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["completed"] = True
        active_jobs[job_id]["error"] = str(e)
        
        # Move job to completed jobs
        completed_jobs[job_id] = active_jobs[job_id]
        if job_id in active_jobs:
            del active_jobs[job_id]

@app.post("/search", response_model=DocumentSearchResponse, tags=["Documents"])
async def search_documents(request: DocumentSearchRequest, background_tasks: BackgroundTasks):
    """Search for and download document files from the web"""
    logger.info(f"Starting document search for class: {request.doc_class}")
    
    # Validate document class
    all_classes = get_all_document_classes()
    if request.doc_class not in all_classes:
        raise HTTPException(status_code=400, detail=f"Invalid document class: {request.doc_class}")
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job data
    job_data = {
        "job_id": job_id,
        "doc_class": request.doc_class,
        "status": "queued",
        "start_time": datetime.now().isoformat(),
        "estimated_completion": (datetime.now().timestamp() + 300),  # Estimate 5 minutes
        "completed": False
    }
    
    # Store job data
    active_jobs[job_id] = job_data
    
    # Start the search process in the background
    background_tasks.add_task(
        run_document_search,
        job_id=job_id,
        doc_class=request.doc_class,
        limit=request.limit,
        file_types=request.file_types,
        query=request.query
    )
    
    return job_data

@app.get("/search/{job_id}", response_model=JobStatusResponse, tags=["Documents"])
async def get_job_status(job_id: str):
    """Get the status of a document search job"""
    # Check active jobs first
    if job_id in active_jobs:
        return active_jobs[job_id]
    
    # Then check completed jobs
    if job_id in completed_jobs:
        return completed_jobs[job_id]
    
    # Job not found
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@app.get("/documents", response_model=List[DocumentResponse], tags=["Documents"])
async def list_documents(
    doc_class: Optional[str] = Query(None, description="Filter by document class"),
    limit: int = Query(50, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip")
):
    """List downloaded documents"""
    # Filter documents by class if specified
    filtered_docs = list(downloaded_documents.values())
    if doc_class:
        filtered_docs = [doc for doc in filtered_docs if doc["doc_class"] == doc_class]
    
    # Apply pagination
    paginated_docs = filtered_docs[offset:offset+limit]
    
    # Format response
    response = []
    for doc in paginated_docs:
        response.append({
            "id": doc["id"],
            "doc_class": doc["doc_class"],
            "title": doc["title"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "download_url": f"/document/download/{doc['id']}",
            "timestamp": doc["timestamp"]
        })
    
    return response

@app.get("/document/download/{doc_id}", tags=["Documents"])
async def download_document(doc_id: str):
    """Download a specific document"""
    if doc_id not in downloaded_documents:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    document = downloaded_documents[doc_id]
    return FileResponse(
        path=document["file_path"],
        filename=document["title"],
        media_type="application/octet-stream"
    )

@app.post("/report", response_model=ReportResponse, tags=["Reports"])
async def generate_document_report(request: ReportRequest):
    """Generate a report of downloaded documents"""
    logger.info(f"Generating {request.output_format} report for doc_class: {request.doc_class}")
    
    try:
        # Filter documents by class if specified
        if request.doc_class:
            filtered_docs = [doc for doc in downloaded_documents.values() 
                           if doc["doc_class"] == request.doc_class]
        else:
            filtered_docs = list(downloaded_documents.values())
        
        if not filtered_docs:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Generate report ID
        report_id = str(uuid.uuid4())
        report_file = f"report_{report_id}.{request.output_format}"
        report_path = os.path.join("data/reports", report_file)
        
        # Generate the report (simplified example - real implementation would create proper Excel/PDF)
        with open(report_path, 'w') as f:
            json.dump(filtered_docs, f, indent=2)
        
        return {
            "report_id": report_id,
            "doc_class": request.doc_class,
            "document_count": len(filtered_docs),
            "download_url": f"/report/download/{report_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/report/download/{report_id}", tags=["Reports"])
async def download_report(report_id: str):
    """Download a generated report"""
    # Search for report file
    for ext in ["excel", "pdf", "json"]:
        report_path = os.path.join("data/reports", f"report_{report_id}.{ext}")
        if os.path.exists(report_path):
            return FileResponse(
                path=report_path,
                filename=f"document_report.{ext}",
                media_type="application/octet-stream"
            )
    
    raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

# Delete a document
@app.delete("/document/{doc_id}", tags=["Documents"])
async def delete_document(doc_id: str):
    """Delete a specific document"""
    if doc_id not in downloaded_documents:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    document = downloaded_documents[doc_id]
    
    try:
        # Delete the file
        if os.path.exists(document["file_path"]):
            os.remove(document["file_path"])
        
        # Remove from document list
        del downloaded_documents[doc_id]
        
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)