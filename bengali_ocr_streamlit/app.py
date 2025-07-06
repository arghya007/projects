import streamlit as st
from PIL import Image, UnidentifiedImageError
import pytesseract
import os
import io
import zipfile
from pymongo import MongoClient
from bson import ObjectId
import base64
import datetime
import traceback

# ========== Configuration ==========
DATABASE_NAME = "bengali_ocr_db"
COLLECTION_NAME = "documents"

# Linux (Streamlit Cloud) configuration
POPPLER_PATH = "/usr/bin"
# Debug: Show PATH and /usr/bin contents 
st.write("Current PATH:", os.environ.get('PATH', ''))
try:
    bin_contents = os.listdir('/usr/bin')
    st.write("Listing /usr/bin contents (first 10 files):", bin_contents[:10])
    st.write("'pdfinfo' in /usr/bin:", 'pdfinfo' in bin_contents)
    st.write("'tesseract' in /usr/bin:", 'tesseract' in bin_contents)
except Exception as e:
    st.warning(f"Failed to list /usr/bin contents: {str(e)}")
# Check if tesseract and pdfinfo are in /usr/bin
tesseract_path = os.path.join('/usr/bin', 'tesseract')
pdfinfo_path = os.path.join('/usr/bin', 'pdfinfo')
if not os.path.exists(tesseract_path):
    st.warning(f"Tesseract not found at {tesseract_path}. Ensure 'tesseract-ocr' is in packages.txt")
if not os.path.exists(pdfinfo_path):
    st.warning(f"pdfinfo not found at {pdfinfo_path}. Ensure 'poppler-utils' is in packages.txt")
# Warn about inotify limit
st.warning("If app fails to load, check logs for 'inotify watch limit reached'. Minimize repository files or contact Streamlit support.")

MONGO_URI = st.secrets["MONGO_URI"]
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB limit

# ========== Error Handling ==========
def handle_error(e, message="An error occurred"):
    st.error(f"🚨 {message}: {str(e)}")
    st.text(traceback.format_exc())
    st.session_state.update({
        'processed_images': [],
        'current_page': 0,
        'extracted_texts': [],
        'corrected_texts': []
    })

# ========== Database Connection ==========
def get_mongo_client():
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        handle_error(e, "Database connection failed")
        return None

# ========== File Processing ==========
def process_pdf_to_images(file_bytes):
    try:
        from pdf2image import convert_from_bytes
        return convert_from_bytes(
            file_bytes,
            poppler_path=POPPLER_PATH,
            fmt='jpeg',
            dpi=300
        ) or []
    except Exception as e:
        handle_error(e, "PDF processing failed")
        return []

def process_zip_to_images(file_bytes):
    images = []
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zip_ref:
            for f in zip_ref.namelist():
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    with zip_ref.open(f) as file:
                        try:
                            img_bytes = file.read()
                            images.append(Image.open(io.BytesIO(img_bytes)).convert('RGB'))
                        except (UnidentifiedImageError, IOError):
                            continue
        return images
    except Exception as e:
        handle_error(e, "ZIP processing failed")
        return []

def perform_ocr(image, lang='ben'):
    try:
        # Preprocess image for better OCR results
        processed_img = image.convert('L').point(lambda x: 0 if x < 128 else 255)
        
        # Perform OCR with Bengali language
        return pytesseract.image_to_string(
            processed_img,
            lang=lang,
            config='--oem 3 --psm 6'
        ).strip()
    except Exception as e:
        handle_error(e, "OCR failed")
        return ""

# ========== Main UI ==========
def main_ui():
    st.title("📜 Bengali Document OCR System")
    st.markdown("""
    **Upload documents, extract Bengali text, and save corrections to the database**
    """)
    
    # Initialize session state
    st.session_state.setdefault('processed_images', [])
    st.session_state.setdefault('extracted_texts', [])
    st.session_state.setdefault('corrected_texts', [])
    st.session_state.setdefault('current_page', 0)
    st.session_state.setdefault('current_doc_id', None)
    st.session_state.setdefault('connection_valid', False)
    st.session_state.setdefault('upload_error', None)

    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Connection test
        if st.button("🔌 Test Database Connection"):
            client = get_mongo_client()
            if client:
                st.success("Connection successful!")
                st.session_state.connection_valid = True
                client.close()
            else:
                st.session_state.connection_valid = False
                st.error("Connection failed")

        # Document upload section
        st.subheader("📤 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose document", 
            type=["pdf", "zip", "png", "jpg", "jpeg"],
            help="Upload PDFs, ZIP files, or images containing Bengali text"
        )
        
        # File size validation
        if uploaded_file and uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File too large! Max size is {MAX_FILE_SIZE//(1024*1024)}MB")
            st.session_state.upload_error = "FILE_TOO_LARGE"
        elif uploaded_file:
            st.session_state.upload_error = None
            
        doc_name = st.text_input("Document Name:", placeholder="Enter document name")
        doc_author = st.text_input("Author (optional):", placeholder="Document author")

        # Upload button
        upload_disabled = not (
            st.session_state.connection_valid and 
            uploaded_file and 
            doc_name and
            (st.session_state.upload_error is None)
        )
        
        if st.button("🚀 Upload", disabled=upload_disabled, help="Save document to database"):
            handle_file_upload(uploaded_file, doc_name, doc_author)

# ========== File Handling ==========
def handle_file_upload(file, name, author):
    client = get_mongo_client()
    if not client: 
        return

    try:
        # Get file bytes directly from uploader
        file_bytes = file.getvalue()
        
        # Validate file size
        if len(file_bytes) > MAX_FILE_SIZE:
            st.error(f"File size exceeds {MAX_FILE_SIZE//(1024*1024)}MB limit")
            return
            
        document = {
            "metadata": {
                "name": name,
                "author": author or "Unknown",
                "upload_date": datetime.datetime.now(datetime.UTC)
            },
            "file_data": {
                "file_name": file.name,
                "content": base64.b64encode(file_bytes).decode(),
                "type": file.type
            },
            "pages": []
        }

        db = client[DATABASE_NAME]
        result = db[COLLECTION_NAME].insert_one(document)
        
        if result.acknowledged:
            st.session_state.update({
                'current_doc_id': str(result.inserted_id),
                'processed_images': [],
                'extracted_texts': [],
                'corrected_texts': [],
                'current_page': 0,
                'doc_name': name
            })
            st.success("Document uploaded successfully!")
            # Process file content from bytes
            process_file_content(file_bytes, file.type)
    except Exception as e:
        handle_error(e, "Upload failed")
    finally:
        client.close()

def process_file_content(file_bytes, file_type):
    try:
        images = []
        if file_type == "application/pdf":
            images = process_pdf_to_images(file_bytes)
        elif file_type == "application/zip":
            images = process_zip_to_images(file_bytes)
        elif file_type.startswith("image/"):
            images = [Image.open(io.BytesIO(file_bytes))]
        else:
            st.error(f"Unsupported file type: {file_type}")
            return

        if not images:
            st.error("No valid images found in the document")
            return

        st.session_state.processed_images = images
        st.session_state.extracted_texts = [''] * len(images)
        st.session_state.corrected_texts = [''] * len(images)
        st.rerun()  # Updated from experimental_rerun to rerun
    except Exception as e:
        handle_error(e, "File processing failed")

# ========== Document Display ==========
def display_document():
    if not st.session_state.processed_images:
        return

    st.subheader(f"Editing: {st.session_state.get('doc_name', 'Document')}")
    display_navigation()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.header("📄 Document Preview")
        display_image()
    with col2:
        st.header("✏️ Text Editor")
        process_ocr_page()
        display_editor()
        handle_save()

def display_navigation():
    current_page = st.session_state.current_page
    total_pages = len(st.session_state.processed_images)
    
    cols = st.columns([1, 3, 1])
    with cols[0]:
        if st.button("◀ Previous", disabled=current_page == 0):
            st.session_state.current_page = max(0, current_page - 1)
            st.rerun()  # Updated from experimental_rerun to rerun
    with cols[1]:
        st.markdown(f"**Page {current_page + 1} of {total_pages}**")
    with cols[2]:
        if st.button("Next ▶", disabled=current_page >= total_pages - 1):
            st.session_state.current_page = min(total_pages - 1, current_page + 1)
            st.rerun()  # Updated from experimental_rerun to rerun

def display_image():
    try:
        current_page = st.session_state.current_page
        img = st.session_state.processed_images[current_page]
        
        # Resize for better display
        max_size = (800, 800)
        img.thumbnail(max_size, Image.LANCZOS)
        
        st.image(
            img,
            use_column_width=True,
            caption=f"Page {current_page + 1}"
        )
    except Exception as e:
        st.error(f"Error displaying image: {e}")

def display_editor():
    current_page = st.session_state.current_page
    text = st.session_state.corrected_texts[current_page] or st.session_state.extracted_texts[current_page]
    
    new_text = st.text_area(
        "Edit Extracted Text",
        value=text,
        height=400,
        key=f"editor_{current_page}",
        placeholder="OCR results will appear here..."
    )
    
    if new_text != text:
        st.session_state.corrected_texts[current_page] = new_text

# ========== OCR Processing ==========
def process_ocr_page():
    current_page = st.session_state.current_page
    if st.session_state.extracted_texts[current_page]:
        return
    
    with st.spinner("Performing OCR..."):
        try:
            image = st.session_state.processed_images[current_page]
            text = perform_ocr(image)
            st.session_state.extracted_texts[current_page] = text
            if not st.session_state.corrected_texts[current_page]:
                st.session_state.corrected_texts[current_page] = text
        except Exception as e:
            handle_error(e, "OCR processing failed")

# ========== Save Handling ==========
def handle_save():
    if not st.button("💾 Save Document", help="Save all pages to database"):
        return
    
    client = get_mongo_client()
    if not client: 
        return

    try:
        db = client[DATABASE_NAME]
        doc_id = ObjectId(st.session_state.current_doc_id)
        
        pages = [{
            "page_number": i+1,
            "extracted_text": st.session_state.extracted_texts[i],
            "corrected_text": st.session_state.corrected_texts[i],
            "last_updated": datetime.datetime.now(datetime.UTC)
        } for i in range(len(st.session_state.extracted_texts))]

        result = db[COLLECTION_NAME].update_one(
            {"_id": doc_id},
            {"$set": {"pages": pages}}
        )
        
        if result.modified_count > 0:
            st.success("Document saved successfully!")
        else:
            st.warning("Document was not updated")
    except Exception as e:
        handle_error(e, "Save failed")
    finally:
        client.close()

# ========== Run Application ==========
if __name__ == "__main__":
    try:
        main_ui()
        if st.session_state.get('current_doc_id') and st.session_state.get('processed_images'):
            display_document()
    except Exception as e:
        handle_error(e, "Application error")