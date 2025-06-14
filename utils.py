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
