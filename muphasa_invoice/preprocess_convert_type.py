import os
import glob
import email
from email import policy
import eml2png
from PIL import Image
import pytesseract
import PyPDF2

# Function to save the attachment and extract text if it's a PDF
def process_attachments(msg, attach_path):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        
        filename = part.get_filename()
        if filename and filename.endswith('.pdf'):
            filepath = os.path.join(attach_path, filename)
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
            return True
    
    return False

# Preprocess email to extract content from invoice
def preprocess_email_content(eml_directory="email_invoice", preprocess_path="preprocess"):
    # Ensure the save path exists
    os.makedirs(preprocess_path, exist_ok=True)

    # Iterate over all .eml files in the directory
    for eml_file in glob.glob(os.path.join(eml_directory, '*.eml')):
        # Check the attachtment file as pdf
        with open(eml_file, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        check_attachment_pdf = process_attachments(msg, preprocess_path)
        
        print("Converting to PNG ====> ", eml_file)
        # Convert email to png
        try:
            png_path = os.path.join(preprocess_path, f"{os.path.basename(eml_file)}.png")
            if  check_attachment_pdf == False:
                with open(png_path, 'wb') as f:
                    f.write(eml2png.to_png(eml_file))
        except:
           print('Error while converting to PNG =====> ', eml_file)
           continue

    return True

# OCR - png to text
pytesseract.pytesseract.tesseract_cmd = pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
def extract_text_from_image(image_path):
  """
  Extracts text from a PNG image using Tesseract OCR.

  Args:
      image_path (str): The path to the PNG image file.

  Returns:
      str: The extracted text from the image, or an empty string if no text is found.
  """

  try:
    # Open the image using Pillow (handles various image formats)
    img = Image.open(image_path)

    # Convert the image to grayscale (improves OCR accuracy)
    gray_img = img.convert('L')

    # Use Tesseract to extract text (config option for better handling of different layouts)
    text = pytesseract.image_to_string(gray_img, config='--psm 6')

    return text.strip()  # Remove any leading/trailing whitespace

  except Exception as e:
    print(f"An error occurred during text extraction: {e}")
    return ""

# Extract text from pdf
def extract_text_from_pdf(pdf_path):
  """
  Extracts text from a PDF file using PyPDF2.

  Args:
      pdf_path (str): The path to the PDF file.

  Returns:
      str: The extracted text from the PDF, or an empty string if extraction fails.
  """

  try:
    # Open the PDF file in binary read mode
    with open(pdf_path, 'rb') as pdf_file:
      pdf_reader = PyPDF2.PdfReader(pdf_file)

      text = ""
      for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        try:
          # Extract text using the appropriate method (handles encrypted PDFs)
          text += page.extract_text() if hasattr(page, 'extract_text') else page.extract_content()
        except:
          print(f"Error extracting text from page {page_num + 1}")

      return text.strip()  # Remove leading/trailing whitespace

  except Exception as e:
    print(f"An error occurred during PDF processing: {e}")
    return ""
