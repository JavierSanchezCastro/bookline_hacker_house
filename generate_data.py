from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr
from models import Base, Languages, TextContent, Translations, Products
# Connecting to an SQLite database (or any other database URL)
# engine = create_engine("mysql+pymysql://user:1234@localhost:3307/test") # Old URL
# For Docker, 'db' is the hostname of the MySQL service.
# For local execution outside Docker, this would need to be 'localhost' or 127.0.0.1
engine = create_engine("mysql+pymysql://user:1234@db:3306/test")
# Note: The port in docker-compose for mysql is 3306 internally, 3307 is the host mapping.
# The service 'db' is accessible on port 3306 from within the Docker network.

Base.metadata.create_all(engine)

"""
--------------------------------------
"""
from sqlalchemy.orm import sessionmaker

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear idiomas
spanish = Languages(name="Spanish")
catalan = Languages(name="Catalan")
english = Languages(name="English")
french = Languages(name="French")

# Agregar idiomas a la sesión antes de los TextContent
session.add(spanish)
session.add(catalan)
session.add(english)
session.add(french)
session.commit()  # Aquí se asegura de que los idiomas tengan un ID asignado

# Crear y agregar productos y sus traducciones
products = [
    {"es": "Ensalada César", "ca": "Amanida Cèsar", "en": "Caesar Salad", "fr": "Salade César"},
    {"es": "Pizza Margarita", "ca": "Pizza Margarita", "en": "Margherita Pizza", "fr": "Pizza Margherita"},
    {"es": "Paella Valenciana", "ca": "Paella Valenciana", "en": "Valencian Paella", "fr": "Paella Valenciana"},
    {"es": "Croquetas de jamón", "ca": "Croquetes de pernil", "en": "Ham Croquettes", "fr": "Croquettes au jambon"},
    {"es": "Tarta de queso", "ca": "Pastís de formatge", "en": "Cheesecake", "fr": "Gâteau au fromage"},
    {"es": "Sopa de marisco", "ca": "Sopa de marisc", "en": "Seafood Soup", "fr": "Soupe de fruits de mer"},
    {"es": "Gazpacho andaluz", "ca": "Gaspatxo andalús", "en": "Andalusian Gazpacho", "fr": "Gazpacho andalou"},
    {"es": "Pulpo a la gallega", "ca": "Polp a la gallega", "en": "Galician Octopus", "fr": "Poulpe à la galicienne"},
    {"es": "Calamares a la romana", "ca": "Calamars a la romana", "en": "Fried Squid", "fr": "Calamars frits"},
    {"es": "Arroz con leche", "ca": "Arròs amb llet", "en": "Rice Pudding", "fr": "Riz au lait"}
]

# Crear los objetos TextContent y sus traducciones
for product in products:
    # Crear TextContent en español
    text_spanish = TextContent(original_text=product["es"], original_language_id=spanish.id)
    text_spanish_desc = TextContent(original_text=f"Desc: {product["es"]}", original_language_id=spanish.id)
    session.add(text_spanish)
    session.add(text_spanish_desc)
    session.commit()

    # Crear traducciones
    translation_ca = Translations(text_content_id=text_spanish.id, language_id=catalan.id, translation=product["ca"])
    translation_en = Translations(text_content_id=text_spanish.id, language_id=english.id, translation=product["en"])
    translation_fr = Translations(text_content_id=text_spanish.id, language_id=french.id, translation=product["fr"])

    translation_desc_ca = Translations(text_content_id=text_spanish_desc.id, language_id=catalan.id, translation=f"Desc: {product["ca"]}")
    translation_desc_en = Translations(text_content_id=text_spanish_desc.id, language_id=english.id, translation=f"Desc: {product["en"]}")
    translation_desc_fr = Translations(text_content_id=text_spanish_desc.id, language_id=french.id, translation=f"Desc: {product["fr"]}")
    
    # Crear un producto
    product_entry = Products(name_id=text_spanish.id, description_id=text_spanish_desc.id)

    # Agregar traducciones y el producto a la sesión
    session.add(translation_ca)
    session.add(translation_en)
    session.add(translation_fr)

    session.add(translation_desc_ca)
    session.add(translation_desc_en)
    session.add(translation_desc_fr)


    session.add(product_entry)

# Confirmar transacción
session.commit()

# Consultar y verificar las relaciones
print("Productos en español:")
products_in_spanish = session.query(Products).join(TextContent, TextContent.id == Products.name_id).join(Languages).filter(Languages.name == "Spanish").all()

for product in products_in_spanish:
    print(f"- {product.name("Spanish")}")

print("\nTraducciones para 'Ensalada César':")
# Consultar las traducciones de un producto específico
translations_for_product = session.query(Translations).join(TextContent, TextContent.id == Translations.text_content_id).join(Languages, Languages.id == Translations.language_id).filter(TextContent.original_text == "Ensalada César").all()
for translation in translations_for_product:
    print(f"- {translation.translation} ({translation.language.name})")


def get_text_i18(text_content_id, language_name):
    # Consultar la traducción en el idioma solicitado
    translation = session.query(Translations).join(Languages).filter(
        Translations.text_content_id == text_content_id,
        Languages.name == language_name
    ).first()

    if translation:
        return translation.translation
    else:
        # Si no se encuentra la traducción, se devuelve el texto original
        original_text = session.query(TextContent).filter(
            TextContent.id == text_content_id
        ).first()
        
        if original_text:
            return original_text.original_text
        else:
            return None  # En caso de que no exista el text_content_id

# Ejemplo de uso de la función
text_content_id = 1  # El ID del contenido que deseas buscar
language_name = "English"  # El idioma en el que quieres obtener la traducción

translated_text = get_text_i18(text_content_id, language_name)
print(f"Translated Text: {translated_text}")

translated_text = get_text_i18(text_content_id, "Catalan")
print(f"Translated Text: {translated_text}")

translated_text = get_text_i18(text_content_id, "French")
print(f"Translated Text: {translated_text}")

translated_text = get_text_i18(3, "English")
print(f"Translated Text: {translated_text}")


# Cerrar la sesión
session.close()


