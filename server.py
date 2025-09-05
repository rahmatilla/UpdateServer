from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from typing import Dict
import shutil
import os
import json
import hashlib
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

domen = os.getenv("DOMEN")

# Директория для хранения моделей и метаданных
MODELS_DIR = "./models"
META_FILE = os.path.join(MODELS_DIR, "models_metadata.json")
os.makedirs(MODELS_DIR, exist_ok=True)

# -------------------------------
# Загрузка/сохранение метаданных
# -------------------------------
def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r") as f:
            return json.load(f)
    else:
        # Если файла нет — инициализируем пустую структуру
        return {"versions": {}, "links": {}}

def save_metadata(data):
    with open(META_FILE, "w") as f:
        json.dump(data, f, indent=4)

def calculate_md5(file_path: str) -> str:
    """Вычислить MD5-хэш файла"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

metadata = load_metadata()
CURRENT_VERSIONS = metadata.get("versions", {})
MODEL_LINKS = metadata.get("links", {})
MODEL_HASHES = metadata.get("hashes", {})

app.mount("/files", StaticFiles(directory="models"), name="files")

# -------------------------------
# Pydantic модель
# -------------------------------
class VersionRequest(BaseModel):
    versions: Dict[str, str]

# -------------------------------
# Эндпоинты
# -------------------------------
@app.post("/check_models")
def check_models(request: VersionRequest):
    update_required = False
    models_to_update = {}

    for model, current_version in CURRENT_VERSIONS.items():
        device_version = request.versions.get(model)
        if device_version != current_version:
            update_required = True
            models_to_update[model] = {
                "url": MODEL_LINKS[model],
                "md5": MODEL_HASHES.get(model, "")
            }

    if update_required:
        return {
            "update_required": True,
            "versions": CURRENT_VERSIONS,
            "models": models_to_update
        }
    else:
        return {"update_required": False}


@app.post("/upload_model")
async def upload_model(
    file: UploadFile,
    model_name: str = Form(...),
    version: str = Form(...)
):
    """Админ загружает новую модель или архив приложения"""
    try:
        # Сохраняем файл
        file_path = os.path.join(MODELS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Вычисляем MD5
        md5 = calculate_md5(file_path)

        # Обновляем метаданные
        CURRENT_VERSIONS[model_name] = version
        MODEL_LINKS[model_name] = f"http://{domen}/files/{file.filename}"
        MODEL_HASHES[model_name] = md5

        save_metadata({"versions": CURRENT_VERSIONS, "links": MODEL_LINKS, "hashes": MODEL_HASHES})

        return {
            "success": True,
            "message": f"Model {model_name} updated to version {version}",
            "versions": CURRENT_VERSIONS,
            "link": MODEL_LINKS[model_name],
            "md5": md5
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
