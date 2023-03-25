# import barcode
import os

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak


class RefillCardGenerator:

    def __init__(self):
        self.images_folder = "barcodes"
        self.pdfs_folder = "cards"

    def generate_pdf(self, products, filename):
        """Given list of products, generate a PDF of the refill cards and return path to PDF."""
        if not products: return False

        filepath = os.path.join(self.pdfs_folder, filename)
        doc = SimpleDocTemplate(os.path.abspath(filepath), pagesize=(3 * inch, 5 * inch),
                                rightMargin=2, leftMargin=2,
                                topMargin=0 * inch, bottomMargin=2)

        # pdfmetrics.registerFont(TTFont("upcfont", "upcfont.ttf"))

        story = []
        for product in products:
            try:
                if product[2] is not None and product[2].isdigit():
                    image_file = os.path.join(self.images_folder, product[1])

                    styles = getSampleStyleSheet()
                    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
                    item_name = '<font size=13>{}</font>'.format(product[0])
                    item_code = '<font size=14># {}</font>'.format(product[1])
                    # code_fonty = '<font size=54 face="upcfont">{}</font>'.format(product[2])
                    # code_file = Image("{}.png".format(image_file))
                    barcode = product[2]
                    barcode = barcode[:-1] if len(barcode) == 12 else barcode
                    image_path = os.path.join("new_barcodes/", barcode + ".png")
                    if not os.path.exists(image_path):
                        if len(barcode) >= 11:
                            print(f"No barcode image file for {barcode}")
                        continue
                    code_file = Image(image_path, width=115, height=59)  # .format(image_file))
                    story.append(Paragraph(item_name, styles["Center"]))
                    story.append(Spacer(1, 3))
                    story.append(Paragraph(item_code, styles["Center"]))
                    story.append(Spacer(1, 1.4 * inch))
                    # story.append(Spacer(1, 1.5*inch))
                    # story.append(Spacer(1, 1.95*inch))
                    # story.append(Paragraph(code_fonty, styles["Center"]))
                    story.append(code_file)
                    story.append(PageBreak())
            except AttributeError:
                continue

        doc.build(story)
        return True
