import os
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Products, TextContent, Languages, Translations
from utils import ProductShow, ProductShowMultipleTranslation, ProductCreate, TranslatableTextInput

# Configuración de la base de datos
#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:1234@localhost:3307/test" # Old URL
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://user:1234@localhost:3307/test")

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


# Funciones y ruta para crear productos

def get_language_db_entry(db: Session, language_code: str) -> Languages:
    """Obtiene el objeto Languages de la BD o lanza HTTPException si no existe."""
    lang_db = db.query(Languages).filter(Languages.code == language_code).first()
    if not lang_db:
        raise HTTPException(status_code=400, detail=f"Language code '{language_code}' not found.")
    return lang_db

def create_text_content_with_translations(db: Session, text_input: TranslatableTextInput) -> TextContent:
    """
    Crea un TextContent y sus traducciones asociadas.
    Devuelve la instancia de TextContent creada.
    """
    # 1. Obtener el idioma original
    original_lang_db = get_language_db_entry(db, text_input.original_language_code)

    # 2. Crear TextContent
    db_text_content = TextContent(
        original_text=text_input.original_text,
        original_language_id=original_lang_db.id
    )
    db.add(db_text_content)
    db.flush()

    # 3. Crear Traducciones (si las hay)
    if text_input.translations:
        for translation_input in text_input.translations:
            translation_lang_db = get_language_db_entry(db, translation_input.language_code)

            if translation_lang_db.id == original_lang_db.id:
                print(f"Advertencia: Se intentó añadir una traducción para el idioma original '{translation_input.language_code}' para el texto '{text_input.original_text}'. Se omitirá.")
                continue

            db_translation = Translations(
                text_content_id=db_text_content.id,
                language_id=translation_lang_db.id,
                translation=translation_input.text
            )
            db.add(db_translation)

    return db_text_content


@app.post("/product/", response_model=ProductShow, status_code=201)
def create_product(product_data: ProductCreate, db: SessionDB, lang: Language):
    """
    Crea un nuevo producto con nombre y descripción traducibles.
    """
    try:
        name_text_content = create_text_content_with_translations(db, product_data.name)
        description_text_content = create_text_content_with_translations(db, product_data.description)

        db_product = Products(
            name_id=name_text_content.id,
            description_id=description_text_content.id
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return ProductShow.model_validate(db_product, context={"lang": lang})

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error al crear producto: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear el producto.")