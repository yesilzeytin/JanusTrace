import re

class RegexBuilder:
    """
    Constructs a regex pattern from a user-defined tag structure and tokens.
    """
    def __init__(self, config: dict):
        self.config = config

    def compile_pattern(self) -> str:
        """
        Compiles the tag structure into a python regex string with named groups.
        """
        # Check if direct regex rule is provided
        regex_rules = self.config.get('regex_rules', {})
        if 'id_pattern' in regex_rules:
            return regex_rules['id_pattern']

        tag_structure = self.config.get('tag_structure', '')
        tokens = self.config.get('tokens', {})
        
        # We need to escape special regex characters in the structure (like '.')
        # BUT we must preserve the {token} placeholders.
        # Strategy: Split by placeholders, escape the parts, then rejoin.
        
        # Find all placeholders like {token_name}
        # We use a regex to find them
        placeholder_re = re.compile(r'\{(\w+)\}')
        
        parts = []
        last_pos = 0
        
        for match in placeholder_re.finditer(tag_structure):
            # Text before the placeholder
            text_before = tag_structure[last_pos:match.start()]
            if text_before:
                parts.append(re.escape(text_before))
            
            token_name = match.group(1)
            if token_name in tokens:
                # Replace with named group
                parts.append(f"(?P<{token_name}>{tokens[token_name]})")
            else:
                # Token not defined? Treat as literal text (escaped)
                # Or keep as {token_name}?
                # User probably forgot to define it.
                # Let's escape it to be safe, so it matches literal "{token_name}"
                parts.append(re.escape(match.group(0)))
                
            last_pos = match.end()
            
        # Text after the last placeholder
        text_after = tag_structure[last_pos:]
        if text_after:
            parts.append(re.escape(text_after))
            
        return "".join(parts)
