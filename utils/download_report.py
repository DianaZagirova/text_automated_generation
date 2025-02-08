import re
import base64
import markdown
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontSize=24,
    spaceAfter=30,
    textColor='#2a2a2a'
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading1'],
    fontSize=18,
    spaceAfter=12,
    textColor='#2a2a2a'
)

subheading_style = ParagraphStyle(
    'CustomSubheading',
    parent=styles['Heading2'],
    fontSize=14,
    spaceAfter=10,
    textColor='#2a2a2a'
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=12,
    leading=16,
    spaceBefore=6,
    spaceAfter=12,
    textColor='#2a2a2a',
    alignment=4  # Justified
)

caption_style = ParagraphStyle(
    'CustomCaption',
    parent=styles['Italic'],
    fontSize=10,
    leading=12,
    textColor='#666666',
    alignment=1  # Center
)

def process_html_links(html: str) -> str:
    """
    Looks for <a href="...">...</a> tags in the HTML and replaces them
    with ReportLab <link href="..."> syntax colored blue, making them
    clickable within the PDF.
    """
    pattern = re.compile(r'<a href="([^"]+)">(.*?)</a>', flags=re.IGNORECASE)
    matches = list(pattern.finditer(html))

    # Replace from the end to the beginning so positions don't shift
    for m in reversed(matches):
        url = m.group(1)
        text = m.group(2)
        pdf_link = f'<font color="blue"><link href="{url}">{text}</link></font>'
        start, end = m.span()
        html = html[:start] + pdf_link + html[end:]
    return html

def create_downloadable_report(content: str, images_dir: str) -> bytes:
    """
    Create a downloadable version of the report with embedded images and preserved links.
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Add a title at the very top
        story.append(Paragraph("Research Report", title_style))
        story.append(Spacer(1, 24))

        # Regex to find your base64 images plus source text
        image_pattern = (
            r'<div class="image-container">\s*'
            r'<img src="data:image/png;base64,([^"]+)"[^>]*>\s*'
            r'<em>Source:\s*([^<]+)</em>\s*</div>'
        )

        # Split content by the <div class="image-container"> ... tags
        parts = re.split(image_pattern, content)

        for i in range(len(parts)):
            # Even indices (i % 3 == 0) are normal text portions
            if i % 3 == 0:  
                text_block = parts[i].strip()
                if text_block:
                    # Break the text block into lines
                    paragraphs = text_block.split('\n')

                    for paragraph in paragraphs:
                        paragraph = paragraph.strip()
                        if not paragraph:
                            continue

                        # Check for "##" heading
                        heading_match = re.match(r'^##\s+(.+)$', paragraph)
                        if heading_match:
                            heading_text = heading_match.group(1).strip()
                            story.append(Spacer(1, 12))
                            story.append(Paragraph(heading_text, heading_style))
                            story.append(Spacer(1, 8))
                            continue

                        # Check for "###" subheading
                        subheading_match = re.match(r'^###\s+(.+)$', paragraph)
                        if subheading_match:
                            subheading_text = subheading_match.group(1).strip()
                            story.append(Spacer(1, 12))
                            story.append(Paragraph(subheading_text, subheading_style))
                            story.append(Spacer(1, 8))
                            continue

                        # Otherwise treat as normal paragraph
                        # 1) Convert the paragraph (Markdown -> HTML)
                        html_para = markdown.markdown(paragraph)
                        # 2) Convert HTML <a> tags to PDF clickable links
                        html_para = process_html_links(html_para)

                        # Create a styled paragraph and add it
                        story.append(Paragraph(html_para, normal_style))
                        story.append(Spacer(1, 4))

            # i % 3 == 1: This should be the base64 image data
            elif i % 3 == 1:
                try:
                    img_data = parts[i]
                    img_bytes = base64.b64decode(img_data)
                    img_buffer = BytesIO(img_bytes)
                    pil_img = Image.open(img_buffer)

                    max_width = 450
                    width, height = pil_img.size
                    if width > max_width:
                        ratio = max_width / width
                        width = max_width
                        height = int(height * ratio)

                    # Add image to story
                    story.append(Spacer(1, 12))
                    reportlab_img = ReportLabImage(img_buffer, width=width, height=height)
                    story.append(reportlab_img)
                    story.append(Spacer(1, 12))
                except Exception as e:
                    print(f"Error processing image in PDF: {str(e)}")

            # i % 3 == 2: This would be the "Source" text captured from the regex
            elif i % 3 == 2:
                source_text = parts[i].strip()
                if source_text:
                    # Add the source below the image
                    story.append(Paragraph(f"<i>Source: {source_text}</i>", caption_style))
                    story.append(Spacer(1, 12))

        # Finally build the PDF
        doc.build(story)

        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content

    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise