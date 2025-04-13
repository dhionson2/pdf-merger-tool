import io
import pathlib
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


def create_cover_page(title: str, subtitle: str = "") -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height / 2 + 40, title)

    if subtitle:
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height / 2 - 10, subtitle)

    c.save()
    buffer.seek(0)
    return buffer


def create_summary_page(file_list: list[str]) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Sumário")

    c.setFont("Helvetica", 12)
    y = height - 80
    for idx, name in enumerate(file_list, start=1):
        display_name = name.replace(".pdf", "").replace("+", " ").replace("-", " ")
        c.drawString(60, y, f"{idx}. {display_name}")
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12)

    c.save()
    buffer.seek(0)
    return buffer


def add_page_numbers(writer: PdfWriter):
    for page_number, page in enumerate(writer.pages, start=1):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont("Helvetica", 10)
        can.drawRightString(570, 20, f"{page_number}")
        can.save()

        packet.seek(0)
        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)


def remove_footer_page_numbers(input_paths: list[pathlib.Path]) -> list[io.BytesIO]:
    cleaned_pdfs = []

    for pdf_path in input_paths:
        doc = fitz.open(pdf_path)
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text.isdigit() and 0 < int(text) < 1000:
                            bbox = span["bbox"]
                            y_position = bbox[1]
                            if y_position > page.rect.height * 0.85:
                                rect = fitz.Rect(bbox)
                                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        cleaned_pdfs.append(buffer)

    return cleaned_pdfs


def merge_pdfs_with_summary_and_cover(input_paths: list[pathlib.Path], output_path: pathlib.Path, title: str, subtitle: str = ""):
    writer = PdfWriter()

    # Capa
    cover = PdfReader(create_cover_page(title, subtitle))
    for p in cover.pages:
        writer.add_page(p)

    # Sumário
    summary = PdfReader(create_summary_page([p.name for p in input_paths]))
    for p in summary.pages:
        writer.add_page(p)

    # Limpa numeração antiga dos PDFs originais
    cleaned = remove_footer_page_numbers(input_paths)

    # Conteúdo real
    for buf in cleaned:
        reader = PdfReader(buf)
        for page in reader.pages:
            writer.add_page(page)

    # Numeração (inclui capa + sumário)
    add_page_numbers(writer)

    # Salvar
    with open(output_path, "wb") as f:
        writer.write(f)
