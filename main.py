import streamlit as st
from dotenv import load_dotenv
from previous_requests import show_previous_requests_page
from process_new_file import show_text_processing_page
from auth import check_authentication, show_logout_button

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="AI ICD10 Coding Testing",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""

def main():
    # Check authentication first
    if not check_authentication():
        return
    
    st.title("📄 AI ICD10 Coding Testing")
    
    # Show logout button in sidebar
    show_logout_button()
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["📝 Process new file", "📋 Previous Requests"]
    )
    
    if page == "📝 Process new file":
        show_text_processing_page()
    else:
        show_previous_requests_page()

if __name__ == "__main__":
    main()