#!/usr/bin/env python3
"""
Simple test to isolate QR code generation issue
"""

import sys
sys.path.append('/app/backend')

from qr_generator import QRGenerator, ErrorCorrectionLevel, generate_vcard, create_qr_image, create_qr_svg

def test_basic_qr_generation():
    print("Testing basic QR code generation...")
    
    try:
        # Test vCard generation
        print("1. Testing vCard generation...")
        vcard = generate_vcard(
            name="Test User",
            phone="+33 1 23 45 67 89",
            email="test@example.com",
            company="Test Company",
            title="Test Title",
            url_work="https://work.com",
            url_home="https://home.com"
        )
        print("✅ vCard generation successful")
        print(f"vCard content: {vcard[:100]}...")
        
        # Test QR generator initialization
        print("2. Testing QR generator initialization...")
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        print("✅ QR generator initialization successful")
        
        # Test adding data
        print("3. Testing add_data...")
        qr.add_data(vcard)
        print("✅ add_data successful")
        
        # Test make (this is where the error likely occurs)
        print("4. Testing make...")
        qr.make()
        print("✅ make successful")
        
        # Test image creation
        print("5. Testing image creation...")
        qr_image_base64 = create_qr_image(
            qr_generator=qr,
            color="#000000",
            marker_shape="square",
            dot_shape="square"
        )
        print("✅ Image creation successful")
        print(f"Image base64 length: {len(qr_image_base64)}")
        
        # Test SVG creation
        print("6. Testing SVG creation...")
        svg_content = create_qr_svg(
            qr_generator=qr,
            color="#000000",
            marker_shape="square",
            dot_shape="square"
        )
        print("✅ SVG creation successful")
        print(f"SVG content length: {len(svg_content)}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_qr_generation()