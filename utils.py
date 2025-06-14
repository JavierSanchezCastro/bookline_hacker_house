# Definir el modelo de respuesta (Pydantic)
from pydantic import BaseModel, ConfigDict, PositiveInt, Field, model_validator
from typing import Annotated, Optional
from pydantic import BeforeValidator

class LanguageShow(BaseModel):
    name: str
    # Assuming code might be needed by TranslationsShow or other places, adding it here.
    # If LanguageShow is strictly *only* for product name, this might differ.
    # Based on TranslationsShow using LanguageShow, it implies LanguageShow should carry enough info.
    code: str # Added code as it's used by filter_translations_by_context logic via trans_orm.language.code
    model_config = ConfigDict(from_attributes=True)

class TranslationsShow(BaseModel):
    language: LanguageShow
    translation: str
    model_config = ConfigDict(from_attributes=True) # Added model_config

class TextContentShow(BaseModel):
    original_text: str
    translations: list[TranslationsShow] # This will be populated based on the validator's output

    model_config = ConfigDict(from_attributes=True) # Ensure from_attributes is enabled

    @model_validator(mode='before')
    @classmethod
    def filter_translations_by_context(cls, data, info):
        # data is the input value to validate.
        # info contains validation context and config.

        # Early exit if context is not available or data is not an ORM object with necessary attributes
        # TextContent ORM model has 'language' attribute for its original_language_id FK
        if not info.context or not hasattr(data, 'translations') or not hasattr(data, 'original_text') or not hasattr(data, 'language'):
             return data

        target_langs = info.context.get('target_langs')

        if not target_langs:
            return {
                "original_text": data.original_text,
                "translations": data.translations
            }

        target_langs_set = set(target_lang.strip() for target_lang in target_langs if target_lang.strip())

        filtered_translations_orm_objects = [
            trans_orm for trans_orm in data.translations
            if trans_orm.language.code in target_langs_set  # Assumes trans_orm.language is a Language ORM object with a 'code'
        ]

        return {
            "original_text": data.original_text,
            "translations": filtered_translations_orm_objects
        }
    
Translatable = BeforeValidator(lambda value, info: value(info.context.get("lang", "Spanish")))

class ProductShow(BaseModel):
    name: Annotated[str, Translatable]
    description: Annotated[str, Translatable]
    model_config = ConfigDict(from_attributes=True)

class ProductShowMultipleTranslation(BaseModel):
    name_rel: Annotated[TextContentShow, Field(serialization_alias="name")]
    description_rel: Annotated[TextContentShow, Field(serialization_alias="description")]
    model_config = ConfigDict(from_attributes=True)
