import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APP_ACCESS_TOKEN = os.getenv('APP_ACCESS_TOKEN')

def check_authentication():
    """Check if user is authenticated"""
    if not APP_ACCESS_TOKEN:
        st.error("⚠️ Application access token not configured. Please contact the administrator.")
        st.stop()
    
    # Check if user is already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Show authentication form
    st.title("🔐 Authentication Required")
    st.write("Please enter the access token to continue:")
    
    with st.form("auth_form"):
        token_input = st.text_input("Access Token:", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if token_input == APP_ACCESS_TOKEN:
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Invalid access token. Please try again.")
                return False
    
    return False

def show_logout_button():
    """Show logout button in sidebar"""
    if st.session_state.get('authenticated', False):
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()