import os
import time
import json
import requests
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Import project modules
from crawlers.firecrawl_client import crawl_web
from utils.logger import DocuScraperLogger
from config.document_classes import get_document_class, get_all_document_classes

# Initialize logger
logger = DocuScraperLogger("doc-agent")

class DocumentValidationError(Exception):
    """Exception raised when document validation fails"""
    pass

def run_agent(
    doc_class: str,
    limit: int = 10,
    deep_validation: bool = False,
    parallel_downloads: bool = True,
    max_workers: int = 5
) -> List[Dict[str, Any]]:
    """
    Run document search agent to find documents of a specific class
    
    Args:
        doc_class: Type of document to search for (e.g., "incorporation", "passport")
        limit: Maximum number of results to return
        deep_validation: Whether to perform deep validation on results
        parallel_downloads: Whether to download documents in parallel
        max_workers: Maximum number of parallel download workers
        
    Returns:
        List of document objects
    """
    start_time = time.time()
    logger.info(f"Starting document search for class: {doc_class}")
    
    # Get document class configuration
    doc_class_config = get_document_class(doc_class)
    if not doc_class_config:
        logger.error(f"Unknown document class: {doc_class}")
        return []
    
    # Get search queries for document class
    search_queries = doc_class_config.get("search_queries", [])
    if not search_queries:
        logger.warning(f"No search queries defined for document class: {doc_class}")
        # Generate a default query
        search_queries = [f"{doc_class} document sample filetype:pdf"]
    
    # Search for documents using each query
    all_results = []
    for query in search_queries[:2]:  # Limit to first 2 queries for efficiency
        logger.info(f"Searching with query: {query}")
        try:
            # Use FireCrawl to search for documents
            search_results = crawl_web(
                query=query, 
                limit=limit // 2,
                file_types=doc_class_config.get("file_types")
            )
            all_results.extend(search_results)
        except Exception as e:
            logger.error(f"Error searching with query '{query}': {str(e)}")
    
    # Add doc_class to all results
    for result in all_results:
        result["doc_class"] = doc_class
    
    # Filter out duplicate URLs
    unique_results = []
    processed_urls = set()
    for result in all_results:
        url = result.get("url", "")
        if url and url not in processed_urls:
            processed_urls.add(url)
            
            # Check if URL points to a document with supported file type
            file_types = doc_class_config.get("file_types", [".pdf", ".docx"])
            is_supported_file = any(url.lower().endswith(ext) for ext in file_types)
            
            if is_supported_file:
                unique_results.append(result)
    
    # Download documents (parallel or sequential)
    if parallel_downloads and len(unique_results) > 1:
        from utils.parallel_downloader import download_documents_parallel
        documents = download_documents_parallel(
            unique_results, 
            max_workers=max_workers
        )
    else:
        # Sequential download
        documents = []
        for result in unique_results:
            document = download_document(result)
            if document:
                documents.append(document)
    
    # Validate documents if requested
    if deep_validation:
        validated_documents = []
        for document in documents:
            try:
                is_valid = validate_document(
                    document, 
                    doc_class,
                    doc_class_config.get("keywords", [])
                )
                document["validated"] = is_valid
                
                if is_valid or len(validated_documents) < limit // 2:
                    validated_documents.append(document)
            except Exception as e:
                logger.error(f"Error validating document: {str(e)}")
                document["validated"] = False
                validated_documents.append(document)
        
        documents = validated_documents[:limit]
    else:
        # Mark all as validated if deep validation not requested
        for document in documents:
            document["validated"] = True
        documents = documents[:limit]
    
    # Log search completion
    duration_ms = int((time.time() - start_time) * 1000)
    logger.log_document_search(
        doc_class=doc_class,
        query=", ".join(search_queries[:2]),
        results_count=len(documents),
        duration_ms=duration_ms
    )
    
    return documents

def download_document(search_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Download document from URL and save to local storage
    
    Args:
        search_result: Search result containing document URL
        
    Returns:
        Document metadata if download successful, None otherwise
    """
    url = search_result.get("url", "")
    title = search_result.get("title", "Unknown Document")
    doc_class = search_result.get("doc_class", "unknown")
    
    if not url:
        logger.warning("Missing URL in search result")
        return None
    
    logger.info(f"Downloading document: {url}")
    
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
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Create document metadata
        document = {
            "doc_class": doc_class,
            "title": title,
            "url": url,
            "file_path": str(file_path),
            "file_type": file_ext,
            "file_size": os.path.getsize(file_path),
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
        logger.error(f"Error downloading document {url}: {error_msg}")
        
        # Log failed download
        logger.log_document_download(
            url=url,
            file_path="",
            success=False,
            error=error_msg
        )
        
        return None

# Add this import at the top
from utils.file_validator import validate_file_type, get_expected_mime_types

# Update the validate_document function
def validate_document(
    document: Dict[str, Any], 
    doc_class: str,
    keywords: List[str]
) -> bool:
    """
    Validate document based on metadata and file properties
    
    Args:
        document: Document metadata
        doc_class: Document class
        keywords: List of keywords (not used for validation without text extraction)
        
    Returns:
        True if document is valid, False otherwise
    """
    file_path = document.get("file_path")
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"Document file not found: {file_path}")
        return False
    
    # Check if file is empty
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        logger.warning(f"Empty document file: {file_path}")
        return False
    
    # Check if file size is reasonable (between 10KB and 10MB)
    if file_size < 10 * 1024 or file_size > 10 * 1024 * 1024:
        logger.warning(f"Suspicious file size ({file_size} bytes): {file_path}")
        # Don't reject based on size alone, just log a warning
    
    # Validate file type using python-magic
    file_ext = document.get("file_type", "")
    expected_mime_types = get_expected_mime_types(file_ext)
    
    is_valid_type, detected_type = validate_file_type(file_path, expected_mime_types)
    if not is_valid_type:
        logger.warning(f"Invalid file type for {file_path}. Detected: {detected_type}")
        return False
    
    # Log validation
    logger.log_document_validation(
        file_path=file_path,
        doc_class=doc_class,
        is_valid=True,
        confidence=0.8  # Increased confidence with file type validation
    )
    
    return True