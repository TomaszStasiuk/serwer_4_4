from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import List, Optional
import re
import logging
import json

app = FastAPI()

# Konfiguracja loggera dla aplikacji
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False  # Zapobiega podwójnemu logowaniu

class Instruction(BaseModel):
    instruction: str

TERRAIN_MAP = [
    ["Punkt startowy", "Trawa", "Drzewo", "Dom"],
    ["Trawa", "Wiatrak", "Trawa", "Trawa"],
    ["Trawa", "Trawa", "Skały", "Las"],
    ["Góry", "Góry", "Samochód", "Jaskinia"]
]

API_KEY = "7d03adb9-c164-497d-be2b-e42ee7a5a62b"

def parse_instruction(instruction: str) -> List[str]:
    instruction = instruction.lower()
    moves = []

    direction_map = {
        "prawo": "RIGHT",
        "lewo": "LEFT",
        "dół": "DOWN",
        "dol": "DOWN",
        "górę": "UP",
        "gora": "UP",
        "gore": "UP"
    }

    # Znajdź wszystkie wystąpienia liczebników i kierunków
    pattern = r'(\d+)\s+(razy\s+)?(prawo|lewo|dół|dol|górę|gora|gore)'
    matches = re.findall(pattern, instruction)

    for match in matches:
        count = int(match[0])
        direction = match[2]
        moves.extend([direction_map[direction]] * count)

    # Dodaj pojedyncze kierunki bez liczebników
    for direction in direction_map.keys():
        if direction in instruction:
            # Unikaj podwójnego dodawania jeśli już zostały dodane przez liczebnik
            if not re.search(r'\d+\s+razy\s+' + direction, instruction):
                moves.append(direction_map[direction])

    return moves

def get_final_position(moves: List[str]) -> (int, int):
    row, col = 0, 0  # Startujemy z (0,0)
    for move in moves:
        if move == "UP" and row > 0:
            row -= 1
        elif move == "DOWN" and row < 3:
            row += 1
        elif move == "LEFT" and col > 0:
            col -= 1
        elif move == "RIGHT" and col < 3:
            col += 1
    return row, col

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Odczytaj ciało żądania
    try:
        body_bytes = await request.body()
        body = body_bytes.decode('utf-8')
    except Exception:
        body = "<nie można odczytać ciała żądania>"

    # Skopiuj nagłówki i usuń klucz API z logów
    headers = dict(request.headers)
    headers.pop("apikey", None)  # Usuń 'apikey' z nagłówków

    # Logowanie szczegółów żądania
    logger.info(
        f"Request: {request.method} {request.url}\n"
        f"Headers: {json.dumps(headers)}\n"
        f"Body: {body}"
    )

    response = await call_next(request)

    # Logowanie statusu odpowiedzi
    logger.info(f"Response status: {response.status_code}")

    return response

@app.get("/")
def read_root():
    return {"message": "API Map działa poprawnie!"}

@app.post("/map/")
def process_map_instruction(instr: Instruction, apikey: Optional[str] = Header(None)):
    if apikey != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    moves = parse_instruction(instr.instruction)
    if not moves:
        raise HTTPException(status_code=400, detail="Nie rozpoznano żadnych ruchów w instrukcji.")

    row, col = get_final_position(moves)
    description = TERRAIN_MAP[row][col]

    # Upewnij się, że opis ma maksymalnie 2 słowa
    description_words = description.split()
    if len(description_words) > 2:
        description = ' '.join(description_words[:2])

    return {"description": description}

# Opcjonalny endpoint bez ukośnika
@app.post("/map")
def process_map_instruction_no_slash(instr: Instruction, apikey: Optional[str] = Header(None)):
    return process_map_instruction(instr, apikey)
