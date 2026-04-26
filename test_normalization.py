import re

def normalize_spaced_text(text):
    """
    Detects if text is spaced out (e.g. 'P r o d u c t') and fixes it.
    """
    # Check a sample of the text
    sample = text[:200]
    # Count single characters followed by space
    single_char_spaces = len(re.findall(r'\b\w \b', sample))
    total_words = len(sample.split())
    
    if total_words > 0 and single_char_spaces / total_words > 0.7:
        # Likely spaced out. 
        # Fix: 'P r o d u c t' -> 'Product'
        # But 'Product  Manager' (double space) should be 'Product Manager'
        
        # Step 1: Replace double spaces with a placeholder
        text = text.replace('  ', '|||')
        # Step 2: Remove all remaining single spaces
        text = text.replace(' ', '')
        # Step 3: Replace placeholder with a single space
        text = text.replace('|||', ' ')
        
    return text

# Test
test_cases = [
    "P r o d u c t  M a n a g e r",
    "S e n i o r  S o f t w a r e  E n g i n e e r",
    "This is normal text."
]

for t in test_cases:
    print(f"Original: {t}")
    print(f"Fixed:    {normalize_spaced_text(t)}")
    print("-" * 20)
