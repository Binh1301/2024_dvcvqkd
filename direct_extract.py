#!/usr/bin/env python3
"""Direct PDF text extraction and equation searching"""

pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

try:
    # Try PyMuPDF
    import fitz
    doc = fitz.open(pdf_path)
    print(f"PDF Pages: {len(doc)}\n")
    
    # Extract and search for target equations
    equations_found = {}
    all_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        all_text += f"\n\n--- PAGE {page_num + 1} ---\n{text}"
    
    # Search for equations
    target_nums = list(range(3, 12)) + list(range(16, 21)) + [4, 6] + list(range(28, 34))
    
    for eq_num in target_nums:
        # Multiple search patterns
        patterns = [
            f"Eq. {eq_num}", f"Eq.{eq_num}", f"Equation {eq_num}",
            f"({eq_num})", f"eqn {eq_num}", f"expression ({eq_num})"
        ]
        
        for pattern in patterns:
            if pattern in all_text:
                idx = all_text.find(pattern)
                start = max(0, idx - 300)
                end = min(len(all_text), idx + 1000)
                equations_found[f"Eq. {eq_num}"] = all_text[start:end]
                break
    
    # Search for noise terms
    noise_found = {}
    noise_keywords = ["xi", "chi_line", "chi_tot", "homodyne", "heterodyne", "detector noise"]
    
    for keyword in noise_keywords:
        if keyword in all_text:
            idx = all_text.find(keyword)
            start = max(0, idx - 200)
            end = min(len(all_text), idx + 600)
            noise_found[keyword] = all_text[start:end]
    
    # Print results
    print("="*80)
    print("EQUATIONS FOUND:")
    print("="*80)
    for eq_label, content in sorted(equations_found.items()):
        print(f"\n{eq_label}:")
        print("-" * 80)
        print(content[:500])
        print("...\n")
    
    print("\n" + "="*80)
    print("NOISE TERMS FOUND:")
    print("="*80)
    for term, content in sorted(noise_found.items()):
        print(f"\n{term}:")
        print("-" * 80)
        print(content[:400])
        print("...\n")
    
    print(f"\nTotal equations found: {len(equations_found)}")
    print(f"Total noise terms found: {len(noise_found)}")
    
    # Save full text for manual inspection
    with open(r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\extracted_text_full.txt", "w", encoding='utf-8') as f:
        f.write(all_text)
    print(f"\n✓ Full text saved to extracted_text_full.txt")

except Exception as e:
    print(f"ERROR: {e}")
    print(f"Available libraries:")
    try:
        import fitz
        print("  - PyMuPDF: available")
    except:
        print("  - PyMuPDF: NOT available")
    
    try:
        import pdfplumber
        print("  - pdfplumber: available")
    except:
        print("  - pdfplumber: NOT available")
    
    try:
        import pypdf
        print("  - pypdf: available")
    except:
        print("  - pypdf: NOT available")
