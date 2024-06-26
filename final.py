import os
import email
import re
import cohere
from email import policy
from email.parser import BytesParser
import pdfplumber
from html2image import Html2Image
from PIL import Image
import pytesseract
import tempfile

# Set the tesseract command path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
cohere_api_key = 'CCJW0ByGUVyymGBpyMiwyC0924Y26cJt87W0QFHi'
co = cohere.Client(cohere_api_key)

# Define the paths for the input and output folders
input_folder = 'extract_invoice'
output_folder = 'final_invoice'

# Ensure the output directory exists
os.makedirs(output_folder, exist_ok=True)
# Define the folder to save extracted PDFs and invoice data
extracted_data_folder = "extracted_data"
extract_invoice_folder = "extract_invoice"

# Create output folders if they don't exist
for folder in [extracted_data_folder, extract_invoice_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def extract_invoice_data(file_content):
    prompt = f"""
Extract the following information from the invoice text:

Vendor Name: [name]
Vendor Address: [address]
Vendor Store: [store]
Vendor Tax: [tax]
Transaction Number: [transaction_number]
Transaction Date: [transaction_date]
Transaction Time: [transaction_time]
Terminal Number: [terminal_number]
Invoice/Receipt Number: [invoice_number]
Employee: [employee]
Product Category: [product_category]
SKU: [sku]
Product Quantity: [quantity]
Amount: [amount]
Total: [total]
Tax Amount: [tax_amount]

Invoice Text:
{file_content}
"""

    response = co.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=300,
        temperature=0.5,
        k=0,
        p=0.75
    )

    # Parse the response to extract the relevant data
    output = response.generations[0].text.strip()
    
    data = {
        "Vendor Name": re.search(r'Vendor Name:\s*(.*)', output),
        "Vendor Address": re.search(r'Vendor Address:\s*(.*)', output),
        "Vendor Store": re.search(r'Vendor Store:\s*(.*)', output),
        "Vendor Tax": re.search(r'Vendor Tax:\s*(.*)', output),
        "Transaction Number": re.search(r'Transaction Number:\s*(.*)', output),
        "Transaction Date": re.search(r'Transaction Date:\s*(.*)', output),
        "Transaction Time": re.search(r'Transaction Time:\s*(.*)', output),
        "Terminal Number": re.search(r'Terminal Number:\s*(.*)', output),
        "Invoice/Receipt Number": re.search(r'Invoice/Receipt Number:\s*(.*)', output),
        "Employee": re.search(r'Employee:\s*(.*)', output),
        "Product Category": re.search(r'Product Category:\s*(.*)', output),
        "SKU": re.search(r'SKU:\s*(.*)', output),
        "Product Quantity": re.search(r'Product Quantity:\s*(.*)', output),
        "Amount": re.search(r'Amount:\s*(.*)', output),
        "Total": re.search(r'Total:\s*(.*)', output),
        "Tax Amount": re.search(r'Tax Amount:\s*(.*)', output)
    }

    extracted_data = {key: match.group(1) if match else f'{key} not found' for key, match in data.items()}

    return extracted_data

def extract_html_from_email(email_message):
    """
    Extracts the HTML content from an email message.
    """
    for part in email_message.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True).decode(part.get_content_charset())
    return ""

def process_attachments(msg):
    """
    Save attachments and extract text if they are PDFs.

    Args:
    msg (email.message.Message): The email message object.

    Returns:
    bool: True if PDF attached, False otherwise.
    """
    pdf_attached = False
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        
        filename = part.get_filename()
        if filename:
            filepath = os.path.join(extracted_data_folder, filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                if filename.endswith('.pdf'):
                    pdf_attached = True
                    # Save PDF to the extracted_data folder
                    pdf_path = os.path.join(extracted_data_folder, filename)
                    # Convert PDF to text and save to extract_invoice folder
                    convert_pdf_to_text(pdf_path)
                    
            except Exception as e:
                logging.error(f"Error processing attachment {filename}: {e}")
    return pdf_attached

def convert_pdf_to_text(pdf_path):
    """
    Convert a PDF file to a text file.

    Args:
    pdf_path (str): Path to the PDF file.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_text = ""
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
        # Save extracted text to extract_invoice folder
        filename = os.path.basename(pdf_path)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(extract_invoice_folder, txt_filename)
        with open(txt_path, 'w') as f:
            f.write(extracted_text)
    except Exception as e:
        logging.error(f"Error converting PDF to text: {e}")

def eml_to_png(eml_path):
    """
    Convert an EML file to a PNG image using html2image.

    Args:
    eml_path (str): Path to the EML file.

    Returns:
    str: Path to the generated PNG image.
    """
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    # Extract the HTML content from the forwarded message
    html_content = extract_html_from_email(msg)
    if html_content:
        # Save the HTML content to a temporary file
        temp_html_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        temp_html_file.write(html_content.encode())
        temp_html_file.close()

        # Render the HTML content to an image using html2image
        hti = Html2Image(output_path=extracted_data_folder)
        png_filename = os.path.splitext(os.path.basename(eml_path))[0] + ".png"
        png_path = os.path.join(extracted_data_folder, png_filename)
        hti.screenshot(html_file=temp_html_file.name, save_as=png_filename)

        # Remove the temporary HTML file
        os.unlink(temp_html_file.name)
        return png_path

def png_to_text(png_path):
    """
    Convert a PNG image to text using OCR.

    Args:
    png_path (str): Path to the PNG image.

    Returns:
    str: Extracted text.
    """
    img = Image.open(png_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text

# Define input folder
eml_folder = "files"

# Process each EML file in the input folder
for eml_file in os.listdir(eml_folder):
    if eml_file.endswith(".eml"):
        eml_path = os.path.join(eml_folder, eml_file)
        # Read and parse the EML file
        with open(eml_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
        # Check if there are PDF attachments
        pdf_attached = process_attachments(msg)
        if not pdf_attached:
            # Convert EML to PNG
            png_path = eml_to_png(eml_path)
            # Convert PNG to text and save to extract_invoice folder
            extracted_text = png_to_text(png_path)
            filename = os.path.splitext(eml_file)[0] + ".txt"
            txt_path = os.path.join(extract_invoice_folder, filename)
            with open(txt_path, 'w') as f:
                f.write(extracted_text)
for filename in os.listdir(input_folder):
    if filename.endswith('.txt'):
        with open(os.path.join(input_folder, filename), 'r') as file:
            file_content = file.read()
            extracted_data = extract_invoice_data(file_content)
            
            # Create the output file content
            output_content = "\n".join([f"{key}: {value}" for key, value in extracted_data.items()])
            
            # Save the extracted information in a new file in the output directory
            output_filename = f"{filename.split('.')[0]}_extracted.txt"
            with open(os.path.join(output_folder, output_filename), 'w') as output_file:
                output_file.write(output_content)