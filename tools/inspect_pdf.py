import sys, pdfplumber

path = sys.argv[1]
with pdfplumber.open(path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"=== page {i} size={page.width:.0f}x{page.height:.0f} ===")
        txt = page.extract_text(layout=True, x_density=6.0)
        print(txt)
