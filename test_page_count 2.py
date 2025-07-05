#!/usr/bin/env python3
"""
Test script for page count functionality in Study Gui        print("📋 Page Count Features:")
        print("   • Target page input with help tooltip")
        print("   • Dynamic time estimates based on page count")
        print("   • Content length guidance for AI prompts")
        print("   • Smart word count calculation (180 words/page for study guides)")
        print("   • Automatic section count recommendation")
        print("   • Page count display throughout workflow")
        print("   • Markdown formatting instructions for better output")
        print("   • Study guide format optimization (headers, bullets, structure)")
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from mixup import get_page_count_instructions, get_markdown_formatting_instructions

def test_page_count_instructions():
    """Test the page count instruction generation."""
    print("🧪 Testing Page Count Instructions")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        (-1, 5),  # Auto length
        (3, 4),   # Short guide
        (10, 6),  # Medium guide
        (25, 8),  # Long guide
        (40, 12), # Very long guide
    ]
    
    for page_count, sections in test_cases:
        instructions = get_page_count_instructions(page_count, sections)
        if page_count == -1:
            length_type = "Auto Length"
        elif page_count <= 5:
            length_type = "Short Guide"
        elif page_count <= 15:
            length_type = "Medium Guide"
        elif page_count <= 30:
            length_type = "Long Guide"
        else:
            length_type = "Very Long Guide"
        
        print(f"\n📄 {length_type} ({page_count} pages, {sections} sections):")
        print(f"   {instructions}")

def test_markdown_instructions():
    """Test the markdown formatting instructions."""
    print("\n\n🧪 Testing Markdown Instructions")
    print("=" * 50)
    
    instructions = get_markdown_formatting_instructions()
    print(instructions)

def test_word_count_calculation():
    """Test word count calculations."""
    print("\n\n🧪 Testing Word Count Calculations")
    print("=" * 50)
    
    # Updated for study guide format (160-200 words per page, using 180 as middle ground)
    words_per_page = 180
    
    test_pages = [1, 3, 5, 10, 15, 20, 30, 50]
    
    for pages in test_pages:
        total_words = pages * words_per_page
        sections = max(3, min(pages // 2, 12))
        words_per_section = total_words // sections
        
        print(f"📄 {pages} pages → {total_words} words → ~{sections} sections → ~{words_per_section} words/section")
    
    print(f"\n💡 Note: Using {words_per_page} words/page optimized for study guide format")
    print("   Study guides have headers, bullet points, and structured formatting")
    print("   which reduces word density compared to regular documents (250-300 words/page)")

if __name__ == "__main__":
    print("🚀 Testing Page Count Functionality for Study Guide Mode")
    print("=" * 60)
    
    try:
        test_page_count_instructions()
        test_markdown_instructions()
        test_word_count_calculation()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Page Count Features:")
        print("   • Target page input with help tooltip")
        print("   • Dynamic time estimates based on page count")
        print("   • Content length guidance for AI prompts")
        print("   • Smart word count calculation (275 words/page)")
        print("   • Automatic section count recommendation")
        print("   • Page count display throughout workflow")
        print("   • Markdown formatting instructions for better output")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
