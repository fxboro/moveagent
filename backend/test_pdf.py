"""Standalone three-page WeasyPrint regression check with a local PDF artifact."""

import sys
from io import BytesIO
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.document_builder import compile_premium_watermarked_pdf, render_premium_document


MOCK_LARGE_CONTENT = '''
<h2>Executive Summary &amp; Career Trajectory</h2>
<p>This fictional quantitative engineering profile exercises executive typography.
Academic credentials, labor-market conditions and recognition require independent review.</p>
<h2>Strategic Institutional Vectors</h2>
<p>TU Muenchen and RWTH Aachen are illustrative research targets, not confirmed
admissions matches. Curriculum and ECTS requirements must be checked per program.</p>
<h2 style="break-before: page;">Module Matching &amp; ECTS Dissection Matrix</h2>
<p>This section must begin on page 2. The diagonal watermark, continuing header
and Page X of Y footer must appear on every page without clipping.</p>
<p>Sample module review: advanced engineering mechanics, quantitative methods,
distributed systems and research methodology. No credit equivalence is asserted.</p>
<h2 style="break-before: page;">Visa Compliance &amp; Proof of Funds Mapping</h2>
<p>Page 3 verification. Current blocked-account amounts and visa requirements
must be verified against official sources before advice. This is a rendering fixture.</p>
'''


def execute_pdf_test(output_path=None):
    from pypdf import PdfReader

    print('Initializing premium WeasyPrint render test...')
    output = Path(output_path) if output_path else Path(__file__).with_name('test_premium_output.pdf')
    document = render_premium_document('Chidi Chukwuma', MOCK_LARGE_CONTENT, content_is_html=True)
    data = compile_premium_watermarked_pdf('Chidi Chukwuma', MOCK_LARGE_CONTENT, content_is_html=True)
    reader = PdfReader(BytesIO(data))
    if len(reader.pages) != 3:
        raise AssertionError(f'Expected 3 pages, got {len(reader.pages)}')
    headings = ('Executive Summary', 'Module Matching', 'Visa Compliance')
    for number, (page, layout, heading) in enumerate(zip(reader.pages, document.pages, headings), 1):
        text = page.extract_text()
        for expected in (heading, f'Page {number} of 3', 'CONFIDENTIAL', 'EURO-AFRO ELITE CONSULTANCY'):
            if expected not in text:
                raise AssertionError(f'Page {number} missing {expected!r}')
        watermark_boxes = []
        for box in layout._page_box.descendants():
            if box.element is not None and box.element.get('class') == 'watermark' and box.__class__.__name__ == 'TextBox':
                watermark_boxes.append(box)
            if box.__class__.__name__ == 'TextBox' and box.transformation_matrix is None:
                if box.position_x < 0 or box.position_y < 0 or box.position_x + box.width > layout.width + 1 or box.position_y + box.height > layout.height + 1:
                    raise AssertionError(f'Page {number} has text outside page bounds')
        if not watermark_boxes:
            raise AssertionError(f'Page {number} missing watermark text box')
        transformed_watermarks = [box for box in layout._page_box.descendants()
                                  if box.element is not None and box.element.get('class') == 'watermark'
                                  and box.transformation_matrix is not None]
        if not transformed_watermarks:
            raise AssertionError(f'Page {number} watermark is not diagonal')
        for box in transformed_watermarks:
            for horizontal, vertical in ((box.position_x, box.position_y), (box.position_x + box.width, box.position_y),
                                         (box.position_x, box.position_y + box.height), (box.position_x + box.width, box.position_y + box.height)):
                horizontal, vertical = box.transformation_matrix.transform_point(horizontal, vertical)
                if not (0 <= horizontal <= layout.width and 0 <= vertical <= layout.height):
                    raise AssertionError(f'Page {number} watermark is clipped')
    output.write_bytes(data)
    print(f'PASS: 3 pages, page counters, diagonal watermarks and page bounds verified: {output.resolve()}')
    return output


if __name__ == '__main__':
    try:
        execute_pdf_test()
    except Exception as error:
        print(f'PDF engine test failed: {error}', file=sys.stderr)
        print('Ensure WeasyPrint native dependencies (especially Pango and its DLL search path on Windows) are configured.', file=sys.stderr)
        sys.exit(1)