import os
import csv
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any

# Import from your modules — using YOUR actual variable names
from database import get_db_connection, init_db, get_all_cases
from config import reg_div, metro_list

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="DCLM Land Litigation System")

# Static files & templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
init_db()

# --------------------------
# Helper: Verify Admin Login
# --------------------------
def verify_admin(username: Optional[str], password: Optional[str]) -> bool:
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        return False
    return username.strip() == admin_user and password.strip() == admin_pass

# --------------------------
# Routes
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Extract region names from reg_div keys
    regions: List[str] = list(reg_div.keys())
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "regions": regions}
    )

@app.get("/api/divisions/{region}")
async def get_divisions(region: str):
    # Return divisions for selected region, or empty list if not found
    return {"divisions": reg_div.get(region, [])}

@app.get("/api/metro-areas")
async def get_metro_areas():
    # Use your metro list from config
    return {"metro_areas": metro_list}

@app.post("/submit")
async def submit_case(
    request: Request,
    region: str = Form(...),
    division: str = Form(...),
    metro_area: Optional[str] = Form(None),
    land_location: str = Form(...),
    land_size: str = Form(...),
    lawyer_name: str = Form(...),
    court_name: str = Form(...),
    dispute_reason: str = Form(...),
    years_litigation: int = Form(...)  # ✅ Added new field
):
    conn = get_db_connection()
    if not conn:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "regions": list(reg_div.keys()), "error": "Database connection failed. Please try again later."}
        )

    try:
        cursor = conn.cursor()
        # ✅ Updated query to include new column
        query = """
            INSERT INTO land_cases
            (region, division, metro_area, land_location, land_size, lawyer_name, court_name, dispute_reason, years_litigation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            region, division, metro_area, land_location,
            land_size, lawyer_name, court_name, dispute_reason, years_litigation
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "regions": list(reg_div.keys()), "success": True}
        )

    except Exception as e:
        print(f"Submission error: {e}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "regions": list(reg_div.keys()), "error": "Failed to submit form. Please check your entries."}
        )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "show_login": True}
    )

@app.post("/admin", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if verify_admin(username, password):
        cases = get_all_cases()
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "show_login": False, "cases": cases}
        )
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "show_login": True, "error": "Invalid username or password"}
    )

@app.get("/export/csv")
async def export_csv(request: Request, username: Optional[str] = None, password: Optional[str] = None):
    if not verify_admin(username, password):
        return RedirectResponse(url="/admin", status_code=303)

    cases = get_all_cases()
    output = StringIO()
    writer = csv.writer(output)
    # ✅ Updated header to include new field
    writer.writerow([
        "ID", "Region", "Division", "Metro Area", "Land Location",
        "Land Size", "Lawyer Name", "Court Name", "Dispute Reason",
        "Years in Litigation", "Submitted At"
    ])

    for case in cases:
        # ✅ Added new field to CSV row
        writer.writerow([
            case.get("id", ""),
            case.get("region", ""),
            case.get("division", ""),
            case.get("metro_area", ""),
            case.get("land_location", ""),
            case.get("land_size", ""),
            case.get("lawyer_name", ""),
            case.get("court_name", ""),
            case.get("dispute_reason", ""),
            case.get("years_litigation", ""),
            case.get("submitted_at", datetime.now()).strftime("%Y-%m-%d %H:%M")
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dclm_land_cases_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    # ✅ Updated port to match your chosen free port 8010
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)