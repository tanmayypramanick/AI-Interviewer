import fitz  # PyMuPDF
import logging
from io import BytesIO
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_bytes):
    """
    Extract text from a PDF file using PyMuPDF, with OCR fallback for image-based PDFs.
    Args:
        pdf_bytes (bytes): Raw PDF file bytes.
    Returns:
        str: Extracted text, or empty string if extraction fails.
    """
    try:
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        
        # Iterate through pages
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
                logger.debug(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
            else:
                logger.debug(f"Page {page_num + 1}: No text found")
                
                # Try OCR if available and no text extracted
                if OCR_AVAILABLE:
                    try:
                        # Convert page to image
                        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
                        img = Image.open(BytesIO(pix.tobytes("png")))
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip():
                            text += ocr_text + "\n"
                            logger.debug(f"Page {page_num + 1}: OCR extracted {len(ocr_text)} characters")
                        else:
                            logger.debug(f"Page {page_num + 1}: OCR found no text")
                    except Exception as ocr_e:
                        logger.error(f"Page {page_num + 1}: OCR failed: {str(ocr_e)}")
        
        pdf_document.close()
        
        if not text.strip():
            logger.error("No text extracted from PDF")
            return ""
        
        logger.debug(f"Total extracted text: {len(text)} characters")
        return text.strip()
    
    except fitz.fitz.DocumentError as e:
        logger.error(f"PDF document error: {str(e)}")
        if "password" in str(e).lower():
            return ""  # Specific handling for password-protected PDFs
        return ""
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return ""

def chunk_text(text, max_chunk_size=512):
    """
    Split text into chunks for indexing.
    """
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    logger.debug(f"Created {len(chunks)} chunks")
    return chunks

def create_index(chunks):
    """
    Create a FAISS index for text chunks.
    """
    if not chunks:
        return None, []
    
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(chunks, convert_to_numpy=True)
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        logger.debug(f"Created FAISS index with {len(chunks)} chunks")
        return index, chunks
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        return None, []

def search_similar(query, index, chunks, model, top_k=3):
    """
    Search for similar text chunks.
    """
    if not index or not chunks:
        return []
    
    try:
        query_embedding = model.encode([query], convert_to_numpy=True)
        distances, indices = index.search(query_embedding, top_k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(chunks):
                results.append({"text": chunks[idx], "distance": float(distance)})
        
        logger.debug(f"Search returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return []

def extract_keywords(text):
    """
    Extract keywords from text.
    """
    if not text:
        return []
    
    try:
        # Simple keyword extraction (extend as needed)
        words = re.findall(r'\w+', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        logger.debug(f"Extracted {len(keywords)} keywords")
        return keywords[:20]  # Limit to top 20
    except Exception as e:
        logger.error(f"Keyword extraction failed: {str(e)}")
        return []