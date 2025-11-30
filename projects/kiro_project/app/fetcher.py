"""Content fetching module for Web Content Summarizer."""

import httpx


def fetch_content(url: str, timeout: float = 10.0) -> tuple[str | None, str | None]:
    """
    Fetches HTML content from a URL.
    
    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds (default: 10.0)
        
    Returns:
        A tuple of (html_content, error_message) where:
        - html_content: The HTML content as a string if successful, None if error
        - error_message: None if successful, error description if failed
    """
    # Set appropriate user-agent header to avoid blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # Create httpx client with timeout configuration
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            # Fetch content from URL
            response = client.get(url, headers=headers)
            
            # Check for HTTP error status codes
            if response.status_code >= 400:
                return None, f"The website returned an error (status code: {response.status_code})"
            
            # Return successful content
            return response.text, None
            
    except httpx.TimeoutException:
        return None, "Unable to reach the website. The request timed out. Please check the URL and try again."
    
    except httpx.ConnectError:
        return None, "Connection to the website was refused. The website may be down or blocking automated access."
    
    except httpx.TooManyRedirects:
        return None, "The website has too many redirects. Please check the URL."
    
    except httpx.HTTPStatusError as e:
        return None, f"The website returned an error (status code: {e.response.status_code})"
    
    except httpx.RemoteProtocolError as e:
        return None, "The website closed the connection unexpectedly. It may be blocking automated access."
    
    except httpx.UnsupportedProtocol:
        return None, "The URL protocol is not supported. Please use http:// or https://"
    
    except Exception as e:
        # Catch any other unexpected errors
        # Log the actual error for debugging but return user-friendly message
        error_str = str(e).lower()
        print(f"Unexpected error fetching content: {e}")
        
        # Provide more specific error messages based on common issues
        if "ssl" in error_str or "certificate" in error_str:
            return None, "SSL certificate error. The website's security certificate may be invalid."
        elif "dns" in error_str or "name resolution" in error_str:
            return None, "Website not found. Please check the URL and try again."
        elif "forbidden" in error_str or "403" in error_str:
            return None, "Access forbidden. The website is blocking automated access."
        elif "unauthorized" in error_str or "401" in error_str:
            return None, "Access unauthorized. The website requires authentication."
        else:
            return None, "Failed to fetch website content. Please try again."
