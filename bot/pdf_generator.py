import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Register a font that supports Cyrillic if available, otherwise fallback
# In a real deployed env, we need a ttf file.
# For this demo, we'll try to use a standard font or download one.
# reportlab standard fonts don't support Cyrillic well.
# We will use "Helvetica" which often works for basic English, but for Cyrillic we need a specific font.
# Let's assume we might need to skip Cyrillic or use English for the PDF to be safe, 
# OR use a known font path. Since we don't have a font file, let's transliterate or use English for the PDF invoices 
# to avoid square boxes, OR try to find a system font.
# BETTER APPROACH: Write the invoice in English "Invoice #123" to look international/premium.

def create_invoice_pdf(order_id, client_name, service_name, price_tjs):
    """
    Generates a PDF invoice for the given order.
    Returns the absolute path to the generated file.
    """
    
    # Calculate days based on rate 600 TJS
    rate = 600
    try:
        days = int(int(price_tjs) / rate)
        if days < 1: days = 1
    except:
        days = 1
        
    filename = f"invoice_{order_id}.pdf"
    file_path = os.path.join("bot", "static", "invoices", filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    # --- Header ---
    c.setFont("Helvetica-Bold", 24)
    c.drawString(2 * cm, height - 3 * cm, "AMINI AUTOMATION")
    
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 3.5 * cm, "Digital Agency | Telegram Solutions")
    c.drawString(2 * cm, height - 3.9 * cm, "Dushanbe, Tajikistan")
    c.drawString(2 * cm, height - 4.3 * cm, "@amini.automation")
    
    # --- Invoice Info ---
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - 2 * cm, height - 3 * cm, "INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 2 * cm, height - 3.7 * cm, f"#{order_id}")
    c.drawRightString(width - 2 * cm, height - 4.2 * cm, datetime.now().strftime("%d %B %Y"))
    
    # --- Client Info ---
    c.line(2 * cm, height - 5 * cm, width - 2 * cm, height - 5 * cm)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, height - 6 * cm, "BILL TO:")
    c.setFont("Helvetica", 12)
    # Transliterate basic assumption or just use as is (hope for ascii)
    # If client name is Cyrillic, it might break in Helvetica.
    # Safe fallback: "Valued Client" if non-ascii detected?
    safe_client_name = client_name if client_name.isascii() else f"Client #{order_id}"
    c.drawString(2 * cm, height - 6.5 * cm, safe_client_name)
    
    # --- Table Header ---
    y = height - 9 * cm
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(2 * cm, y - 0.5 * cm, width - 4 * cm, 1 * cm, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.5 * cm, y, "DESCRIPTION")
    c.drawString(12 * cm, y, "DAYS")
    c.drawString(14 * cm, y, "RATE")
    c.drawString(17 * cm, y, "AMOUNT")
    
    # --- Table Content ---
    y -= 1.5 * cm
    c.setFont("Helvetica", 10)
    
    # Service Name (safe)
    safe_service = service_name if service_name.isascii() else "Telegram Bot Development"
    
    c.drawString(2.5 * cm, y, safe_service)
    c.drawString(12 * cm, y, str(days))
    c.drawString(14 * cm, y, "600 TJS")
    c.drawString(17 * cm, y, f"{price_tjs} TJS")
    
    c.line(2 * cm, y - 1 * cm, width - 2 * cm, y - 1 * cm)
    
    # --- Total ---
    y -= 2.5 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 2 * cm, y, f"TOTAL: {price_tjs} TJS")
    
    # --- Footer ---
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(2 * cm, 3 * cm, "Payment Terms: 50% Upfront, 50% Upon Completion.")
    c.drawString(2 * cm, 2.5 * cm, "Contact: @aminzoda.03")
    
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 1 * cm, "Thank you for your business!")
    
    c.save()
    return file_path
