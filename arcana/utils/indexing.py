import os
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from docx import Document
from pptx import Presentation
import chardet
from arcana.utils.fiber import FiberDBMS
import nltk

# Ensure NLTK data is available before importing NLTK functions
import arcana.utils.nltk_setup
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
import csv
import re
import ast
from openai.types.chat import ChatCompletionMessageParam

from arcana.utils.response import openai_api_call
from arcana.core.config import INDEX_FILE

try:
    import wordninja
except ImportError:  # pragma: no cover - optional dependency
    wordninja = None

# NLTK data is now downloaded once in Arcanalte.py at startup.

def extract_keywords(text, lang: str = 'en', minimum_nltk_keywords: int = 3) -> List[str]:
    """Generate keyword tags for *text*.

    NLTK is used first for fast, local keyword extraction. If NLTK fails to
    surface a sufficient number of keywords, an OpenAI-compatible model is
    called to generate higher quality tags. The model fallback is intentionally
    lightweight and keeps the existing Fiber DBMS workflow unchanged.
    """
    nltk_keywords = _extract_keywords_with_nltk(text, lang)
    if len(nltk_keywords) >= minimum_nltk_keywords:
        return nltk_keywords

    model_keywords = generate_keywords_with_model(text, lang)
    # Fall back to the NLTK output if the API could not provide anything better
    return model_keywords or nltk_keywords


def _extract_keywords_with_nltk(text: str, lang: str) -> List[str]:
    """Return keyword candidates using the existing NLTK pipeline."""
    stop_words = set(stopwords.words('english')) if lang == 'en' else set()
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
    if lang == 'en':
        return [w for w in words if w.lower() not in stop_words]
    return words


def generate_keywords_with_model(text: str, lang: str = 'en', max_keywords: int = 10) -> List[str]:
    """Use the hosted model API to derive concise keyword tags for a text."""
    if not text.strip():
        return []

    prompt = (
        "Extract up to {max_keywords} concise search keywords for the following "
        "text. Respond with a comma-separated list of lowercase keywords only. "
        "Avoid stop words and duplicates."
    ).format(max_keywords=max_keywords)

    user_content = f"Language: {lang}\nText: {text.strip()}"
    messages: Iterable[ChatCompletionMessageParam] = [
        {"role": "system", "content": "You create keyword tags for fast document search."},
        {"role": "user", "content": f"{prompt}\n\n{user_content}"},
    ]

    try:
        response_text = ''.join(openai_api_call(messages, "Idx")).strip()
    except Exception as exc:  # pragma: no cover - defensive programming
        print(f"Keyword generation API failed: {exc}")
        return []

    if not response_text:
        return []

    # Accept comma, newline, or semicolon separated keywords
    raw_keywords = re.split(r'[\n;,]', response_text)
    cleaned_keywords: List[str] = []
    seen = set()
    for keyword in raw_keywords:
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]+', '', keyword.strip().lower())
        if cleaned and cleaned not in seen:
            cleaned_keywords.append(cleaned)
            seen.add(cleaned)

    return cleaned_keywords[:max_keywords]

def detect_language(text):
    # Simple check: if contains CJK, treat as Chinese
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    return 'en'


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\s*\n(?=\w)", "", text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()

    def _split_long_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if wordninja is not None:
            split_tokens = wordninja.split(token)
            if len(split_tokens) > 1:
                return " ".join(split_tokens)
        return re.sub(r"(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)", " ", token)

    text = re.sub(r"[A-Za-z0-9]{30,}", _split_long_token, text)
    return text


def _split_for_indexing(text: str, max_chars: int = 500, max_words: int = 90) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= max_chars:
            chunks.append(sentence)
            continue
        words = sentence.split()
        if len(words) > 1:
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i:i + max_words]))
        else:
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i + max_chars])
    return chunks


def indexing(cache_dir: str):
    """
    Traverses a directory, processes all supported files, extracts content and
    keywords, and builds a search index using FiberDBMS.

    Args:
        cache_dir (str): The path to the directory containing files to be indexed.

    Returns:
        int: The total number of entries indexed.
    """
    cache_dir = os.path.abspath(cache_dir)

    dbms = FiberDBMS()
    # Load existing database if present to avoid duplicates
    existing_entries = set()
    if os.path.exists(INDEX_FILE):
        try:
            dbms.load_from_file(INDEX_FILE)
            existing_entries = set()
            for entry in dbms.database:
                name = entry.get('name', '')
                content = entry.get('content', '')
                existing_entries.add((name, content))
                # Allow duplicate detection against legacy records that stored only the basename.
                existing_entries.add((Path(name).name, content))
            print(f"Loaded existing index with {len(existing_entries)} entries. New indexing will skip duplicates.")
        except Exception as exc:
            print(f"Could not load existing index for duplicate checking: {exc}")

    entries = []

    # Traverse the cache directory for all supported file types
    for root, _, files in os.walk(cache_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            try:
                # Process different file types and extract content
                if file_extension == ".txt":
                    with open(file_path, 'rb') as f:
                        raw_data = f.read()
                        encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                elif file_extension == ".docx":
                    doc = Document(file_path)
                    content = "\n".join([para.text for para in doc.paragraphs])
                elif file_extension == ".pptx":
                    presentation = Presentation(file_path)
                    all_texts = []
                    for slide in presentation.slides:
                        slide_texts = []
                        if slide.shapes.title:
                            slide_texts.append(slide.shapes.title.text)
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                slide_texts.append(shape.text_frame.text)  # type: ignore
                        all_texts.append("\n".join(slide_texts))
                    content = "\n".join(all_texts)
                elif file_extension in [".xls", ".xlsx", ".csv"]:
                    df = pd.read_excel(file_path) if "xls" in file_extension else pd.read_csv(file_path)
                    content = df.to_csv(index=False)
                elif file_extension == ".pdf":
                    reader = PdfReader(file_path)
                    content = "\n\n".join([page.extract_text() or '' for page in reader.pages])
                else:
                    content = None  # Ignore unsupported formats

                # Add the file content to the database
                if content:  # Ensure content is not None
                    relative_path = os.path.relpath(file_path, cache_dir)
                    normalised_path = Path(relative_path).as_posix()
                    normalized_content = _normalize_text(content)
                    chunks = _split_for_indexing(normalized_content)
                    for i in chunks:
                        duplicate_keys = {
                            (normalised_path, i),
                            (Path(normalised_path).name, i),
                        }
                        if any(key in existing_entries for key in duplicate_keys):
                            continue
                        lang = detect_language(i)
                        keywords = extract_keywords(i, lang)
                        entries.append([normalised_path, i, ','.join(keywords)])
                        for key in duplicate_keys:
                            existing_entries.add(key)
                print(f"Processed {file}: {len(entries)} entries indexed.")
            except Exception as e:
                print(f"Failed to process {file}: {e}")
    print(f"Indexed {len(entries)} entries from {cache_dir}")

    # Add all new entries to dbms in one go
    for name, content, tags in entries:
        dbms.add_entry(name=name, content=content, tags=tags.split(','))

    # Save the database using the dbms's save method to the configured file
    dbms.save(INDEX_FILE)
    print(f"Database saved to {INDEX_FILE}")
    return len(entries)

def correct_malformed_row(row):
    # If row is a dict with a single key, try to split it
    if isinstance(row, dict) and len(row) == 1:
        key = list(row.keys())[0]
        fields = key.split('\t')
        if len(fields) == 4:
            name, timestamp, content, tags = fields
            if tags.startswith('[') and tags.endswith(']'):
                try:
                    tags_list = ast.literal_eval(tags)
                    tags = ','.join(str(t).strip() for t in tags_list)
                except Exception:
                    tags = tags
            return {
                'name': name,
                'timestamp': timestamp,
                'content': content,
                'tags': tags
            }
    return None
