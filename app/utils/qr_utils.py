# app/utils/qr_utils.py

import qrcode
import os

def generate_qr(asset_id):
    # Asset detail page ka URL (Angular frontend ke liye)
    asset_url = f"http://localhost:4200/assets/{asset_id}"  

    # QR code generate
    qr = qrcode.make(asset_url)

    # Static folder for storing QR images
    qr_folder = "static/qr_codes"
    os.makedirs(qr_folder, exist_ok=True)

    # Path jaha image save hogi
    qr_path = f"{qr_folder}/asset_{asset_id}.png"
    qr.save(qr_path)

    return qr_path