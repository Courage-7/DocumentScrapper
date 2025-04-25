import os
import time
import hashlib
import requests
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.logger import DocuScraperLogger
from utils.file_validator import validate_file_type

# Initialize logger
logger = DocuScraperLogger("parallel-downloader")

def download_documents_parallel(
    search_results: List[Dict[str, Any]], 
    max_workers: int = 5,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Download multiple documents in parallel
    
    Args:
        search_results: List of search results containing document URLs
        max_workers: Maximum number of parallel downloads
        timeout: Download timeout in seconds
        
    Returns:
        List of document metadata for successfully downloaded documents
    """
    if not search_results:
        return []
    
    logger.info(f"Starting parallel download of {len(search_results)} documents with {max_workers} workers")
    start_time = time.time()
    
    # Create a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit download tasks
        future_to_result = {
            executor.submit(download_single_document, result, timeout): result 
            for result in search_results
        }
        
        # Collect results as they complete
        documents = []
        for future in concurrent.futures.as_completed(future_to_result):
            result = future_to_result[future]
            try:
                document = future.result()
                if document:
                    documents.append(document)
            except Exception as e:
                url = result.get("url", "unknown")
                logger.error(f"Error downloading document {url}: {str(e)}")
    
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Parallel download completed in {duration_ms}ms. Downloaded {len(documents)}/{len(search_results)} documents")
    
    return documents

def download_single_document(
    search_result: Dict[str, Any],
    timeout: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Download a single document from URL and save to local storage
    
    Args:
        search_result: Search result containing document URL
        timeout: Download timeout in seconds
        
    Returns:
        Document metadata if download successful, None otherwise
    """
    url = search_result.get("url", "")
    title = search_result.get("title", "Unknown Document")
    doc_class = search_result.get("doc_class", "unknown")
    
    if not url:
        return None
    
    try:
        # Create file path from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        file_ext = os.path.splitext(url)[1].lower()
        if not file_ext:
            file_ext = ".pdf"  # Default to PDF if no extension
            
        # Create directory structure
        doc_dir = Path(f"data/raw_docs/{doc_class}")
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = doc_dir / f"{url_hash}{file_ext}"
        
        # Download the file
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Validate file type
        is_valid_type, detected_type = validate_file_type(str(file_path))
        
        # Create document metadata
        document = {
            "doc_class": doc_class,
            "title": title,
            "url": url,
            "file_path": str(file_path),
            "file_type": file_ext,
            "file_size": os.path.getsize(file_path),
            "mime_type": detected_type,
            "timestamp": datetime.now().isoformat(),
            "download_successful": True,
            "validated": False
        }
        
        # Log successful download
        logger.log_document_download(
            url=url,
            file_path=str(file_path),
            success=True
        )
        
        return document
    
    except Exception as e:
        error_msg = str(e)
        logger.log_document_download(
            url=url,
            file_path="",
            success=False,
            error=error_msg
        )
        return None