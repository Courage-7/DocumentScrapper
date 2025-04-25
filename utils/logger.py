import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class DocuScraperLogger:
    """
    Custom logger for DocuScraper application
    
    Features:
    - Console logging
    - File logging with rotation
    - JSON structured logging for machine parsing
    - Different log levels for different components
    """
    
    def __init__(
        self, 
        name: str, 
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        json_logging: bool = True
    ):
        """Initialize logger"""
        self.name = name
        self.log_dir = log_dir
        self.json_logging = json_logging
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Remove existing handlers if any
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # Create file handler
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        
        if json_logging:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message"""
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        self.logger.critical(message, extra=extra)
    
    def log_document_search(
        self, 
        doc_class: str, 
        query: str, 
        results_count: int,
        duration_ms: int
    ):
        """Log document search operation"""
        extra = {
            "operation": "document_search",
            "doc_class": doc_class,
            "query": query,
            "results_count": results_count,
            "duration_ms": duration_ms
        }
        self.info(f"Document search: {doc_class} - {results_count} results", extra=extra)
    
    def log_document_download(
        self, 
        url: str, 
        file_path: str, 
        success: bool, 
        error: Optional[str] = None
    ):
        """Log document download operation"""
        extra = {
            "operation": "document_download",
            "url": url,
            "file_path": file_path,
            "success": success
        }
        if error:
            extra["error"] = error
            self.error(f"Document download failed: {url}", extra=extra)
        else:
            self.info(f"Document downloaded: {file_path}", extra=extra)
    
    def log_document_validation(
        self, 
        file_path: str, 
        doc_class: str, 
        is_valid: bool,
        confidence: Optional[float] = None
    ):
        """Log document validation operation"""
        extra = {
            "operation": "document_validation",
            "file_path": file_path,
            "doc_class": doc_class,
            "is_valid": is_valid
        }
        if confidence is not None:
            extra["confidence"] = confidence
            
        if is_valid:
            self.info(f"Document validated: {file_path}", extra=extra)
        else:
            self.warning(f"Document invalid: {file_path}", extra=extra)
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: int,
        client_ip: Optional[str] = None
    ):
        """Log API request"""
        extra = {
            "operation": "api_request",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms
        }
        if client_ip:
            extra["client_ip"] = client_ip
            
        self.info(f"API {method} {endpoint}: {status_code}", extra=extra)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage()
        }
        
        # Add extra fields if available
        if hasattr(record, "operation"):
            log_data["operation"] = record.operation
            
        # Add all extra fields
        for key, value in record.__dict__.items():
            if key not in ["args", "exc_info", "exc_text", "msg", "message", 
                          "levelname", "levelno", "pathname", "filename", 
                          "module", "name", "lineno", "funcName", "created", 
                          "asctime", "msecs", "relativeCreated", "thread", 
                          "threadName", "processName", "process"]:
                log_data[key] = value
                
        return json.dumps(log_data)


# Example usage
if __name__ == "__main__":
    # Create logger
    logger = DocuScraperLogger("docuscraper-test")
    
    # Log some messages
    logger.info("Application started")
    logger.warning("This is a warning", {"source": "test"})
    logger.error("This is an error", {"error_code": 500})
    
    # Log document operations
    logger.log_document_search("invoice", "invoice template", 5, 1200)
    logger.log_document_download(
        "https://example.com/invoice.pdf", 
        "data/raw_docs/invoice/doc1.pdf",
        True
    )
    logger.log_document_validation(
        "data/raw_docs/invoice/doc1.pdf",
        "invoice",
        True,
        0.95
    )