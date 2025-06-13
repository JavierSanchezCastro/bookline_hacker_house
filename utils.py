# Definir el modelo de respuesta (Pydantic)
from pydantic import BaseModel, ConfigDict, PositiveInt

class LanguageShow(BaseModel):
    name: str

class TranslationsShow(BaseModel):
    language: LanguageShow
    translation: str

class TextContentShow(BaseModel):
    original_text: str
    translations: list[TranslationsShow]


"""
"""
from pydantic import field_serializer, field_validator
from typing import get_origin, Annotated, get_args
#class Translatable:
#    """Marca un campo como traducible."""
#    pass
#
# 2) Esquema base que detecta en Annotated[str, Translatable()]
class TranslatableSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*")
    def _translate_annotated(self, value, field):
        # Si el campo tiene el marcador Translatable
        print(f"{field=}")
        print(f"{value=}")
        if hasattr(field, "annotation") and isinstance(field.annotation, Annotated):
            print("if")
            # Usamos los metadatos para verificar si el campo tiene Translatable
            metadata = field.annotation.__args__[-1]  # metadata contiene Translatable() si está presente
            if any(isinstance(m, Translatable) for m in metadata):

                # Obtenemos el idioma del contexto
                lang = field.context.get("lang", "en")
                # Llamamos al método dinámico que tu modelo SQLAlchemy genera
                return getattr(self, field.name)(lang)
        return value
    
from pydantic import BeforeValidator
    
Translatable = BeforeValidator(lambda value, info: value(info.context.get("lang", "Spanish")))

class ProductShow(BaseModel):
    #id: Annotated[int, PositiveInt]
    #name_rel: TextContentShow
    name: Annotated[str, Translatable]
    description: Annotated[str, Translatable]
    model_config = ConfigDict(from_attributes=True) 

class ProductShow2(BaseModel):
    name: str
    description: str
    model_config = ConfigDict(from_attributes=True) 

    #@field_validator("name", mode="before")
    #@classmethod
    #def _serialize_name(cls, value, info):
#
    #    # info.context viene de model_dump(context=...)
    #    lang = info.context.get("lang", "Spanish")
    #    # `self` es ya la instancia de Products; name aquí será ignorado
    #    return value(lang)


    #model_config = ConfigDict(from_attributes=True)
    #description: str


#class ProductShow(TranslatableSchema):
#    #id: Annotated[int, PositiveInt]
#    #name_rel: TextContentShow
#    name: str
#    model_config = ConfigDict(from_attributes=True) 
#
#    @field_validator("name", mode="before")
#    @classmethod
#    def _serialize_name(cls, value, info):
#
#        # info.context viene de model_dump(context=...)
#        lang = info.context.get("lang", "Spanish")
#        # `self` es ya la instancia de Products; name aquí será ignorado
#        return value(lang)
#
#
#    #model_config = ConfigDict(from_attributes=True)
#    #description: str
#