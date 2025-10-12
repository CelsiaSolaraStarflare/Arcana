import streamlit as st
import openai
from arcana.utils.response import openai_api_call

# Ensure NLTK data is available before importing NLTK functions
import arcana.utils.nltk_setup
from arcana.utils.fiber import FiberDBMS
from arcana.core.config import INDEX_FILE, CACHE_DIR
import os
import json
import datetime
import re
from typing import Iterable, List, Tuple
from docx import Document
from pptx import Presentation
import chardet
from PyPDF2 import PdfReader
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from html import unescape
from arcana.utils.indexing import extract_keywords, detect_language
from arcana.utils.document_agent import AgentSummaryResult, get_document_agent


BASE_SYSTEM_PROMPT = (
    "You are a helpful AI assistant named Arcana. You will be provided with search results "
    "from a user's documents and, when enabled, web supplements. Prioritize the provided "
    "document snippets for answers and cite the source document's name for information "
    "taken from them, like this: `(Source: document_name.pdf)`. If the provided text does "
    "not contain the answer but the question involves widely known general knowledge, "
    "answer accurately using your own knowledge. When web supplement results are provided, "
    "you may incorporate them and cite the corresponding URLs. Always conclude your reply "
    "with a line that begins with `Sources:` followed by a comma-separated list of the "
    "sources you used. If you had to rely solely on general knowledge and no citations are "
    "available, end with `Sources: No sources cited.` Be friendly, cute, and helpful."
)


def _unique_preserve_order(items: Iterable[str]) -> List[str]:
    """Return a list of unique items while preserving their original order."""

    seen = set()
    unique_items: List[str] = []
    for item in items:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)
    return unique_items


def _parse_keyword_response(response_text: str) -> List[str]:
    """Parse the raw keyword response text returned by the language model."""

    if not response_text:
        return []

    cleaned = response_text.replace("Keywords:", "")
    # Split on commas, semicolons, or newlines and remove numbering/bullets
    raw_candidates = re.split(r"[\n,;]", cleaned)
    parsed: List[str] = []
    for candidate in raw_candidates:
        candidate = re.sub(r"^[\s\-•*\d\.]+", "", candidate).strip()
        if candidate:
            parsed.append(candidate)
    return _unique_preserve_order(parsed)


def _clean_html_snippet(snippet: str) -> str:
    """Convert a raw HTML snippet from Bing into a readable plain-text summary."""

    if not snippet:
        return ""

    text = unescape(snippet)
    # Remove simple HTML tags that occasionally show up in RSS descriptions
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


_NEWS_SENSITIVE_KEYWORDS = {
    "breaking",
    "headline",
    "news",
    "latest",
    "update",
    "updates",
    "today",
    "yesterday",
    "report",
    "reports",
    "reported",
    "reporting",
    "controversy",
    "conflict",
    "war",
    "ceasefire",
    "election",
    "elections",
    "politic",
    "policy",
    "government",
    "diplomatic",
    "sanction",
    "protest",
    "scandal",
    "shooting",
    "crisis",
    "emergency",
    "pandemic",
    "outbreak",
    "virus",
    "earthquake",
    "flood",
    "wildfire",
    "court ruling",
    "verdict",
    "indictment",
    "charged",
    "arrest",
    "sports score",
    "tournament",
    "transfer window",
}


def _looks_like_news_or_sensitive_query(query: str) -> bool:
    """Heuristically detect if a query is about current events or boundary-sensitive topics."""

    if not query:
        return False

    normalized = re.sub(r"\s+", " ", query).strip().lower()
    if not normalized:
        return False

    for keyword in _NEWS_SENSITIVE_KEYWORDS:
        if keyword in normalized:
            return True

    month_names = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]
    if any(month in normalized for month in month_names) and re.search(r"\b20[2-9][0-9]\b", normalized):
        return True

    # Terms like "this week" or explicit recency requests imply current events
    recency_patterns = [r"\bthis week\b", r"\bthis month\b", r"\blast week\b", r"\blast month\b", r"\brecent\b"]
    if any(re.search(pattern, normalized) for pattern in recency_patterns):
        return True

    return False


def search_bing(query: str, max_results: int = 3) -> List[dict]:
    """Fetch supplemental search results from Bing's RSS feed for the query."""

    if not query:
        return []

    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "format": "rss"},
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        return []

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        return []

    items: List[dict] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = _clean_html_snippet(item.findtext("description") or "")
        if title and link:
            items.append({"title": title, "link": link, "snippet": description})
        if len(items) >= max_results:
            break

    return items


def _build_sources_default_line(doc_results: Iterable[dict], web_results: Iterable[dict]) -> str:
    """Build a fallback `Sources:` line based on available document and web snippets."""

    def _format_web_source(result: dict) -> str:
        link = (result.get("link") or "").strip()
        if not link:
            return ""

        title = (result.get("title") or "").strip()
        if title:
            safe_title = re.sub(r"\s+", " ", title).strip()
            safe_title = safe_title.replace("[", "(").replace("]", ")")
            return f"[{safe_title}]({link})"

        return link

    doc_names: List[str] = []
    for result in doc_results:
        raw_name = result.get("name")
        if not raw_name:
            continue
        name = str(raw_name).strip()
        if not name:
            continue
        doc_names.append(f"{name} (Local)")
    web_sources: List[str] = []
    for result in web_results:
        formatted = _format_web_source(result)
        if formatted:
            web_sources.append(f"{formatted} (Web)")

    ordered_sources = _unique_preserve_order([*doc_names, *web_sources])
    if not ordered_sources:
        return "Sources: No sources cited."

    return "Sources: " + ", ".join(ordered_sources)


def _ensure_sources_line(response_text: str, default_line: str) -> str:
    """Guarantee the assistant response ends with a `Sources:` line."""

    if not response_text:
        return default_line

    trimmed_response = response_text.rstrip("\n")
    lines = trimmed_response.splitlines()

    # Find the last non-empty line to check whether it already contains sources
    last_nonempty_line = ""
    for line in reversed(lines):
        if line.strip():
            last_nonempty_line = line.strip()
            break

    if last_nonempty_line.lower().startswith("sources:"):
        return trimmed_response + ("\n" if response_text.endswith("\n") else "")

    lower_sources_line = default_line.strip().lower()
    if lower_sources_line.startswith("sources:"):
        appended_line = default_line
    else:
        appended_line = "Sources: No sources cited."

    suffix = "\n" if not response_text.endswith("\n") else ""
    return response_text + suffix + appended_line


def generate_keywords_with_gpt(query: str, language: str, max_keywords: int = 15) -> Tuple[List[str], str]:
    """Generate a list of search keywords using the language model."""

    if not query:
        return [], ""

    prompt = [
        {
            "role": "system",
            "content": (
                "You craft focused keyword lists for searching a document database. "
                "Return a concise list (comma separated) of topical keywords and phrases that "
                "will help retrieve passages relevant to the user's request. "
                "Prioritize terms that are likely to appear in the source documents and stay on topic. "
                "Do not add explanations."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate search keywords for the following query. "
                f"Primary language hint: {language}. "
                f"Query: {query}"
            ),
        },
    ]

    try:
        stream = openai_api_call(prompt, "Normal")
        chunks: List[str] = []
        for piece in stream:
            chunks.append(piece)
        response_text = "".join(chunks).strip()
        keywords = _parse_keyword_response(response_text)
        if not keywords:
            return [], response_text
        return keywords[:max_keywords], response_text
    except Exception:
        return [], ""


def query_dbms_with_keywords(dbms: FiberDBMS, keywords: List[str], max_results: int = 5) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """Query the DBMS with combinations of the provided keywords."""

    if not keywords:
        return [], []

    aggregated_results: List[dict] = []
    search_attempts: List[Tuple[str, int]] = []
    seen_entries = set()

    def add_results(query_text: str, new_results: List[dict]):
        if new_results is None:
            count = 0
        else:
            count = 0
            for result in new_results:
                identifier = (result.get("name"), result.get("content"))
                if identifier in seen_entries:
                    continue
                seen_entries.add(identifier)
                aggregated_results.append(result)
                count += 1
                if len(aggregated_results) >= max_results:
                    break
        search_attempts.append((query_text, count))
        return len(aggregated_results) >= max_results

    # First, try a combined query using the most important keywords.
    combined_query = " ".join(keywords[: min(5, len(keywords))])
    if combined_query:
        add_results(combined_query, dbms.query(combined_query, top_n=max_results))

    if len(aggregated_results) < max_results:
        for keyword in keywords:
            if add_results(keyword, dbms.query(keyword, top_n=max_results)):
                break

    return aggregated_results[:max_results], search_attempts

# NLTK data is now handled centrally in Arcanalte.py

# Chat History Management Functions

def get_chat_histories_dir():
    """Get the directory where chat histories are stored."""
    chat_dir = os.path.join(os.path.dirname(__file__), "chat_histories")
    os.makedirs(chat_dir, exist_ok=True)
    return chat_dir

def save_chat_history(session_name=None):
    """Save the current chat session to a file."""
    if "messages" not in st.session_state or not st.session_state.messages:
        st.warning("No messages to save!")
        return None
    
    if session_name is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"chat_{timestamp}"
    
    # Filter out system messages for cleaner history
    user_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]

    # Generate a short tagline based on the conversation
    tagline = generate_chat_tagline(user_messages)

    chat_data = {
        "session_name": session_name,
        "tagline": tagline,
        "timestamp": datetime.datetime.now().isoformat(),
        "messages": user_messages,
        "processed_file_name": st.session_state.get('processed_file_name', None)
    }
    
    chat_dir = get_chat_histories_dir()
    file_path = os.path.join(chat_dir, f"{session_name}.json")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        return file_path
    except Exception as e:
        st.error(f"Failed to save chat history: {e}")
        return None

def load_chat_history(file_path):
    """Load a chat session from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        # Clear current messages completely and load from history
        st.session_state.messages = []
        
        # Add the initial system message first
        st.session_state.messages.append({
            "role": "system",
            "content": BASE_SYSTEM_PROMPT,
        })
        
        # Add the welcome message only if there are no user messages in history
        user_messages_in_history = [msg for msg in chat_data.get("messages", []) if msg["role"] == "user"]
        if not user_messages_in_history:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Hey, I'm Arcana, your Indexademics AI assistant. Ask me anything about your indexed files!"
            })
        
        # Load the chat history messages
        if chat_data.get("messages"):
            st.session_state.messages.extend(chat_data["messages"])
        
        # Restore processed file context if it exists
        st.session_state.processed_file_name = chat_data.get('processed_file_name', None)
        
        # Set the current session name to the loaded chat's name for continuous saving
        st.session_state.current_session_name = chat_data.get('session_name', None)
        
        return True
    except Exception as e:
        st.error(f"Failed to load chat history: {e}")
        return False

def get_available_chat_histories():
    """Get a list of available chat history files."""
    chat_dir = get_chat_histories_dir()
    histories = []
    
    for filename in os.listdir(chat_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(chat_dir, filename)
            try:
                # Get file modification time for better sorting
                file_mtime = os.path.getmtime(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                histories.append({
                    'filename': filename,
                    'filepath': file_path,
                    'session_name': chat_data.get('session_name', filename[:-5]),
                    'tagline': chat_data.get('tagline', ''),
                    'timestamp': chat_data.get('timestamp', 'Unknown'),
                    'message_count': len(chat_data.get('messages', [])),
                    'modified_time': file_mtime
                })
            except:
                continue
    
    # Sort by file modification time (most recently modified first)
    histories.sort(key=lambda x: x['modified_time'], reverse=True)
    return histories

def generate_chat_tagline(messages):
    """Generate a short tagline from the conversation."""
    try:
        content = " ".join(msg["content"] for msg in messages if msg["role"] == "user")
        if not content:
            return ""
        lang = detect_language(content)
        keywords = extract_keywords(content, lang)
        return " ".join(keywords[:3])
    except Exception:
        return ""

def auto_generate_chat_title(messages):
    """Generate a meaningful title for the chat based on the conversation content."""
    try:
        # Extract user messages for title generation
        user_messages = [msg['content'] for msg in messages if msg['role'] == 'user']
        
        if not user_messages:
            return f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Use first few user messages to generate title
        conversation_sample = " ".join(user_messages[:3])  # First 3 user messages
        
        # Limit the sample to avoid token limits
        if len(conversation_sample) > 500:
            conversation_sample = conversation_sample[:500] + "..."
        
        title_prompt = [
            {"role": "system", "content": "You are a helpful assistant that generates short, descriptive titles for chat conversations. Generate a concise title (3-6 words) that captures the main topic of the conversation. Only return the title, nothing else."},
            {"role": "user", "content": f"Generate a short title for this conversation: {conversation_sample}"}
        ]
        
        # Import here to avoid circular imports
        from response import openai_api_call
        
        title_generator = openai_api_call(title_prompt, "Normal")
        generated_title = "".join(title_generator).strip()
        
        # Clean up the title
        generated_title = generated_title.replace('"', '').replace("'", "")
        if len(generated_title) > 50:
            generated_title = generated_title[:50].strip()
        
        # Fallback if generation fails or is empty
        if not generated_title or len(generated_title) < 3:
            return f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return generated_title
        
    except Exception as e:
        print(f"Failed to generate title: {e}")
        return f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

def auto_save_current_chat():
    """Automatically save the current chat with an AI-generated title."""
    if "messages" not in st.session_state or not st.session_state.messages:
        return None
    
    # Check if there are any meaningful messages (user/assistant, not just system)
    meaningful_messages = [msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
    
    if len(meaningful_messages) < 2:  # Need at least 1 user message and 1 assistant response
        return None
    
    with st.spinner("🤖 Generating title and saving chat..."):
        # Generate AI title
        auto_title = auto_generate_chat_title(st.session_state.messages)
        
        # Save with the generated title
        file_path = save_chat_history(auto_title)
        
        if file_path:
            st.success(f"💾 Auto-saved chat as: '{auto_title}'")
            return file_path
        
    return None

def continuous_save_chat():
    """Continuously update the current chat session without showing notifications."""
    if "messages" not in st.session_state or not st.session_state.messages:
        return None
    
    # Check if there are any meaningful messages
    meaningful_messages = [msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
    
    if len(meaningful_messages) < 1:  # Need at least some conversation
        return None
    
    # Check if we already have a current session name, if not generate one
    if not hasattr(st.session_state, 'current_session_name') or not st.session_state.current_session_name:
        if len(meaningful_messages) >= 2:  # Only generate title when we have full exchange
            st.session_state.current_session_name = auto_generate_chat_title(st.session_state.messages)
        else:
            st.session_state.current_session_name = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save silently in the background
    file_path = save_chat_history(st.session_state.current_session_name)
    return file_path

def delete_chat_history(file_path):
    """Delete a chat history file."""
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        st.error(f"Failed to delete chat history: {e}")
        return False

def extract_content_from_file(uploaded_file):
    """Extracts text content from an uploaded file object."""
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    content = ""
    try:
        if file_extension == ".txt":
            # Use chardet to detect encoding for robust text file reading
            raw_data = uploaded_file.getvalue()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            content = raw_data.decode(encoding, errors='replace')
        elif file_extension == ".docx":
            doc = Document(uploaded_file)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif file_extension == ".pptx":
            presentation = Presentation(uploaded_file)
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
        elif file_extension == ".pdf":
            reader = PdfReader(uploaded_file)
            content = "\n".join([page.extract_text() or '' for page in reader.pages])
        elif file_extension in [".xls", ".xlsx", ".csv"]:
            # For simplicity, we'll read CSV from the buffer; Excel might need saving to disk
            if "xls" in file_extension:
                # To handle xls/xlsx from stream, pandas may need the 'openpyxl' or 'xlrd' engine
                df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == ".xlsx" else 'xlrd')
            else:
                df = pd.read_csv(uploaded_file)
            content = df.to_string()
        else:
            st.warning(f"Unsupported file format: {file_extension}. Cannot interpret this file.")
            return None
    except Exception as e:
        st.error(f"Failed to process and interpret file {uploaded_file.name}: {e}")
        return None
    return content

def chatbot_page():
    st.title("Chat With Arcana")
    
    # Add custom CSS for ChatGPT-like styling
    st.markdown("""
    <style>
    .sidebar .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .chat-history-item {
        background-color: #f7f7f8;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        border: 1px solid #e5e5e7;
    }
    
    .chat-history-item:hover {
        background-color: #ececf1;
    }
    
    .new-chat-btn {
        background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        margin-bottom: 16px;
    }
    
    /* Reduce sidebar spacing */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Style section headers */
    .sidebar-section-header {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    }

    .arcana-toolbar {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 16px 6px;
        margin: 16px 0;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
    }

    .arcana-toolbar .toolbar-title {
        font-weight: 600;
        color: #1f2937;
        font-size: 0.9rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .arcana-toolbar div[data-testid="stHorizontalBlock"] {
        margin-bottom: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize or load the database automatically
    if 'dbms' not in st.session_state or not isinstance(st.session_state.dbms, FiberDBMS):
        dbms = FiberDBMS()
        if os.path.exists(INDEX_FILE):
            with st.spinner("Loading existing database..."):
                try:
                    dbms.load_from_file(INDEX_FILE)
                    st.success("Database loaded successfully!")
                except Exception as e:
                    st.warning(f"Failed to load existing database: {e}. Starting with empty database.")
        else:
            st.info("No indexed files found. You can upload files directly or go to the 'Files' page to index documents.")
        st.session_state.dbms = dbms

    dbms = st.session_state.dbms
    
    with st.sidebar:
        # New Chat Button (prominent like ChatGPT)
        if st.button("➕ New Chat", key="new_chat_btn", use_container_width=True, type="primary"):
            # Auto-save current chat before clearing
            auto_save_current_chat()
            
            # Reset messages but keep the initial system prompt
            init_messages()
            st.session_state.processed_file_name = None
            # Reset the current session name for a fresh start
            st.session_state.current_session_name = None
            st.rerun()
        
        st.markdown("---")
        
        # Chat History Section (collapsible like ChatGPT)
        histories = get_available_chat_histories()
        if histories:
            with st.expander("💬 Chat History", expanded=True):
                # Show recent chats with clean design
                for i, history in enumerate(histories[:5]):  # Show only 5 most recent
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            if st.button(
                                f"📄 {history['session_name'][:25]}...",
                                key=f"chat_{i}",
                                help=f"{history['message_count']} messages • {history['timestamp'][:10]}",
                                use_container_width=True
                            ):
                                # Save current chat before switching
                                continuous_save_chat()
                                if load_chat_history(history['filepath']):
                                    st.success("Chat loaded!")
                                    st.rerun()
                            if history.get('tagline'):
                                st.caption(history['tagline'])
                        
                        with col2:
                            if st.button("🗑️", key=f"del_{i}", help="Delete chat"):
                                if delete_chat_history(history['filepath']):
                                    st.success("Deleted!")
                                    st.rerun()
                
                # Show more button if there are more than 5 chats
                if len(histories) > 5:
                    with st.expander("📚 Show All Chats", expanded=False):
                        for i, history in enumerate(histories[5:], start=5):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                if st.button(
                                    f"📄 {history['session_name'][:20]}...",
                                    key=f"chat_all_{i}",
                                    help=f"{history['message_count']} messages • {history['timestamp'][:10]}",
                                    use_container_width=True
                                ):
                                    # Save current chat before switching
                                    continuous_save_chat()
                                    if load_chat_history(history['filepath']):
                                        st.success("Chat loaded!")
                                        st.rerun()
                                if history.get('tagline'):
                                    st.caption(history['tagline'])
                            with col2:
                                if st.button("🗑️", key=f"del_all_{i}", help="Delete chat"):
                                    if delete_chat_history(history['filepath']):
                                        st.success("Deleted!")
                                        st.rerun()
        else:
            st.caption("💬 No chat history yet")
        
        st.markdown("---")
        
        # File Upload Section (prominent and visible)
        st.markdown("### 📄 Upload Document")
        st.markdown("Upload a file to chat with it directly:")
        
        uploaded_file = st.file_uploader(
            "Choose a file to analyze",
            type=['txt', 'pdf', 'docx', 'pptx', 'csv', 'xlsx', 'xls'],
            help="Supported formats: PDF, Word, PowerPoint, Text, Excel, CSV"
        )
        
        # Show current file context if one is loaded
        if st.session_state.get('processed_file_name'):
            st.success(f"📄 Currently chatting with: **{st.session_state.processed_file_name}**")
            if st.button("❌ Clear File Context", use_container_width=True):
                st.session_state.processed_file_name = None
                # Remove file context from messages
                st.session_state.messages = [msg for msg in st.session_state.messages 
                                           if not (msg.get("role") == "system" and "uploaded the file" in msg.get("content", ""))]
                st.rerun()
        
        st.markdown("---")
        
        # Session Info (compact)
        if "messages" in st.session_state and st.session_state.messages:
            meaningful_messages = [msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
            if len(meaningful_messages) >= 2:
                st.caption(f"💬 {len(meaningful_messages)} messages • Auto-saves when starting new chat")
        if uploaded_file is not None:
            # Check if this file has been processed already to avoid reprocessing on every rerun
            if st.session_state.get('processed_file_name') != uploaded_file.name:
                with st.spinner(f"🔍 Processing {uploaded_file.name}..."):
                    file_content = extract_content_from_file(uploaded_file)
                    if file_content:
                        # Save the uploaded file to CACHE_DIR/Uploads directory
                        uploads_dir = os.path.join(CACHE_DIR, "Uploads")
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        try:
                            # Save the original file
                            file_path = os.path.join(uploads_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Also save extracted content as txt for easy reference
                            txt_filename = os.path.splitext(uploaded_file.name)[0] + "_extracted.txt"
                            txt_path = os.path.join(uploads_dir, txt_filename)
                            with open(txt_path, "w", encoding="utf-8") as f:
                                f.write(file_content)
                            
                            st.info(f"💾 Saved to {uploads_dir}: {uploaded_file.name} + extracted text")
                        except Exception as e:
                            st.warning(f"Could not save file to {uploads_dir}: {e}")
                            # Continue with processing even if file saving fails
                        
                        # Index the new file content into the database
                        with st.spinner(f"📚 Indexing content..."):
                            lines = file_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line:
                                    lang = detect_language(line)
                                    keywords = extract_keywords(line, lang)
                                    dbms.add_entry(name=uploaded_file.name, content=line, tags=keywords)
                            dbms.save(INDEX_FILE) # Save the updated index

                        # Add the file content as a system message for context, with priority instructions
                        context_message = (
                            f"The user has uploaded the file `{uploaded_file.name}`. "
                            f"For the user's next questions, you MUST prioritize the content of this file as the primary and ONLY source of information. "
                            f"Ignore any previous search results from the general document database. "
                            f"All answers must come directly from the file content provided below. "
                            f"Explicitly mention that you are answering based on the uploaded file."
                            f"\n\n--- FILE CONTENT ---\n{file_content}\n--- END FILE CONTENT ---"
                        )
                        st.session_state.messages.append({"role": "system", "content": context_message})
                        st.session_state.processed_file_name = uploaded_file.name
                        st.success(f"✅ {uploaded_file.name} indexed and ready for questions!")
                        st.rerun()
                    else:
                        st.session_state.processed_file_name = None # Reset if processing fails

    # Remove the old clear button since it's now in sidebar as "New Chat"

    if "messages" not in st.session_state or not st.session_state.messages:
        init_messages()

    # Display existing conversation (excluding system messages)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User input area
    user_input = st.chat_input("Ask me anything about your documents...")

    # Response toolbar directly beneath the input
    with st.container():
        st.markdown("<div class=\"arcana-toolbar\">", unsafe_allow_html=True)
        st.markdown("<div class=\"toolbar-title\">Assistant tools</div>", unsafe_allow_html=True)
        toolbar_cols = st.columns([1.5, 1.5, 1], gap="medium")
        with toolbar_cols[0]:
            st.markdown("**Web Search**")
            web_supplement_enabled = st.checkbox(
                "Web supplement (Bing)",
                help=(
                    "When enabled, Arcana fetches public web search results from Bing to"
                    " supplement your indexed documents."
                ),
                key="web_supplement_enabled",
                label_visibility="collapsed",
            )
        with toolbar_cols[1]:
            st.markdown("**Assistant Mode**")
            response_type = st.selectbox(
                "Mode",
                ["Normal", "IDX", "Math", "Reasoning"],
                help="""
                **Normal**: General conversation with search context
                **IDX**: Strictly based on indexed files
                **Math**: Specialized for mathematical queries
                **Reasoning**: Uses a deep reasoning model that thinks step-by-step before replying
                """,
                label_visibility="collapsed",
            )
        with toolbar_cols[2]:
            st.markdown("**Agent Mode**")
            agent_mode_enabled = st.checkbox(
                "Agent Mode",
                help=(
                    "When enabled, Arcana's agent reads full documents, generates summaries, "
                    "and stores them for future chats before answering."
                ),
                key="agent_mode_enabled",
                label_visibility="collapsed",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if user_input:
        st.session_state.pending_sources_default = "Sources: No sources cited."
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # If a file has NOT been processed, search the database for context.
        # If a file HAS been processed, its context is already in the messages, so we skip this.
        results: List[dict] = []
        search_attempts: List[Tuple[str, int]] = []
        keywords: List[str] = []
        keyword_generation_raw = ""
        keyword_source = "n/a"
        bing_results: List[dict] = []
        news_sensitive_query = False
        agent_summary_results: List[AgentSummaryResult] = []

        if st.session_state.get('processed_file_name') is None:
            with st.spinner("Searching for relevant information..."):
                lang = detect_language(user_input)
                keyword_source = "nltk"
                keyword_generation_raw = ""
                keywords = []
                if response_type == "Normal":
                    gpt_keywords, keyword_generation_raw = generate_keywords_with_gpt(user_input, lang)
                    if gpt_keywords:
                        keywords = gpt_keywords
                        keyword_source = "language_model"
                if not keywords:
                    keywords = extract_keywords(user_input, lang)
                    keyword_source = "nltk" if keywords else keyword_source

                results = []
                search_attempts = []
                if keywords:
                    if keyword_source == "language_model":
                        results, search_attempts = query_dbms_with_keywords(dbms, keywords)
                    else:
                        query_text = " ".join(keywords[:20])
                        raw_results = dbms.query(
                            query_text,
                            top_n=min(20, max(1, len(keywords)))
                        )
                        raw_results = raw_results or []
                        results = raw_results[:5]
                        search_attempts = [(query_text, len(results))]

                news_sensitive_query = False
                if web_supplement_enabled:
                    bing_results = search_bing(user_input)
                    news_sensitive_query = _looks_like_news_or_sensitive_query(user_input)
                
                assistant_reply_lines = [
                    "INTERNAL SEARCH CONTEXT (not visible to the user):",
                    "Evaluate the following snippets and only cite information that is accurate and relevant.",
                    "If no snippets answer the query, explain that the indexed files lacked the information and rely on web supplements or well-known general knowledge to respond accurately.",
                    f"Keyword generation method: {keyword_source}",
                ]

                if keywords:
                    assistant_reply_lines.append(
                        "Keywords considered: " + ", ".join(keywords[:20])
                    )
                if search_attempts:
                    assistant_reply_lines.append("Search attempts:")
                    for query_text, count in search_attempts:
                        assistant_reply_lines.append(
                            f"- `{query_text}` → {count} new snippet(s)"
                        )
                if keyword_generation_raw and keyword_source == "language_model":
                    assistant_reply_lines.append(
                        "Raw keyword suggestion response: " + keyword_generation_raw
                    )

                if agent_mode_enabled:
                    target_files = _unique_preserve_order(
                        result.get("name") for result in results if result.get("name")
                    )
                    if target_files:
                        with st.spinner("🧠 Agent is summarizing documents..."):
                            agent = get_document_agent()
                            for file_name in target_files:
                                summary_result = agent.summarise_document(file_name, dbms)
                                if summary_result.summary_text:
                                    agent_summary_results.append(summary_result)
                                elif summary_result.reason:
                                    st.warning(f"Agent could not summarise {file_name}: {summary_result.reason}")
                    elif keywords:
                        st.info("Agent mode enabled, but no documents were retrieved to summarise.")

                if web_supplement_enabled:
                    assistant_reply_lines.append(
                        "When citing information from web supplements, format the citation as a Markdown link like `[Title](URL)` and include it in the final 'Sources:' line."
                    )
                    if news_sensitive_query:
                        assistant_reply_lines.append(
                            "The user's request appears to involve current events or other boundary-sensitive information. Before writing the visible reply, quietly reason about whether the local document snippets are reliable or outdated. Cross-check key facts against the Bing web results and discard any conflicting or unverifiable claims. Keep this deliberation internal and only present conclusions you can support with citations."
                        )
                    if bing_results:
                        assistant_reply_lines.append(
                            "Web supplement results from Bing (cite using the provided URLs):"
                        )
                        for result in bing_results:
                            assistant_reply_lines.append(
                                f"- {result['title']} ({result['link']}): {result['snippet']}"
                            )
                    else:
                        assistant_reply_lines.append(
                            "Bing web supplement returned no usable results. If you rely on general knowledge, end with 'Sources: No sources cited.'"
                        )

                if agent_mode_enabled:
                    if agent_summary_results:
                        assistant_reply_lines.append(
                            "Agent analysed the full documents listed below. Use their summaries in the following context and cite the original file names."
                        )
                        for summary in agent_summary_results:
                            assistant_reply_lines.append(
                                f"- `{summary.file_name}` (summary stored as `{summary.summary_name}`)"
                            )
                    else:
                        assistant_reply_lines.append(
                            "Agent mode is enabled, but no summaries were available for this query."
                        )

                assistant_reply = "\n".join(assistant_reply_lines) + "\n\n"

                if results:
                    assistant_reply += "Here are the top results from your documents:\n\n"
                    for idx, result in enumerate(results, 1):
                        assistant_reply += f"**Result {idx} from `{result['name']}`:**\n"
                        assistant_reply += f"_{result['content']}_\n\n"
                elif keywords:
                    assistant_reply += (
                        "No specific passages were retrieved. Let the user know that the indexed documents did not contain "
                        "information matching their request, then answer using web supplements if available or accurate "
                        "general knowledge."
                    )
                else:
                    assistant_reply += (
                        "Keyword extraction failed. Inform the user that the system could not understand the query well "
                        "enough to search the documents."
                    )

                if agent_summary_results:
                    assistant_reply += "\nAgent-generated document overviews:\n\n"
                    for summary in agent_summary_results:
                        assistant_reply += f"### Agent summary for `{summary.file_name}`\n{summary.summary_text}\n\n"

                assistant_reply += (
                    "\nAlways end the final response with a 'Sources:' line listing every citation or 'Sources: No sources cited.'"
                )

                combined_results = list(results)
                if agent_summary_results:
                    combined_results.extend(
                        {
                            "name": summary.summary_name or f"{summary.file_name} (agent summary)",
                            "content": summary.summary_text,
                        }
                        for summary in agent_summary_results
                    )

                st.session_state.pending_sources_default = _build_sources_default_line(combined_results, bing_results)
                st.session_state.messages.append({"role": "system", "content": assistant_reply})
        else:
            if agent_mode_enabled and st.session_state.get('processed_file_name'):
                processed_name = st.session_state['processed_file_name']
                with st.spinner("🧠 Agent is summarizing the uploaded file..."):
                    agent = get_document_agent()
                    summary_result = agent.summarise_document(processed_name, dbms)
                if summary_result.summary_text:
                    agent_summary_results.append(summary_result)
                    if summary_result.created:
                        st.success(f"Agent summary saved for {processed_name}.")
                elif summary_result.reason:
                    st.warning(f"Agent could not summarise {processed_name}: {summary_result.reason}")

            if agent_summary_results:
                summary_context_lines = [
                    "AGENT SUMMARY CONTEXT (uploaded file):",
                    "The agent analysed the active uploaded file and produced the summary below. Use it while answering and cite the original document name.",
                ]
                for summary in agent_summary_results:
                    summary_context_lines.append(f"### Agent summary for `{summary.file_name}`\n{summary.summary_text}")
                st.session_state.messages.append({"role": "system", "content": "\n\n".join(summary_context_lines)})

                combined_results = [
                    {
                        "name": summary.summary_name or f"{summary.file_name} (agent summary)",
                        "content": summary.summary_text,
                    }
                    for summary in agent_summary_results
                ]
                st.session_state.pending_sources_default = _build_sources_default_line(combined_results, [])

        with st.spinner("Arcana is thinking..."):
            try:
                # Make sure to initialize 'processed_file_name' if it doesn't exist
                if 'processed_file_name' not in st.session_state:
                    st.session_state.processed_file_name = None

                messages_to_send = list(st.session_state.messages)
                if response_type == "Reasoning":
                    messages_to_send.append({
                        "role": "system",
                        "content": (
                            "You are in deep reasoning mode. Think through the problem step by step before answering. "
                            "Provide a thorough explanation that breaks complex ideas into clear stages so the user can "
                            "understand the concept deeply."
                        )
                    })

                with st.chat_message("assistant"):
                    # Use st.write_stream to render the response in real-time
                    response_generator = openai_api_call(messages_to_send, response_type)
                    collected_chunks = []

                    def stream_and_collect():
                        for chunk in response_generator:
                            collected_chunks.append(chunk)
                            yield chunk

                    st.write_stream(stream_and_collect())
                    full_response = "".join(collected_chunks)
                    default_sources_line = st.session_state.get(
                        "pending_sources_default",
                        "Sources: No sources cited.",
                    )
                    ensured_response = _ensure_sources_line(full_response, default_sources_line)
                    if ensured_response != full_response:
                        extra_text = ensured_response[len(full_response):]
                        if extra_text:
                            st.markdown(extra_text)
                        full_response = ensured_response
                    st.session_state.pending_sources_default = "Sources: No sources cited."

                    if response_type == "Reasoning" and response_generator.has_reasoning():
                        with st.expander("Show Arcana's reasoning", expanded=False):
                            reasoning_text = response_generator.reasoning.replace("\n", "  \n")
                            st.markdown(reasoning_text or "(Reasoning trace was empty.)")
                
                # Append the full response to the message history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Continuously save the chat in the background
                continuous_save_chat()
                
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred while communicating with the AI: {e}")

def init_messages():
    """Initializes or resets the chat message history in the session state."""
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey, I'm Arcana, your Indexademics AI assistant. Ask me anything about your indexed files!"},
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
    ]
