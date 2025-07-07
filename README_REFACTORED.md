# 🌌 Arcana AI Assistant - Refactored

> **Intelligent document processing and AI chatbot system with organized, modular architecture**

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
./run.sh
# or
streamlit run app.py
```

## 📁 Project Structure

The codebase has been completely refactored for better organization and maintainability:

```
📦 Arcana/
├── 🎯 app.py                    # Main Streamlit application
├── 🚀 run.sh                    # Quick start script
├── 📋 requirements.txt          # Dependencies
├── ⚙️ setup.py                  # Package setup
├── 📖 README.md                 # This file
├── 🗃️ legacy_backup/            # Original files (backup)
└── 📁 arcana/                   # Main package
    ├── 🏗️ core/                 # Core application logic
    │   ├── app.py               # Original app components
    │   ├── app_extreme.py       # Extended features
    │   └── config.py            # Configuration settings
    ├── 📄 pages/                # UI page components
    │   ├── chatbot.py           # AI chatbot interface
    │   ├── finder.py            # File management
    │   ├── editor.py            # Document editor
    │   ├── mixup.py             # Presentation generator
    │   ├── settings.py          # App settings
    │   ├── longresponse.py      # Long-form analysis
    │   ├── flashcards.py        # Flashcard system
    │   └── speech_to_text.py    # Voice input
    ├── 🔧 utils/                # Utility functions
    │   ├── fiber.py             # Database management
    │   ├── indexing.py          # File indexing
    │   ├── response.py          # API handling
    │   ├── funcs.py             # Helper functions
    │   ├── theme.py             # UI theming
    │   └── nltk_setup.py        # NLP setup
    ├── 🌐 localization/         # Translation files
    │   └── translation.py       # Multi-language support
    ├── 🧪 tests/                # Test files
    │   ├── test_simple.py
    │   ├── test_theta.py
    │   ├── test_page_count.py
    │   └── test_markdown_parser.py
    └── 🎮 demos/                # Demo applications
        ├── demo_translation.py
        ├── theta_demo.py
        ├── theta_demo_new.py
        └── ui_translation_preview.py
```

## ✨ Features

### 🔧 Core Features
- **📁 File Management**: Upload, organize, and index documents
- **🤖 AI Chatbot**: Chat with your documents using advanced AI
- **📊 Presentation Generator**: Create presentations from your content
- **📚 Study Guide Creator**: Generate study materials automatically
- **✏️ Document Editor**: AI-assisted document editing

### 🚀 Advanced Features
- **📜 Long Response Analysis**: Deep analysis of lengthy documents
- **🃏 Flashcard System**: Interactive learning with Q&A cards
- **🎙️ Speech to Text**: Voice input support
- **🌐 Multi-language Support**: Interface in multiple languages
- **⚙️ Customizable Settings**: Personalize your experience

## 🛠️ Development

### Code Organization Benefits
- **🎯 Modular Structure**: Clear separation of concerns
- **🔄 Easy Maintenance**: Simple to update and extend
- **📖 Better Readability**: Well-organized, documented code
- **🧪 Testable**: Isolated components for easy testing
- **🔌 Extensible**: Add new features easily

### Import Structure
```python
# Core components
from arcana.core.config import APP_TITLE
from arcana.core.app import initialize_app

# Page components  
from arcana.pages.chatbot import chatbot_page
from arcana.pages.finder import files_page

# Utilities
from arcana.utils.fiber import FiberDBMS
from arcana.utils.indexing import indexing

# Localization
from arcana.localization.translation import TRANSLATIONS
```

## 🎯 Usage

1. **📤 Upload Files**: Use the Files page to upload documents
2. **🔍 Index Content**: Process files for AI chatbot access
3. **💬 Chat**: Ask questions about your documents
4. **🎨 Create**: Generate presentations and study materials
5. **✏️ Edit**: Use AI-powered document editing

## 🏆 Credits

**Development Team:**
- **Osmond G11**: Core algorithms, DBMS, API functions
- **Celsia G11**: UI development, platform integration
- **Brian G10**: Debugging, testing, mirroring
- **Pete G10**: Database management, testing

**Technologies:**
- **Streamlit**: Web application framework
- **OpenAI API**: AI language models  
- **NLTK**: Natural language processing
- **Python**: Core programming language

## 📜 License

Licensed under CC-BY-ND-SA by Indexademics
- ✅ Attribution required
- ✅ Sharing with proper credit allowed
- ❌ No derivatives without permission
- ❌ No unauthorized redistribution

---

**Made with ❤️ by the Arcana Team**

*Transform your documents into intelligent conversations!*