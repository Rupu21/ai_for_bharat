"""Text extraction module for Web Content Summarizer."""

from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    """
    Extracts clean text from HTML content.
    
    Parses HTML using BeautifulSoup, removes script, style, and navigation elements,
    and extracts meaningful text content from the body.
    
    Args:
        html: The HTML content as a string
        
    Returns:
        Extracted text string with HTML tags removed and cleaned
    """
    # Handle empty or None input
    if not html:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script tags and their content
    for script in soup.find_all('script'):
        script.decompose()
    
    # Remove style tags and their content
    for style in soup.find_all('style'):
        style.decompose()
    
    # Remove navigation elements
    for nav in soup.find_all('nav'):
        nav.decompose()
    
    # Remove header elements (often contain navigation)
    for header in soup.find_all('header'):
        header.decompose()
    
    # Remove footer elements
    for footer in soup.find_all('footer'):
        footer.decompose()
    
    # Remove aside elements (sidebars)
    for aside in soup.find_all('aside'):
        aside.decompose()
    
    # Extract text from the body if it exists, otherwise from the whole document
    body = soup.find('body')
    if body:
        text = body.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    
    # Clean up the text: remove extra whitespace
    # Split by whitespace and rejoin to normalize spacing
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Strip whitespace from each line
        cleaned_line = ' '.join(line.split())
        if cleaned_line:  # Only add non-empty lines
            cleaned_lines.append(cleaned_line)
    
    # Join lines with single space
    cleaned_text = ' '.join(cleaned_lines)
    
    return cleaned_text
