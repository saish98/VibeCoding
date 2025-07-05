# Utils package for Tax Advisor API 

import pdfplumber
import re
from typing import Dict, Any

def extract_salary_slip_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts key fields from a salary slip PDF using pdfplumber.
    Returns a dictionary with employee details, earnings, deductions, gross/net salary, etc.
    """
    print("DEBUG: extract_salary_slip_data called")  # Guaranteed debug print
    data = {
        'employee': {},
        'earnings': {},
        'deductions': {},
        'gross_salary': None,
        'net_salary': None,
        'reimbursement': None
    }
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        # Extract employee details
        emp_patterns = {
            'name': r'Name[:\s]+([A-Za-z ]+)',
            'designation': r'Designation[:\s]+([A-Za-z ]+)',
            'department': r'Department[:\s]+([A-Za-z ]+)',
            'location': r'Location[:\s]+([A-Za-z ]+)',
            'bank_name': r'Bank Name[:\s]+([A-Za-z0-9 ]+)',
            'account_no': r'Account No[:\s]+([0-9]+)'
        }
        for key, pat in emp_patterns.items():
            m = re.search(pat, text)
            if m:
                data['employee'][key] = m.group(1).strip()
        # Extract earnings and deductions tables
        earnings = {}
        deductions = {}
        lines = text.splitlines()
        earnings_section = False
        deductions_section = False
        for line in lines:
            if 'Earnings' in line:
                earnings_section = True
                deductions_section = False
                continue
            if 'Deductions' in line:
                deductions_section = True
                earnings_section = False
                print('--- Deductions Section Start ---')  # DEBUG
                continue
            if earnings_section and line.strip():
                m = re.match(r'\d+\s+([A-Za-z ]+)\s+(\d+)', line)
                if m:
                    earnings[m.group(1).strip()] = float(m.group(2))
            if deductions_section and line.strip():
                print(f'DEDUCTION LINE: "{line}"')  # DEBUG
                m = re.match(r'(\d+)?\s*([A-Za-z ]+)\s+(\d+)', line)
                if m:
                    key = m.group(2).strip()
                    value = float(m.group(3))
                    deductions[key] = value
        data['earnings'] = earnings
        data['deductions'] = deductions
        # Extract gross, net, reimbursement
        gross = re.search(r'Gross Salary\s+(\d+)', text)
        if gross:
            data['gross_salary'] = float(gross.group(1))
        # Print every line for debugging
        for idx, line in enumerate(lines):
            print(f"LINE {idx}: {line}")
        # Robust Net Salary extraction: scan lines for 'Net Salary' and extract the number
        for idx, line in enumerate(lines):
            if 'Net Salary' in line:
                print(f'NET SALARY LINE: "{line}"')  # DEBUG
                m = re.search(r'Net Salary.*?([\d,]+)', line)
                if m:
                    data['net_salary'] = float(m.group(1).replace(',', ''))
                    break
                # If not found, try the next line
                elif idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    print(f'NET SALARY NEXT LINE: "{next_line}"')  # DEBUG
                    m2 = re.search(r'([\d,]+)', next_line)
                    if m2:
                        data['net_salary'] = float(m2.group(1).replace(',', ''))
                        break
        reimb = re.search(r'Reimbursement\s+(\d+)', text)
        if reimb:
            data['reimbursement'] = float(reimb.group(1))
    return data 