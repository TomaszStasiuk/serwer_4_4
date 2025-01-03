# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()


# Definicja modelu danych wejściowych
class Instruction(BaseModel):
    instruction: str


# Mapa 4x4 z opisami pól (maksymalnie 2 słowa)
TERRAIN_MAP = [
    ["Punkt startowy", "Trawa", "Drzewo", "Dom"],
    ["Łąka", "Wiatrak", "Bagno", "Most"],
    ["Ruiny", "Skały", "Bagno", "Las"],
    ["Góry", "Pszczoły", "Samochód", "Jaskinia"]
]


# Funkcja do parsowania instrukcji ruchu
def parse_instruction(instruction: str) -> List[str]:
    """
    Parsuje instrukcję ruchu z języka naturalnego na listę kierunków.
    Obsługuje frazy takie jak "w prawo", "w lewo", "w dół", "w górę".
    """
    instruction = instruction.lower()
    moves = []

    # Słownik mapujący słowa na kierunki
    direction_map = {
        "prawo": "RIGHT",
        "lewo": "LEFT",
        "dół": "DOWN",
        "dol": "DOWN",  # alternatywna forma
        "górę": "UP",
        "gora": "UP",  # alternatywna forma
        "gore": "UP"  # alternatywna forma
    }

    # Rozbij instrukcję na słowa
    words = instruction.split()

    # Iteruj przez słowa i mapuj na kierunki
    for i in range(len(words)):
        word = words[i]
        if word in direction_map:
            moves.append(direction_map[word])
        # Opcjonalnie: obsługa liczebników, np. "dwa razy w prawo"
        elif word.isdigit() and i + 2 < len(words):
            num = int(word)
            next_word = words[i + 2]
            if next_word in direction_map:
                moves.extend([direction_map[next_word]] * num)

    return moves


# Funkcja do określenia finalnej pozycji
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


# Endpoint główny
@app.get("/")
def read_root():
    return {"message": "API Map działa poprawnie!"}


# Endpoint do przetwarzania instrukcji ruchu
@app.post("/map/")
def process_map_instruction(instr: Instruction):
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