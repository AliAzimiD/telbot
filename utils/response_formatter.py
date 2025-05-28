import re
import logging
from typing import List, NamedTuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FormattedResponse:
    """Formatted response container."""
    text: str
    parse_mode: str = "Markdown"

class ResponseFormatter:
    """Formats responses for Telegram."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.max_chunk_size = config_manager.max_message_length - 100  # Buffer for formatting
    
    def format_response(self, response_data: dict) -> FormattedResponse:
        """Format response based on type and content."""
        response_type = response_data.get('type', 'default')
        text = response_data.get('text', '')
        
        # Clean and format the text
        formatted_text = self._clean_response_text(text)
        
        # Add response-specific formatting
        if response_type == 'query_response':
            formatted_text = self._format_query_response(formatted_text)
        elif response_type == 'error_response':
            formatted_text = self._format_error_response(formatted_text)
        elif response_type == 'status_response':
            formatted_text = self._format_status_response(formatted_text)
        
        return FormattedResponse(
            text=formatted_text,
            parse_mode=response_data.get('parse_mode', 'Markdown')
        )
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and normalize response text."""
        if not text:
            return "No response available."
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Fix common markdown issues
        text = self._fix_markdown_formatting(text)
        
        # Ensure text ends properly
        text = text.strip()
        
        return text
    
    def _fix_markdown_formatting(self, text: str) -> str:
        """Fix common markdown formatting issues."""
        # Escape special characters that might break Telegram markdown
        # But preserve intended markdown formatting
        
        # Fix unmatched asterisks
        asterisk_count = text.count('*')
        if asterisk_count % 2 != 0:
            # Add closing asterisk if odd number
            text += '*'
        
        # Fix unmatched underscores
        underscore_count = text.count('_')
        if underscore_count % 2 != 0:
            text += '_'
        
        # Escape other problematic characters
        text = text.replace('[', '\\[').replace(']', '\\]')
        
        return text
    
    def _format_query_response(self, text: str) -> str:
        """Format query response with appropriate styling."""
        # Add query response indicator
        if not text.startswith('📊') and not text.startswith('🔍'):
            # Add emoji based on content type
            if any(word in text.lower() for word in ['count', 'total', 'number']):
                text = f"📊 **Analysis Result**\n\n{text}"
            else:
                text = f"🔍 **Data Insight**\n\n{text}"
        
        return text
    
    def _format_error_response(self, text: str) -> str:
        """Format error response with appropriate styling."""
        if not text.startswith('❌'):
            text = f"❌ **Error**\n\n{text}"
        
        return text
    
    def _format_status_response(self, text: str) -> str:
        """Format status response (already formatted in message router)."""
        return text
    
    def split_long_message(self, text: str) -> List[str]:
        """Split long messages into chunks."""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit
            if len(current_chunk) + len(paragraph) + 2 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If single paragraph is too long, split by sentences
                if len(paragraph) > self.max_chunk_size:
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 > self.max_chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = ""
                        
                        current_chunk += sentence + ". "
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure we have at least one chunk
        if not chunks:
            chunks = [text[:self.max_chunk_size]]
        
        return chunks
    
    def format_table(self, data: List[dict], max_rows: int = 10) -> str:
        """Format data as a markdown table."""
        if not data:
            return "No data available."
        
        # Limit rows for readability
        if len(data) > max_rows:
            data = data[:max_rows]
            truncated = True
        else:
            truncated = False
        
        # Get column names
        columns = list(data[^3_0].keys())
        
        # Create table header
        header = "| " + " | ".join(columns) + " |"
        separator = "|" + "|".join([" --- " for _ in columns]) + "|"
        
        # Create table rows
        rows = []
        for row in data:
            row_text = "| " + " | ".join([str(row.get(col, "")) for col in columns]) + " |"
            rows.append(row_text)
        
        table = "\n".join([header, separator] + rows)
        
        if truncated:
            table += f"\n\n*Showing first {max_rows} rows*"
        
        return f"``````"