from pypdf import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import openpyxl
import groq

client = groq.Client(api_key="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")

# === Extract PDF Text ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# === Extract DOCX Text ===
def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

# === Generate Section-wise Questions ===
def generate_section_questions(section, prompt, requirement_text):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"""Given the following business requirement, generate 3-5 detailed, section-specific questions for the '{section}' section:

{requirement_text}
"""}
    ]
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.3,
        max_tokens=1024
    )
    return response.choices[0].message.content

# === Save Questions to Excel (as BytesIO) ===
def save_questionnaire_to_excel(questions_dict):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Questions"
    ws.append(["Section", "Questions", "Answers"])
    
    for section, questions in questions_dict.items():
        for q in questions.strip().split("\n"):
            if q.strip():
                ws.append([section, q.strip(), ""])  # Leave answers blank

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream

# === Generate BRD Section from Q&A ===
def generate_brd_section(section, qna_text):
    messages = [
        {"role": "system", "content": f"You're a BRD expert writing the '{section}' section."},
        {"role": "user", "content": f"""Based on this Q&A, generate a clear and professional '{section}' section in paragraph or bullet format:

{qna_text}
"""}
    ]
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.2,
        max_tokens=2048
    )
    return response.choices[0].message.content

# === Save BRD to Word File ===
def save_brd_to_word(brd_sections):
    doc = Document()
    for section, content in brd_sections.items():
        heading = doc.add_heading(section, level=1)
        heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        for para in content.strip().split("\n"):
            if para.strip():
                p = doc.add_paragraph(para.strip())
                p.style.font.size = Pt(11)
                p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output
