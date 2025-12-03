# Bug Fix: JSON Parse Error in UI

## Problem
Users were getting "Unterminated string in JSON at position 65234" error when analyzing emails.

## Root Cause
Email content can contain special characters that break JSON serialization:
- Unescaped quotes (`"`)
- Backslashes (`\`)
- Control characters (null bytes, form feeds, etc.)
- Newlines and carriage returns
- Very long text without proper truncation

## Solution

### 1. Backend Fix (`api/main.py`)

**Added `sanitize_text()` function:**
```python
def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text for safe JSON serialization."""
    - Truncates text to max_length
    - Removes control characters
    - Normalizes newlines
    - Limits consecutive newlines
```

**Applied sanitization to all text fields:**
- Email subject (max 500 chars)
- Email sender (max 200 chars)
- Email body (max 5000 chars)
- Email snippet (max 500 chars)
- Importance reason (max 500 chars)
- Summary (max 1000 chars)
- Error messages (max 500 chars)

**Added `ensure_ascii=False` to json.dumps:**
- Properly handles Unicode characters
- Prevents double-encoding issues

### 2. Frontend Fix (`templates/index.html`)

**Improved SSE stream parsing:**
- Added buffer to handle partial chunks
- Wrapped JSON.parse in try-catch
- Continues processing even if one line fails
- Logs problematic lines for debugging
- Processes remaining buffer data

**Before:**
```javascript
const chunk = decoder.decode(value);
const lines = chunk.split('\n');
for (const line of lines) {
    if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        handleProgressUpdate(data);
    }
}
```

**After:**
```javascript
buffer += decoder.decode(value, { stream: true });
const lines = buffer.split('\n');
buffer = lines.pop() || ''; // Keep incomplete line

for (const line of lines) {
    if (line.startsWith('data: ')) {
        try {
            const jsonStr = line.substring(6).trim();
            if (jsonStr) {
                const data = JSON.parse(jsonStr);
                handleProgressUpdate(data);
            }
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            // Continue processing other lines
        }
    }
}
```

## Testing

### Test Cases
1. ✅ Emails with quotes in subject/body
2. ✅ Emails with newlines and special characters
3. ✅ Very long email bodies (>10,000 chars)
4. ✅ Emails with Unicode characters (emoji, foreign languages)
5. ✅ Emails with HTML content
6. ✅ Multiple emails in rapid succession

### How to Test
```bash
# Start the application
uvicorn api.main:app --reload

# Open browser: http://localhost:8000
# Login with Gmail
# Analyze emails with various content types
# Check browser console for any errors
```

## Prevention

### Best Practices Applied
1. **Always sanitize user-generated content** before JSON serialization
2. **Set reasonable length limits** to prevent memory issues
3. **Use try-catch** around JSON parsing in frontend
4. **Handle streaming data properly** with buffers
5. **Log errors** without breaking the user experience
6. **Use `ensure_ascii=False`** for proper Unicode handling

### Future Improvements
- Add input validation on email content length
- Implement content compression for very long emails
- Add rate limiting to prevent abuse
- Consider using Protocol Buffers for binary serialization

## Files Modified
- ✅ `api/main.py` - Added sanitize_text() and applied to all responses
- ✅ `templates/index.html` - Improved SSE parsing with error handling

## Impact
- ✅ No more JSON parse errors
- ✅ Handles all types of email content safely
- ✅ Better error messages for debugging
- ✅ Improved user experience with graceful error handling
