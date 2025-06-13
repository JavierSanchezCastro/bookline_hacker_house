from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
import inspect


def _snake_to_camel(snake: str) -> str:
    parts = snake.split('_')
    return ''.join(p.capitalize() for p in parts)

class AutoRelationshipMeta(DeclarativeMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        # Solo para clases que ya tienen __table__ construida
        if hasattr(cls, '__table__'):
            for col in cls.__table__.columns:
                if not col.name.endswith('_id'):
                    continue

                if not col.foreign_keys:
                    continue

                print("---------------------")

                print(f"{cls.__table__.name=}")

                print(f"{col.name=}")
                
                # Determinar nombre de la clase target a partir de la tabla referenciada
                fk = next(iter(col.foreign_keys))

                print(f"{fk=}")

                target_table = fk.column.table.name       # e.g. 'text_content'

                print(f"{target_table=}")

                if target_table != 'text_content':
                    continue

                if cls.__table__.name == "translations":
                    continue

                print("OK")

                base_name = col.name[:-3]        # e.g. 'name_id' → 'name'
                rel_name  = f"{base_name}_rel"   # e.g. 'name_rel'
                target_cls = _snake_to_camel(target_table)  # → 'TextContent'
                # Crear la relationship solo si no la has definido manualmente
                if not hasattr(cls, rel_name):
                    setattr(
                        cls,
                        rel_name,
                        relationship(
                            target_cls,
                            foreign_keys=[getattr(cls, col.name)]
                        )
                    )

                if not hasattr(cls, f"{base_name}_original_text"):
                    def make_prop(rn):
                        def prop(self):
                            rel_obj = getattr(self, rn)
                            return rel_obj.original_text if rel_obj else None
                        return prop

                    setattr(
                        cls,
                        f"{base_name}_original_text",
                        property(make_prop(rel_name))
                    )

                if not hasattr(cls, base_name):
                    def make_translator(rn):
                        def translator(self, lang: str = "Spanish"):
                            rel_obj = getattr(self, rn)
                            if rel_obj is None:
                                return None
                            # Buscar en las traducciones cargadas
                            for tr in rel_obj.translations:
                                if tr.language.name == lang:
                                    return tr.translation
                            # Fallback al texto original
                            return rel_obj.original_text
                        return translator

                    setattr(
                        cls,
                        base_name,
                        make_translator(rel_name)
                    )
    
    def __new__(cls, name, bases, dct):
        # Añadir la función 'iterate_attributes' a las clases que heredan de 'Base'
        def iterate_attributes(self):
            atts = {}
            for attribute, value in vars(self).items():
                print(f"Attribute: {attribute} - Value: {value}")
                atts[attribute] = value
            
            return atts
        
        def iterate_functions(self):
            # Obtener todos los métodos de la clase
            functions = inspect.getmembers(cls, predicate=inspect.isfunction)
            for function_name, function in functions:
                print(f"Function: {function_name}, Function object: {function}")

        dct['iterate_attributes'] = iterate_attributes
        dct['iterate_functions'] = iterate_functions

        
        return super().__new__(cls, name, bases, dct)

# Base con el metaclase personalizado
Base = declarative_base(metaclass=AutoRelationshipMeta)
from sqlalchemy.orm import Session, class_mapper
from sqlalchemy.orm import relationship


class Languages(Base):
    __tablename__ = 'languages'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)

class TextContent(Base):
    __tablename__ = 'text_content'
    id = Column(Integer, primary_key=True)
    original_text = Column(String(200), nullable=False)
    original_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    
    language = relationship('Languages')
    translations = relationship('Translations', back_populates='text_content')

#Languages.texts = relationship('TextContent', back_populates='language')

class Translations(Base):
    __tablename__ = 'translations'
    text_content_id = Column(Integer, ForeignKey('text_content.id'), primary_key=True)
    language_id = Column(Integer, ForeignKey('languages.id'), primary_key=True)
    translation = Column(String(200), nullable=False)

    text_content = relationship('TextContent', back_populates='translations')
    language = relationship('Languages')



class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name_id = Column(Integer, ForeignKey('text_content.id'), nullable=False)
    description_id = Column(Integer, ForeignKey('text_content.id'), nullable=False)

    def hello(self):
        return "hola"

    #def iterate_attributes(self):
    #    # Itera sobre los atributos de la instancia de la clase
    #    for attribute, value in vars(self).items():
    #        print(f"{attribute}: {value}")
        
    
    #name = relationship('TextContent', foreign_keys=[name_id])
    #description = relationship('TextContent', foreign_keys=[description_id])

    #def get_translated(self, db: Session, language: str):
    #    """Devuelve el objeto traducido completo."""
    #    
    #    # Primero, iteramos sobre las relaciones
    #    for column in class_mapper(self.__class__).relationships:
    #        # column.key nos da el nombre del campo (por ejemplo, 'name', 'description', etc.)
    #        field_name = column.key
    #        field_value = getattr(self, field_name)
#
    #        # Si el campo es una relación con TextContent
    #        if isinstance(field_value, TextContent):
    #            # Renombramos el campo a <name>_rel
    #            setattr(self, f"{field_name}_rel", field_value)
    #            # Obtenemos la traducción de ese campo
    #            translated_value = self.translate_field(db, field_name, language)
    #            
    #            # Creamos un nuevo objeto TextContent con el texto traducido y lo asignamos
    #            translated_text_content = TextContent(original_text=translated_value)
    #            setattr(self, field_name, translated_text_content)  # Asignamos el objeto TextContent traducido
#
    #    # Luego, iteramos sobre las columnas para procesar las claves foráneas (_id)
    #    for column in class_mapper(self.__class__).columns:
    #        # Si la columna es una clave foránea a TextContent (termina en '_id')
    #        if column.name.endswith('_id'):
    #            # Obtenemos el nombre del campo sin el sufijo '_id'
    #            field_name = column.name.replace('_id', '')
    #            field_value = getattr(self, f"{field_name}_rel", None)
#
    #            # Si encontramos la relación correspondiente, asignamos el texto traducido
    #            if field_value:
    #                # Asignamos el texto traducido del campo relacionado
    #                translated_value = getattr(self, f"{field_name}_rel").original_text
    #                setattr(self, field_name, translated_value)
#
    #    return self