import qrcode

# Function to generate QR Code for medicines
def generate_qr_code(medicine_id, medicine_name):
    qr_data = f"Medicine ID: {medicine_id}\nName: {medicine_name}"
    qr = qrcode.make(qr_data)
    qr.save(f"{medicine_name}.png")  # Save as image

    print(f"✅ QR Code generated for {medicine_name}!")

# Generate QR codes for sample medicines
generate_qr_code(1, "Paracetamol")
generate_qr_code(2, "Aspirin")
generate_qr_code(3, "Ibuprofen")
