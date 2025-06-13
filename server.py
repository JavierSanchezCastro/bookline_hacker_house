from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Products, TextContent, Languages, Translations, Base
from utils import ProductShow, ProductShow2

# Configuración de la base de datos
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:1234@localhost:3307/test"

# Crear motor y sesión
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la aplicación FastAPI
app = FastAPI()

# Obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

from pydantic import BaseModel

# Clase base para los modelos que incluyen relaciones con `text_content`
class TextContentMixin(BaseModel):
    def get_translation(self, db: Session, language: Optional[str] = None):
        """Obtiene la traducción del contenido de texto o el texto original si no se encuentra."""
        if not language:
            language = "Spanish"  # idioma por defecto si no se pasa uno
        text_content = db.query(TextContent).filter(TextContent.id == self.id).first()
        if text_content:
            return get_text_i18(db, text_content.id, language)
        return None

from pydantic import root_validator
# Modelo de Pydantic que representa el producto con la traducción del nombre y la descripción
#class ProductShow(TextContentMixin):
#    id: int
#    name: str
#    description: str

    #@root_validator(pre=True)
    #def resolve_translations(cls, values, db: Session, product: Products, language: Optional[str] = None):
    #    # Si no se pasa un idioma, se usa el español por defecto
    #    language = language or "Spanish"
    #    
    #    # Resolver la traducción para 'name' y 'description' basándonos en la relación FK
    #    name_translation = get_text_i18(db, product.name_id, language)
    #    description_translation = get_text_i18(db, product.description_id, language)
    #    
    #    # Asignar las traducciones al modelo de Pydantic
    #    values['name'] = name_translation
    #    values['description'] = description_translation

#    #    return values

#    #@classmethod
    #def from_orm(cls, db: Session, product: Products, language: Optional[str] = None):
    #    """Crea una instancia de ProductShow desde un objeto Products y obtiene las traducciones."""
    #    # Obtener el nombre y la descripción con las traducciones
    #    name = get_text_i18(db, product.name_id, language)  # Traducción del nombre
    #    description = get_text_i18(db, product.description_id, language)  # Traducción de la descripción
    #    return cls(id=product.id, name=name, description=description)

@app.get("/product/{product_id}", response_model=ProductShow2)
def get_product_by_id(product_id: int, language: Optional[str] = None, db: Session = Depends(get_db)):
    # Obtener el producto por ID
    product = db.query(Products).filter(Products.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product.get_translated("Spanish")
    