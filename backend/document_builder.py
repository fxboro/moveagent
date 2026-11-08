from io import BytesIO
from html import escape
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from lxml import html
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def watermark(canvas, document):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#eee7d6'))
    canvas.translate(A4[0]/2, A4[1]/2)
    canvas.rotate(42)
    canvas.setFont('Helvetica-Bold', 25)
    canvas.drawCentredString(0, 0, 'EURO-AFRO ELITE CONSULTANCY')
    canvas.restoreState()
    canvas.setFillColor(colors.HexColor('#777777'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(54, 30, 'CONFIDENTIAL | Draft for human review')
    canvas.drawRightString(A4[0]-54, 30, f'Page {document.page}')

PDF_CSS = '''
@page {
    size: A4;
    margin: 20mm;
    @top-left { content: "EURO-AFRO ELITE CONSULTANCY"; font: 8pt sans-serif; color: #777; }
    @bottom-left { content: "CONFIDENTIAL | Draft for human review"; font: 8pt sans-serif; color: #777; }
    @bottom-right { content: "Page " counter(page) " of " counter(pages); font: 8pt sans-serif; color: #777; }
}
body { margin: 0; font: 10pt sans-serif; line-height: 1.6; color: #222; }
h1 { font: 24pt serif; color: #9a7936; margin: 0 0 8mm; }
h2 { font: bold 15pt serif; margin: 7mm 0 3mm; break-after: avoid; }
h3 { font: bold 12pt serif; break-after: avoid; }
p { margin: 0 0 4mm; orphans: 3; widows: 3; overflow-wrap: anywhere; }
.candidate { font: 14pt serif; margin-bottom: 8mm; }
.watermark {
    position: fixed; top: 110mm; left: 0; width: 170mm;
    text-align: center; transform: rotate(-38deg); z-index: -1;
    font: bold 23pt sans-serif; color: #eee7d6; white-space: nowrap;
}
'''

def render_premium_document(candidate_name: str, doc_content: str, *, content_is_html=False):
    from weasyprint import CSS, HTML

    if content_is_html:
        root = html.fragment_fromstring(doc_content, create_parent='div')
        for element in root.iterdescendants():
            if element.tag not in {'h2', 'h3', 'p', 'strong', 'em', 'ul', 'ol', 'li', 'br'}:
                raise ValueError(f'Unsupported dossier HTML tag: {element.tag}')
            page_break = element.get('style', '').replace(' ', '').strip(';') == 'break-before:page'
            element.attrib.clear()
            if page_break:
                element.set('style', 'break-before: page;')
        content = html.tostring(root, encoding='unicode')
    else:
        content = ''.join(f'<p>{escape(paragraph) or "&#160;"}</p>' for paragraph in doc_content.split('\n'))
    markup = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>Strategic dossier: {escape(candidate_name)}</title></head><body>
    <div class="watermark">EURO-AFRO ELITE CONSULTANCY</div>
    <h1>STRATEGIC DOSSIER</h1><p class="candidate">{escape(candidate_name)}</p>
    {content}</body></html>'''
    return HTML(string=markup).render(stylesheets=[CSS(string=PDF_CSS)])


def compile_premium_watermarked_pdf(candidate_name: str, doc_content: str, output_path=None, *, content_is_html=False):
    if content_is_html:
        data = render_premium_document(candidate_name, doc_content, content_is_html=True).write_pdf()
    else:
        stream = BytesIO()
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle('GoldTitle', fontName='Times-Roman', fontSize=24, leading=29, textColor=colors.HexColor('#9a7936'), spaceAfter=24))
        styles.add(ParagraphStyle('DossierBody', fontName='Helvetica', fontSize=10, leading=16, alignment=TA_LEFT, spaceAfter=10, splitLongWords=True))
        story = [Paragraph('STRATEGIC DOSSIER', styles['GoldTitle']), Paragraph(escape(candidate_name), styles['Heading2']), Spacer(1, 16)]
        story.extend(Paragraph(escape(paragraph) or '&#160;', styles['DossierBody']) for paragraph in doc_content.split('\n'))
        SimpleDocTemplate(stream, pagesize=A4, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54).build(story, onFirstPage=watermark, onLaterPages=watermark)
        data = stream.getvalue()
    if output_path:
        from pathlib import Path
        Path(output_path).write_bytes(data)
    return data

def compile_editable_word_doc(candidate_name: str, doc_content: str, output_path=None):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.8)
    normal = doc.styles['Normal']
    normal.font.name, normal.font.size = 'Arial', Pt(11)
    title = doc.add_heading(f'Placement Dossier: {candidate_name}', 0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(180, 150, 72)
    section.header.paragraphs[0].text = 'EURO-AFRO ELITE CONSULTANCY'
    section.footer.paragraphs[0].text = 'CONFIDENTIAL | Draft for human review'
    for paragraph in doc_content.split('\n'):
        doc.add_paragraph(paragraph)
    stream = BytesIO()
    doc.save(stream)
    data = stream.getvalue()
    if output_path:
        from pathlib import Path
        Path(output_path).write_bytes(data)
    return data
