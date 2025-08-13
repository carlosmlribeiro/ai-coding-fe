import streamlit as st
import requests
from typing import Optional
import os
from pydantic import ValidationError
from models import RequestsListResponse, RequestData, APIError

# Configuration
GCP_BASE_URL = os.getenv('GCP_BASE_URL', "http://127.0.0.1:8088")
REQUESTS_ENDPOINT = f"{GCP_BASE_URL}/code/list"
AUTH_TOKEN = os.getenv('API_AUTH_TOKEN')

def get_auth_headers() -> dict:
    """Get authorization headers"""
    if AUTH_TOKEN:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        return headers
    else:
        st.warning("No authentication token found. Please set API_AUTH_TOKEN in your .env file.")
        return {}

def get_requests_data(request_id_filter: str = "") -> Optional[RequestsListResponse]:
    """Get previous requests data with Pydantic validation"""
    try:
        params = {}
        if request_id_filter:
            params['request_id'] = request_id_filter
        
        headers = get_auth_headers()
        
        response = requests.get(REQUESTS_ENDPOINT, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                # Validate response with Pydantic
                response_data = response.json()
                requests_response = RequestsListResponse(**response_data)
                return requests_response
                
            except ValidationError as e:
                st.error(f"Requests response validation error: {e}")
                st.error("Raw response data:")
                st.json(response.json())
                return None
        else:
            # Try to parse error response
            try:
                error_data = response.json()
                api_error = APIError(**error_data)
                st.error(f"Requests API Error: {api_error.error}")
            except:
                st.error(f"Requests API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error fetching requests: {str(e)}")
        return None

def show_previous_requests_page():
    st.header("Previous Requests")
    
    # Filter section
    st.subheader("Filter Requests")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        request_id_filter = st.text_input(
            "Filter by Request ID:",
            placeholder="Enter request ID to filter...",
            help="Leave empty to show all requests"
        )
    
    with col2:
        st.write("")  # Spacing
        refresh_button = st.button("🔄 Refresh Data")
    
    # Fetch and display data
    if refresh_button or st.session_state.get('auto_refresh', True):
        with st.spinner("Fetching requests..."):
            requests_response = get_requests_data(request_id_filter)
            
            if requests_response is not None:
                requests_data = requests_response.requests
                
                if len(requests_data) == 0:
                    st.info("No requests found matching the criteria.")
                else:
                    # Display summary
                    st.subheader(f"Found {len(requests_data)} request(s)")
                    
                    # Display pagination info if available
                    if requests_response.total:
                        st.info(f"Total requests: {requests_response.total}")
                    
                    # Display each request
                    for idx, request in enumerate(requests_data):
                        # Parse timestamps
                        created_at = request.created_at
                        reviewed_at = request.reviewed_at or 'Not reviewed'
                        
                        # Create expander title with key info
                        title = f"Request ID: {request.request_id} | Status: {request.status} | Created: {created_at}"
                        
                        with st.expander(title):
                            # Request metadata
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Type:** {request.type}")
                                st.write(f"**Source:** {request.source}")
                                st.write(f"**Agent ID:** {request.agent_id}")
                            
                            with col2:
                                st.write(f"**Status:** {request.status}")
                                st.write(f"**Created At:** {created_at}")
                                st.write(f"**Reviewed At:** {reviewed_at}")
                            
                            with col3:
                                st.write(f"**Reviewer ID:** {request.reviewer_id or 'N/A'}")
                                if request.reviewer_comments:
                                    st.write(f"**Reviewer Comments:** {request.reviewer_comments}")
                            
                            st.divider()
                            
                            # Input and Output Data
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("Input Data")
                                if request.input_data:
                                    # Display input text if available
                                    if isinstance(request.input_data, dict) and 'text' in request.input_data:
                                        st.write("**Input Text:**")
                                        st.write(request.input_data.get('text', ''))
                                    else:
                                        st.json(request.input_data)
                                else:
                                    st.write("No input data available")
                            
                            with col2:
                                st.subheader("Output Data")
                                if request.output_data:
                                    # Display structured output if available
                                    if isinstance(request.output_data, dict):
                                        # Show diagnoses if available
                                        if 'diagnoses' in request.output_data:
                                            st.write(f"**Diagnoses:** {len(request.output_data.get('diagnoses', []))}")
                                            for diag_idx, diagnosis in enumerate(request.output_data.get('diagnoses', [])):
                                                main_prefix = "MAIN " if diagnosis.get('is_main_diagnosis') is True else ""
                                                with st.expander(f"{main_prefix}Diagnosis {diag_idx + 1}: {diagnosis.get('text', 'Unknown')[:30]}..."):
                                                    icd10 = diagnosis.get('icd10_code', '')
                                                    document = diagnosis.get('document', '')
                                                    st.write(f"**Code:** {icd10} - {document}")
                                                    if diagnosis.get('pna') is True:
                                                        st.write("**PNA:** ✅")
                                        
                                        # Show procedures if available
                                        if 'procedures' in request.output_data:
                                            st.write(f"**Procedures:** {len(request.output_data.get('procedures', []))}")
                                            for proc_idx, procedure in enumerate(request.output_data.get('procedures', [])):
                                                with st.expander(f"Procedure {proc_idx + 1}: {procedure.get('text', 'Unknown')[:30]}..."):
                                                    icd10 = procedure.get('icd10_code', '')
                                                    document = procedure.get('document', '')
                                                    st.write(f"**Code:** {icd10} - {document}")
                                        
                                        # Show raw JSON if no structured data
                                        if 'diagnoses' not in request.output_data and 'procedures' not in request.output_data:
                                            st.json(request.output_data)
                                    else:
                                        st.json(request.output_data)
                                else:
                                    st.write("No output data available")
                            
                            # Approved Output (if different from output_data)
                            if request.approved_output and request.approved_output != request.output_data:
                                st.divider()
                                st.subheader("Approved Output")
                                if isinstance(request.approved_output, dict):
                                    # Show approved diagnoses if available
                                    if 'diagnoses' in request.approved_output:
                                        st.write(f"**Approved Diagnoses:** {len(request.approved_output.get('diagnoses', []))}")
                                        for diag_idx, diagnosis in enumerate(request.approved_output.get('diagnoses', [])):
                                            with st.expander(f"Approved Diagnosis {diag_idx + 1}: {diagnosis.get('text', 'Unknown')[:30]}..."):
                                                st.write(f"**Original Text:** {diagnosis.get('text', 'N/A')}")
                                                icd10 = diagnosis.get('icd10_code', '')
                                                document = diagnosis.get('document', '')
                                                st.write(f"**Code:** {icd10} - {document}")
                                                if diagnosis.get('pna') is True:
                                                    st.write("**PNA:** ✅")
                                    
                                    # Show approved procedures if available
                                    if 'procedures' in request.approved_output:
                                        st.write(f"**Approved Procedures:** {len(request.approved_output.get('procedures', []))}")
                                        for proc_idx, procedure in enumerate(request.approved_output.get('procedures', [])):
                                            with st.expander(f"Approved Procedure {proc_idx + 1}: {procedure.get('text', 'Unknown')[:30]}..."):
                                                st.write(f"**Original Text:** {procedure.get('text', 'N/A')}")
                                                icd10 = procedure.get('icd10_code', '')
                                                document = procedure.get('document', '')
                                                st.write(f"**Code:** {icd10} - {document}")
                                    
                                    # Show raw JSON if no structured data
                                    if 'diagnoses' not in request.approved_output and 'procedures' not in request.approved_output:
                                        st.json(request.approved_output)
                                else:
                                    st.json(request.approved_output)
            else:
                st.error("Failed to fetch requests data")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox(
        "Auto-refresh on page load",
        value=st.session_state.get('auto_refresh', True)
    )