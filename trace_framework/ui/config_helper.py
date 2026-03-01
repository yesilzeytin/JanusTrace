import re

class ConfigHelper:
    @staticmethod
    def generate_regex_from_id(example_id: str) -> str:
        """
        Generates a regex pattern based on an example Requirement ID.
        
        Args:
            example_id: A sample ID (e.g., 'REQ-001')
            
        Returns:
            A python regex string with a named group 'id'.
        """
        if not example_id:
            return ""

        # Remove prefix if present in the example
        pro_id = example_id
        
        # Strategy:
        # 1. Tokenize by separating digits and non-digits.
        # 2. Escape non-digits.
        # 3. Replace digits with \d+.
        
        parts = re.split(r'(\d+)', pro_id)
        regex_parts = []
        for part in parts:
            if part.isdigit():
                regex_parts.append(r'\d+')
            else:
                regex_parts.append(re.escape(part))
        
        core_regex = "".join(regex_parts)
        
        # Wrap the core part in the named group 'id'
        full_regex = f"(?P<id>{core_regex})"
            
        return full_regex

    @staticmethod
    def wrap_with_enclosement(regex: str, start: str, end: str) -> str:
        """
        Wraps the regex with start and end enclosement characters (escaped).
        """
        s = re.escape(start) if start else ""
        e = re.escape(end) if end else ""
        return f"{s}{regex}{e}"

class VisualBuilder:
    """
    Helper for building regex patterns from visual blocks.
    Component format: {'type': 'fixed|separator|var', 'value': '...', 'extra': '...'}
    """
    @staticmethod
    def compile_regex(components: list) -> str:
        pattern_parts = []
        for comp in components:
            ctype = comp.get('type')
            val = comp.get('value', '')
            
            if ctype == 'fixed':
                pattern_parts.append(re.escape(val))
            
            elif ctype == 'separator':
                pattern_parts.append(re.escape(val))
                
            elif ctype == 'var':
                # Val is type (Digits, Letters, Alphanumeric)
                # Extra is count (e.g. 3 or +)
                count_str = comp.get('extra', '+')
                quantifier = "+" if count_str == "+" else f"{{{count_str}}}"
                
                if val == 'Digits (D)':
                    pattern_parts.append(f"\\d{quantifier}")
                elif val == 'Letters (L)':
                    pattern_parts.append(f"[a-zA-Z]{quantifier}")
                elif val == 'Alphanumeric (A)':
                    pattern_parts.append(f"[a-zA-Z0-9]{quantifier}")
                else:
                    # Fallback
                    pattern_parts.append(r".+")
                    
        # Wrap everything in a named group 'id' ?
        # Usually checking the whole ID structure.
        core = "".join(pattern_parts)
        return f"(?P<id>{core})"

    @staticmethod
    def generate_description(components: list) -> str:
        if not components:
            return "No components defined."
            
        desc_parts = []
        for comp in components:
            ctype = comp.get('type')
            val = comp.get('value', '')
            
            if ctype == 'fixed':
                desc_parts.append(f"Fixed text '{val}'")
            elif ctype == 'separator':
                desc_parts.append(f"Separator '{val}'")
            elif ctype == 'var':
                count = comp.get('extra', '+')
                count_text = "any number of" if count == "+" else f"{count} fixed"
                
                type_map = {
                    'Digits (D)': 'digits',
                    'Letters (L)': 'letters',
                    'Alphanumeric (A)': 'alphanumeric characters'
                }
                t_text = type_map.get(val, 'characters')
                desc_parts.append(f"Variable ({count_text} {t_text})")
                
        return " followed by ".join(desc_parts) + "."

