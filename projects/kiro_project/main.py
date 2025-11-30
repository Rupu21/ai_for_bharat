from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.validators import validate_url
from app.fetcher import fetch_content
from app.extractor import extract_text
from app.summarizer import generate_summary, extract_highlights

app = FastAPI(title="Web Content Summarizer")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic Models
class SummarizeRequest(BaseModel):
    """Request model for summarization endpoint."""
    url: str


class SummarizeResponse(BaseModel):
    """Response model for successful summarization."""
    success: bool
    url: str
    summary: str | None = None
    highlights: list[str] | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    success: bool
    error: str


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest):
    """
    Summarize content from a provided URL.
    
    Args:
        request: SummarizeRequest containing the URL to process
        
    Returns:
        SummarizeResponse with summary and highlights, or error information
        
    Raises:
        HTTPException: For validation errors (400) or processing errors (500)
    """
    url = request.url
    
    # Step 1: Validate URL
    is_valid, error_message = validate_url(url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Step 2: Fetch content from URL
    html_content, fetch_error = fetch_content(url)
    if fetch_error:
        raise HTTPException(status_code=500, detail=fetch_error)
    
    # Step 3: Extract text from HTML
    text_content = extract_text(html_content)
    
    # Check if any content was extracted
    if not text_content or not text_content.strip():
        return SummarizeResponse(
            success=True,
            url=url,
            summary=None,
            highlights=None,
            error="No content could be extracted from the website"
        )
    
    # Step 4: Generate summary
    summary, summary_error = generate_summary(text_content)
    if summary_error:
        raise HTTPException(status_code=500, detail=summary_error)
    
    # Step 5: Extract highlights
    highlights, highlights_error = extract_highlights(text_content)
    if highlights_error:
        raise HTTPException(status_code=500, detail=highlights_error)
    
    # Return successful response
    return SummarizeResponse(
        success=True,
        url=url,
        summary=summary,
        highlights=highlights,
        error=None
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
