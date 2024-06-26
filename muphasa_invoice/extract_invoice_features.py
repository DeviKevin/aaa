import cohere

def extract_feature_with_llm(text):
    cohere_api_key = 'CCJW0ByGUVyymGBpyMiwyC0924Y26cJt87W0QFHi'
    co = cohere.Client(cohere_api_key)

    # prompt = """I want you to act as a data annotator. 
    #     Your task is to put the extracted text from the energy invoice into the specified json format. 
    #     You should only change the "input" and output the desired json format.
    #     The "charge_period_end_date" should always be later than the "charge_period_start_date". 
    #     If you cannot find one of the keys in the extracted text, simply do not output the whole line for it. (e.g. if you cannot find the "mpan" key, please do not output "mpan": "",).
    #     Never output "any key": "not found" or "any key": "null" if you did not find it in the extracted text.
    #     The desired format:
    #     {
    #         "vendor_name": "input", # only the vendor/supplier name, do not input the "Vendor Name" label
    #         "invoice_date": "input", # input the date of the invoice in the format dd/mm/yyyy (e.g. 01/01/2021). Note that the extracted text may have a different format, but you should enter it as dd/mm/yyyy.
    #         "invoice_number": "input", # only the invoice number, do not input the "Invoice Number" label
    #         "total_amount": "input", # should be a number with 2 decimal places (e.g. 12,345.67), do not input the currency symbol.
    #         "charge_period_start_date": "input", # input the date of the invoice in the format dd/mm/yyyy (e.g. 01/01/2021). Note that the extracted text may have a different format, but you should enter it as dd/mm/yyyy.
    #         "charge_period_end_date": "input", # input the date of the invoice in the format dd/mm/yyyy (e.g. 01/01/2021). Note that the extracted text may have a different format, but you should enter it as dd/mm/yyyy.
    #         "mpan": "input", # do not input more than 13 characters which are usually only digits (e.g. "1234567890123"), it may contain spaces or dashes and be broken down into groups of 2, 4, 4 and 3 characters.
    #         "account_number": "input" # only the account number, do not input the "Account Number" label
    #     }
    #     The extracted text:""" + text
    
    prompt = f"""
    Extract the following information and the item names and their corresponding costs from the invoice text below without explanation:
    - Vendor Details
    - Vendor Name
    - Vendor Address
    - Vendor Store#
    - Vendor Tax#
    - Transaction Details
    - Transaction Number
    - Transaction Date
    - Transaction Time
    - Terminal Number
    - Invoice/Receipt Number
    - Employee#
    - Purchase Details
    - Product Category
    - SKU
    - Product Quantity
    - Amount
    - Total
    - Tax Amount
    - Payment Details
    - Payment Method
    - Payment Reference# 

    Invoice text:
    {text}

    Information:
    """

    # OpenAI API
    # response = openai.Completion.create(
    #     engine="gpt-3.5-turbo-instruct",
    #     prompt=prompt,
    #     max_tokens=150,
    #     temperature=0
    # )    
    # return response.choices[0].text.strip()
    
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

    extracted_info = response.generations[0].text.strip()
    return extracted_info