# FastAPI Multilingual Product API

This project demonstrates a FastAPI application with multilingual support for product data, using SQLAlchemy for ORM, a MySQL database, and Pydantic for data validation and serialization. It showcases dynamic relationship creation and a flexible translation mechanism.

## Project Setup

Follow these steps to set up and run the project:

### Prerequisites

*   **Docker:** Ensure you have Docker installed and running. ([Installation Guide](https://docs.docker.com/get-docker/))
*   **Docker Compose:** Ensure you have Docker Compose installed. (It's usually included with Docker Desktop. [Installation Guide](https://docs.docker.com/compose/install/))

### Running the Application

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder-name>
    ```

2.  **Build and Start Services:**
    Use Docker Compose to build the images and start the API and database services.
    ```bash
    docker-compose up -d --build
    ```
    This command will:
    *   Build the Docker image for the FastAPI application (if not already built or if `Dockerfile` changed).
    *   Start the `api` and `db` services in detached mode (`-d`).
    *   The API will be available at `http://localhost:8000`.
    *   The MySQL database will be accessible on port `3307` on your host machine (mapping to port `3306` in the container).

3.  **Populate Initial Data:**
    After the services are up and running (especially the database), you need to populate it with initial data using the `generate_data.py` script.
    Run the following command in your terminal:
    ```bash
    docker-compose exec api python generate_data.py
    ```
    This command executes `python generate_data.py` inside the running `api` service container. It will create the necessary tables (if they don't exist) and fill them with sample languages, text content, translations, and products. You only need to run this once, or when you want to reset the data (after clearing the database volume).

    *To check logs for the API service:*
    ```bash
    docker-compose logs api
    ```
    *To check logs for the database service:*
    ```bash
    docker-compose logs db
    ```
    *To stop the services:*
    ```bash
    docker-compose down
    ```
    *To stop and remove volumes (deletes database data):*
    ```bash
    docker-compose down -v
    ```

## Project Explanation

This project provides a RESTful API for managing product information with support for multiple languages.

### Core Features:

*   **Multilingual Product Data:** Product names and descriptions can be stored and retrieved in various languages.
*   **Dynamic Translation Retrieval:** The API can serve product details translated into a language specified via the `Accept-Language` header.
*   **Comprehensive Data Model:** Utilizes SQLAlchemy to define relationships between products, text content, languages, and translations.

### Technical Stack:

*   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python.
*   **SQLAlchemy:** The Python SQL toolkit and Object Relational Mapper (ORM) used for database interaction.
*   **Pydantic:** Used for data validation, serialization, and settings management. It plays a crucial role in transforming database models to API responses, including handling translations.
*   **MySQL:** The relational database used to store application data.
*   **Docker & Docker Compose:** For containerizing the application and managing services, ensuring a consistent development and deployment environment.

## Automatic Relationships and Translations: The `AutoRelationshipMeta` Magic

The `models.py` file defines a metaclass `AutoRelationshipMeta` that enhances SQLAlchemy models (like the `Products` model) with dynamic attributes and methods for easier handling of translatable content.

When a model uses `Base` (which itself uses `AutoRelationshipMeta`), the metaclass automatically inspects the model's columns. If a column name ends with `_id` (e.g., `name_id`, `description_id`) and it's a foreign key pointing to the `text_content` table, the following are automatically generated for that base name (e.g., `name`, `description`):

1.  **SQLAlchemy Relationship (`<basename>_rel`):**
    *   An attribute like `product.name_rel` or `product.description_rel` is created.
    *   This attribute is a standard SQLAlchemy `relationship` that links to the `TextContent` model.
    *   It allows direct access to the related `TextContent` object, which holds the original text and its translations.
    *   Example: `product.name_rel.original_text` would give the original text for the product's name.

2.  **Original Text Alias (`<basename>_original_text`):**
    *   An attribute like `product.name_original_text` is created as a Python property.
    *   This is a convenient alias for `product.<basename>_rel.original_text`.
    *   Example: `product.name_original_text` directly gives the name in its original language.

3.  **Translation Method (`<basename>(lang: str)`):**
    *   A method like `product.name(lang="en")` or `product.description(lang="fr")` is created.
    *   This method takes a language code (e.g., "en", "es", "fr") as an argument.
    *   It attempts to find the translation for that language within the associated `TextContent` object's `translations` collection.
    *   If a translation for the specified language is found, it's returned.
    *   If no translation is found for the requested language, it defaults to returning the `original_text` from the `TextContent` object.
    *   Example: `product.name(lang="ca")` would return the Catalan name of the product if available, otherwise the original name.

### Summary from `models.py` (Products class):

The comments in the `Products` class in `models.py` summarize this behavior:

```python
# class Products(Base):
#     __tablename__ = 'products'
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name_id: Mapped[int] = mapped_column(ForeignKey('text_content.id'), nullable=False)
#     description_id: Mapped[int]= mapped_column(ForeignKey('text_content.id'), nullable=False)

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
```

This automation significantly simplifies accessing translated data directly from the model instances without repetitive boilerplate code. You can find the implementation details in `AutoRelationshipMeta` within `models.py`.

## Pydantic, Translations, and Request Context

The API uses Pydantic models not only for request validation but also for serializing response data. A key part of the multilingual feature is how these Pydantic models provide translated content. This is achieved using a custom `Translatable` type and Pydantic's validation context.

### The `Translatable` Type Alias

In `utils.py`, you'll find the `Translatable` type:

```python
# From utils.py
from pydantic import BeforeValidator
from typing import Annotated

Translatable = BeforeValidator(lambda value, info: value(info.context.get("lang", "Spanish")))

class ProductShow(BaseModel):
    name: Annotated[str, Translatable]
    description: Annotated[str, Translatable]
    model_config = ConfigDict(from_attributes=True)
```

*   **`Translatable`**: This is an `Annotated` type that uses Pydantic's `BeforeValidator`.
*   **`BeforeValidator`**: This allows a function to process a field's value *before* any standard validation rules are applied.
*   **The Lambda Function `lambda value, info: value(info.context.get("lang", "Spanish"))`**:
    *   When a SQLAlchemy model instance (e.g., a `Products` object) is passed to `ProductShow.model_validate()` (or used in a FastAPI response model), this lambda is called for fields annotated with `Translatable` (like `name` and `description`).
    *   `value`: In this context, `value` will be the callable method that `AutoRelationshipMeta` created on the SQLAlchemy model instance (e.g., `product.name`, `product.description`).
    *   `info.context`: Pydantic's validation functions receive an `info` object which has a `context` attribute. This `context` is a dictionary that can be passed during model validation.
    *   `info.context.get("lang", "Spanish")`: This attempts to retrieve a `lang` key from the validation context. This `lang` key is expected to hold the desired language code (e.g., "en", "es"). If the `lang` key is not found in the context, it defaults to "Spanish".
    *   The lambda then calls the method (`value`) with the retrieved language code: `value(retrieved_lang_code)`. For example, if `value` is `product.name` and `lang` is "fr", it effectively calls `product.name(lang="fr")`.

### How Language Context is Provided (FastAPI Endpoint)

In `server.py`, the `/product/{product_id}` endpoint demonstrates how this context is supplied:

```python
# From server.py (simplified)
@app.get("/product/{product_id}", response_model=ProductShow)
def get_product_by_id(product_id: int, db: SessionDB, lang: Language):
    product = db.query(Products).filter(Products.id == product_id).first()
    # ... (error handling) ...

    # Here, the 'lang' obtained from Accept-Language header is passed into the context
    product_response = ProductShow.model_validate(product, context={"lang": lang})
    return product_response

# The 'lang: Language' dependency gets the language code:
# Language = Annotated[str, Depends(get_language)]
# def get_language(request: Request) -> str:
#    return request.state.language
#
# And 'request.state.language' is set by the 'require_accept_language' dependency:
# def require_accept_language(request: Request, accept_language: Annotated[str | None, Header()] = None):
#    request.state.language = accept_language # Simplified, you'd parse it properly
```

1.  A middleware-like dependency `require_accept_language` reads the `Accept-Language` header from the incoming request and stores the (potentially parsed) language code in `request.state.language`.
2.  The `Language` dependency (`Annotated[str, Depends(get_language)]`) retrieves this language code for the endpoint.
3.  When the SQLAlchemy `product` object is converted to a `ProductShow` Pydantic model using `ProductShow.model_validate(product, context={"lang": lang})`, the `lang` variable (containing the language code from the header) is passed into the `context` dictionary.
4.  The `Translatable` validator then picks up this `lang` from the context and calls the appropriate translation method on the `product` object.

This setup allows the API to dynamically translate fields based on the `Accept-Language` header provided by the client, falling back to a default language if the header is missing or the specific translation isn't available.

For more details on Pydantic validators and context, refer to the [Pydantic Documentation](https://docs.pydantic.dev/latest/concepts/validators/#beforeafter-validators_and_wrap-validators) and [Pydantic Validation Context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context).

## API Usage Examples (Screenshots)

*(Space for API screenshots, request/response examples, or GIF demonstrations will be added here by the user.)*

For example, you might include:
*   A `curl` command or Postman screenshot showing a request to `/product/{product_id}` with an `Accept-Language: es` header and the corresponding Spanish response.
*   A similar example with `Accept-Language: en` and the English response.
*   An example of a request to `/multiple/product/{product_id}` showing all translations.
