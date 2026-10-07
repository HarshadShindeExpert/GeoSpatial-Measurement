import html
import re

class InputSanitizer:
    @staticmethod
    def sanitize_string(text: str) -> str:
        """
        Escapes HTML special characters and strips unsafe executable scripts to prevent XSS attacks.
        """
        if not text:
            return ""
        
        # Escape HTML tags (<, >, &, ", ')
        escaped = html.escape(str(text))
        
        # Remove any javascript: or data: URI schemes
        escaped = re.sub(r'javascript\s*:', '', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'data\s*:', '', escaped, flags=re.IGNORECASE)
        
        return escaped

    @classmethod
    def sanitize_dict(cls, data: dict) -> dict:
        """
        Recursively sanitizes dictionary keys and values for XSS protection.
        """
        sanitized = {}
        for k, v in data.items():
            clean_k = cls.sanitize_string(str(k))
            if isinstance(v, str):
                sanitized[clean_k] = cls.sanitize_string(v)
            elif isinstance(v, dict):
                sanitized[clean_k] = cls.sanitize_dict(v)
            elif isinstance(v, list):
                sanitized[clean_k] = [cls.sanitize_string(x) if isinstance(x, str) else x for x in v]
            else:
                sanitized[clean_k] = v
        return sanitized
