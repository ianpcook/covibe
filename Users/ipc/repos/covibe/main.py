"""Main entry point for running the Covibe API server."""

import uvicorn
from src.covibe.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.covibe.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )