from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional
import logging
import openai
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Wczytuje zmienne z .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(os.environ)

if not OPENAI_API_KEY:
    print("Nie udało się wczytać zmiennej OPENAI_API_KEY. Sprawdź konfigurację.")
else:
    print("Zmienne środowiskowa OPENAI_API_KEY została poprawnie załadowana.")
client = openai.Client(api_key=OPENAI_API_KEY)

# FastAPI setup
app = FastAPI()

# Konfiguracja loggera
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Model danych wejściowych
class Instruction(BaseModel):
    instruction: str

# Klucz API do autoryzacji
API_KEY = "7d03adb9-c164-497d-be2b-e42ee7a5a62b"

# Funkcja generująca prompt
def generate_prompt(instruction: str) -> str:
    return f"""
    Masz mapę w układzie współrzędnych 4x4, gdzie punkt startowy to (1,1), a granica mapy to (4,4). Poruszasz się w kierunkach: góra (-1 w osi X), dół (+1 w osi X), lewo (-1 w osi Y), prawo (+1 w osi Y). Oto mapa:

    (1,1) GPS — Punkt startowy
    (1,2) Trawa
    (1,3) Drzewo
    (1,4) Dom
    (2,1) Trawa
    (2,2) Wiatrak
    (2,3) Trawa
    (2,4) Trawa
    (3,1) Trawa
    (3,2) Trawa
    (3,3) Skały
    (3,4) Drzewa
    (4,1) Góry
    (4,2) Góry
    (4,3) Samochód
    (4,4) Jaskinia

    Zaczynasz od (1,1). Na podstawie podanej instrukcji lotu, przetłumacz ruch na współrzędne końcowe i opisz, co znajduje się pod dronem w sposób zrozumiały w języku naturalnym.

    Instrukcja: "{instruction}"

    Zwróć odpowiedź w formacie JSON: {{"description": "opis miejsca"}}.
    """

# Funkcja do komunikacji z OpenAI API
def ask_chatgpt_with_prompt(instruction: str) -> str:
    try:
        prompt = generate_prompt(instruction)
        response = client.chat_completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś asystentem pomagającym w nawigacji drona. Twoim zadaniem jest analiza mapy i opis miejsca, nad którym dron zawisł, na podstawie instrukcji lotu."},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        logger.error(f"Błąd komunikacji z OpenAI API: {e}")
        return f"Błąd: {e}"

# Middleware do logowania
@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    logger.info(f"Request: {request.method} {request.url}\nBody: {body.decode('utf-8')}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Endpoint testowy
@app.get("/")
def read_root():
    return {"message": "API działa poprawnie!"}

# Endpoint obsługujący mapę
@app.post("/map/")
def process_map_instruction(instr: Instruction, apikey: Optional[str] = Header(None)):
    if apikey != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Zapytanie do ChatGPT
    description = ask_chatgpt_with_prompt(instr.instruction)
    if "Błąd" in description:
        raise HTTPException(status_code=500, detail=description)

    # Zwracanie odpowiedzi
    return json.loads(description)


