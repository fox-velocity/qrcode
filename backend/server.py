from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
from io import BytesIO

from qr_generator import QRGenerator, ErrorCorrectionLevel, generate_vcard, create_qr_image, create_qr_svg


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class QRCodeRequest(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    url_work: str = ""
    url_home: str = ""
    color: str = "#000000"
    marker_shape: str = "square"  # square, circle, rounded
    dot_shape: str = "square"     # square, circle, rounded
    logo_base64: Optional[str] = None
    logo_size: int = 30

class QRCodeResponse(BaseModel):
    qr_image_base64: str
    vcard_content: str

class QRCodeSVGResponse(BaseModel):
    svg_content: str
    vcard_content: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/qr-code", response_model=QRCodeResponse)
async def generate_qr_code(request: QRCodeRequest):
    """Generate QR code with vCard data"""
    try:
        # Generate vCard content
        vcard_content = generate_vcard(
            name=request.name,
            phone=request.phone,
            email=request.email,
            company=request.company,
            title=request.title,
            url_work=request.url_work,
            url_home=request.url_home
        )
        
        # Create QR code generator
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        qr.add_data(vcard_content)
        qr.make()
        
        # Create QR code image
        qr_image_base64 = create_qr_image(
            qr_generator=qr,
            color=request.color,
            marker_shape=request.marker_shape,
            dot_shape=request.dot_shape,
            logo_base64=request.logo_base64,
            logo_size=request.logo_size
        )
        
        return QRCodeResponse(
            qr_image_base64=qr_image_base64,
            vcard_content=vcard_content
        )
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")

@api_router.post("/qr-code-svg", response_model=QRCodeSVGResponse)
async def generate_qr_code_svg(request: QRCodeRequest):
    """Generate QR code as SVG"""
    try:
        # Generate vCard content
        vcard_content = generate_vcard(
            name=request.name,
            phone=request.phone,
            email=request.email,
            company=request.company,
            title=request.title,
            url_work=request.url_work,
            url_home=request.url_home
        )
        
        # Create QR code generator
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        qr.add_data(vcard_content)
        qr.make()
        
        # Create QR code SVG
        svg_content = create_qr_svg(
            qr_generator=qr,
            color=request.color,
            marker_shape=request.marker_shape,
            dot_shape=request.dot_shape
        )
        
        return QRCodeSVGResponse(
            svg_content=svg_content,
            vcard_content=vcard_content
        )
        
    except Exception as e:
        logger.error(f"Error generating QR code SVG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating QR code SVG: {str(e)}")

@api_router.get("/download-png")
async def download_png(
    name: str,
    phone: str = "",
    email: str = "",
    company: str = "",
    title: str = "",
    url_work: str = "",
    url_home: str = "",
    color: str = "#000000",
    marker_shape: str = "square",
    dot_shape: str = "square",
    logo_base64: str = None,
    logo_size: int = 30
):
    """Download QR code as PNG file"""
    try:
        # Generate vCard content
        vcard_content = generate_vcard(
            name=name,
            phone=phone,
            email=email,
            company=company,
            title=title,
            url_work=url_work,
            url_home=url_home
        )
        
        # Create QR code generator
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        qr.add_data(vcard_content)
        qr.make()
        
        # Create QR code image
        qr_image_base64 = create_qr_image(
            qr_generator=qr,
            color=color,
            marker_shape=marker_shape,
            dot_shape=dot_shape,
            logo_base64=logo_base64,
            logo_size=logo_size
        )
        
        # Extract image data
        image_data = base64.b64decode(qr_image_base64.split(',')[1])
        
        # Create filename
        first_name = name.split(' ')[0] if name else 'QRCode'
        last_name = ''.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
        filename = f"{first_name}{last_name}FoxVelocityCreation.png"
        
        return Response(
            content=image_data,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading PNG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading PNG: {str(e)}")

@api_router.get("/download-svg")
async def download_svg(
    name: str,
    phone: str = "",
    email: str = "",
    company: str = "",
    title: str = "",
    url_work: str = "",
    url_home: str = "",
    color: str = "#000000",
    marker_shape: str = "square",
    dot_shape: str = "square"
):
    """Download QR code as SVG file"""
    try:
        # Generate vCard content
        vcard_content = generate_vcard(
            name=name,
            phone=phone,
            email=email,
            company=company,
            title=title,
            url_work=url_work,
            url_home=url_home
        )
        
        # Create QR code generator
        qr = QRGenerator(version=1, error_correction=ErrorCorrectionLevel.H)
        qr.add_data(vcard_content)
        qr.make()
        
        # Create QR code SVG
        svg_content = create_qr_svg(
            qr_generator=qr,
            color=color,
            marker_shape=marker_shape,
            dot_shape=dot_shape
        )
        
        # Create filename
        first_name = name.split(' ')[0] if name else 'QRCode'
        last_name = ''.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
        filename = f"{first_name}{last_name}FoxVelocityCreation.svg"
        
        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading SVG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading SVG: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
