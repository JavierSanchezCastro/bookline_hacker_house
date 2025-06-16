import reflex as rx
import httpx
from typing import List, Dict

class TranslationState(rx.State):
    """The state for managing translations."""
    all_translations: List[Dict] = []

    async def fetch_translations(self):
        """Fetches all translations from the FastAPI backend."""
        try:
            async with httpx.AsyncClient() as client:
                    response = await client.get("http://api:8000/all_translations")
                response.raise_for_status()  # Raise an exception for bad status codes
                raw_data = response.json()
                processed_data = []
                for item in raw_data:
                    translations_str = ", ".join([f"{t['language_code']}: {t['translation']}" for t in item.get('translations', [])])
                    processed_data.append({
                        "original_text": item.get("original_text"),
                        "translations": translations_str
                    })
                self.all_translations = processed_data
        except httpx.HTTPStatusError as hse:
            print(f"HTTP error occurred: {hse.response.status_code} - {hse.response.text}")
        except httpx.RequestError as e:
            print(f"An error occurred while requesting translations: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    @rx.background
    async def on_load_fetch(self):
        async with self: # Lock the state
            await self.fetch_translations()

def translation_page() -> rx.Component:
    """Defines the UI for the translations dashboard."""
    return rx.vstack(
        rx.heading("Translations Dashboard", size="5"),
        rx.button("Load Translations", on_click=TranslationState.fetch_translations),
        rx.data_table(
            data=TranslationState.all_translations,
            columns=["original_text", "translations"]
        ),
        spacing="5",
        align="center"
    )

# Initialize and configure the app
app = rx.App()
app.add_page(translation_page, on_load=TranslationState.on_load_fetch)
