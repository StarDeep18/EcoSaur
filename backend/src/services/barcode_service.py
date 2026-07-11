import httpx

async def fetch_ingredients_by_barcode(barcode: str) -> str:
    """
    Queries the OpenFoodFacts API to get ingredients by barcode.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                ingredients = product.get("ingredients_text", "")
                if ingredients:
                    return ingredients
                return "Product found, but ingredients are not listed in OpenFoodFacts. Please take a photo of the label."
            else:
                return "Barcode not found in OpenFoodFacts database. Please scan the ingredient label instead."
    except Exception as e:
        print(f"Barcode API Error: {e}")
        return "Failed to connect to barcode database. Please use the camera scan."
