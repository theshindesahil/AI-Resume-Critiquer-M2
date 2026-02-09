"""
Input validation utilities for Resume Critiquer application.
Validates uploaded files, extracted text, and user inputs.
"""
from typing import Tuple, Optional
from src import config


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate an uploaded file.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message will be empty string
    """
    # Check file exists
    if uploaded_file is None:
        return False, "No file provided"

    # Check file type
    file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
    if file_extension not in config.ALLOWED_FILE_TYPES:
        return False, f"File type '.{file_extension}' not allowed. Allowed types: {', '.join(config.ALLOWED_FILE_TYPES)}"

    # Check file size
    if uploaded_file.size > config.MAX_FILE_SIZE_BYTES:
        size_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File '{uploaded_file.name}' is {size_mb:.1f}MB, exceeds maximum size of {config.MAX_FILE_SIZE_MB}MB"

    # Check minimum file size (resumes shouldn't be empty or tiny)
    min_size = 100  # 100 bytes minimum
    if uploaded_file.size < min_size:
        return False, f"File '{uploaded_file.name}' is too small ({uploaded_file.size} bytes). May be empty or corrupted."

    return True, ""


def validate_file_batch(uploaded_files: list) -> Tuple[bool, str]:
    """
    Validate batch of uploaded files.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uploaded_files:
        return False, "No files uploaded"

    if len(uploaded_files) > config.MAX_FILES_PER_BATCH:
        return False, f"Too many files ({len(uploaded_files)}). Maximum allowed: {config.MAX_FILES_PER_BATCH}"

    # Validate each file
    for file in uploaded_files:
        is_valid, error = validate_uploaded_file(file)
        if not is_valid:
            return False, error

    return True, ""


def validate_extracted_text(text: str, filename: str = "") -> Tuple[bool, str]:
    """
    Validate extracted resume text.

    Args:
        text: Extracted text from resume
        filename: Original filename (for error messages)

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_ref = f" from '{filename}'" if filename else ""

    if not text or not text.strip():
        return False, f"No text could be extracted{file_ref}. File may be empty, corrupted, or scanned image PDF."

    text_length = len(text.strip())

    if text_length < config.MIN_RESUME_TEXT_LENGTH:
        return False, f"Extracted text{file_ref} is too short ({text_length} characters). Minimum: {config.MIN_RESUME_TEXT_LENGTH} characters."

    if text_length > config.MAX_RESUME_TEXT_LENGTH:
        return False, f"Extracted text{file_ref} is too long ({text_length} characters). Maximum: {config.MAX_RESUME_TEXT_LENGTH} characters."

    return True, ""


def validate_chunk_params(chunk_size: int, chunk_overlap: int) -> Tuple[bool, str]:
    """
    Validate chunking parameters.

    Args:
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if chunk_size < config.MIN_CHUNK_SIZE:
        return False, f"Chunk size ({chunk_size}) is too small. Minimum: {config.MIN_CHUNK_SIZE}"

    if chunk_size > config.MAX_CHUNK_SIZE:
        return False, f"Chunk size ({chunk_size}) is too large. Maximum: {config.MAX_CHUNK_SIZE}"

    if chunk_overlap < 0:
        return False, "Chunk overlap cannot be negative"

    if chunk_overlap >= chunk_size:
        return False, f"Chunk overlap ({chunk_overlap}) must be less than chunk size ({chunk_size})"

    return True, ""


def validate_target_role(target_role: Optional[str]) -> Tuple[bool, str]:
    """
    Validate target job role input.

    Args:
        target_role: Target job role string (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Target role is optional, so empty/None is valid
    if not target_role:
        return True, ""

    # Check length
    if len(target_role) > 100:
        return False, "Target job role is too long (max 100 characters)"

    # Check for suspicious content (basic sanity check)
    if target_role.strip() != target_role:
        target_role = target_role.strip()  # Auto-fix whitespace

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and injection attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for use in paths and database
    """
    import re

    # Remove directory separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Keep only alphanumeric, spaces, dots, hyphens, underscores
    filename = re.sub(r'[^a-zA-Z0-9\s\._-]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename or "unnamed_file"
