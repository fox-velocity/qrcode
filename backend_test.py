#!/usr/bin/env python3
"""
Backend API Testing for QR Code Generator
Tests all QR code generation endpoints with comprehensive scenarios
"""

import requests
import json
import base64
import os
from io import BytesIO
from PIL import Image
import xml.etree.ElementTree as ET

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"Testing backend at: {API_URL}")

class QRCodeTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def test_result(self, test_name, success, message=""):
        if success:
            print(f"✅ {test_name}")
            self.passed += 1
        else:
            print(f"❌ {test_name}: {message}")
            self.failed += 1
            self.errors.append(f"{test_name}: {message}")
            
    def summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        
        if self.errors:
            print(f"\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.failed == 0

def create_sample_logo_base64():
    """Create a simple test logo in base64 format"""
    # Create a simple 50x50 red circle
    img = Image.new('RGBA', (50, 50), (255, 255, 255, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([5, 5, 45, 45], fill=(255, 0, 0, 255))
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def test_basic_connectivity():
    """Test basic API connectivity"""
    tester = QRCodeTester()
    
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        tester.test_result("Basic API connectivity", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("Basic API connectivity", False, str(e))
    
    return tester

def test_qr_code_generation():
    """Test POST /api/qr-code endpoint"""
    tester = QRCodeTester()
    
    # Test 1: Empty form data
    try:
        payload = {
            "name": "",
            "phone": "",
            "email": "",
            "company": "",
            "title": "",
            "url_work": "",
            "url_home": "",
            "color": "#000000",
            "marker_shape": "square",
            "dot_shape": "square"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        tester.test_result("QR Code generation with empty data", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tester.test_result("Response contains qr_image_base64", 
                              "qr_image_base64" in data,
                              "Missing qr_image_base64 field")
            tester.test_result("Response contains vcard_content", 
                              "vcard_content" in data,
                              "Missing vcard_content field")
            
            # Validate base64 image format
            if "qr_image_base64" in data:
                tester.test_result("QR image is valid base64", 
                                  data["qr_image_base64"].startswith("data:image/png;base64,"),
                                  "Invalid base64 image format")
                
    except Exception as e:
        tester.test_result("QR Code generation with empty data", False, str(e))
    
    # Test 2: Full form data
    try:
        payload = {
            "name": "Jean Dupont",
            "phone": "+33 1 23 45 67 89",
            "email": "jean.dupont@example.com",
            "company": "FoxVelocity Creation",
            "title": "Développeur Senior",
            "url_work": "https://foxvelocity.com",
            "url_home": "https://jeandupont.fr",
            "color": "#ff0000",
            "marker_shape": "circle",
            "dot_shape": "rounded"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        tester.test_result("QR Code generation with full data", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Validate vCard content
            vcard = data.get("vcard_content", "")
            tester.test_result("vCard contains name", 
                              "Jean Dupont" in vcard,
                              "Name not found in vCard")
            tester.test_result("vCard contains email", 
                              "jean.dupont@example.com" in vcard,
                              "Email not found in vCard")
            tester.test_result("vCard contains company", 
                              "FoxVelocity Creation" in vcard,
                              "Company not found in vCard")
            
    except Exception as e:
        tester.test_result("QR Code generation with full data", False, str(e))
    
    # Test 3: Different colors
    colors_to_test = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"]
    for color in colors_to_test:
        try:
            payload = {
                "name": "Test User",
                "color": color,
                "marker_shape": "square",
                "dot_shape": "square"
            }
            
            response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
            tester.test_result(f"QR Code generation with color {color}", 
                              response.status_code == 200,
                              f"Status: {response.status_code}")
        except Exception as e:
            tester.test_result(f"QR Code generation with color {color}", False, str(e))
    
    # Test 4: Different shapes
    shapes = ["square", "circle", "rounded"]
    for marker_shape in shapes:
        for dot_shape in shapes:
            try:
                payload = {
                    "name": "Test User",
                    "color": "#000000",
                    "marker_shape": marker_shape,
                    "dot_shape": dot_shape
                }
                
                response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
                tester.test_result(f"QR Code with marker:{marker_shape}, dot:{dot_shape}", 
                                  response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                tester.test_result(f"QR Code with marker:{marker_shape}, dot:{dot_shape}", False, str(e))
    
    # Test 5: Logo upload
    try:
        logo_base64 = create_sample_logo_base64()
        payload = {
            "name": "Test User",
            "color": "#000000",
            "marker_shape": "square",
            "dot_shape": "square",
            "logo_base64": logo_base64,
            "logo_size": 25
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        tester.test_result("QR Code generation with logo", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("QR Code generation with logo", False, str(e))
    
    return tester

def test_qr_code_svg_generation():
    """Test POST /api/qr-code-svg endpoint"""
    tester = QRCodeTester()
    
    # Test 1: Basic SVG generation
    try:
        payload = {
            "name": "Marie Martin",
            "phone": "+33 6 12 34 56 78",
            "email": "marie.martin@example.fr",
            "company": "Tech Solutions",
            "title": "Chef de Projet",
            "color": "#0066cc",
            "marker_shape": "rounded",
            "dot_shape": "circle"
        }
        
        response = requests.post(f"{API_URL}/qr-code-svg", json=payload, timeout=10)
        tester.test_result("SVG QR Code generation", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tester.test_result("SVG response contains svg_content", 
                              "svg_content" in data,
                              "Missing svg_content field")
            tester.test_result("SVG response contains vcard_content", 
                              "vcard_content" in data,
                              "Missing vcard_content field")
            
            # Validate SVG content
            if "svg_content" in data:
                svg_content = data["svg_content"]
                tester.test_result("SVG content is valid XML", 
                                  svg_content.startswith('<?xml') and '<svg' in svg_content,
                                  "Invalid SVG format")
                
                # Try to parse SVG as XML
                try:
                    ET.fromstring(svg_content)
                    tester.test_result("SVG is well-formed XML", True)
                except ET.ParseError as e:
                    tester.test_result("SVG is well-formed XML", False, str(e))
                    
    except Exception as e:
        tester.test_result("SVG QR Code generation", False, str(e))
    
    # Test 2: Different shapes in SVG
    shapes = ["square", "circle", "rounded"]
    for shape in shapes:
        try:
            payload = {
                "name": "Test User",
                "marker_shape": shape,
                "dot_shape": shape,
                "color": "#333333"
            }
            
            response = requests.post(f"{API_URL}/qr-code-svg", json=payload, timeout=10)
            tester.test_result(f"SVG QR Code with {shape} shapes", 
                              response.status_code == 200,
                              f"Status: {response.status_code}")
        except Exception as e:
            tester.test_result(f"SVG QR Code with {shape} shapes", False, str(e))
    
    return tester

def test_png_download():
    """Test GET /api/download-png endpoint"""
    tester = QRCodeTester()
    
    # Test 1: Basic PNG download
    try:
        params = {
            "name": "Pierre Durand",
            "phone": "+33 1 98 76 54 32",
            "email": "pierre.durand@example.com",
            "company": "Innovation Labs",
            "title": "Ingénieur Logiciel",
            "color": "#008000",
            "marker_shape": "square",
            "dot_shape": "circle"
        }
        
        response = requests.get(f"{API_URL}/download-png", params=params, timeout=10)
        tester.test_result("PNG download", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
        
        if response.status_code == 200:
            tester.test_result("PNG content type", 
                              response.headers.get('content-type') == 'image/png',
                              f"Content-Type: {response.headers.get('content-type')}")
            
            # Check filename in Content-Disposition header
            content_disposition = response.headers.get('content-disposition', '')
            tester.test_result("PNG filename contains FoxVelocityCreation", 
                              'FoxVelocityCreation.png' in content_disposition,
                              f"Content-Disposition: {content_disposition}")
            
            # Validate PNG content
            try:
                img = Image.open(BytesIO(response.content))
                tester.test_result("PNG is valid image", 
                                  img.format == 'PNG',
                                  f"Image format: {img.format}")
            except Exception as e:
                tester.test_result("PNG is valid image", False, str(e))
                
    except Exception as e:
        tester.test_result("PNG download", False, str(e))
    
    # Test 2: PNG download with logo
    try:
        logo_base64 = create_sample_logo_base64()
        params = {
            "name": "Sophie Leblanc",
            "email": "sophie@example.fr",
            "color": "#ff6600",
            "logo_base64": logo_base64,
            "logo_size": "20"
        }
        
        response = requests.get(f"{API_URL}/download-png", params=params, timeout=10)
        tester.test_result("PNG download with logo", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("PNG download with logo", False, str(e))
    
    # Test 3: Different colors and shapes
    test_cases = [
        {"color": "#ff0000", "marker_shape": "circle", "dot_shape": "square"},
        {"color": "#00ff00", "marker_shape": "rounded", "dot_shape": "circle"},
        {"color": "#0000ff", "marker_shape": "square", "dot_shape": "rounded"}
    ]
    
    for i, case in enumerate(test_cases):
        try:
            params = {
                "name": f"Test User {i+1}",
                **case
            }
            
            response = requests.get(f"{API_URL}/download-png", params=params, timeout=10)
            tester.test_result(f"PNG download case {i+1}", 
                              response.status_code == 200,
                              f"Status: {response.status_code}")
        except Exception as e:
            tester.test_result(f"PNG download case {i+1}", False, str(e))
    
    return tester

def test_svg_download():
    """Test GET /api/download-svg endpoint"""
    tester = QRCodeTester()
    
    # Test 1: Basic SVG download
    try:
        params = {
            "name": "Antoine Moreau",
            "phone": "+33 2 11 22 33 44",
            "email": "antoine.moreau@example.fr",
            "company": "Digital Agency",
            "title": "Designer UX/UI",
            "color": "#9900cc",
            "marker_shape": "rounded",
            "dot_shape": "rounded"
        }
        
        response = requests.get(f"{API_URL}/download-svg", params=params, timeout=10)
        tester.test_result("SVG download", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
        
        if response.status_code == 200:
            tester.test_result("SVG content type", 
                              response.headers.get('content-type') == 'image/svg+xml',
                              f"Content-Type: {response.headers.get('content-type')}")
            
            # Check filename in Content-Disposition header
            content_disposition = response.headers.get('content-disposition', '')
            tester.test_result("SVG filename contains FoxVelocityCreation", 
                              'FoxVelocityCreation.svg' in content_disposition,
                              f"Content-Disposition: {content_disposition}")
            
            # Validate SVG content
            svg_content = response.text
            tester.test_result("SVG download content is valid", 
                              svg_content.startswith('<?xml') and '<svg' in svg_content,
                              "Invalid SVG format")
            
            # Try to parse as XML
            try:
                ET.fromstring(svg_content)
                tester.test_result("Downloaded SVG is well-formed XML", True)
            except ET.ParseError as e:
                tester.test_result("Downloaded SVG is well-formed XML", False, str(e))
                
    except Exception as e:
        tester.test_result("SVG download", False, str(e))
    
    # Test 2: Different shapes
    shapes = ["square", "circle", "rounded"]
    for shape in shapes:
        try:
            params = {
                "name": f"Test {shape.title()}",
                "marker_shape": shape,
                "dot_shape": shape,
                "color": "#444444"
            }
            
            response = requests.get(f"{API_URL}/download-svg", params=params, timeout=10)
            tester.test_result(f"SVG download with {shape} shapes", 
                              response.status_code == 200,
                              f"Status: {response.status_code}")
        except Exception as e:
            tester.test_result(f"SVG download with {shape} shapes", False, str(e))
    
    return tester

def test_error_handling():
    """Test error handling scenarios"""
    tester = QRCodeTester()
    
    # Test 1: Invalid color format (should still work or handle gracefully)
    try:
        payload = {
            "name": "Test User",
            "color": "invalid-color",
            "marker_shape": "square",
            "dot_shape": "square"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        # This should either work (fallback to default) or return an error
        tester.test_result("Invalid color handling", 
                          response.status_code in [200, 400, 422],
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("Invalid color handling", False, str(e))
    
    # Test 2: Invalid shape
    try:
        payload = {
            "name": "Test User",
            "color": "#000000",
            "marker_shape": "invalid-shape",
            "dot_shape": "square"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        tester.test_result("Invalid shape handling", 
                          response.status_code in [200, 400, 422],
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("Invalid shape handling", False, str(e))
    
    # Test 3: Invalid logo base64
    try:
        payload = {
            "name": "Test User",
            "color": "#000000",
            "logo_base64": "invalid-base64-data"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        # Should handle gracefully (ignore logo or return error)
        tester.test_result("Invalid logo base64 handling", 
                          response.status_code in [200, 400, 422],
                          f"Status: {response.status_code}")
    except Exception as e:
        tester.test_result("Invalid logo base64 handling", False, str(e))
    
    return tester

def test_vcard_format():
    """Test vCard format compliance"""
    tester = QRCodeTester()
    
    try:
        payload = {
            "name": "Émilie Rousseau",
            "phone": "+33 3 55 66 77 88",
            "email": "emilie.rousseau@example.fr",
            "company": "Créative Solutions",
            "title": "Directrice Artistique",
            "url_work": "https://creative-solutions.fr",
            "url_home": "https://emilie-rousseau.com"
        }
        
        response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            vcard = data.get("vcard_content", "")
            
            # Test vCard format compliance
            tester.test_result("vCard starts with BEGIN:VCARD", 
                              vcard.startswith("BEGIN:VCARD"),
                              "vCard doesn't start with BEGIN:VCARD")
            
            tester.test_result("vCard ends with END:VCARD", 
                              vcard.strip().endswith("END:VCARD"),
                              "vCard doesn't end with END:VCARD")
            
            tester.test_result("vCard contains VERSION", 
                              "VERSION:" in vcard,
                              "vCard missing VERSION field")
            
            tester.test_result("vCard contains FN (Full Name)", 
                              "FN:" in vcard,
                              "vCard missing FN field")
            
            # Test specific data
            tester.test_result("vCard contains correct name", 
                              "Émilie Rousseau" in vcard,
                              "Name not found in vCard")
            
            tester.test_result("vCard contains correct email", 
                              "emilie.rousseau@example.fr" in vcard,
                              "Email not found in vCard")
            
            tester.test_result("vCard contains correct company", 
                              "Créative Solutions" in vcard,
                              "Company not found in vCard")
            
        else:
            tester.test_result("vCard format test", False, f"Status: {response.status_code}")
            
    except Exception as e:
        tester.test_result("vCard format test", False, str(e))
    
    return tester

def main():
    """Run all tests"""
    print("🚀 Starting QR Code Generator Backend Tests")
    print("=" * 60)
    
    all_testers = []
    
    # Run all test suites
    print("\n📡 Testing Basic Connectivity...")
    all_testers.append(test_basic_connectivity())
    
    print("\n🎯 Testing QR Code Generation (POST /api/qr-code)...")
    all_testers.append(test_qr_code_generation())
    
    print("\n🎨 Testing SVG QR Code Generation (POST /api/qr-code-svg)...")
    all_testers.append(test_qr_code_svg_generation())
    
    print("\n📥 Testing PNG Download (GET /api/download-png)...")
    all_testers.append(test_png_download())
    
    print("\n📄 Testing SVG Download (GET /api/download-svg)...")
    all_testers.append(test_svg_download())
    
    print("\n🔧 Testing vCard Format...")
    all_testers.append(test_vcard_format())
    
    print("\n⚠️  Testing Error Handling...")
    all_testers.append(test_error_handling())
    
    # Overall summary
    total_passed = sum(t.passed for t in all_testers)
    total_failed = sum(t.failed for t in all_testers)
    all_errors = []
    for t in all_testers:
        all_errors.extend(t.errors)
    
    print(f"\n{'='*60}")
    print(f"🏁 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📊 Total Tests: {total_passed + total_failed}")
    
    if all_errors:
        print(f"\n🚨 CRITICAL ERRORS:")
        for error in all_errors:
            print(f"  - {error}")
    
    success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("🎉 All tests passed! Backend is working correctly.")
        return True
    else:
        print(f"⚠️  {total_failed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)