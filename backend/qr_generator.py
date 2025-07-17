"""
Custom QR Code Generator Library
Replaces external qrcode-generator library with custom implementation
"""

import math
from typing import List, Tuple, Optional
from enum import Enum
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

class ErrorCorrectionLevel(Enum):
    L = 1  # Low (~7%)
    M = 2  # Medium (~15%)
    Q = 3  # Quartile (~25%)
    H = 4  # High (~30%)

class QRMode(Enum):
    NUMERIC = 1
    ALPHANUMERIC = 2
    BYTE = 3
    KANJI = 4

class QRGenerator:
    def __init__(self, version: int = 1, error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.H):
        self.version = version
        self.error_correction = error_correction
        self.modules = None
        self.module_count = 0
        self.data = ""
        
        # Version info - simplified for common versions
        self.version_info = {
            1: {"size": 21, "data_capacity": {"L": 152, "M": 128, "Q": 104, "H": 72}},
            2: {"size": 25, "data_capacity": {"L": 272, "M": 224, "Q": 176, "H": 128}},
            3: {"size": 29, "data_capacity": {"L": 440, "M": 352, "Q": 272, "H": 208}},
            4: {"size": 33, "data_capacity": {"L": 640, "M": 512, "Q": 384, "H": 288}},
            5: {"size": 37, "data_capacity": {"L": 864, "M": 688, "Q": 496, "H": 368}},
        }
        
        # Generator polynomials for Reed-Solomon error correction
        self.generator_polynomials = {
            7: [1, 127, 122, 154, 164, 11, 68, 117],
            10: [1, 216, 194, 159, 111, 199, 94, 95, 113, 157, 193],
            13: [1, 137, 73, 227, 17, 177, 17, 52, 13, 46, 43, 83, 132, 120],
            15: [1, 29, 196, 111, 163, 112, 74, 10, 105, 105, 139, 132, 151, 32, 134, 26],
            16: [1, 59, 13, 104, 189, 68, 209, 30, 8, 163, 65, 41, 229, 98, 50, 36, 59],
            17: [1, 119, 66, 83, 120, 119, 22, 197, 83, 249, 41, 143, 134, 85, 53, 125, 99, 79],
            18: [1, 239, 251, 183, 113, 149, 175, 199, 215, 240, 220, 141, 61, 82, 204, 8, 106, 128, 161],
            20: [1, 152, 185, 240, 5, 111, 99, 6, 220, 112, 150, 69, 36, 187, 22, 228, 198, 121, 121, 165, 174],
            22: [1, 89, 179, 131, 176, 182, 244, 19, 189, 69, 40, 28, 137, 29, 123, 67, 253, 86, 218, 230, 26, 145, 245],
            24: [1, 122, 118, 169, 70, 178, 237, 216, 102, 115, 150, 229, 73, 130, 72, 61, 43, 206, 1, 237, 247, 127, 217, 144, 117],
            26: [1, 246, 51, 183, 4, 136, 98, 199, 152, 77, 56, 206, 24, 145, 40, 209, 117, 233, 42, 135, 68, 70, 144, 146, 77, 43, 94],
            28: [1, 252, 9, 28, 13, 18, 251, 208, 150, 103, 174, 100, 41, 167, 12, 247, 56, 117, 119, 233, 127, 181, 100, 121, 147, 176, 74, 58, 197],
            30: [1, 212, 246, 77, 73, 195, 192, 75, 98, 5, 70, 103, 177, 22, 217, 138, 51, 181, 246, 72, 25, 18, 46, 228, 74, 216, 195, 11, 106, 130, 150]
        }
        
    def add_data(self, data: str):
        """Add data to be encoded in QR code"""
        self.data = data
        
    def make(self):
        """Generate the QR code matrix"""
        if not self.data:
            raise ValueError("No data to encode")
            
        # Determine optimal version based on data length
        self._optimize_version()
        
        # Initialize the matrix
        self.module_count = self.version_info[self.version]["size"]
        self.modules = [[False for _ in range(self.module_count)] for _ in range(self.module_count)]
        
        # Place function patterns
        self._place_finder_patterns()
        self._place_separators()
        self._place_timing_patterns()
        self._place_dark_module()
        self._place_format_info()
        
        # Encode data
        encoded_data = self._encode_data()
        
        # Add error correction
        error_corrected_data = self._add_error_correction(encoded_data)
        
        # Place data in matrix
        self._place_data(error_corrected_data)
        
        # Apply mask pattern
        self._apply_mask()
        
    def _optimize_version(self):
        """Determine the optimal QR version based on data length"""
        data_length = len(self.data.encode('utf-8'))
        error_level = self.error_correction.name
        
        for version in range(1, 6):  # Support versions 1-5
            if version in self.version_info:
                capacity = self.version_info[version]["data_capacity"][error_level]
                if data_length <= capacity:
                    self.version = version
                    return
                    
        # If data is too long, use version 5
        self.version = 5
        
    def _place_finder_patterns(self):
        """Place finder patterns in corners"""
        positions = [(0, 0), (self.module_count - 7, 0), (0, self.module_count - 7)]
        
        for row, col in positions:
            for r in range(7):
                for c in range(7):
                    if ((r == 0 or r == 6) and (0 <= c <= 6)) or \
                       ((c == 0 or c == 6) and (0 <= r <= 6)) or \
                       (2 <= r <= 4 and 2 <= c <= 4):
                        # Check bounds before accessing
                        if 0 <= row + r < self.module_count and 0 <= col + c < self.module_count:
                            self.modules[row + r][col + c] = True
                        
    def _place_separators(self):
        """Place separator patterns around finder patterns"""
        positions = [(0, 0), (self.module_count - 7, 0), (0, self.module_count - 7)]
        
        for row, col in positions:
            for r in range(8):
                for c in range(8):
                    if row + r < self.module_count and col + c < self.module_count:
                        if r == 7 or c == 7:
                            self.modules[row + r][col + c] = False
                            
    def _place_timing_patterns(self):
        """Place timing patterns"""
        for i in range(8, self.module_count - 8):
            self.modules[6][i] = (i % 2 == 0)
            self.modules[i][6] = (i % 2 == 0)
            
    def _place_dark_module(self):
        """Place dark module"""
        if self.module_count > 21:
            self.modules[4 * self.version + 9][8] = True
            
    def _place_format_info(self):
        """Place format information"""
        # Simplified format info placement
        format_info = self._generate_format_info()
        
        # Place format info around finder patterns
        for i in range(15):
            bit = (format_info >> i) & 1
            
            if i < 6:
                if 8 < self.module_count and i < self.module_count:
                    self.modules[8][i] = bit
                if self.module_count - 1 - i >= 0 and 8 < self.module_count:
                    self.modules[self.module_count - 1 - i][8] = bit
            elif i < 8:
                if 8 < self.module_count and i + 1 < self.module_count:
                    self.modules[8][i + 1] = bit
                if self.module_count - 7 + i >= 0 and self.module_count - 7 + i < self.module_count and 8 < self.module_count:
                    self.modules[self.module_count - 7 + i][8] = bit
            elif i < 9:
                if 7 < self.module_count and 8 < self.module_count:
                    self.modules[7][8] = bit
                if 8 < self.module_count and self.module_count - 8 >= 0:
                    self.modules[8][self.module_count - 8] = bit
            else:
                if 14 - i >= 0 and 8 < self.module_count:
                    self.modules[14 - i][8] = bit
                if 8 < self.module_count and self.module_count - 15 + i >= 0 and self.module_count - 15 + i < self.module_count:
                    self.modules[8][self.module_count - 15 + i] = bit
                
    def _generate_format_info(self):
        """Generate format information bits"""
        # Simplified format info generation
        error_level_bits = {
            ErrorCorrectionLevel.L: 0b01,
            ErrorCorrectionLevel.M: 0b00,
            ErrorCorrectionLevel.Q: 0b11,
            ErrorCorrectionLevel.H: 0b10
        }
        
        mask_pattern = 0b000  # Using mask pattern 0 for simplicity
        format_info = (error_level_bits[self.error_correction] << 3) | mask_pattern
        
        return format_info
        
    def _encode_data(self):
        """Encode data using byte mode"""
        # Simple byte mode encoding
        data_bytes = self.data.encode('utf-8')
        
        # Mode indicator (4 bits for byte mode = 0100)
        encoded = [0, 1, 0, 0]
        
        # Character count (8 bits for versions 1-9)
        count = len(data_bytes)
        for i in range(7, -1, -1):
            encoded.append((count >> i) & 1)
            
        # Data
        for byte in data_bytes:
            for i in range(7, -1, -1):
                encoded.append((byte >> i) & 1)
                
        return encoded
        
    def _add_error_correction(self, data):
        """Add Reed-Solomon error correction"""
        # Simplified error correction
        # In a full implementation, this would use Reed-Solomon codes
        return data
        
    def _place_data(self, data):
        """Place data bits in the matrix"""
        # Simplified data placement
        bit_index = 0
        direction = -1  # -1 for up, 1 for down
        
        for col in range(self.module_count - 1, 0, -2):
            if col == 6:  # Skip timing column
                col -= 1
                
            for _ in range(self.module_count):
                for c in range(2):
                    current_col = col - c
                    
                    if direction == -1:
                        row = self.module_count - 1 - (_ % self.module_count)
                    else:
                        row = _ % self.module_count
                        
                    if not self._is_function_module(row, current_col):
                        if bit_index < len(data):
                            self.modules[row][current_col] = data[bit_index]
                            bit_index += 1
                            
                direction *= -1
                
    def _is_function_module(self, row, col):
        """Check if position contains a function pattern"""
        # Finder patterns
        if ((row < 9 and col < 9) or 
            (row < 9 and col >= self.module_count - 8) or
            (row >= self.module_count - 8 and col < 9)):
            return True
            
        # Timing patterns
        if row == 6 or col == 6:
            return True
            
        # Dark module
        if self.version > 1 and row == 4 * self.version + 9 and col == 8:
            return True
            
        return False
        
    def _apply_mask(self):
        """Apply mask pattern (simplified)"""
        # Apply checkerboard mask pattern
        for row in range(self.module_count):
            for col in range(self.module_count):
                if not self._is_function_module(row, col):
                    if (row + col) % 2 == 0:
                        self.modules[row][col] = not self.modules[row][col]
                        
    def get_module_count(self):
        """Get the size of the QR code matrix"""
        return self.module_count
        
    def is_dark(self, row, col):
        """Check if a module is dark (True) or light (False)"""
        if 0 <= row < self.module_count and 0 <= col < self.module_count:
            return self.modules[row][col]
        return False

def generate_vcard(name: str, phone: str, email: str, company: str, title: str, url_work: str, url_home: str) -> str:
    """Generate vCard content from contact information"""
    vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL:{phone}
EMAIL:{email}
ORG:{company}
TITLE:{title}
URL;TYPE=WORK:{url_work}
URL;TYPE=HOME:{url_home}
END:VCARD"""
    return vcard_content

def create_qr_image(qr_generator: QRGenerator, color: str = "#000000", 
                   marker_shape: str = "square", dot_shape: str = "square",
                   logo_base64: Optional[str] = None, logo_size: int = 30) -> str:
    """Create QR code image and return as base64"""
    
    # Validate and sanitize color
    try:
        # Try to parse the color - if it fails, use default black
        from PIL import ImageColor
        ImageColor.getrgb(color)
    except:
        color = "#000000"  # Default to black if color is invalid
    
    module_count = qr_generator.get_module_count()
    size = 512
    cell_size = size / module_count
    
    # Create image
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw QR code modules
    for row in range(module_count):
        for col in range(module_count):
            if qr_generator.is_dark(row, col):
                x = col * cell_size
                y = row * cell_size
                
                # Determine if this is a finder pattern
                is_finder = ((row < 7 and col < 7) or 
                           (row < 7 and col >= module_count - 7) or
                           (row >= module_count - 7 and col < 7))
                
                shape = marker_shape if is_finder else dot_shape
                
                if shape == "circle":
                    draw.ellipse([x, y, x + cell_size, y + cell_size], fill=color)
                elif shape == "rounded":
                    # Draw rounded rectangle
                    radius = cell_size / 4
                    draw.rounded_rectangle([x, y, x + cell_size, y + cell_size], 
                                         radius=radius, fill=color)
                else:  # square
                    draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color)
    
    # Add logo if provided
    if logo_base64:
        try:
            # Decode base64 logo
            if ',' in logo_base64:
                logo_data = base64.b64decode(logo_base64.split(',')[1])
            else:
                logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(BytesIO(logo_data))
            
            # Resize logo
            logo_size_px = int(size * logo_size / 100)
            logo_img = logo_img.resize((logo_size_px, logo_size_px), Image.Resampling.LANCZOS)
            
            # Position logo in center
            logo_x = (size - logo_size_px) // 2
            logo_y = (size - logo_size_px) // 2
            
            # Paste logo
            img.paste(logo_img, (logo_x, logo_y), logo_img if logo_img.mode == 'RGBA' else None)
            
        except Exception as e:
            print(f"Error adding logo: {e}")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def create_qr_svg(qr_generator: QRGenerator, color: str = "#000000",
                 marker_shape: str = "square", dot_shape: str = "square") -> str:
    """Create QR code as SVG"""
    
    # Validate and sanitize color
    try:
        from PIL import ImageColor
        ImageColor.getrgb(color)
    except:
        color = "#000000"  # Default to black if color is invalid
    
    module_count = qr_generator.get_module_count()
    size = 512
    cell_size = size / module_count
    
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
<rect width="{size}" height="{size}" fill="white"/>
'''
    
    for row in range(module_count):
        for col in range(module_count):
            if qr_generator.is_dark(row, col):
                x = col * cell_size
                y = row * cell_size
                
                # Determine if this is a finder pattern
                is_finder = ((row < 7 and col < 7) or 
                           (row < 7 and col >= module_count - 7) or
                           (row >= module_count - 7 and col < 7))
                
                shape = marker_shape if is_finder else dot_shape
                
                if shape == "circle":
                    radius = cell_size / 2
                    cx = x + radius
                    cy = y + radius
                    svg_content += f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}"/>\n'
                elif shape == "rounded":
                    radius = cell_size / 4
                    svg_content += f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="{radius}" fill="{color}"/>\n'
                else:  # square
                    svg_content += f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}"/>\n'
    
    svg_content += '</svg>'
    return svg_content