import streamlit as st
import dashscope
from dashscope.audio.asr import Recognition
from http import HTTPStatus
import os
import tempfile
import shutil
from typing import Any, cast

def speech_to_text_page():
    """
    Simplified Speech to Text page without premium streamlit-webrtc
    """
    st.title("🎙️ Speech to Text")
    st.subtitle("Upload audio files and convert them to text using DashScope Paraformer ASR.")
    
    # Instructions
    st.markdown("### How to use:")
    st.markdown("1. **Upload an audio file** (WAV, MP3, etc.)")
    st.markdown("2. **Click transcribe** to convert speech to text")
    st.markdown("3. **Copy the transcribed text** for use elsewhere")
    
    # File uploader for audio
    uploaded_file = st.file_uploader(
        "Choose an audio file", 
        type=['wav', 'mp3', 'flac', 'aac', 'm4a', 'ogg'],
        help="Upload an audio file to transcribe"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Audio file uploaded: {uploaded_file.name}")
        
        # Show file details
        st.info(f"File size: {len(uploaded_file.getvalue()) / 1024:.1f} KB")
        
        # Audio player
        st.audio(uploaded_file, format='audio/wav')
        
        # Transcribe button
        if st.button("🎯 Transcribe Audio", type="primary"):
            with st.spinner("Transcribing your audio..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Initialize DashScope API key
                    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")
                    
                    # Use DashScope for transcription
                    resp = cast(Any, Recognition).recognize(
                        tmp_path,
                        model="paraformer-realtime-v2",
                        format="wav",
                        sample_rate=16000,
                    )
                    
                    # Clean up temporary file
                    os.unlink(tmp_path)
                    
                    if resp.status_code == HTTPStatus.OK:
                        # Get transcribed text
                        recognized_text = getattr(resp, 'text', None) or getattr(resp, 'output', None)
                        if recognized_text is None and isinstance(resp, dict):
                            recognized_text = resp.get('text') or resp.get('output')
                        
                        if recognized_text:
                            st.success("✅ Transcription completed!")
                            st.session_state.last_transcript = recognized_text
                        else:
                            st.error("❌ No text recognized from audio")
                            
                    else:
                        st.error(f"❌ Transcription failed: {resp.code}: {resp.message}")
                        
                except Exception as e:
                    st.error(f"❌ Error during transcription: {str(e)}")
                    
    else:
        st.info("👆 Please upload an audio file to get started")
    
    # Display the transcribed text
    if "last_transcript" in st.session_state and st.session_state.last_transcript:
        st.markdown("---")
        st.subheader("📝 Transcribed Text")
        st.text_area(
            "Your transcribed text:",
            value=st.session_state.last_transcript,
            height=200,
            help="You can copy this text and use it elsewhere."
        )
        
        # Option to clear the transcript
        if st.button("🗑️ Clear Transcript"):
            del st.session_state.last_transcript
            st.rerun()
    
    # Additional info
    st.markdown("---")
    st.markdown("### 💡 Tips:")
    st.markdown("- For best results, use clear audio with minimal background noise")
    st.markdown("- Supported formats: WAV, MP3, FLAC, AAC, M4A, OGG")
    st.markdown("- Maximum file size: 50MB")
    
    # Note about premium features
    st.markdown("---")
    st.markdown("### 🔧 Note:")
    st.markdown("**Live recording features have been disabled** to avoid premium dependencies.")
    st.markdown("Upload pre-recorded audio files instead.")