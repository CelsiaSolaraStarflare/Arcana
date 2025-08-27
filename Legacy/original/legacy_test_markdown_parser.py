#!/usr/bin/env python3
"""
Test script for the markdown parser functionality in mixup.py
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from docx import Document
from mixup import parse_markdown_content_to_word, parse_markdown_to_word_runs

def test_markdown_parser():
    """Test the markdown parser with sample content."""
    
    # Create a new document
    doc = Document()
    
    # Test markdown content
    test_content = """
# Main Header

This is a paragraph with **bold text**, *italic text*, and `code text`.

## Section Header

Here's a list:
- First item with **bold**
- Second item with *italic*
- Third item with `code`

### Subsection

1. Numbered list item one
2. Item with [a link](https://example.com)
3. Final numbered item

> This is a blockquote with important information.

Here's some `inline code` and more **bold** text.

---

## Code Block Example

```python
def hello_world():
    print("Hello, World!")
```

That was a code block.
"""
    
    # Parse the markdown content
    print("🧪 Testing markdown parser...")
    parse_markdown_content_to_word(doc, test_content)
    
    # Save test document
    test_file = "test_markdown_output.docx"
    doc.save(test_file)
    print(f"✅ Test document saved as: {test_file}")
    
    # Test individual run parsing
    print("🧪 Testing markdown run parser...")
    test_para = doc.add_paragraph()
    test_text = "This has **bold**, *italic*, `code`, and [link](https://example.com) formatting."
    parse_markdown_to_word_runs(test_para, test_text)
    
    doc.save(test_file)
    print(f"✅ Updated test document with run parsing test")
    
    return test_file

if __name__ == "__main__":
    try:
        test_file = test_markdown_parser()
        print(f"\n🎉 Markdown parser test completed successfully!")
        print(f"📄 Check the generated file: {test_file}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
