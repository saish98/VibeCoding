# Utils package for Tax Advisor API 

import pdfplumber
import re
from typing import Dict, Any

def extract_salary_slip_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts key fields from a salary slip PDF using pdfplumber.
    Returns a dictionary with employee details, earnings, deductions, gross/net salary, etc.
    """
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
                continue
            if earnings_section and line.strip():
                m = re.match(r'\d+\s+([A-Za-z ]+)\s+(\d+)', line)
                if m:
                    earnings[m.group(1).strip()] = float(m.group(2))
            if deductions_section and line.strip():
                m = re.match(r'\d+\s+([A-Za-z ]+)\s+(\d+)', line)
                if m:
                    deductions[m.group(1).strip()] = float(m.group(2))
        data['earnings'] = earnings
        data['deductions'] = deductions
        # Extract gross, net, reimbursement
        gross = re.search(r'Gross Salary\s+(\d+)', text)
        if gross:
            data['gross_salary'] = float(gross.group(1))
        net = re.search(r'Net Salary\s+(\d+)', text)
        if net:
            data['net_salary'] = float(net.group(1))
        reimb = re.search(r'Reimbursement\s+(\d+)', text)
        if reimb:
            data['reimbursement'] = float(reimb.group(1))
    return data 