import streamlit as st
import requests
from typing import Optional
import os
from pydantic import ValidationError
from models import OCRRequest, OCRResponse, ProcessTextRequest, ProcessTextResponse, APIError

# Configuration
GCP_BASE_URL = os.getenv('GCP_BASE_URL', "https://europe-west1-doctor-ai-464910.cloudfunctions.net/ai-icd10-core")
OCR_ENDPOINT = f"{GCP_BASE_URL}/ocr/scan"
PROCESS_ENDPOINT = f"{GCP_BASE_URL}/code/create"
AUTH_TOKEN = os.getenv('API_AUTH_TOKEN')

def get_auth_headers() -> dict:
    """Get authorization headers"""
    if AUTH_TOKEN:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        return headers
    else:
        st.warning("No authentication token found. Please set API_AUTH_TOKEN in your .env file.")
        return {}

def get_mime_type(filename: str) -> str:
    """Get MIME type based on file extension"""
    extension = filename.lower().split('.')[-1]
    mime_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }
    return mime_types.get(extension, 'application/octet-stream')

def call_ocr_api(file_content: bytes, filename: str) -> Optional[str]:
    """Call GCP OCR API with Pydantic validation"""
    try:
        # Create request model
        mime_type = get_mime_type(filename)
        ocr_request = OCRRequest(
            file_content=file_content,
            filename=filename,
            mime_type=mime_type
        )
        
        files = {'file': (ocr_request.filename, ocr_request.file_content, ocr_request.mime_type)}
        headers = get_auth_headers()
        
        response = requests.post(OCR_ENDPOINT, files=files, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                # Validate response with Pydantic
                response_data = response.json()
                ocr_response = OCRResponse(**response_data)
                
                # Check if the API returned an error in the response
                if ocr_response.status == 'error':
                    st.error(f"OCR API Error: {ocr_response.error}")
                    return None
                
                # Handle None case
                if ocr_response.text is None:
                    st.warning("No text was extracted from the response")
                    return ""
                    
                return ocr_response.text
                
            except ValidationError as e:
                st.error(f"OCR Response validation error: {e}")
                return None
        else:
            # Try to parse error response
            try:
                error_data = response.json()
                api_error = APIError(**error_data)
                st.error(f"OCR API Error: {api_error.error}")
            except:
                st.error(f"OCR API Error: {response.status_code} - {response.text}")
            return None
            
    except ValidationError as e:
        st.error(f"OCR Request validation error: {e}")
        return None
    except requests.exceptions.Timeout:
        st.error("OCR API request timed out")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error to OCR API: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error calling OCR API: {str(e)}")
        return None

def call_process_api(text: str) -> Optional[ProcessTextResponse]:
    """Call GCP text processing API with Pydantic validation"""
    try:
        # Create request model
        process_request = ProcessTextRequest(text=text)
        
        headers = get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        response = requests.post(
            PROCESS_ENDPOINT, 
            json=process_request.dict(), 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                # Validate response with Pydantic
                response_data = response.json()
                process_response = ProcessTextResponse(**response_data)
                
                # Check if the API returned an error in the response
                if process_response.status == 'error':
                    st.error(f"Process API Error: {process_response.error}")
                    return None
                
                # Check for success status
                if process_response.status == 'success':
                    return process_response
                else:
                    st.error(f"Process API returned unexpected status: {process_response.status}")
                    return None
                    
            except ValidationError as e:
                st.error(f"Process Response validation error: {e}")
                return None
        else:
            # Try to parse error response
            try:
                error_data = response.json()
                api_error = APIError(**error_data)
                st.error(f"Process API Error: {api_error.error}")
            except:
                st.error(f"Process API error: {response.status_code} - {response.text}")
            return None
            
    except ValidationError as e:
        st.error(f"Process Request validation error: {e}")
        return None
    except Exception as e:
        st.error(f"Error calling process API: {str(e)}")
        return None

def show_text_processing_page():
    st.header("Process file")
    
    # File upload or text input section
    st.subheader("Use either a pdf or copy paste the text")
    
    input_method = st.radio(
        "Choose input method:",
        ["Upload File", "Direct Text Input"]
    )
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose a file for processing",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            help="Upload an image or PDF file to extract text using OCR"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🔍 Run OCR", disabled=uploaded_file is None):
                if uploaded_file is not None:
                    with st.spinner("Processing OCR..."):
                        file_content = uploaded_file.read()
                        ocr_result = call_ocr_api(file_content, uploaded_file.name)
                        
                        if ocr_result:
                            st.session_state.ocr_text = ocr_result
                            st.success("OCR completed successfully!")
                            st.info(f"Text extracted successfully! ({len(ocr_result)} characters)")
                            # Force a rerun to update the text area
                            st.rerun()
                        else:
                            st.error("OCR processing failed - no text extracted")
        
        with col2:
            if uploaded_file:
                st.info(f"File uploaded: {uploaded_file.name}")
    
    # Text area section
    st.subheader("Text Content")
    
    text_content = st.text_area(
        "Text to process:",
        value=st.session_state.ocr_text,
        height=300,
        help="This text will be sent for processing. You can edit it if needed."
    )
    
    # Process text button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Process Text", disabled=not text_content.strip()):
            if text_content.strip():
                with st.spinner("Processing text..."):
                    result = call_process_api(text_content)
                    
                    if result:
                        st.success(f"✅ Text processed successfully!")
                        
                        # Display summary of results
                        diagnoses_count = len(result.diagnoses)
                        procedures_count = len(result.procedures)
                        
                        st.info(f"Found {diagnoses_count} diagnoses and {procedures_count} procedures")
                        
                        # Display request ID if available
                        if result.request_id:
                            st.info(f"Request ID: {result.request_id}")
                        
                        # Display detailed results
                        if diagnoses_count > 0:
                            st.subheader("Diagnoses")
                            for idx, diagnosis in enumerate(result.diagnoses):
                                with st.expander(f"Diagnosis {idx + 1}: {diagnosis.original_text[:50]}..."):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Original Text:** {diagnosis.original_text}")
                                        st.write(f"**English Translation:** {diagnosis.english_translation}")
                                        if diagnosis.chapter:
                                            st.write(f"**Chapter:** {diagnosis.chapter}")
                                    with col2:
                                        st.write(f"**ICD10 Code:** {diagnosis.icd10_code}")
                                        st.write(f"**Confidence:** {diagnosis.confidence}")
                                        if diagnosis.reasoning:
                                            st.write(f"**Reasoning:** {diagnosis.reasoning}")
                        
                        if procedures_count > 0:
                            st.subheader("Procedures")
                            for idx, procedure in enumerate(result.procedures):
                                with st.expander(f"Procedure {idx + 1}: {procedure.original_text[:50]}..."):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Original Text:** {procedure.original_text}")
                                        st.write(f"**English Translation:** {procedure.english_translation}")
                                        if procedure.chapter:
                                            st.write(f"**Chapter:** {procedure.chapter}")
                                    with col2:
                                        st.write(f"**ICD10 Code:** {procedure.icd10_code}")
                                        st.write(f"**Confidence:** {procedure.confidence}")
                                        if procedure.reasoning:
                                            st.write(f"**Reasoning:** {procedure.reasoning}")
                        
                        st.balloons()
                    else:
                        st.error("Text processing failed")