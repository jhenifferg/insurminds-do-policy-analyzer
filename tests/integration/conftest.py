"""Deterministic synthetic documents used by integration tests."""

from io import BytesIO

import pymupdf
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def make_text_pdf(page_texts: list[str]) -> bytes:
    """Create a native-text PDF without external files or network access."""
    writer = PdfWriter()

    for page_text in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        content = DecodedStreamObject()
        content.set_data(
            f"BT /F1 12 Tf 72 720 Td ({page_text}) Tj ET".encode("latin-1")
        )
        page[NameObject("/Contents")] = writer._add_object(content)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def make_text_image(lines: list[str]) -> bytes:
    """Create a high-contrast PNG with synthetic OCR content."""
    font = ImageFont.load_default(size=56)
    line_height = 90
    image = Image.new("RGB", (1800, 120 + line_height * len(lines)), "white")
    draw = ImageDraw.Draw(image)

    for line_number, line in enumerate(lines):
        draw.text(
            (60, 40 + line_number * line_height),
            line,
            fill="black",
            font=font,
        )

    output = BytesIO()
    image.save(output, format="PNG")
    image.close()
    return output.getvalue()


def make_scanned_pdf(lines: list[str]) -> bytes:
    """Create a PDF containing only a raster image and no useful text layer."""
    image_bytes = make_text_image(lines)
    pdf = pymupdf.open()
    page = pdf.new_page(width=900, height=500)
    page.insert_image(page.rect, stream=image_bytes)
    result = pdf.tobytes()
    pdf.close()
    return result
