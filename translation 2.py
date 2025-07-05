"""translation.py - UI Translation System for Arcana Extreme"""
import streamlit as st

# --- Translation System for UI ---

# Supported languages and their translations
TRANSLATIONS = {
    "en": {
        # Main navigation and app
        "app_title": "Arcana Extreme",
        "app_subtitle": "Your intelligent assistant for creating documents, presentations, and study materials.",
        "menu": "Menu",
        "back_to_menu": "← Menu",
        "language_selector": "🌐 Interface Language:",
        
        # Main pages
        "introduction": "Introduction",
        "files": "Files", 
        "citations": "Citations",
        "chatbot": "Chatbot",
        "speech_to_text": "Speech to Text",
        "mixup": "Mixup",
        "editor": "Editor",
        "long_response": "Long Response",
        "settings": "Settings",
        
        # Introduction page
        "show_system_info": "Show System Information",
        
        # Citations page
        "citations_title": "📚 Academic & Resource Citations",
        "citations_subtitle": "This document provides citations for academic materials and resources used within Arcana.",
        
        # Settings page
        "settings_title": "Settings",
        "settings_subtitle": "Customize your chatbot experience.",
        "choose_theme": "Choose a theme:",
        "light_theme": "Light",
        "dark_theme": "Dark",
        "selected_theme": "Selected theme:",
        "view_update_log": "View Update Log",
        "no_changelog": "No changelog available yet.",
        "language_settings": "Language Settings",
        "ui_language": "Interface Language",
        "language_description": "Choose your preferred language for the interface. The application will restart to apply changes.",
        
        # Files page
        "files_title": "📂 File Management",
        "upload_files": "Upload Files",
        "indexed_files": "Indexed Files",
        "search_files": "Search Files",
        "file_status": "File Status",
        "indexing_complete": "Indexing Complete",
        "no_files_found": "No files found",
        "upload_new_files": "Upload New Files",
        "upload_documents": "Upload documents, PDFs, or other supported files.",
        "files_uploaded_success": "{0} files uploaded successfully!",
        "database_indexing": "Database Indexing",
        "reindex_info": "Re-indexing is required after moving, renaming, or uploading files to ensure the chatbot can find them.",
        "reindex_button": "Re-Index All Files",
        "reindex_help": "Click here to process all files in the Finder and update the search database. This can take a moment.",
        "indexing_progress": "Indexing in progress... Please wait.",
        "indexing_success": "Indexing complete! 🎉 {0} entries were processed.",
        "database_updated": "Database updated successfully!",
        
        # Chatbot page
        "chatbot_title": "💬 AI Assistant",
        "chat_input": "Ask me anything about your documents...",
        "send": "Send",
        "clear_chat": "Clear Chat",
        "chat_history": "Chat History",
        "new_chat": "➕ New Chat",
        "chat_loaded": "Chat loaded!",
        "chat_deleted": "Deleted!",
        "delete_chat": "Delete chat",
        "show_all_chats": "📚 Show All Chats",
        "clear_file_context": "❌ Clear File Context",
        "no_chat_history": "💬 No chat history yet",
        "no_indexed_files_chatbot": "No indexed files found. You can upload files directly or go to the 'Files' page to index documents.",
        "database_loaded": "Database loaded successfully!",
        "database_load_failed": "Failed to load existing database: {0}. Starting with empty database.",
        "loading_database": "Loading existing database...",
        
        # Mixup page (Study Guide, Presentations, etc.)
        "mixup_title": "🔀 Content Generator",
        "choose_mode": "Choose a generation mode:",
        "presentation": "Presentation",
        "study_guide": "Study Guide",
        "flashcards": "Q&A Flashcards",
        
        # Study Guide specific
        "sg_header": "📚 Study Guide Generator",
        "sg_configure": "Step 1: Configure Your Study Guide",
        "sg_topic_input": "What topic would you like to study?",
        "sg_topic_placeholder": "e.g., Cell Biology, World War II, Calculus Derivatives",
        "sg_style": "Study Guide Style:",
        "sg_generation_options": "⚙️ Generation Options",
        "sg_extreme_mode": "🚀 Extreme Mode",
        "sg_target_pages": "📄 Target Pages",
        "sg_auto_length": "📝 **Auto Length**: AI will determine optimal study guide length based on topic complexity.",
        "sg_short_guide": "📄 **Short Guide**: ~{} pages • Quick generation • Concise content",
        "sg_medium_guide": "📄 **Medium Guide**: ~{} pages • Moderate generation time • Balanced detail",
        "sg_long_guide": "📄 **Long Guide**: ~{} pages • Extended generation time • Comprehensive detail",
        "sg_very_long_guide": "📄 **Very Long Guide**: ~{} pages • Very long generation time • Extensive detail",
        
        # Presentation specific
        "ppt_header": "✨ Presentation Generator",
        "ppt_choose_topic": "Step 1: Choose a Topic",
        "ppt_topic_input": "What is your presentation about?",
        
        # Editor page
        "editor_title": "📝 AI Document Editor",
        "editor_subtitle": "Paste your text below, provide an editing instruction, and let the Arcana AI assist you.",
        "create_new": "Create New",
        "open_file": "Open File",
        "save_file": "Save File",
        "export": "Export",
        "version_history": "📚 Version History",
        "no_version_history": "No version history yet. Make some edits to see versions here!",
        "total_versions": "Total versions:",
        "created": "Created:",
        "instruction": "Instruction:",
        "revert": "⏪ Revert",
        "confirm_revert": "⚠️ **Confirm Revert Action**",
        "revert_confirmation": "Are you sure you want to revert to Version {0}?",
        "revert_info": "💡 You will be able to revert back to your current version at any time.",
        "yes_revert": "✅ Yes, Revert",
        "cancel": "❌ Cancel",
        "your_document": "Your Document",
        "original_text": "Original Text",
        "original_text_placeholder": "Paste your original text here to get started.",
        
        # Speech to Text page
        "stt_title": "🎙️ Speech to Text",
        "stt_subtitle": "Record your voice and convert it to text using DashScope Paraformer ASR.",
        "start_recording": "Start Recording",
        "stop_recording": "Stop Recording",
        "transcription": "Transcription",
        "recording_controls": "Recording Controls",
        "recording_in_progress": "🔴 Recording in progress...",
        "recording_instructions": "Click 'Stop' in the recorder above to finish recording, then click 'Transcribe Audio' below.",
        "recording_start_info": "Click 'Start' in the recorder above to begin recording your voice.",
        "transcribe_audio": "🎯 Transcribe Audio",
        "transcribing": "Transcribing your audio...",
        
        # Long Response page
        "lr_title": "� Long-Form Text Analyzer",
        "generate_response": "Generate Response",
        "response_length": "Response Length",
        
        # Common UI elements
        "generate": "Generate",
        "download": "⬇️ Download",
        "upload": "📤 Upload",
        "delete": "🗑️ Delete",
        "edit": "✏️ Edit",
        "save": "💾 Save",
        "cancel": "❌ Cancel",
        "confirm": "✅ Confirm",
        "back": "⬅️ Back",
        "next": "➡️ Next",
        "finish": "🏁 Finish",
        "loading": "Loading...",
        "processing": "Processing...",
        "complete": "✅ Complete!",
        "error": "❌ Error:",
        "success": "🎉 Success!",
        "warning": "⚠️ Warning:",
        "info": "ℹ️ Info:",
        
        # File types and formats
        "word_document": "📄 Word Document",
        "powerpoint": "📊 PowerPoint",
        "text_format": "📋 Text Format",
        "pdf_file": "📕 PDF File",
        
        # Common messages
        "no_files_indexed": "No indexed files found. Content will be generated from general knowledge. To use your own documents as context, please go to the 'Files' page and index them first.",
        "analyzing": "Analyzing your documents...",
        "generating_content": "Generating content...",
    },
    
    "es": {
        # Main navigation and app
        "app_title": "Arcana Extremo",
        "app_subtitle": "Tu asistente inteligente para crear documentos, presentaciones y materiales de estudio.",
        "menu": "Menú",
        "back_to_menu": "← Menú",
        "language_selector": "🌐 Idioma de Interfaz:",
        
        # Main pages
        "introduction": "Introducción",
        "files": "Archivos",
        "citations": "Citas",
        "chatbot": "Chatbot",
        "speech_to_text": "Voz a Texto",
        "mixup": "Mezcla",
        "editor": "Editor",
        "long_response": "Respuesta Larga",
        "settings": "Configuración",
        
        # Settings page
        "settings_title": "Configuración",
        "settings_subtitle": "Personaliza tu experiencia con el chatbot.",
        "choose_theme": "Elige un tema:",
        "light_theme": "Claro",
        "dark_theme": "Oscuro",
        "selected_theme": "Tema seleccionado:",
        "view_update_log": "Ver Registro de Actualizaciones",
        "no_changelog": "No hay registro de cambios disponible aún.",
        "language_settings": "Configuración de Idioma",
        "ui_language": "Idioma de Interfaz",
        "language_description": "Elige tu idioma preferido para la interfaz. La aplicación se reiniciará para aplicar los cambios.",
        
        # Files page
        "files_title": "📂 Gestión de Archivos",
        "upload_files": "Subir Archivos",
        "indexed_files": "Archivos Indexados",
        "search_files": "Buscar Archivos",
        "file_status": "Estado del Archivo",
        "indexing_complete": "Indexación Completa",
        "no_files_found": "No se encontraron archivos",
        
        # Chatbot page
        "chatbot_title": "💬 Asistente IA",
        "chat_input": "Escribe tu mensaje aquí...",
        "send": "Enviar",
        "clear_chat": "Limpiar Chat",
        "chat_history": "Historial de Chat",
        
        # Mixup page
        "mixup_title": "🔀 Generador de Contenido",
        "choose_mode": "Elige un modo de generación:",
        "presentation": "Presentación",
        "study_guide": "Guía de Estudio",
        "flashcards": "Tarjetas P&R",
        
        # Study Guide specific
        "sg_header": "📚 Generador de Guías de Estudio",
        "sg_configure": "Paso 1: Configura tu Guía de Estudio",
        "sg_topic_input": "¿Qué tema te gustaría estudiar?",
        "sg_topic_placeholder": "ej., Biología Celular, Segunda Guerra Mundial, Derivadas de Cálculo",
        "sg_style": "Estilo de Guía de Estudio:",
        "sg_generation_options": "⚙️ Opciones de Generación",
        "sg_extreme_mode": "🚀 Modo Extremo",
        "sg_target_pages": "📄 Páginas Objetivo",
        "sg_auto_length": "📝 **Longitud Automática**: La IA determinará la longitud óptima basada en la complejidad del tema.",
        "sg_short_guide": "📄 **Guía Corta**: ~{} páginas • Generación rápida • Contenido conciso",
        "sg_medium_guide": "📄 **Guía Media**: ~{} páginas • Tiempo moderado • Detalle equilibrado",
        "sg_long_guide": "📄 **Guía Larga**: ~{} páginas • Tiempo extendido • Detalle comprensivo",
        "sg_very_long_guide": "📄 **Guía Muy Larga**: ~{} páginas • Tiempo muy largo • Detalle extensivo",
        
        # Presentation specific
        "ppt_header": "✨ Generador de Presentaciones",
        "ppt_choose_topic": "Paso 1: Elige un Tema",
        "ppt_topic_input": "¿De qué trata tu presentación?",
        
        # Common UI elements
        "generate": "Generar",
        "download": "⬇️ Descargar",
        "upload": "📤 Subir",
        "delete": "🗑️ Eliminar",
        "edit": "✏️ Editar",
        "save": "💾 Guardar",
        "cancel": "❌ Cancelar",
        "confirm": "✅ Confirmar",
        "back": "⬅️ Atrás",
        "next": "➡️ Siguiente",
        "finish": "🏁 Terminar",
        "loading": "Cargando...",
        "processing": "Procesando...",
        "complete": "✅ ¡Completo!",
        "error": "❌ Error:",
        "success": "🎉 ¡Éxito!",
        "warning": "⚠️ Advertencia:",
        "info": "ℹ️ Info:",
        
        # Common messages
        "no_files_indexed": "No se encontraron archivos indexados. El contenido se generará desde conocimiento general. Para usar tus propios documentos como contexto, ve a la página 'Archivos' e indexa primero.",
        "analyzing": "Analizando tus documentos...",
        "generating_content": "Generando contenido...",
    },
    
    "fr": {
        # Main navigation and app
        "app_title": "Arcana Extrême",
        "app_subtitle": "Votre assistant intelligent pour créer des documents, présentations et matériels d'étude.",
        "menu": "Menu",
        "back_to_menu": "← Menu",
        "language_selector": "🌐 Langue d'Interface:",
        
        # Main pages
        "introduction": "Introduction",
        "files": "Fichiers",
        "citations": "Citations",
        "chatbot": "Chatbot",
        "speech_to_text": "Parole vers Texte",
        "mixup": "Mixage",
        "editor": "Éditeur",
        "long_response": "Réponse Longue",
        "settings": "Paramètres",
        
        # Settings page
        "settings_title": "Paramètres",
        "settings_subtitle": "Personnalisez votre expérience chatbot.",
        "choose_theme": "Choisissez un thème:",
        "light_theme": "Clair",
        "dark_theme": "Sombre",
        "selected_theme": "Thème sélectionné:",
        "view_update_log": "Voir le Journal de Mise à Jour",
        "no_changelog": "Aucun journal de modifications disponible encore.",
        "language_settings": "Paramètres de Langue",
        "ui_language": "Langue d'Interface",
        "language_description": "Choisissez votre langue préférée pour l'interface. L'application redémarrera pour appliquer les changements.",
        
        # Common UI elements
        "generate": "Générer",
        "download": "⬇️ Télécharger",
        "upload": "📤 Téléverser",
        "delete": "🗑️ Supprimer",
        "edit": "✏️ Modifier",
        "save": "💾 Sauvegarder",
        "cancel": "❌ Annuler",
        "confirm": "✅ Confirmer",
        "back": "⬅️ Retour",
        "next": "➡️ Suivant",
        "finish": "🏁 Terminer",
        "loading": "Chargement...",
        "processing": "Traitement...",
        "complete": "✅ Terminé!",
        "error": "❌ Erreur:",
        "success": "🎉 Succès!",
        "warning": "⚠️ Avertissement:",
        "info": "ℹ️ Info:",
    },
    
    "de": {
        # Main navigation and app
        "app_title": "Arcana Extrem",
        "app_subtitle": "Ihr intelligenter Assistent für das Erstellen von Dokumenten, Präsentationen und Lernmaterialien.",
        "menu": "Menü",
        "back_to_menu": "← Menü",
        "language_selector": "🌐 Interface-Sprache:",
        
        # Main pages
        "introduction": "Einführung",
        "files": "Dateien",
        "citations": "Zitate",
        "chatbot": "Chatbot",
        "speech_to_text": "Sprache zu Text",
        "mixup": "Mischung",
        "editor": "Editor",
        "long_response": "Lange Antwort",
        "settings": "Einstellungen",
        
        # Settings page
        "settings_title": "Einstellungen",
        "settings_subtitle": "Passen Sie Ihre Chatbot-Erfahrung an.",
        "choose_theme": "Wählen Sie ein Design:",
        "light_theme": "Hell",
        "dark_theme": "Dunkel",
        "selected_theme": "Ausgewähltes Design:",
        "view_update_log": "Update-Protokoll anzeigen",
        "no_changelog": "Noch kein Änderungsprotokoll verfügbar.",
        "language_settings": "Spracheinstellungen",
        "ui_language": "Interface-Sprache",
        "language_description": "Wählen Sie Ihre bevorzugte Sprache für die Benutzeroberfläche. Die Anwendung wird neu gestartet, um die Änderungen anzuwenden.",
        
        # Common UI elements
        "generate": "Generieren",
        "download": "⬇️ Herunterladen",
        "upload": "📤 Hochladen",
        "delete": "🗑️ Löschen",
        "edit": "✏️ Bearbeiten",
        "save": "💾 Speichern",
        "cancel": "❌ Abbrechen",
        "confirm": "✅ Bestätigen",
        "back": "⬅️ Zurück",
        "next": "➡️ Weiter",
        "finish": "🏁 Beenden",
        "loading": "Laden...",
        "processing": "Verarbeitung...",
        "complete": "✅ Fertig!",
        "error": "❌ Fehler:",
        "success": "🎉 Erfolg!",
        "warning": "⚠️ Warnung:",
        "info": "ℹ️ Info:",
    },
    
    "zh": {
        # Main navigation and app
        "app_title": "阿卡纳极致版",
        "app_subtitle": "您创建文档、演示文稿和学习材料的智能助手。",
        "menu": "菜单",
        "back_to_menu": "← 菜单",
        "language_selector": "🌐 界面语言:",
        
        # Main pages
        "introduction": "介绍",
        "files": "文件",
        "citations": "引用",
        "chatbot": "聊天机器人",
        "speech_to_text": "语音转文字",
        "mixup": "混合",
        "editor": "编辑器",
        "long_response": "长回复",
        "settings": "设置",
        
        # Settings page
        "settings_title": "设置",
        "settings_subtitle": "自定义您的聊天机器人体验。",
        "choose_theme": "选择主题:",
        "light_theme": "浅色",
        "dark_theme": "深色",
        "selected_theme": "选择的主题:",
        "view_update_log": "查看更新日志",
        "no_changelog": "尚无更新日志可用。",
        "language_settings": "语言设置",
        "ui_language": "界面语言",
        "language_description": "选择您首选的界面语言。应用程序将重新启动以应用更改。",
        
        # Common UI elements
        "generate": "生成",
        "download": "⬇️ 下载",
        "upload": "📤 上传",
        "delete": "🗑️ 删除",
        "edit": "✏️ 编辑",
        "save": "💾 保存",
        "cancel": "❌ 取消",
        "confirm": "✅ 确认",
        "back": "⬅️ 返回",
        "next": "➡️ 下一步",
        "finish": "🏁 完成",
        "loading": "加载中...",
        "processing": "处理中...",
        "complete": "✅ 完成!",
        "error": "❌ 错误:",
        "success": "🎉 成功!",
        "warning": "⚠️ 警告:",
        "info": "ℹ️ 信息:",
    }
}

def get_available_languages():
    """Returns list of available language codes and names."""
    return {
        "en": "English",
        "es": "Español", 
        "fr": "Français",
        "de": "Deutsch",
        "zh": "中文"
    }

def init_language_state():
    """Initialize language selection in session state."""
    if 'ui_language' not in st.session_state:
        st.session_state.ui_language = 'en'  # Default to English

def t(key, *args):
    """
    Translation function - returns translated text for the current language.
    Args:
        key: Translation key
        *args: Format arguments for strings with placeholders
    """
    init_language_state()
    lang = st.session_state.ui_language
    
    # Get translation, fallback to English if not found
    translation = TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key))
    
    # Format with arguments if provided
    if args:
        try:
            translation = translation.format(*args)
        except:
            pass  # If formatting fails, return unformatted string
    
    return translation

def render_language_selector():
    """Renders the language selector in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('language_settings')}")
    
    languages = get_available_languages()
    current_lang = st.session_state.get('ui_language', 'en')
    
    selected_lang = st.sidebar.selectbox(
        t("language_selector"),
        options=list(languages.keys()),
        format_func=lambda x: f"{languages[x]}",
        index=list(languages.keys()).index(current_lang),
        key="language_selector"
    )
    
    if selected_lang != current_lang:
        st.session_state.ui_language = selected_lang
        st.sidebar.success(t("success") + " " + t("language_description"))
        st.rerun()

def set_page_config_with_translation():
    """Set page config with translated title."""
    init_language_state()
    st.set_page_config(
        page_title=t("app_title"),
        layout="wide"
    )
