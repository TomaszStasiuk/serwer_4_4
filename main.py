# main.py

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Przykładowa klasa wejściowa
class Instruction(BaseModel):
    instruction: str

# Przykładowa mapa - 2D array (4x4)
TERRAIN_MAP = [
    ["start", "pole trawy", "drzewo", "dom"],
    ["pole", "wiatrak", "bagno", "most"],
    ["ruiny", "skały", "bagno", "las"],
    ["góry", "pszczoly", "samochód", "jaskinia"]
]

@app.get("/")
def root():
    return {"message": "Hello from FastAPI on Railway!"}

@app.post("/map/")
def check_map(instr: Instruction):
    # Zrobimy pseudo parser ruchów, tu cokolwiek prostego
    text = instr.instruction.lower()
    # Jako przykład: "w prawo" -> column++, "w dół" -> row++
    row, col = 0, 0
    if "prawo" in text:
        col = min(col + 1, 3)
    if "dół" in text or "dol" in text:
        row = min(row + 1, 3)
    # Zwróć krótką informację
    return {"description": TERRAIN_MAP[row][col]}