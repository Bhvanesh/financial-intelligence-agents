from pypdf import PdfReader

def load_pdf_text(path: str)-> str:
    reader = PdfReader(path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"[page {number}]\n{text}")
        #page 1
        #text of the page
    return "\n".join(pages)
 