import streamlit as st
import dashscope
from dashscope.audio.asr import Recognition
from http import HTTPStatus
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import av
import io
import os
import tempfile
import shutil
from typing import Any, cast

class AudioRecorder(AudioProcessorBase):
    def __init__(self) -> None:
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.audio_frames.append(frame)
        return frame

    def get_audio(self):
        if not self.audio_frames:
            return None
        
        buffer = io.BytesIO()
        
        first_frame = self.audio_frames[0]
        container = av.open(buffer, mode='w', format='wav')
        stream = container.add_stream('audio', codec='pcm_s16le', rate=first_frame.sample_rate, layout='mono')

        for frame in self.audio_frames:
            packets = stream.encode(frame)  # type: ignore
            container.mux(packets)

        packets = stream.encode(None)  # type: ignore
        container.mux(packets)
        
        container.close()
        buffer.seek(0)
        self.audio_frames.clear()
        return buffer

def speech_to_text_page():
    st.title("🎤 Speech to Text")
    st.write("Record your voice and convert it to text using DashScope Paraformer ASR.")
    
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AudioRecorder,
        media_stream_constraints={"video": False, "audio": True},
    )

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Recording Controls")
        if webrtc_ctx.state.playing:
            st.success("🔴 Recording in progress...")
            st.info("Click 'Stop' in the recorder above to finish recording, then click 'Transcribe Audio' below.")
        else:
            st.info("Click 'Start' in the recorder above to begin recording your voice.")
    
    with col2:
        st.subheader("Transcription")
        if not webrtc_ctx.state.playing:
            if st.button("🎯 Transcribe Audio", type="primary"):
                if webrtc_ctx.audio_processor:
                    audio_buffer = webrtc_ctx.audio_processor.get_audio()
                    if audio_buffer:
                        try:
                            with st.spinner("Transcribing your audio..."):
                                # Initialize DashScope API key (reuse LLM key if set)
                                dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")

                                # DashScope API currently expects a file path, so write to a temp file
                                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                                    shutil.copyfileobj(audio_buffer, tmp_wav)
                                    tmp_wav_path = tmp_wav.name

                                # Call DashScope Paraformer model (synchronous)
                                resp = cast(Any, Recognition).recognize(
                                    tmp_wav_path,
                                    model="paraformer-realtime-v2",
                                    format="wav",
                                    sample_rate=16000,
                                )

                                # Cleanup temp file
                                os.remove(tmp_wav_path)

                                if resp.status_code == HTTPStatus.OK:
                                    # resp may be dict or object; attempt to access 'text' else 'output'
                                    recognized_text = getattr(resp, 'text', None) or getattr(resp, 'output', None)
                                    if recognized_text is None and isinstance(resp, dict):
                                        recognized_text = resp.get('text') or resp.get('output')
                                    if recognized_text:
                                        st.session_state.last_transcript = recognized_text
                                    else:
                                        raise RuntimeError("DashScope response format unexpected")
                                else:
                                    raise RuntimeError(f"DashScope ASR error {resp.code}: {resp.message}")
                        except Exception as e:
                            st.error(f"Error transcribing audio: {e}")
                    else:
                        st.warning("No audio recorded. Please start the recorder and say something.")
        else:
            st.info("Stop recording first, then transcribe.")

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