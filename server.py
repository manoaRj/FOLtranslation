from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# instance fastapi
app = FastAPI(title="Traducteur Logique Premier Ordre", description="API pour traduire des phrases en logique de premier ordre")

# routeur
api_router = APIRouter(prefix="/api")


# Definie les Models
class SentenceInput(BaseModel):
    sentence: str

class TranslationResult(BaseModel):
    original_sentence: str
    fol_translation: str
    explanation: str
    symbols_used: List[str]

class LogicalSymbols(BaseModel):
    symbols: Dict[str, str]
    description: str

# Traduction logique premiere ordre
class FOLTranslator:
    def __init__(self):
        # symbole logique
        self.symbols = {
            "forall": "∀",      # Pour tout
            "exists": "∃",      # Il existe  
            "and": "∧",         # Et
            "or": "∨",          # Ou
            "not": "¬",         # Non/Négation
            "implies": "→",     # Implique
            "equivalent": "↔",  # Équivaut
            "therefore": "∴",   # Donc
            "because": "∵",     # Parce que
        }
        
        # traduction
        self.patterns = [
            # quantificateur universel
            {
                "pattern": r"tous? les? (\w+) sont (\w+)",
                "template": "∀x ({predicate1}(x) → {predicate2}(x))",
                "explanation": "Quantification universelle : Pour tout x, si x est un {predicate1}, alors x est {predicate2}"
            },
            {
                "pattern": r"tout (\w+) est (\w+)",
                "template": "∀x ({predicate1}(x) → {predicate2}(x))",
                "explanation": "Quantification universelle : Pour tout x, si x est un {predicate1}, alors x est {predicate2}"
            },
            {
                "pattern": r"chaque (\w+) est (\w+)",
                "template": "∀x ({predicate1}(x) → {predicate2}(x))",
                "explanation": "Quantification universelle : Pour chaque x, si x est un {predicate1}, alors x est {predicate2}"
            },
            # il existe
            {
                "pattern": r"il existe un (\w+) (\w+)",
                "template": "∃x ({predicate1}(x) ∧ {predicate2}(x))",
                "explanation": "Quantification existentielle : Il existe un x tel que x est {predicate1} et x est {predicate2}"
            },
            {
                "pattern": r"il y a un (\w+) (\w+)",
                "template": "∃x ({predicate1}(x) ∧ {predicate2}(x))",
                "explanation": "Quantification existentielle : Il existe un x tel que x est {predicate1} et x est {predicate2}"
            },
            {
                "pattern": r"certains (\w+) sont (\w+)",
                "template": "∃x ({predicate1}(x) ∧ {predicate2}(x))",
                "explanation": "Quantification existentielle : Il existe des x tels que x est {predicate1} et x est {predicate2}"
            },
            # condition
            {
                "pattern": r"si (\w+) alors (\w+)",
                "template": "{predicate1} → {predicate2}",
                "explanation": "Implication logique : Si {predicate1} alors {predicate2}"
            },
            {
                "pattern": r"si (\w+) est (\w+) alors il est (\w+)",
                "template": "{predicate2}({predicate1}) → {predicate3}({predicate1})",
                "explanation": "Implication avec prédicats : Si {predicate1} est {predicate2}, alors {predicate1} est {predicate3}"
            },
            # conjonction
            {
                "pattern": r"(\w+) et (\w+)",
                "template": "{predicate1} ∧ {predicate2}",
                "explanation": "Conjonction logique : {predicate1} et {predicate2}"
            },
            # ou
            {
                "pattern": r"(\w+) ou (\w+)",
                "template": "{predicate1} ∨ {predicate2}",
                "explanation": "Disjonction logique : {predicate1} ou {predicate2}"
            },
            # negation
            {
                "pattern": r"(\w+) n'est pas (\w+)",
                "template": "¬{predicate2}({predicate1})",
                "explanation": "Négation : {predicate1} n'est pas {predicate2}"
            },
            {
                "pattern": r"il n'y a pas de (\w+) (\w+)",
                "template": "¬∃x ({predicate1}(x) ∧ {predicate2}(x))",
                "explanation": "Négation existentielle : Il n'existe pas de x tel que x est {predicate1} et {predicate2}"
            },
            # entite specifique
            {
                "pattern": r"(\w+) est (\w+)",
                "template": "{predicate2}({predicate1})",
                "explanation": "Prédicat simple : {predicate1} a la propriété {predicate2}"
            }
        ]

    def translate_sentence(self, sentence: str) -> TranslationResult:
        sentence = sentence.lower().strip()
        
        # pour mettre en seul phrase
        for pattern_info in self.patterns:
            match = re.search(pattern_info["pattern"], sentence, re.IGNORECASE)
            if match:
                groups = match.groups()
                template = pattern_info["template"]
                explanation = pattern_info["explanation"]
                
                # remplace espace
                for i, group in enumerate(groups, 1):
                    template = template.replace(f"{{predicate{i}}}", group)
                    explanation = explanation.replace(f"{{predicate{i}}}", group)
                
                # extraire symbole
                symbols_used = []
                for symbol in self.symbols.values():
                    if symbol in template:
                        symbols_used.append(symbol)
                
                return TranslationResult(
                    original_sentence=sentence,
                    fol_translation=template,
                    explanation=explanation,
                    symbols_used=symbols_used
                )
        
        # en cas de phrase non trouvee
        return TranslationResult(
            original_sentence=sentence,
            fol_translation="[Traduction non disponible - phrase trop complexe]",
            explanation="Cette phrase ne correspond à aucun pattern de traduction connu. Essayez des phrases plus simples comme 'Tous les hommes sont mortels' ou 'Il existe un chat noir'.",
            symbols_used=[]
        )

# initialiser la traducteur
translator = FOLTranslator()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Traducteur de Logique de Premier Ordre - API Active"}

@api_router.post("/translate", response_model=TranslationResult)
async def translate_sentence(input: SentenceInput):
    """
    Traduit une phrase française en logique de premier ordre
    """
    if not input.sentence.strip():
        raise HTTPException(status_code=400, detail="La phrase ne peut pas être vide")
    
    try:
        result = translator.translate_sentence(input.sentence)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la traduction: {str(e)}")

@api_router.get("/symbols", response_model=LogicalSymbols)
async def get_logical_symbols():
    """
    retourne symbole non dispo
    """
    return LogicalSymbols(
        symbols=translator.symbols,
        description="Symboles de logique de premier ordre utilisés dans les traductions"
    )

@api_router.get("/examples")
async def get_examples():
    """
    Retourne des exemples de phrases et traductions
    """
    examples = [
        {
            "phrase": "Tous les hommes sont mortels",
            "traduction": "∀x (Homme(x) → Mortel(x))",
            "explication": "Pour tout x, si x est un homme, alors x est mortel"
        },
        {
            "phrase": "Il existe un chat noir",
            "traduction": "∃x (Chat(x) ∧ Noir(x))",
            "explication": "Il existe un x tel que x est un chat et x est noir"
        },
        {
            "phrase": "Si Paul est intelligent alors il réussit",
            "traduction": "Intelligent(Paul) → Réussit(Paul)",
            "explication": "Si Paul est intelligent, alors Paul réussit"
        },
        {
            "phrase": "Socrate est philosophe",
            "traduction": "Philosophe(Socrate)",
            "explication": "Socrate a la propriété d'être philosophe"
        },
        {
            "phrase": "Certains oiseaux sont noirs",
            "traduction": "∃x (Oiseau(x) ∧ Noir(x))",
            "explication": "Il existe des x tels que x est un oiseau et x est noir"
        }
    ]
    
    return {"examples": examples}

# mampiditra an le routeur
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],   
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)