import groq
import re
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import xlsxwriter
import os
import textwrap
client = groq.Client(api_key="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")

def extract_text_from_pdf(pdf_path):
    """Extract text from a given PDF file."""
    pdf_reader = PdfReader(pdf_path)
    text = "".join([page.extract_text() for page in pdf_reader.pages])
    return text

def generate_design_content(brd_content: str, metadata: str):
    prompt1 = """You are a ETL and DWH architect. Generate a detailed Design Document used in an ETL project. The document should include High level Design which includes:
    Make a DWH Document
    Fact Tables
    Dimension Tables
    You are ETL Architect. Generate a low level design document which includes:
    ER Diagram of Fact Tables with the Dimension Tables
    Technical Details of ETL System
    Data Flow Diagram
    Source Target Mapping wi   th the logics
    """

    messages = [
        {"role": "system", "content": prompt1},
        {"role": "user", "content": f"I will be giving you the Businees Requirement Document: {brd_content} and metadata: {metadata}, give the structured design document which can be used professionaly"}
    ]
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.2,
        max_tokens=7000,
        top_p=0.2,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    return response.choices[0].message.content

def generate_kpi_content(brd_content: str, metadata: str):
    prompt2= """You are a senior BI Analyst and KPI documentation expert. "
            "Based on the provided BRD and metadata, generate a professional **KPI Definition Document**.\n\n"
            "The document should start with a **Table of Contents** and define **at least 20 KPIs** aligned to the business goals. "
            "Each KPI must follow this format:\n\n"
            "1. **KPI Name**\n"
            "2. **Description** – Business purpose of the KPI\n"
            "3. **Business Objective** – What strategic goal it supports\n"
            "4. **Formula / Logic** – Calculation method with clarity\n"
            "5. **Data Source** – Tables or systems feeding the KPI\n"
            "6. **Frequency** – Daily, Weekly, Monthly\n"
            "7. **Owner / Department** – Responsible party\n"
            "8. **Thresholds / Targets** – Acceptable or goal values\n"
            "9. **Visualization Type** – Suggested chart/graph\n"
            "10. **Drill-down Dimensions** – Filters like region/product/etc.\n"
            "11. **Related KPIs** – Dependencies or supporting metrics\n\n"
            "Ensure clarity, conciseness, and relevance to business performance." """
    
    messages = [
        {"role": "system", "content": prompt2},
        {"role": "user", "content": f"Generate a KPI document with more than 20 KPIs based on the {brd_content} and metadata: {metadata}"}
    ]
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",  # Groq model
        messages=messages,
        temperature=0.2,
        max_tokens=7000,
        top_p=0.2,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    return response.choices[0].message.content
def generate_technical_content(brd_content: str, metadata: str):
    prompt3 = """"You are a developer
            "Generate a detailed and professional **Technical Specification Document** suitable for developer handoff. "
            "The document should follow this structure:\n\n"
            "1. Table of Contents\n"
            "2. Introduction – Overview, business context, and technical goals\n"
            "3. Technical Objectives – Key deliverables, outcomes, and technologies\n"
            "4. System Architecture – Logical and physical diagrams (text format)\n"
            "5. Current Architecture – Description of the existing system\n"
            "6. Proposed Architecture – Updated design and improvements\n"
            "7. Data Integration – Sources, ingestion, transformation, and quality\n"
            "8. Data Storage & Modeling – Fact/dim schema, partitioning, indexing\n"
            "9. Data Visualization & Reporting – Dashboards, KPIs, and tools\n"
            "10. Security & Access Control – Classification, masking, permissions\n"
            "11. Performance & Scalability – Volume projections, tuning, scaling\n"
            "12. Testing & QA – Test strategy, data validation, automation\n"
            "13. Deployment & Maintenance – CI/CD, environments, support\n"
            "14. Glossary & Acronyms – Key technical/business terms"
        """
    messages = [
        {"role": "system", "content": prompt3},
        {"role": "user", "content": f"I will be providing with the Business Requirement document: {brd_content} and metadata: {metadata}, give the structured technical document which can be used by the professionals"}
    ]
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",  # Groq model
        messages=messages,
        temperature=0.2,
        max_tokens=7000,
        top_p=0.2,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    return response.choices[0].message.content

def create_pdf(file_path, title, content):
    
    """Creates an Excel file with the given title and formats bold text."""
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet()
    
    # Define formats
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    content_format = workbook.add_format({'text_wrap': True})
    bold_format = workbook.add_format({'bold': True, 'text_wrap': True})
    
    # Write title
    worksheet.write(0, 0, title, title_format)
    
    # Adjust column width
    worksheet.set_column(0, 0, 100)
    
    # Write content line by line
    lines = content.split("\n")
    row = 2  # Start after title
    
    for line in lines:
        # Find bold text enclosed in **text**
        matches = re.findall(r"\*\*(.*?)\*\*", line)
        
        if matches:
            # Replace **bold text** with just bold text
            for match in matches:
                line = line.replace(f"**{match}**", match)
            
            worksheet.write(row, 0, line, bold_format)
        else:
            worksheet.write(row, 0, line, content_format)
        
        row += 1
    
    workbook.close()
    # print(f"✅ Excel file saved at: {file_path}")
    return True

if __name__ == "__main__":
    # answers = ask_questions()
    brd_pdf_path = input("Enter the path to the BRD PDF file: ")
    metadata_pdf_path = input("Enter the path to the Metadata PDF file: ")

    # Extract content
    brd_content = extract_text_from_pdf(brd_pdf_path)
    metadata = extract_text_from_pdf(metadata_pdf_path)

    design_doc = generate_design_content(brd_content, metadata)
    kpi_list = generate_kpi_content(brd_content, metadata)
    technical_doc = generate_technical_content(brd_content,metadata)

    # Create PDF for design document
    if design_doc:
        design_pdf_path = "Design_Document.xlsx"
        if create_pdf(design_pdf_path, "System Design Document", design_doc):
            print(f"\n✅ Design document saved to: {design_pdf_path}")

    # Create PDF for technical document
    if technical_doc:
        technical_pdf_path = "Technical_Document.xlsx"
        if create_pdf(technical_pdf_path, "Technical Specification Document", technical_doc):
            print(f"✅ Technical document saved to: {technical_pdf_path}")

    if kpi_list:
        kpi_pdf_path = "kpi_list.xlsx"
        if create_pdf(kpi_pdf_path, "KPI Document", kpi_list):
            print(f"✅ Technical document saved to: {kpi_pdf_path}")
    
    # print("Generated Design Document:\n", design_doc)
    # print("Generated Technical Document:\n", technical_doc)
    # print("Generated KPI Document:\n",kpi_list)
