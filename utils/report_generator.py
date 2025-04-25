import os
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from utils.logger import DocuScraperLogger

# Initialize logger
logger = DocuScraperLogger("report-generator")

def generate_report(
    documents: List[Dict[str, Any]], 
    output_format: str = "excel", 
    output_path: Optional[str] = None
) -> str:
    """
    Generate a report of downloaded documents
    
    Args:
        documents: List of document metadata
        output_format: Format of the report ('excel' or 'text')
        output_path: Path to save the report (optional)
        
    Returns:
        Path to the generated report
    """
    if not documents:
        logger.warning("No documents to generate report")
        return ""
    
    # Create reports directory if it doesn't exist
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine output path
    if not output_path:
        if output_format.lower() == "excel":
            output_path = str(reports_dir / f"document_report_{timestamp}.xlsx")
        else:
            output_path = str(reports_dir / f"document_report_{timestamp}.txt")
    
    try:
        # Extract relevant fields for the report
        report_data = []
        for doc in documents:
            report_data.append({
                "Document Class": doc.get("doc_class", "Unknown"),
                "Title": doc.get("title", "Untitled"),
                "URL": doc.get("url", ""),
                "File Path": doc.get("file_path", ""),
                "File Type": doc.get("file_type", ""),
                "File Size (bytes)": doc.get("file_size", 0),
                "Downloaded": doc.get("download_successful", False),
                "Validated": doc.get("validated", False),
                "Timestamp": doc.get("timestamp", "")
            })
        
        # Generate report based on format
        if output_format.lower() == "excel":
            return generate_excel_report(report_data, output_path)
        else:
            return generate_text_report(report_data, output_path)
            
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return ""

def generate_excel_report(report_data: List[Dict[str, Any]], output_path: str) -> str:
    """Generate Excel report"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(report_data)
        
        # Write to Excel
        df.to_excel(output_path, index=False, sheet_name="Documents")
        
        logger.info(f"Excel report generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        return ""

def generate_text_report(report_data: List[Dict[str, Any]], output_path: str) -> str:
    """Generate text report"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("DOCUMENT REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, doc in enumerate(report_data, 1):
                f.write(f"Document #{i}\n")
                f.write("-" * 40 + "\n")
                for key, value in doc.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
        
        logger.info(f"Text report generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating text report: {str(e)}")
        return ""