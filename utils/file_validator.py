import os
import logging
from typing import Optional, List, Tuple

# Configure logging
logger = logging.getLogger("file-validator")

def validate_file_type(file_path: str, expected_types: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate file type using python-magic
    
    Args:
        file_path: Path to the file
        expected_types: List of expected MIME types (optional)
        
    Returns:
        Tuple of (is_valid, detected_mime_type)
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False, "File not found"
    
    try:
        import magic
        mime = magic.Magic(mime=True)
        detected_type = mime.from_file(file_path)
        
        logger.info(f"Detected MIME type for {file_path}: {detected_type}")
        
        # If no expected types provided, just return the detected type
        if not expected_types:
            return True, detected_type
        
        # Check if detected type matches any expected type
        for expected_type in expected_types:
            if expected_type in detected_type:
                return True, detected_type
                
        logger.warning(f"File type mismatch for {file_path}. Expected: {expected_types}, Got: {detected_type}")
        return False, detected_type
        
    except ImportError:
        logger.warning("python-magic not installed. Using basic extension check.")
        # Fallback to basic extension check
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower()
        
        # Map extensions to MIME types
        ext_to_mime = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        
        detected_type = ext_to_mime.get(file_ext, 'application/octet-stream')
        
        if not expected_types:
            return True, detected_type
            
        for expected_type in expected_types:
            if expected_type in detected_type:
                return True, detected_type
                
        return False, detected_type
        
    except Exception as e:
        logger.error(f"Error validating file type: {str(e)}")
        return False, f"Error: {str(e)}"

def get_expected_mime_types(file_ext: str) -> List[str]:
    """Get expected MIME types for a file extension"""
    ext_to_mime = {
        '.pdf': ['application/pdf'],
        '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        '.doc': ['application/msword'],
        '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        '.xls': ['application/vnd.ms-excel'],
        '.txt': ['text/plain'],
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg'],
        '.png': ['image/png']
    }
    
    return ext_to_mime.get(file_ext.lower(), [])