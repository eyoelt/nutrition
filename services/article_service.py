from database.db import database
import sqlite3
import json
from models.article import Article


class ArticleService:

    # ---------------------------------------------------------
    # SAVE ARTICLES (Regular articles - not recipes)
    # ---------------------------------------------------------
    def save_articles(self, articles):
        conn = database.connect()
        cursor = conn.cursor()
        saved = 0

        for article in articles:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO articles(
                    title,
                    url,
                    source,
                    category,
                    summary,
                    author,
                    published_date,
                    scraped_date
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.title,
                    article.url,
                    article.source,
                    article.category,
                    article.summary,
                    article.author,
                    article.published_date,
                    article.scraped_date
                ))

                if cursor.rowcount > 0:
                    saved += 1

            except Exception as e:
                print(f"Article Save Error: {e}")

        conn.commit()
        conn.close()
        return saved

    # ---------------------------------------------------------
    # SAVE RECIPES (Using the recipe-specific columns)
    # ---------------------------------------------------------
    def save_recipes(self, recipes):
        conn = database.connect()
        cursor = conn.cursor()
        saved = 0

        for recipe in recipes:
            try:
                # Extract nutrition data
                nutrition = recipe.get("nutrition", {})
                
                # Handle recipe_yield - could be list or string
                recipe_yield = recipe.get("recipeYield")
                if isinstance(recipe_yield, list):
                    recipe_yield = ", ".join(recipe_yield)
                
                # Handle ingredients and instructions - could be lists
                ingredients = recipe.get("ingredients", [])
                if isinstance(ingredients, list):
                    ingredients = "\n".join(ingredients)
                
                instructions = recipe.get("instructions", [])
                if isinstance(instructions, list):
                    instructions = "\n".join(instructions)
                
                cursor.execute("""
                INSERT OR IGNORE INTO articles(
                    title,
                    url,
                    source,
                    category,
                    summary,
                    ingredients,
                    instructions,
                    calories,
                    protein,
                    fat,
                    carbohydrates,
                    fiber,
                    sugar,
                    cholesterol,
                    sodium,
                    prep_time,
                    cook_time,
                    total_time,
                    recipe_yield,
                    image_url,
                    author,
                    published_date,
                    scraped_date
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recipe.get("title"),
                    recipe.get("url"),
                    recipe.get("source"),
                    "recipe",  # Category
                    recipe.get("summary", recipe.get("title")),
                    ingredients,
                    instructions,
                    nutrition.get("calories"),
                    nutrition.get("proteinContent"),
                    nutrition.get("fatContent"),
                    nutrition.get("carbohydrateContent"),
                    nutrition.get("fiberContent"),
                    nutrition.get("sugarContent"),
                    nutrition.get("cholesterolContent"),
                    nutrition.get("sodiumContent"),
                    recipe.get("prepTime"),
                    recipe.get("cookTime"),
                    recipe.get("totalTime"),
                    recipe_yield,
                    recipe.get("image_url"),
                    recipe.get("author"),
                    recipe.get("published_date"),
                    recipe.get("scraped_date")
                ))

                if cursor.rowcount > 0:
                    saved += 1

            except Exception as e:
                print(f"Recipe Save Error: {e}")
                print(f"Problematic recipe: {recipe.get('title')}")
                # Print the recipe data for debugging if needed
                # print(f"Recipe data: {recipe}")

        conn.commit()
        conn.close()
        return saved

    # ---------------------------------------------------------
    # GET ALL ARTICLES
    # ---------------------------------------------------------
    def get_articles(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM articles
            ORDER BY scraped_date DESC
        """)

        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        articles = []
        for row in rows:
            articles.append(dict(row))
        
        conn.close()
        return articles

    # ---------------------------------------------------------
    # GET RECIPES
    # ---------------------------------------------------------
    def get_recipes(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM articles
            WHERE category = 'recipe'
            ORDER BY scraped_date DESC
        """)

        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        recipes = []
        for row in rows:
            recipe_dict = dict(row)
            
            # Convert ingredients and instructions back to lists
            if recipe_dict.get("ingredients"):
                recipe_dict["ingredients"] = recipe_dict["ingredients"].split("\n")
            else:
                recipe_dict["ingredients"] = []
                
            if recipe_dict.get("instructions"):
                recipe_dict["instructions"] = recipe_dict["instructions"].split("\n")
            else:
                recipe_dict["instructions"] = []
            
            recipes.append(recipe_dict)
        
        conn.close()
        return recipes

    # ---------------------------------------------------------
    # GET RECIPE TABLE (for management view)
    # ---------------------------------------------------------
    def get_recipe_table(self):
        rows = self.get_recipes()
        table = []

        for row in rows:
            try:
                # Get ingredients and instructions (already lists from get_recipes)
                ingredients = row.get("ingredients", [])
                instructions = row.get("instructions", [])

                table.append({
                    "Title": row.get("title", ""),
                    "Source": row.get("source", ""),
                    "Category": row.get("category", ""),
                    "Author": row.get("author", ""),
                    "Published": row.get("published_date", ""),
                    "Ingredients": len(ingredients),
                    "Instructions": len(instructions),
                    "Calories": row.get("calories"),
                    "Protein": row.get("protein"),
                    "Carbs": row.get("carbohydrates"),
                    "Fat": row.get("fat"),
                    "Prep Time": row.get("prep_time"),
                    "Cook Time": row.get("cook_time"),
                    "Total Time": row.get("total_time"),
                    "Yield": row.get("recipe_yield"),
                    "URL": row.get("url", "")
                })

            except Exception as e:
                print(f"Error processing recipe row: {e}")
                continue

        return table

    # ---------------------------------------------------------
    # GET NON RECIPE ARTICLES
    # ---------------------------------------------------------
    def get_non_recipe_articles(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM articles
            WHERE category IS NULL
               OR category != 'recipe'
        """)

        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        articles = []
        for row in rows:
            articles.append(dict(row))
        
        conn.close()
        return articles

    # ---------------------------------------------------------
    # METRICS
    # ---------------------------------------------------------
    def get_total_articles(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_total_sources(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_total_categories(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT category)
            FROM articles
            WHERE category IS NOT NULL
        """)

        total = cursor.fetchone()[0]
        conn.close()
        return total

    # ---------------------------------------------------------
    # CLEAR
    # ---------------------------------------------------------
    def clear_articles(self):
        conn = database.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM articles")
        conn.commit()
        conn.close()


# Create singleton instance
article_service = ArticleService()