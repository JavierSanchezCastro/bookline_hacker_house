from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeMeta, Mapped
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
                
                fk = next(iter(col.foreign_keys))

                target_table = fk.column.table.name  # e.g. 'text_content'


                if target_table != 'text_content':
                    continue

                if cls.__table__.name == "translations":
                    continue


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
                        def translator(self, lang: str = "es"):
                            rel_obj = getattr(self, rn)
                            if rel_obj is None:
                                return None
                            # Buscar en las traducciones cargadas
                            for tr in rel_obj.translations:
                                if tr.language.code == lang:
                                    return tr.translation
                            # Fallback al texto original
                            return rel_obj.original_text
                        return translator

                    setattr(
                        cls,
                        base_name,
                        make_translator(rel_name)
                    )

# Base con el metaclase personalizado
Base = declarative_base(metaclass=AutoRelationshipMeta)
from sqlalchemy.orm import Session, class_mapper, mapped_column
from sqlalchemy.orm import relationship


class Languages(Base):
    __tablename__ = 'languages'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    code = Column(String(5), nullable=False)

class TextContent(Base):
    __tablename__ = 'text_content'
    id = Column(Integer, primary_key=True)
    original_text = Column(String(200), nullable=False)
    original_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    
    language = relationship('Languages')
    translations = relationship('Translations', back_populates='text_content')


class Translations(Base):
    __tablename__ = 'translations'
    text_content_id = Column(Integer, ForeignKey('text_content.id'), primary_key=True)
    language_id = Column(Integer, ForeignKey('languages.id'), primary_key=True)
    translation = Column(String(200), nullable=False)

    text_content = relationship('TextContent', back_populates='translations')
    language = relationship('Languages')


class Products(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name_id: Mapped[int] = mapped_column(ForeignKey('text_content.id'), nullable=False)
    description_id: Mapped[int]= mapped_column(ForeignKey('text_content.id'), nullable=False)

    # Campos creados automáticamente
    # name_rel = relationship(...)
    # description_rel = relationship(...)
    # (alias) name_original_text = name_rel.original_text
    # (alias) description_original_text = description_rel.original_text

    # Funciones creadas automáticamente
    # name(lang: str) -> devuelve el name traducido al "lang" enviado
    # description(lang: str) -> devuelve el description traducido al "lang" enviado

    # ATENCIÓN
    # Solo se crean estos campos y funciones a las columnas que sean FK de text_content
    # Es decir, que si tuvieses otro campos que apunte a otra tabla, la 'magia' no tendrá en cuenta y no creará ningún campo/funcion para esa columna (obviamente)
