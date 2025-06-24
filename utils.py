# Definir el modelo de respuesta (Pydantic)
from pydantic import BaseModel, ConfigDict, PositiveInt, Field
from typing import Annotated
from pydantic import BeforeValidator

class LanguageShow(BaseModel):
    name: str

class TranslationsShow(BaseModel):
    language: LanguageShow
    translation: str

class TextContentShow(BaseModel):
    original_text: str
    translations: list[TranslationsShow]

    
Translatable = BeforeValidator(lambda value, info: value(info.context.get("lang", "Spanish")))

class ProductShow(BaseModel):
    name: Annotated[str, Translatable]
    description: Annotated[str, Translatable]
    model_config = ConfigDict(from_attributes=True)

class ProductShowMultipleTranslation(BaseModel):
    name_rel: Annotated[TextContentShow, Field(serialization_alias="name")]
    description_rel: Annotated[TextContentShow, Field(serialization_alias="description")]
    model_config = ConfigDict(from_attributes=True)

# Nuevos modelos para la creación
from typing import List # Asegurarse de que List está importado de typing

class TranslationInput(BaseModel):
    language_code: str = Field(..., description="Código del idioma (ej: 'en', 'es', 'fr')")
    text: str = Field(..., description="Texto traducido")

class TranslatableTextInput(BaseModel):
    original_text: str = Field(..., description="Texto en el idioma original")
    original_language_code: str = Field(..., description="Código del idioma original (ej: 'en', 'es', 'fr')")
    translations: Optional[List[TranslationInput]] = Field(None, description="Lista opcional de traducciones")

class ProductCreate(BaseModel):
    name: TranslatableTextInput
    description: TranslatableTextInput
    # Aquí irían otros campos no traducibles del producto, si los hubiera
    # ej: price: float
    # ej: stock: int

    model_config = ConfigDict(from_attributes=False) # Importante para la creación
