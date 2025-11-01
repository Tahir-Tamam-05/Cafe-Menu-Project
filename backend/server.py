from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import random
import jwt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Environment variables
SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
ADMIN_EMAIL = os.environ['ADMIN_EMAIL']
JWT_SECRET = os.environ['JWT_SECRET']

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    name: str
    price: float
    description: Optional[str] = ""
    is_special: bool = False
    available: bool = True
    image_url: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItemCreate(BaseModel):
    category: str
    name: str
    price: float
    description: Optional[str] = ""
    is_special: Optional[bool] = False
    available: Optional[bool] = True
    image_url: Optional[str] = ""

class MenuItemUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_special: Optional[bool] = None
    available: Optional[bool] = None
    image_url: Optional[str] = None

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPVerification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    email: str
    otp: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

# ==================== HELPER FUNCTIONS ====================

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(email: str, otp: str):
    """Send OTP via SendGrid"""
    try:
        message = Mail(
            from_email='noreply@cafemenu.com',
            to_emails=email,
            subject='Your Café Menu Admin OTP',
            html_content=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #6B4423;">Café Menu Admin Login</h2>
                <p>Your OTP for admin login is:</p>
                <div style="background: #F5E6D3; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                    <h1 style="color: #6B4423; font-size: 36px; margin: 0; letter-spacing: 8px;">{otp}</h1>
                </div>
                <p>This OTP is valid for 10 minutes.</p>
                <p style="color: #888; font-size: 14px;">If you didn't request this OTP, please ignore this email.</p>
            </div>
            '''
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"OTP email sent to {email}. Status: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

def create_jwt_token(email: str) -> str:
    """Create JWT token for admin"""
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> str:
    """Verify JWT token and return email"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["email"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current admin from JWT token"""
    email = verify_jwt_token(credentials.credentials)
    if email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Not authorized")
    return email

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send OTP to admin email"""
    if request.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Email not authorized")
    
    # Generate OTP
    otp = generate_otp()
    
    # Store OTP in database
    otp_doc = {
        "email": request.email,
        "otp": otp,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    }
    
    # Delete any existing OTPs for this email
    await db.otp_verifications.delete_many({"email": request.email})
    
    # Insert new OTP
    await db.otp_verifications.insert_one(otp_doc)
    
    # Send email
    send_otp_email(request.email, otp)
    
    return {"message": "OTP sent successfully", "email": request.email}

@api_router.post("/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and return JWT token"""
    if request.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Email not authorized")
    
    # Find OTP in database
    otp_doc = await db.otp_verifications.find_one({"email": request.email})
    
    if not otp_doc:
        raise HTTPException(status_code=404, detail="OTP not found or expired")
    
    # Check if OTP is expired
    expires_at = datetime.fromisoformat(otp_doc["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        await db.otp_verifications.delete_one({"email": request.email})
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Verify OTP
    if otp_doc["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Delete OTP after successful verification
    await db.otp_verifications.delete_one({"email": request.email})
    
    # Create JWT token
    token = create_jwt_token(request.email)
    
    return {"token": token, "email": request.email}

# ==================== PUBLIC MENU ROUTES ====================

@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    """Get all available menu items (public)"""
    menu_items = await db.menu_items.find({"available": True}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime
    for item in menu_items:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return menu_items

@api_router.get("/menu/categories")
async def get_categories():
    """Get all unique categories"""
    categories = await db.menu_items.distinct("category")
    return {"categories": sorted(categories)}

@api_router.get("/menu/specials", response_model=List[MenuItem])
async def get_specials():
    """Get today's special items"""
    specials = await db.menu_items.find({"is_special": True, "available": True}, {"_id": 0}).to_list(1000)
    
    for item in specials:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return specials

# ==================== ADMIN MENU ROUTES ====================

@api_router.get("/admin/menu", response_model=List[MenuItem])
async def get_all_menu_items(admin_email: str = Depends(get_current_admin)):
    """Get all menu items including unavailable (admin only)"""
    menu_items = await db.menu_items.find({}, {"_id": 0}).to_list(1000)
    
    for item in menu_items:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return menu_items

@api_router.post("/admin/menu", response_model=MenuItem)
async def create_menu_item(item: MenuItemCreate, admin_email: str = Depends(get_current_admin)):
    """Create new menu item (admin only)"""
    menu_item = MenuItem(**item.model_dump())
    
    doc = menu_item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.menu_items.insert_one(doc)
    
    return menu_item

@api_router.put("/admin/menu/{item_id}", response_model=MenuItem)
async def update_menu_item(item_id: str, item: MenuItemUpdate, admin_email: str = Depends(get_current_admin)):
    """Update menu item (admin only)"""
    existing_item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in item.model_dump().items() if v is not None}
    
    if update_data:
        await db.menu_items.update_one({"id": item_id}, {"$set": update_data})
    
    # Get updated item
    updated_item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    
    if isinstance(updated_item.get('created_at'), str):
        updated_item['created_at'] = datetime.fromisoformat(updated_item['created_at'])
    
    return MenuItem(**updated_item)

@api_router.delete("/admin/menu/{item_id}")
async def delete_menu_item(item_id: str, admin_email: str = Depends(get_current_admin)):
    """Delete menu item (admin only)"""
    result = await db.menu_items.delete_one({"id": item_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return {"message": "Menu item deleted successfully"}

@api_router.put("/admin/menu/{item_id}/toggle-special")
async def toggle_special(item_id: str, admin_email: str = Depends(get_current_admin)):
    """Toggle special status of menu item"""
    existing_item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    new_status = not existing_item.get('is_special', False)
    await db.menu_items.update_one({"id": item_id}, {"$set": {"is_special": new_status}})
    
    return {"message": "Special status updated", "is_special": new_status}

@api_router.put("/admin/menu/{item_id}/toggle-available")
async def toggle_available(item_id: str, admin_email: str = Depends(get_current_admin)):
    """Toggle availability of menu item"""
    existing_item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    new_status = not existing_item.get('available', True)
    await db.menu_items.update_one({"id": item_id}, {"$set": {"available": new_status}})
    
    return {"message": "Availability updated", "available": new_status}

# ==================== PRELOAD MENU DATA ====================

@app.on_event("startup")
async def preload_menu_data():
    """Preload menu items if database is empty"""
    count = await db.menu_items.count_documents({})
    
    if count == 0:
        logger.info("Preloading menu items...")
        
        menu_data = [
            # LASSI
            {"category": "Lassi", "name": "Sweet Lassi", "price": 40, "description": "Refreshing sweet lassi made from curd and sugar"},
            {"category": "Lassi", "name": "Banana Lassi", "price": 55, "description": "Creamy banana lassi"},
            {"category": "Lassi", "name": "Mango Lassi", "price": 60, "description": "Refreshing mango lassi"},
            {"category": "Lassi", "name": "Fruit Lassi", "price": 60, "description": "Mixed fruit lassi"},
            {"category": "Lassi", "name": "Strawberry Lassi", "price": 60, "description": "Fresh strawberry lassi"},
            {"category": "Lassi", "name": "Pista Lassi", "price": 70, "description": "Rich pistachio lassi"},
            {"category": "Lassi", "name": "Chocolate Lassi", "price": 70, "description": "Chocolate flavored lassi"},
            {"category": "Lassi", "name": "Dryfruit Lassi", "price": 80, "description": "Lassi with mixed dry fruits"},
            {"category": "Lassi", "name": "Fruit & Nut Lassi", "price": 80, "description": "Premium fruit and nut lassi"},
            {"category": "Lassi", "name": "Royal Lassi", "price": 80, "description": "Special royal lassi with saffron"},
            
            # FALOODA
            {"category": "Falooda", "name": "Classic Falooda", "price": 80, "description": "Traditional falooda with rose syrup"},
            {"category": "Falooda", "name": "Pista Falooda", "price": 99, "description": "Pistachio flavored falooda"},
            {"category": "Falooda", "name": "Fruity Falooda", "price": 99, "description": "Falooda with fresh fruits"},
            {"category": "Falooda", "name": "Royal Kashmiri Falooda", "price": 120, "description": "Premium Kashmiri style falooda"},
            
            # MILK SHAKES
            {"category": "Milk Shakes", "name": "Banana Bonkers", "price": 60, "description": "Thick banana milkshake"},
            {"category": "Milk Shakes", "name": "Pista Shake", "price": 60, "description": "Pistachio milkshake"},
            {"category": "Milk Shakes", "name": "Vanilla Shake", "price": 60, "description": "Classic vanilla milkshake"},
            {"category": "Milk Shakes", "name": "Belgian Chocolate", "price": 70, "description": "Rich Belgian chocolate shake"},
            {"category": "Milk Shakes", "name": "Very Berry Strawberry", "price": 70, "description": "Strawberry milkshake"},
            {"category": "Milk Shakes", "name": "Oreo", "price": 85, "description": "Oreo cookie milkshake"},
            {"category": "Milk Shakes", "name": "Chocochip Cookies", "price": 85, "description": "Chocolate chip cookie shake"},
            {"category": "Milk Shakes", "name": "Kala Jamoon", "price": 85, "description": "Kala jamun flavored shake"},
            {"category": "Milk Shakes", "name": "Mango Alphonso", "price": 85, "description": "Alphonso mango shake"},
            {"category": "Milk Shakes", "name": "Blueberry", "price": 85, "description": "Fresh blueberry shake"},
            {"category": "Milk Shakes", "name": "Kesar Pista", "price": 85, "description": "Saffron and pistachio shake"},
            {"category": "Milk Shakes", "name": "Lychee & Lychee", "price": 110, "description": "Double lychee shake"},
            {"category": "Milk Shakes", "name": "Mango Lychee", "price": 120, "description": "Mango and lychee fusion"},
            {"category": "Milk Shakes", "name": "Cherry Bubble Shake", "price": 120, "description": "Cherry shake with popping boba"},
            {"category": "Milk Shakes", "name": "Mango Bubble Shake", "price": 120, "description": "Mango shake with popping boba"},
            {"category": "Milk Shakes", "name": "Berry Bubble Shake", "price": 120, "description": "Mixed berry shake with popping boba"},
            
            # DRY FRUIT SHAKES
            {"category": "Dry Fruit Shakes", "name": "Dry Fruit Shake", "price": 99, "description": "Mixed dry fruit shake"},
            {"category": "Dry Fruit Shakes", "name": "Arabian Night Shake", "price": 109, "description": "Arabian style dry fruit shake"},
            {"category": "Dry Fruit Shakes", "name": "Anjeer Shake", "price": 110, "description": "Fig dry fruit shake"},
            {"category": "Dry Fruit Shakes", "name": "Kaju Anjeer Shake", "price": 120, "description": "Cashew and fig shake"},
            
            # MUDS & HOTTIES
            {"category": "Muds & Hotties", "name": "Mississippi Mud", "price": 120, "description": "Rich chocolate mud"},
            {"category": "Muds & Hotties", "name": "Oreo Mud", "price": 130, "description": "Oreo chocolate mud"},
            {"category": "Muds & Hotties", "name": "KitKat Mud", "price": 130, "description": "KitKat chocolate mud"},
            {"category": "Muds & Hotties", "name": "Choco Blast", "price": 70, "description": "Hot chocolate blast"},
            {"category": "Muds & Hotties", "name": "Cafe Coffee", "price": 80, "description": "Hot café coffee"},
            {"category": "Muds & Hotties", "name": "Minty Coffee", "price": 80, "description": "Coffee with mint"},
            {"category": "Muds & Hotties", "name": "Marshmallow Hot Chocolate", "price": 90, "description": "Hot chocolate with marshmallows"},
            
            # FRIES & CRAZY BITES
            {"category": "Fries & Crazy Bites", "name": "Just Masala Fries", "price": 79, "description": "Masala seasoned fries"},
            {"category": "Fries & Crazy Bites", "name": "Chilli Cheese Fries", "price": 89, "description": "Fries with chili and cheese"},
            {"category": "Fries & Crazy Bites", "name": "Schezwan Fries", "price": 89, "description": "Spicy schezwan fries"},
            {"category": "Fries & Crazy Bites", "name": "Peri Peri Fries", "price": 99, "description": "Peri peri flavored fries"},
            {"category": "Fries & Crazy Bites", "name": "Smilies", "price": 99, "description": "Crispy potato smilies"},
            {"category": "Fries & Crazy Bites", "name": "Crazy Cheesy Nuggets", "price": 99, "description": "Cheese filled nuggets"},
            {"category": "Fries & Crazy Bites", "name": "Cheese Pizza Fingers", "price": 99, "description": "Cheesy pizza fingers"},
            {"category": "Fries & Crazy Bites", "name": "Loaded Nachos", "price": 120, "description": "Nachos with loaded toppings"},
            {"category": "Fries & Crazy Bites", "name": "Wild Wedges", "price": 120, "description": "Spicy potato wedges"},
            
            # MOMOS
            {"category": "Momos", "name": "Mix Veg Momos", "price": 89, "description": "Steamed vegetable momos"},
            {"category": "Momos", "name": "Schezwan Momos", "price": 89, "description": "Spicy schezwan momos"},
            {"category": "Momos", "name": "Paneer Momos", "price": 99, "description": "Paneer filled momos"},
            {"category": "Momos", "name": "Mushroom Momos", "price": 99, "description": "Mushroom filled momos"},
            {"category": "Momos", "name": "Corn N Cheese Momos", "price": 100, "description": "Corn and cheese momos"},
            {"category": "Momos", "name": "Paneer Tikka Momos", "price": 109, "description": "Paneer tikka flavored momos"},
            
            # BURGER PAV
            {"category": "Burger Pav", "name": "Classic Vadapav", "price": 29, "description": "Traditional Mumbai vadapav"},
            {"category": "Burger Pav", "name": "Tandoori Burgerpav", "price": 45, "description": "Tandoori flavored burger"},
            {"category": "Burger Pav", "name": "Crispy N Crunchy BP", "price": 50, "description": "Crispy burger pav"},
            {"category": "Burger Pav", "name": "Horny Corny Burgerpav", "price": 50, "description": "Corn filled burger"},
            {"category": "Burger Pav", "name": "Maharaja Burgerpav", "price": 55, "description": "Special maharaja burger"},
            {"category": "Burger Pav", "name": "Cheesemaar Burgerpav", "price": 55, "description": "Extra cheese burger"},
            
            # COLD COFFEE
            {"category": "Cold Coffee", "name": "Cold Coffee", "price": 60, "description": "Classic cold coffee"},
            {"category": "Cold Coffee", "name": "Chocolate Coffee", "price": 80, "description": "Chocolate flavored cold coffee"},
            {"category": "Cold Coffee", "name": "Oreo & Coffee", "price": 80, "description": "Oreo cold coffee"},
            {"category": "Cold Coffee", "name": "Coffee On Rocks", "price": 80, "description": "Iced coffee on rocks"},
            {"category": "Cold Coffee", "name": "Baby Bubble Coffee", "price": 110, "description": "Coffee with popping boba"},
            {"category": "Cold Coffee", "name": "Mud Coffee", "price": 120, "description": "Coffee mud shake"},
            
            # CAPPUCCINO
            {"category": "Cappuccino", "name": "Classic Cappuccino", "price": 80, "description": "Traditional cappuccino"},
            {"category": "Cappuccino", "name": "Caramel Cappuccino", "price": 90, "description": "Caramel flavored cappuccino"},
            {"category": "Cappuccino", "name": "Mocha Cappuccino", "price": 95, "description": "Chocolate mocha cappuccino"},
            
            # ON NUTELLA
            {"category": "On Nutella", "name": "Nutella Shake", "price": 120, "description": "Creamy Nutella shake"},
            {"category": "On Nutella", "name": "Nutella Brownie Icecream", "price": 135, "description": "Nutella with brownie and ice cream"},
            {"category": "On Nutella", "name": "Nutella Fudge Icecream", "price": 135, "description": "Nutella fudge with ice cream"},
            
            # ON MOJITO
            {"category": "On Mojito", "name": "Blue Blast", "price": 79, "description": "Blue mojito blast"},
            {"category": "On Mojito", "name": "Bubble Gum", "price": 89, "description": "Bubble gum mojito"},
            {"category": "On Mojito", "name": "Boba Melon", "price": 89, "description": "Melon mojito with boba"},
            {"category": "On Mojito", "name": "Mango Bubble", "price": 89, "description": "Mango mojito with boba"},
            {"category": "On Mojito", "name": "Berry Pop Bubble", "price": 99, "description": "Berry mojito with popping boba"},
            
            # ICE CREAMS
            {"category": "Ice Creams", "name": "Fruit Salad Icecream", "price": 90, "description": "Mixed fruit ice cream"},
            {"category": "Ice Creams", "name": "Fruit Salad Jelly", "price": 99, "description": "Fruit salad with jelly"},
            {"category": "Ice Creams", "name": "Mexican Brownie", "price": 80, "description": "Mexican brownie with ice cream"},
            {"category": "Ice Creams", "name": "Chocolate Fudge", "price": 80, "description": "Rich chocolate fudge"},
            {"category": "Ice Creams", "name": "Strawberry Fudge", "price": 80, "description": "Strawberry fudge ice cream"},
            {"category": "Ice Creams", "name": "Mocha Fudge", "price": 85, "description": "Coffee mocha fudge"},
            {"category": "Ice Creams", "name": "Mocha Mexican Brownie", "price": 95, "description": "Mocha brownie ice cream"},
            {"category": "Ice Creams", "name": "Black Currant Fudge", "price": 90, "description": "Black currant fudge"},
            {"category": "Ice Creams", "name": "Butterscotch Fudge", "price": 99, "description": "Butterscotch fudge ice cream"},
            {"category": "Ice Creams", "name": "Berry-O-La Fudge", "price": 99, "description": "Mixed berry fudge"},
            {"category": "Ice Creams", "name": "Gud Bud", "price": 120, "description": "Special gud bud ice cream"},
            {"category": "Ice Creams", "name": "Death By Chocolate", "price": 130, "description": "Ultimate chocolate overload"},
            {"category": "Ice Creams", "name": "Dry Fruit Sundae", "price": 135, "description": "Sundae with dry fruits"},
            {"category": "Ice Creams", "name": "Lychee With Icecream", "price": 135, "description": "Lychee ice cream special"},
            {"category": "Ice Creams", "name": "Roasted Almond", "price": 135, "description": "Roasted almond ice cream"},
            {"category": "Ice Creams", "name": "Choco Almond", "price": 135, "description": "Chocolate almond ice cream"},
            {"category": "Ice Creams", "name": "Sizzling Brownie", "price": 139, "description": "Hot sizzling brownie"},
            {"category": "Ice Creams", "name": "Kerala Puttu Ice Cream", "price": 139, "description": "Traditional Kerala puttu ice cream"},
            
            # FRESH JUICES
            {"category": "Fresh Juices", "name": "Fresh Lime", "price": 40, "description": "Fresh lime juice"},
            {"category": "Fresh Juices", "name": "Masala Lime", "price": 45, "description": "Spicy masala lime"},
            {"category": "Fresh Juices", "name": "Mint Lime", "price": 45, "description": "Refreshing mint lime"},
            {"category": "Fresh Juices", "name": "Watermelon", "price": 60, "description": "Fresh watermelon juice"},
            {"category": "Fresh Juices", "name": "Muskmelon", "price": 60, "description": "Fresh muskmelon juice"},
            {"category": "Fresh Juices", "name": "Pineapple", "price": 70, "description": "Fresh pineapple juice"},
            {"category": "Fresh Juices", "name": "Papaya", "price": 70, "description": "Fresh papaya juice"},
            {"category": "Fresh Juices", "name": "Apple", "price": 80, "description": "Fresh apple juice"},
            {"category": "Fresh Juices", "name": "Orange", "price": 80, "description": "Fresh orange juice"},
            {"category": "Fresh Juices", "name": "Mango", "price": 80, "description": "Fresh mango juice"},
            {"category": "Fresh Juices", "name": "ABC", "price": 90, "description": "Apple, Beetroot, Carrot juice"},
            {"category": "Fresh Juices", "name": "CAP", "price": 90, "description": "Carrot, Apple, Pineapple juice"},
            
            # ADD ONS
            {"category": "Add Ons", "name": "Extra Chocochips", "price": 15, "description": "Add chocolate chips"},
            {"category": "Add Ons", "name": "Extra Chocolate", "price": 15, "description": "Extra chocolate topping"},
            {"category": "Add Ons", "name": "Extra Nuts", "price": 25, "description": "Extra dry fruits and nuts"},
            {"category": "Add Ons", "name": "Extra Cheese", "price": 25, "description": "Extra cheese topping"},
            {"category": "Add Ons", "name": "Extra Sauce", "price": 20, "description": "Extra sauce of your choice"},
        ]
        
        # Create MenuItem objects and insert
        for item_data in menu_data:
            menu_item = MenuItem(**item_data)
            doc = menu_item.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.menu_items.insert_one(doc)
        
        logger.info(f"Preloaded {len(menu_data)} menu items")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
