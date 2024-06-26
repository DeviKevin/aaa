import os
import email
from email import policy
import pdfplumber
import glob
import cohere
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your Cohere API key from environment variables
# cohere_api_key = os.getenv('COHERE_API_KEY')
# if not cohere_api_key:
#     logging.error('Cohere API key not found. Set the COHERE_API_KEY environment variable.')
#     exit(1)
cohere_api_key = 'CCJW0ByGUVyymGBpyMiwyC0924Y26cJt87W0QFHi'
co = cohere.Client(cohere_api_key)

def extract_email_body(msg):
    """
    Extract the body from an email message.

    Args:
    msg (email.message.Message): The email message object.

    Returns:
    str: The email body as a string.
    """
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()
    return ""

def process_attachments(msg, save_path):
    """
    Save attachments and extract text if they are PDFs.

    Args:
    msg (email.message.Message): The email message object.
    save_path (str): The directory path to save attachments.

    Returns:
    str: Extracted text from PDFs.
    """
    extracted_text = ""
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        
        filename = part.get_filename()
        if filename:
            filepath = os.path.join(save_path, filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                if filename.endswith('.pdf'):
                    with pdfplumber.open(filepath) as pdf:
                        for page in pdf.pages:
                            extracted_text += page.extract_text() + "\n"
            except Exception as e:
                logging.error(f"Error processing attachment {filename}: {e}")
    return extracted_text

def extract_information_with_gpt(text):
    
    prompt = f"""
    Give me all features like 
    Vendor Name
    Vendor Address
    Vendor Store
    Vendor Tax
    Transaction Number
    Transaction Date
    Transaction Time
    Terminal Number
    Invoice/Receipt Number
    Employee
    Product Category
    SKU
    Product Quantity
    Amount
    Total
    Tax Amount
    from below invoice without explanation.
    If specified feature is nothing, give N/A value.
    Invoice text:
    {text}

    Information:
    """
    try:
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=150,
            temperature=0.5,
            k=0,
            p=1,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        return response.generations[0].text.strip()
    except Exception as e:
        logging.error(f"Error extracting information with GPT: {e}")
        return ""

# Directory containing .eml files
eml_directory = 'files'  # Change this to your directory path

# Path to save attachments and extracted information
save_path = 'attachments'  # Change this to your desired path

# Ensure the save path exists
os.makedirs(save_path, exist_ok=True)

# Iterate over all .eml files in the directory
for eml_file in glob.glob(os.path.join(eml_directory, '*.eml')):
    try:
        with open(eml_file, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        
        # Extract the body of the email
        email_body = extract_email_body(msg)
        
        # Process attachments and extract text from PDFs
        pdf_text = process_attachments(msg, save_path)
        
        # Combine the email body and PDF text
        combined_text = f"Email Body:\n{email_body}\n\nPDF Content:\n{pdf_text}"
        
        # Save extracted data to a file
        output_path = os.path.join(save_path, f"{os.path.basename(eml_file)}_extracted.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        # Extract information using GPT
        extracted_info = extract_information_with_gpt(combined_text)
        
        # Save the extracted information to a new file
        info_output_path = os.path.join(save_path, f"{os.path.basename(eml_file)}_info.txt")
        with open(info_output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_info)
        
        logging.info(f"Processed {eml_file} and saved extracted information to {info_output_path}")
    except Exception as e:
        logging.error(f"Error processing {eml_file}: {e}")