#!/usr/bin/env python3
"""Strict direct PDF text extraction with equation finding."""
import sys
import json
import re
from pathlib import Path

pdf_path = Path(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf')

result = {
    'import_status': {},
    'coverage_stats': {},
    'best_library': None,
    'best_library_reason': None,
    'equation_findings': {},
    'variable_definition_snippets': {},
    'ocr_used': False,
    'ocr_uncertain_lines': []
}

combined_text = None
text_by_page = None

# === TRY FITZ (PyMuPDF) ===
try:
    import fitz
    result['import_status']['fitz'] = 'available'
    try:
        doc = fitz.open(str(pdf_path))
        text_by_page = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            text_by_page.append(text)
        doc.close()
        
        total_pages = len(text_by_page)
        non_empty = sum(1 for t in text_by_page if t.strip())
        total_chars = sum(len(t) for t in text_by_page)
        has_text = total_chars > 0
        result['coverage_stats']['fitz'] = {
            'total_pages': total_pages,
            'non_empty_pages': non_empty,
            'total_chars': total_chars,
            'has_text': has_text
        }
        if has_text:
            result['best_library'] = 'fitz'
            result['best_library_reason'] = f'fitz extracted {total_chars} chars from {non_empty}/{total_pages} pages'
            combined_text = '\n'.join(text_by_page)
    except Exception as e:
        result['import_status']['fitz'] = f'error: {str(e)[:100]}'
except ImportError:
    result['import_status']['fitz'] = 'not_installed'

# === TRY PDFPLUMBER ===
if not result['best_library']:
    try:
        import pdfplumber
        result['import_status']['pdfplumber'] = 'available'
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                text_by_page = []
                for page in pdf.pages:
                    text = page.extract_text() or ''
                    text_by_page.append(text)
            
            total_pages = len(text_by_page)
            non_empty = sum(1 for t in text_by_page if t.strip())
            total_chars = sum(len(t) for t in text_by_page)
            has_text = total_chars > 0
            result['coverage_stats']['pdfplumber'] = {
                'total_pages': total_pages,
                'non_empty_pages': non_empty,
                'total_chars': total_chars,
                'has_text': has_text
            }
            if has_text:
                result['best_library'] = 'pdfplumber'
                result['best_library_reason'] = f'pdfplumber extracted {total_chars} chars from {non_empty}/{total_pages} pages'
                combined_text = '\n'.join(text_by_page)
        except Exception as e:
            result['import_status']['pdfplumber'] = f'error: {str(e)[:100]}'
    except ImportError:
        result['import_status']['pdfplumber'] = 'not_installed'

# === TRY PYPDF ===
if not result['best_library']:
    try:
        import pypdf
        result['import_status']['pypdf'] = 'available'
        try:
            with open(str(pdf_path), 'rb') as f:
                reader = pypdf.PdfReader(f)
                text_by_page = []
                for page in reader.pages:
                    text = page.extract_text()
                    text_by_page.append(text)
            
            total_pages = len(text_by_page)
            non_empty = sum(1 for t in text_by_page if t.strip())
            total_chars = sum(len(t) for t in text_by_page)
            has_text = total_chars > 0
            result['coverage_stats']['pypdf'] = {
                'total_pages': total_pages,
                'non_empty_pages': non_empty,
                'total_chars': total_chars,
                'has_text': has_text
            }
            if has_text:
                result['best_library'] = 'pypdf'
                result['best_library_reason'] = f'pypdf extracted {total_chars} chars from {non_empty}/{total_pages} pages'
                combined_text = '\n'.join(text_by_page)
        except Exception as e:
            result['import_status']['pypdf'] = f'error: {str(e)[:100]}'
    except ImportError:
        result['import_status']['pypdf'] = 'not_installed'

# === TRY PYPDF2 ===
if not result['best_library']:
    try:
        import PyPDF2
        result['import_status']['PyPDF2'] = 'available'
        try:
            with open(str(pdf_path), 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_by_page = []
                for page in reader.pages:
                    text = page.extract_text()
                    text_by_page.append(text)
            
            total_pages = len(text_by_page)
            non_empty = sum(1 for t in text_by_page if t.strip())
            total_chars = sum(len(t) for t in text_by_page)
            has_text = total_chars > 0
            result['coverage_stats']['PyPDF2'] = {
                'total_pages': total_pages,
                'non_empty_pages': non_empty,
                'total_chars': total_chars,
                'has_text': has_text
            }
            if has_text:
                result['best_library'] = 'PyPDF2'
                result['best_library_reason'] = f'PyPDF2 extracted {total_chars} chars from {non_empty}/{total_pages} pages'
                combined_text = '\n'.join(text_by_page)
        except Exception as e:
            result['import_status']['PyPDF2'] = f'error: {str(e)[:100]}'
    except ImportError:
        result['import_status']['PyPDF2'] = 'not_installed'

# === SEARCH EQUATIONS AND VARIABLES ===
if combined_text and text_by_page:
    # Map text back to pages for accurate page numbering
    page_char_positions = []
    char_pos = 0
    for page_text in text_by_page:
        page_char_positions.append((char_pos, char_pos + len(page_text)))
        char_pos += len(page_text) + 1  # +1 for newline separator
    
    def get_page_number(char_index):
        """Get 1-based page number from character position."""
        for page_idx, (start, end) in enumerate(page_char_positions):
            if start <= char_index < end:
                return page_idx + 1
        return None
    
    # Equation patterns
    eq_patterns = {
        '3': r'(?:Eq\.|Equation)\s*\(\s*3\s*\)',
        '4': r'(?:Eq\.|Equation)\s*\(\s*4\s*\)',
        '5': r'(?:Eq\.|Equation)\s*\(\s*5\s*\)',
        '6': r'(?:Eq\.|Equation)\s*\(\s*6\s*\)',
        '7': r'(?:Eq\.|Equation)\s*\(\s*7\s*\)',
        '8': r'(?:Eq\.|Equation)\s*\(\s*8\s*\)',
        '9': r'(?:Eq\.|Equation)\s*\(\s*9\s*\)',
        '10': r'(?:Eq\.|Equation)\s*\(\s*10\s*\)',
        '11': r'(?:Eq\.|Equation)\s*\(\s*11\s*\)',
        '16': r'(?:Eq\.|Equation)\s*\(\s*16\s*\)',
        '17': r'(?:Eq\.|Equation)\s*\(\s*17\s*\)',
        '18': r'(?:Eq\.|Equation)\s*\(\s*18\s*\)',
        '19': r'(?:Eq\.|Equation)\s*\(\s*19\s*\)',
        '20': r'(?:Eq\.|Equation)\s*\(\s*20\s*\)',
        '28': r'(?:Eq\.|Equation)\s*\(\s*28\s*\)',
        '29': r'(?:Eq\.|Equation)\s*\(\s*29\s*\)',
        '30': r'(?:Eq\.|Equation)\s*\(\s*30\s*\)',
        '31': r'(?:Eq\.|Equation)\s*\(\s*31\s*\)',
        '32': r'(?:Eq\.|Equation)\s*\(\s*32\s*\)',
        '33': r'(?:Eq\.|Equation)\s*\(\s*33\s*\)'
    }
    
    for eq_num, pattern in eq_patterns.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            page_num = get_page_number(match.start())
            start = max(0, match.start() - 100)
            end = min(len(combined_text), match.end() + 250)
            snippet = combined_text[start:end].strip()
            snippet = snippet.replace('\n', ' ')[:400]
            result['equation_findings'][f'Eq.({eq_num})'] = {
                'page': page_num,
                'snippet': snippet
            }
        else:
            result['equation_findings'][f'Eq.({eq_num})'] = 'UNVERIFIABLE'
    
    # Variable definition patterns
    var_patterns = {
        'xi': r'[ξ\s]xi\s*[=:]',
        'chi_line': r'χ[_\s]*line',
        'chi_tot': r'χ[_\s]*tot',
        'homodyne_detector': r'homodyne\s+detector',
        'heterodyne_detector': r'heterodyne\s+detector'
    }
    
    for var, pattern in var_patterns.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            page_num = get_page_number(match.start())
            start = max(0, match.start() - 150)
            end = min(len(combined_text), match.end() + 200)
            snippet = combined_text[start:end].strip()
            snippet = snippet.replace('\n', ' ')[:400]
            result['variable_definition_snippets'][var] = {
                'page': page_num,
                'snippet': snippet
            }
        else:
            result['variable_definition_snippets'][var] = 'UNVERIFIABLE'

print(json.dumps(result, indent=2, ensure_ascii=False))
