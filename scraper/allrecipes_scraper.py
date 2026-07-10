import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError


class AllRecipesScraper:

    def __init__(self, urls):
        self.urls = urls

    def scrape(self):
        recipes = []

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,  # Changed from False to True - no browser window!
                slow_mo=300  # You might want to reduce or remove this for speed
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )

            page = context.new_page()

            for url in self.urls:

                print("=" * 80)
                print("Opening:", url)

                try:

                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    page.wait_for_timeout(5000)

                    print("Title:", page.title())

                    # Optional: Remove these if you don't need debugging files
                    page.screenshot(
                        path="allrecipes_page.png",
                        full_page=True
                    )

                    html = page.content()

                    with open(
                        "debug_allrecipes.html",
                        "w",
                        encoding="utf-8"
                    ) as f:
                        f.write(html)

                    try:
                        page.wait_for_selector(
                            "script[type='application/ld+json']",
                            timeout=10000
                        )
                    except TimeoutError:
                        print("JSON-LD not found.")

                    scripts = page.locator(
                        "script[type='application/ld+json']"
                    ).all()

                    print(f"Found {len(scripts)} JSON-LD blocks.")

                    for script in scripts:

                        try:

                            text = script.inner_text()

                            if not text.strip():
                                continue

                            data = json.loads(text)

                            if isinstance(data, list):
                                items = data

                            elif isinstance(data, dict):
                                if "@graph" in data:
                                    items = data["@graph"]
                                else:
                                    items = [data]

                            else:
                                continue

                            for item in items:

                                recipe = self._parse(item, url)

                                if recipe:
                                    print("Recipe:", recipe["title"])
                                    recipes.append(recipe)

                        except Exception as e:
                            print("JSON Error:", e)

                except Exception as e:
                    print("Playwright Error:", e)

            browser.close()

        print("=" * 80)
        print("TOTAL RECIPES:", len(recipes))

        return recipes

    def _parse(self, data, url):

        obj_type = data.get("@type")

        if isinstance(obj_type, list):
            if "Recipe" not in obj_type:
                return None
        elif obj_type != "Recipe":
            return None

        # --------------------------
        # Instructions
        # --------------------------

        instructions = []

        raw = data.get("recipeInstructions", [])

        if isinstance(raw, list):

            for step in raw:

                if isinstance(step, dict):

                    if "text" in step:
                        instructions.append(step["text"])

                    elif "itemListElement" in step:

                        for s in step["itemListElement"]:

                            if isinstance(s, dict):

                                if "text" in s:
                                    instructions.append(s["text"])

                elif isinstance(step, str):
                    instructions.append(step)

        elif isinstance(raw, str):
            instructions.append(raw)

        # --------------------------
        # Author
        # --------------------------

        author = None

        if isinstance(data.get("author"), dict):
            author = data["author"].get("name")

        # --------------------------
        # Nutrition
        # --------------------------

        nutrition = data.get("nutrition", {})

        # --------------------------
        # Image
        # --------------------------

        image = data.get("image")

        image_url = None

        if isinstance(image, dict):
            image_url = image.get("url")

        elif isinstance(image, list) and len(image) > 0:

            first = image[0]

            if isinstance(first, dict):
                image_url = first.get("url")
            else:
                image_url = first

        elif isinstance(image, str):
            image_url = image

        # --------------------------
        # Return Structured Recipe
        # --------------------------

        return {

            "title": data.get("name"),

            "url": url,

            "source": "AllRecipes",

            "category": "recipe",

            "ingredients": json.dumps(
                data.get("recipeIngredient", []),
                ensure_ascii=False
            ),

            "instructions": json.dumps(
                instructions,
                ensure_ascii=False
            ),

            "calories": nutrition.get("calories"),

            "protein": nutrition.get("proteinContent"),

            "fat": nutrition.get("fatContent"),

            "carbohydrates": nutrition.get("carbohydrateContent"),

            "fiber": nutrition.get("fiberContent"),

            "sugar": nutrition.get("sugarContent"),

            "cholesterol": nutrition.get("cholesterolContent"),

            "sodium": nutrition.get("sodiumContent"),

            "prep_time": data.get("prepTime"),

            "cook_time": data.get("cookTime"),

            "total_time": data.get("totalTime"),

            "recipe_yield": json.dumps(
                data.get("recipeYield"),
                ensure_ascii=False
            ),

            "image_url": image_url,

            "author": author,

            "published_date": data.get("datePublished"),

            "scraped_date": datetime.utcnow().isoformat()

        }