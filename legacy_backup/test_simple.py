import streamlit as st

# Set page config
st.set_page_config(page_title="Theta Test", layout="wide")

# Test the streamlit-theta package
try:
    import streamlit_theta
    st.success("✅ streamlit-theta imported successfully!")
    
    st.title("🧪 Simple Theta Test")
    
    # Test each component
    st.header("🎯 Slide Editor Test")
    try:
        streamlit_theta.slide_editor(slides=[], width=600, height=300)
        st.success("✅ Slide editor loaded")
    except Exception as e:
        st.error(f"❌ Slide editor error: {e}")
    
    st.header("📝 Word Editor Test")
    try:
        streamlit_theta.word_editor(content="<p>Hello World</p>", width=600, height=300)
        st.success("✅ Word editor loaded")
    except Exception as e:
        st.error(f"❌ Word editor error: {e}")
    
    st.header("📊 Excel Editor Test")
    try:
        streamlit_theta.excel_editor(data=[["A", "B"], ["1", "2"]], width=600, height=300)
        st.success("✅ Excel editor loaded")
    except Exception as e:
        st.error(f"❌ Excel editor error: {e}")
    
    st.header("📋 CSV Editor Test")
    try:
        streamlit_theta.csv_editor(data=[["Name", "Age"], ["John", "25"]], headers=["Name", "Age"], width=600, height=300)
        st.success("✅ CSV editor loaded")
    except Exception as e:
        st.error(f"❌ CSV editor error: {e}")
    
    st.header("🎵 Audio Editor Test")
    try:
        streamlit_theta.audio_editor(width=600, height=300)
        st.success("✅ Audio editor loaded")
    except Exception as e:
        st.error(f"❌ Audio editor error: {e}")
    
    st.header("🎬 Video Editor Test")
    try:
        streamlit_theta.video_editor(width=600, height=300)
        st.success("✅ Video editor loaded")
    except Exception as e:
        st.error(f"❌ Video editor error: {e}")

except ImportError as e:
    st.error(f"❌ Failed to import streamlit-theta: {e}")
except Exception as e:
    st.error(f"❌ Unexpected error: {e}")

st.markdown("---")
st.info("💡 If all components show '✅ loaded', the package is working correctly!") 