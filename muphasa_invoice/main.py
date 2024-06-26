import os

from preprocess_convert_type import *
from extract_invoice_features import *
from postprocess_invoice_content import *

def main():
    # working directory
    eml_directory="email_invoice"
    preprocess_path="preprocess"

    # Convert email to png or pdf
    preprocess_email_content(eml_directory, preprocess_path)

    # Extract the text content from png or pdf files
    for converted_file in os.listdir(preprocess_path):
        file_path = os.path.join(preprocess_path, converted_file)
        extracted_text = ''
        if converted_file.endswith('png'):
            extracted_text = extract_text_from_image(file_path)

            if extracted_text == '':
                # print("Extracted text from PNG:", extracted_text)
            # else:
                print("No text found in the image.")
        else:
            extracted_text = extract_text_from_pdf(file_path)
            if extracted_text == '':
                # print("Extracted text from PDF:")
                # print(extracted_text)
            # else:
                print("No text found in the PDF.")
        
        # LLM
        if extracted_text != '':
            feature_text = extract_feature_with_llm(extracted_text)
            if feature_text != '':
                print(f'===== invoice feature text from {converted_file }====')
                print(feature_text)
                # Postprocess
                # invoice_number, invoice_date, invoice_total_amount, money_unit, invoice_bill_to = postprocess_from_llm(feature_text)
            else:
                print('======= Sorry =======')



if __name__ == "__main__":
    main()