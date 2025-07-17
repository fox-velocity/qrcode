#!/usr/bin/env python3
"""
Debug QR code generation step by step
"""

import sys
sys.path.append('/app/backend')

from qr_generator import QRGenerator, ErrorCorrectionLevel, generate_vcard

def debug_qr_step_by_step():
    print("Debugging QR code generation step by step...")
    
    try:
        # Create simple test data
        test_data = "Hello World"
        print(f"Test data: {test_data}")
        
        # Initialize QR generator
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        qr.add_data(test_data)
        
        print(f"Version: {qr.version}")
        print(f"Data: {qr.data}")
        
        # Test version optimization
        print("Testing _optimize_version...")
        qr._optimize_version()
        print(f"Optimized version: {qr.version}")
        
        # Initialize matrix
        qr.module_count = qr.version_info[qr.version]["size"]
        qr.modules = [[False for _ in range(qr.module_count)] for _ in range(qr.module_count)]
        print(f"Module count: {qr.module_count}")
        print(f"Matrix initialized: {len(qr.modules)}x{len(qr.modules[0])}")
        
        # Test function patterns
        print("Testing function patterns...")
        qr._place_finder_patterns()
        qr._place_separators()
        qr._place_timing_patterns()
        qr._place_dark_module()
        qr._place_format_info()
        print("✅ Function patterns placed")
        
        # Test data encoding
        print("Testing data encoding...")
        encoded_data = qr._encode_data()
        print(f"Encoded data length: {len(encoded_data)}")
        print(f"First 20 bits: {encoded_data[:20]}")
        
        # Test error correction
        print("Testing error correction...")
        error_corrected_data = qr._add_error_correction(encoded_data)
        print(f"Error corrected data length: {len(error_corrected_data)}")
        
        # Test data placement (this is where the error likely occurs)
        print("Testing data placement...")
        qr._place_data(error_corrected_data)
        print("✅ Data placement successful")
        
        # Test mask application
        print("Testing mask application...")
        qr._apply_mask()
        print("✅ Mask application successful")
        
        print("\n🎉 All steps completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_qr_step_by_step()