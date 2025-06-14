from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Products, TextContent, Languages, Translations
from utils import ProductShow, ProductShowMultipleTranslation

# Configuración de la base de datos
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:1234@localhost:3307/test"

# Crear motor y sesión
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la aplicación FastAPI
from fastapi import FastAPI, Request
    
def require_accept_language(request: Request, accept_language: Annotated[str | None, Header()] = None):
    request.state.language = accept_language

# Crear la aplicación FastAPI
app = FastAPI(dependencies=[Depends(require_accept_language)])

# Dependencia para DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionDB = Annotated[Session, Depends(get_db)]


# Función para obtener la traducción de un texto
def get_text_i18(db: Session, text_content_id: int, language_name: str) -> Optional[str]:
    translation = db.query(Translations).join(Languages).filter(
        Translations.text_content_id == text_content_id,
        Languages.name == language_name
    ).first()
    
    if translation:
        return translation.translation
    else:
        original_text = db.query(TextContent).filter(TextContent.id == text_content_id).first()
        return original_text.original_text if original_text else None

# Dependencia para Accept-Language header
def get_language(request: Request) -> str:
    return request.state.language 

Language = Annotated[str, Depends(get_language)]


@app.get("/product/{product_id}", response_model=ProductShow)
def get_product_by_id(product_id: int, db: SessionDB, lang: Language):
    product = db.query(Products).filter(Products.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = ProductShow.model_validate(product, context={"lang": lang})
    return product

@app.get("/multiple/product/{product_id}", response_model=ProductShowMultipleTranslation, description="Aquí Accept-Language no se tiene en cuenta, devuelve todas las traducciones")
def get_product_by_id_multiple(product_id: int, db: SessionDB, lang: Language):
    product = db.query(Products).filter(Products.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product