import qrcode
import os
import pyperclip

def SendToPhone(command):
    try:
        # 1. Get the data
        data = pyperclip.paste()
        
        if not data or len(data.strip()) < 1:
            return "Clipboard is empty. Copy something first, sir."
            
        # 2. QR Code Capacity Check (QR codes max out around ~2900 chars)
        if len(data) > 2500:
            return "The clipboard data is too large for a single QR code. Please copy a smaller text or link."
        
        # 3. Generate QR Code
        qr = qrcode.QRCode(
            version=None, 
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # 4. Save and Open Image
        img = qr.make_image(fill_color="black", back_color="white")
        
        os.makedirs("Data", exist_ok=True)
        file_path = os.path.join("Data", "PhoneLink.png")
        img.save(file_path)
        
        # Open the image so you can scan it immediately
        os.startfile(file_path)
        
        return "Scan this QR code to transfer the data."
        
    except Exception as e:
        return f"Error generating Phone Link: {e}"