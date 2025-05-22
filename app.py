# app.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
import uuid
from usage_tracker import MONTHLY_LIMIT, get_usage
from vision_utils import detect_text, calculate_text_similarity, find_line_differences

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.post("/compare/")
async def compare_images(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    path1 = f"photos/{uuid.uuid4()}.jpg"
    path2 = f"photos/{uuid.uuid4()}.jpg"

    with open(path1, "wb") as f:
        f.write(await file1.read())
    with open(path2, "wb") as f:
        f.write(await file2.read())

    text1 = detect_text(path1)
    text2 = detect_text(path2)

    similarity = calculate_text_similarity(text1, text2)
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    diff_result = find_line_differences(lines1, lines2)

    return {
        "similarity": similarity,
        "text1": text1,
        "text2": text2,
        "deleted": diff_result["deleted"],
        "modified": diff_result["modified"],
        "added": diff_result["added"]
    }

@app.get("/usage")
async def get_usage_info():
    data = get_usage()
    return {
        "month": data["month"],
        "count": data["count"],
        "monthly_limit": MONTHLY_LIMIT,
        "limit_reached": data["count"] >= MONTHLY_LIMIT
    }

@app.get("/")
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})