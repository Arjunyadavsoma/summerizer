import os
import easyocr
import streamlit as st
from groq import Groq
from docx import Document
from pdf2image import convert_from_path
import tempfile
import glob

# Initialize EasyOCR and Groq API client
reader = easyocr.Reader(['en'])
os.environ["GROQ_API_KEY"] = "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"  # Replace with your actual API key
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Function to extract text from an image
def extract_text_from_image(image_path):
    try:
        text = reader.readtext(image_path)
        return '\n'.join([t[1] for t in text])
    except Exception as e:
        return f"Error processing image: {str(e)}"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(
                pdf_path,
                dpi=200,  # Lower DPI for faster processing
                output_folder=temp_dir,
                fmt='jpeg',
                thread_count=4,
                use_pdftocairo=True,
                output_file='page'
            )

            extracted_text = []
            image_files = sorted(glob.glob(os.path.join(temp_dir, '*.jpg')))

            for i, image_path in enumerate(image_files):
                text = extract_text_from_image(image_path)
                extracted_text.append(f"--- Page {i+1} ---\n{text}")

            return '\n\n'.join(extracted_text)
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"

# Function to extract text from TXT
def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error processing TXT: {str(e)}"

# Determine file type based on extension
def get_file_type(file_path):
    extension = file_path.split('.')[-1].lower()
    type_mapping = {
        'pdf': 'pdf',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'jfif': 'image',
        'webp': 'image',
        'bmp': 'image',
        'docx': 'docx',
        'txt': 'txt'
    }
    return type_mapping.get(extension, 'unknown')

# Main function to extract text
def extract_text(file_path):
    file_type = get_file_type(file_path)

    if file_type == 'unknown':
        return "Unsupported file type. Supported formats are: PDF, PNG, JPG, JPEG, JFIF, WebP, BMP, DOCX, and TXT"

    extraction_functions = {
        'image': extract_text_from_image,
        'pdf': extract_text_from_pdf,
        'docx': extract_text_from_docx,
        'txt': extract_text_from_txt
    }

    return extraction_functions[file_type](file_path)

# Function to summarize extracted text
def summarize_text(text):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": text}],
            model="llama3-8b-8192"  # Choose an appropriate model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error summarizing text: {str(e)}"

# Streamlit app layout
def main():
    st.title("Text Summarizer")

    # File uploader
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg", "docx", "txt"])

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.read())
            file_path = temp_file.name
        
        st.write("File Uploaded Successfully!")
        
        # Extract text from the file
        extracted_text = extract_text(file_path)
        st.subheader("Extracted Text:")
        st.text_area("Extracted Text", extracted_text, height=300)

        # Summarize the extracted text using Groq
        summary = summarize_text(extracted_text)
        st.subheader("Summary:")
        st.text_area("Summary", summary, height=300)

if __name__ == "__main__":
    main()
