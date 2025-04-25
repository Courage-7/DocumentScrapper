import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from utils.logger import DocuScraperLogger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests"""
    
    def __init__(self, app: ASGIApp):
        """Initialize middleware"""
        super().__init__(app)
        self.logger = DocuScraperLogger("api-requests")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log details"""
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log request
        self.logger.log_api_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip
        )
        
        return response