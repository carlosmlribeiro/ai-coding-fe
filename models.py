from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# Request models
class OCRRequest(BaseModel):
    file_content: bytes = Field(..., description="File content in bytes")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type of the file")

class ProcessTextRequest(BaseModel):
    text: str = Field(..., description="Text to process for ICD10 coding")

# Response models
class OCRResponse(BaseModel):
    status: str = Field(..., description="Response status")
    text: Optional[str] = Field(None, description="Extracted text from OCR")
    error: Optional[str] = Field(None, description="Error message if any")

class Diagnosis(BaseModel):
    original_text: str = Field(..., description="Original diagnosis text")
    english_translation: str = Field(..., description="English translation")
    icd10_code: str = Field(..., description="ICD10 code")
    confidence: float = Field(..., description="Confidence score")
    chapter: Optional[str] = Field(None, description="ICD10 chapter")
    reasoning: Optional[str] = Field(None, description="Reasoning for the code")

class Procedure(BaseModel):
    original_text: str = Field(..., description="Original procedure text")
    english_translation: str = Field(..., description="English translation")
    icd10_code: str = Field(..., description="ICD10 code")
    confidence: float = Field(..., description="Confidence score")
    chapter: Optional[str] = Field(None, description="ICD10 chapter")
    reasoning: Optional[str] = Field(None, description="Reasoning for the code")

class ProcessTextResponse(BaseModel):
    status: str = Field(..., description="Response status")
    diagnoses: List[Diagnosis] = Field(default_factory=list, description="List of diagnoses")
    procedures: List[Procedure] = Field(default_factory=list, description="List of procedures")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    error: Optional[str] = Field(None, description="Error message if any")

# Previous requests models
class RequestData(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    type: str = Field(..., description="Request type")
    source: str = Field(..., description="Request source")
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Request status")
    created_at: str = Field(..., description="Creation timestamp")
    reviewed_at: Optional[str] = Field(None, description="Review timestamp")
    reviewer_id: Optional[str] = Field(None, description="Reviewer ID")
    reviewer_comments: Optional[str] = Field(None, description="Reviewer comments")
    input_data: Optional[dict] = Field(None, description="Input data")
    output_data: Optional[dict] = Field(None, description="Output data")
    approved_output: Optional[dict] = Field(None, description="Approved output data")

class RequestsListResponse(BaseModel):
    requests: List[RequestData] = Field(default_factory=list, description="List of requests")
    total: Optional[int] = Field(None, description="Total number of requests")
    page: Optional[int] = Field(None, description="Current page")
    per_page: Optional[int] = Field(None, description="Items per page")

# API Error model
class APIError(BaseModel):
    status: str = Field(..., description="Error status")
    error: str = Field(..., description="Error message")
    code: Optional[int] = Field(None, description="Error code")