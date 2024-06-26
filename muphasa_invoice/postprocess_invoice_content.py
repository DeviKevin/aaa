from dateutil import parser

def postprocess_from_llm(text):
    invoice_features = text.split('\n')
    
    invoice_number = invoice_features[0].split(':')[1][1:]
    invoice_date = invoice_features[1].split(':')[1][1:]
    # Convert str to DateTime python format
    invoice_date = parser.parse(invoice_date)

    invoice_total_amount = invoice_features[2].split(':')[1][1:]
    if invoice_total_amount[0] == '-':
        invoice_total_amount = invoice_total_amount[2:]
    else:
        invoice_total_amount = invoice_total_amount[1:]
    # Check money unit - USD or CAD...
    money_unit = 'USD'
    if ' ' in invoice_total_amount:
        money_unit = invoice_total_amount.split(' ')[1]
        invoice_total_amount = invoice_total_amount.split(' ')[0]
    invoice_bill_to = invoice_features[3].split(':')[1][1:]

    return invoice_number, invoice_date, invoice_total_amount, money_unit, invoice_bill_to