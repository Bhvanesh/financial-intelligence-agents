import sys
from pdf_loader import load_pdf_text

path = sys.argv[1]
text = load_pdf_text(path)

print("characters:", len(text))
print("approx words:", len(text.split()))
print("----- first 1500 characters -----")
print(text[:5500])