# scraper/bbc_goodfood_all.py

import json
import time
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from typing import List, Dict, Optional
import os


class BBCGoodFoodAllScraper:
    """
    Scraper for BBC Good Food Vegetarian Recipes
    Streamlit Cloud compatible version
    """

    def __init__(
        self,
        max_recipes: int = 11,
        save_progress: bool = True,
        progress_file: str = "scrape_progress.json"
    ):
        self.max_recipes = max_recipes
        self.save_progress = save_progress
        self.progress_file = progress_file
        self.recipe_urls = []
        self.scraped_recipes = []


    def _ensure_playwright_browser(self):
        """
        Streamlit Cloud does not automatically download Chromium.
        This installs the required browser binary.
        """

        try:
            print("🔍 Checking Playwright Chromium browser...")

            subprocess.run(
                ["playwright", "install", "chromium"],
                check=True
            )

            print("✅ Chromium browser installed")

        except Exception as e:
            print(f"❌ Chromium installation failed: {e}")
            raise


    def scrape_all(self) -> List[Dict]:
        """
        Main method to scrape recipes
        """

        print("=" * 80)
        print("Starting BBC Good Food scraping - Latest 3 Vegetarian Recipes...")
        print("=" * 80)

        self._collect_recipe_urls()

        self._scrape_all_recipes()

        self._save_results()

        print(f"\n{'=' * 80}")
        print(
            f"✅ Scraping complete! Total recipes: {len(self.scraped_recipes)}"
        )
        print("=" * 80)

        return self.scraped_recipes


    def _collect_recipe_urls(self):
        """
        Collect the latest 3 recipe URLs from vegetarian category
        """

        print("\n📚 Collecting latest 3 vegetarian recipes...")

        category_url = (
            "https://www.bbcgoodfood.com/"
            "recipes/collection/vegetarian-recipes"
        )


        # FIX FOR STREAMLIT CLOUD
        self._ensure_playwright_browser()


        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox"]
            )

            page = browser.new_page()


            try:

                print(f"  Opening: {category_url}")

                page.goto(
                    category_url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                page.wait_for_timeout(3000)


                all_links = page.locator(
                    "a[href*='/recipes/']"
                ).all()


                print(
                    f"  Found {len(all_links)} total links on page"
                )


                count = 0

                for element in all_links:

                    if count >= 11:  # Only get 3
                        break


                    try:

                        href = element.get_attribute(
                            "href"
                        )

                        text = (
                            element.text_content()
                            .strip()
                        )


                        if (
                            href
                            and "/recipes/" in href
                            and "/collection/" not in href
                            and "/category/" not in href
                            and text
                            and len(text) > 11
                        ):


                            if not href.startswith("http"):

                                href = (
                                    "https://www.bbcgoodfood.com"
                                    + href
                                )


                            if href not in self.recipe_urls:

                                self.recipe_urls.append(
                                    href
                                )

                                count += 1

                                print(
                                    f"  {count}. {text[:50]}"
                                )
                                print(
                                    f"     URL: {href}"
                                )


                    except Exception as e:

                        print(
                            f"  Error getting link: {e}"
                        )

                        continue


                browser.close()


                print(
                    f"\n✅ Found {len(self.recipe_urls)} recipes"
                )


            except Exception as e:

                print(
                    f"  ⚠️ Error getting recipes: {e}"
                )

                browser.close()


    def _scrape_all_recipes(self):
        """Scrape the collected recipe URLs"""
        print(f"\n🍳 Scraping {len(self.recipe_urls)} recipes...")
        
        # FIX FOR STREAMLIT CLOUD
        self._ensure_playwright_browser()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                slow_mo=0,
                args=["--no-sandbox"]
            )
            
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768}
            )
            
            page = context.new_page()
            
            for idx, url in enumerate(self.recipe_urls, 1):
                print(f"\n  [{idx}/{len(self.recipe_urls)}] Scraping recipe...")
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(2000)
                    
                    # Extract recipe data
                    recipe = self._extract_recipe(page, url)
                    
                    if recipe:
                        self.scraped_recipes.append(recipe)
                        print(f"    ✅ {recipe['title']}")
                        
                        # Show ingredients count
                        try:
                            ingredients = json.loads(recipe.get("ingredients", "[]"))
                            print(f"    📝 Ingredients: {len(ingredients)} items")
                        except:
                            pass
                    else:
                        print(f"    ⚠️ No recipe data found")
                        
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                
                # Small delay between requests
                time.sleep(1)
            
            browser.close()
        
        print(f"\n✅ Successfully scraped {len(self.scraped_recipes)} recipes")
    
    def _extract_recipe(self, page, url: str) -> Optional[Dict]:
        """Extract recipe data from the page"""
        try:
            # Try JSON-LD first
            scripts = page.locator("script[type='application/ld+json']").all()
            
            for script in scripts:
                try:
                    text = script.inner_text()
                    if not text.strip():
                        continue
                    
                    data = json.loads(text)
                    
                    # Extract recipe from JSON-LD
                    recipe_data = self._parse_jsonld(data, url)
                    if recipe_data:
                        return recipe_data
                        
                except Exception as e:
                    continue
            
            # Fallback to HTML parsing
            return self._parse_html(page, url)
            
        except Exception as e:
            print(f"    Extraction error: {e}")
            return None
    
    def _parse_jsonld(self, data, url: str) -> Optional[Dict]:
        """Parse recipe from JSON-LD data"""
        try:
            # Handle different JSON-LD structures
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "@graph" in data:
                    items = data["@graph"]
                else:
                    items = [data]
            else:
                return None
            
            for item in items:
                # Check if it's a recipe
                obj_type = item.get("@type")
                is_recipe = False
                if isinstance(obj_type, list):
                    is_recipe = "Recipe" in obj_type
                else:
                    is_recipe = obj_type == "Recipe"
                
                if not is_recipe:
                    continue
                
                # Extract nutrition
                nutrition = item.get("nutrition", {})
                if isinstance(nutrition, list) and nutrition:
                    nutrition = nutrition[0]
                
                # Extract instructions
                instructions = []
                raw_instructions = item.get("recipeInstructions", [])
                if isinstance(raw_instructions, list):
                    for step in raw_instructions:
                        if isinstance(step, dict):
                            text = step.get("text") or step.get("name")
                            if text:
                                instructions.append(text)
                        elif isinstance(step, str):
                            instructions.append(step)
                elif isinstance(raw_instructions, str):
                    instructions.append(raw_instructions)
                
                # Handle author
                author = None
                if isinstance(item.get("author"), dict):
                    author = item["author"].get("name")
                elif isinstance(item.get("author"), list):
                    author = item["author"][0].get("name") if item["author"] else None
                
                # Handle recipe yield
                recipe_yield = item.get("recipeYield")
                if isinstance(recipe_yield, list):
                    recipe_yield = ", ".join(recipe_yield)
                
                # Handle image
                image_url = None
                image = item.get("image")
                if isinstance(image, dict):
                    image_url = image.get("url")
                elif isinstance(image, list) and image:
                    image_url = image[0].get("url") if isinstance(image[0], dict) else image[0]
                elif isinstance(image, str):
                    image_url = image
                
                return {
                    "title": item.get("name", ""),
                    "url": url,
                    "source": "BBC Good Food",
                    "category": "vegetarian",
                    "ingredients": json.dumps(item.get("recipeIngredient", []), ensure_ascii=False),
                    "instructions": json.dumps(instructions, ensure_ascii=False),
                    "calories": nutrition.get("calories"),
                    "protein": nutrition.get("proteinContent"),
                    "fat": nutrition.get("fatContent"),
                    "carbohydrates": nutrition.get("carbohydrateContent"),
                    "fiber": nutrition.get("fiberContent"),
                    "sugar": nutrition.get("sugarContent"),
                    "cholesterol": nutrition.get("cholesterolContent"),
                    "sodium": nutrition.get("sodiumContent"),
                    "prep_time": item.get("prepTime"),
                    "cook_time": item.get("cookTime"),
                    "total_time": item.get("totalTime"),
                    "recipe_yield": recipe_yield,
                    "image_url": image_url,
                    "author": author,
                    "published_date": item.get("datePublished"),
                    "scraped_date": datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"    JSON-LD parsing error: {e}")
            return None
    
    def _parse_html(self, page, url: str) -> Optional[Dict]:
        """Fallback HTML parser"""
        try:
            recipe = {
                "title": "",
                "url": url,
                "source": "BBC Good Food",
                "category": "vegetarian",
                "ingredients": json.dumps([], ensure_ascii=False),
                "instructions": json.dumps([], ensure_ascii=False),
                "calories": None,
                "protein": None,
                "fat": None,
                "carbohydrates": None,
                "fiber": None,
                "sugar": None,
                "cholesterol": None,
                "sodium": None,
                "prep_time": None,
                "cook_time": None,
                "total_time": None,
                "recipe_yield": None,
                "image_url": None,
                "author": None,
                "published_date": None,
                "scraped_date": datetime.utcnow().isoformat()
            }
            
            # Get title
            title_element = page.locator("h1[data-test-id='recipe-title']").first
            if title_element.count():
                recipe["title"] = title_element.text_content().strip()
            
            # Get ingredients
            ingredients = []
            ingredient_elements = page.locator("[data-test-id='recipe-ingredients'] li").all()
            for element in ingredient_elements:
                text = element.text_content().strip()
                if text:
                    ingredients.append(text)
            recipe["ingredients"] = json.dumps(ingredients, ensure_ascii=False)
            
            # Get instructions
            instructions = []
            instruction_elements = page.locator("[data-test-id='recipe-instructions'] li").all()
            for element in instruction_elements:
                text = element.text_content().strip()
                if text:
                    instructions.append(text)
            recipe["instructions"] = json.dumps(instructions, ensure_ascii=False)
            
            return recipe if recipe["title"] else None
            
        except Exception as e:
            print(f"    HTML parsing error: {e}")
            return None
    
    def _save_results(self):
        """Save final results to file"""
        try:
            if self.scraped_recipes:
                # Save all recipes
                with open("all_recipes.json", "w") as f:
                    json.dump(self.scraped_recipes, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Saved {len(self.scraped_recipes)} recipes to all_recipes.json")
                
                # Print summary
                print("\n📋 SAVED RECIPES:")
                for idx, recipe in enumerate(self.scraped_recipes, 1):
                    print(f"  {idx}. {recipe.get('title', 'Unknown')}")
                    print(f"     Source: {recipe.get('source', 'Unknown')}")
                    try:
                        ingredients = json.loads(recipe.get('ingredients', '[]'))
                        print(f"     Ingredients: {len(ingredients)} items")
                    except:
                        pass
                    print()
            else:
                print("\n⚠️ No recipes were scraped")
                
        except Exception as e:
            print(f"Error saving results: {e}")


# Usage function for your Streamlit app
def run_all_bbc_scraper():
    """Function to call from Streamlit - scrapes latest 3 vegetarian recipes"""
    scraper = BBCGoodFoodAllScraper(
        max_recipes=11,  # Only 3 recipes
        save_progress=True
    )
    
    recipes = scraper.scrape_all()
    return recipes