# test_categories.py

from playwright.sync_api import sync_playwright
import time

def test_category(category_name: str, category_url: str):
    """Test if a category page is accessible and has recipe links"""
    print(f"\n{'='*60}")
    print(f"Testing category: {category_name}")
    print(f"URL: {category_url}")
    print('='*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to category page
            print("⏳ Loading page...")
            page.goto(category_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            
            # Check page title
            title = page.title()
            print(f"📄 Page title: {title}")
            
            # Check if we got a valid page (not 404 or error)
            if "404" in title or "Page not found" in title:
                print("❌ Page not found (404)")
                browser.close()
                return False
            
            # --- IMPROVED SELECTOR ---
            # Find recipe links that are in the main recipe list
            # Look for links within article elements or with specific class patterns
            selectors = [
                "article a[href*='/recipes/']",  # Links inside article tags
                "li a[href*='/recipes/']",  # Links inside list items
                "a[href*='/recipes/']:not([href*='/collection/']):not([href*='/category/'])"  # Exclude collection/category links
            ]
            
            recipe_links = []
            for selector in selectors:
                elements = page.locator(selector).all()
                for element in elements:
                    try:
                        href = element.get_attribute("href")
                        text = element.text_content().strip()
                        if href and "/recipes/" in href:
                            # Only keep actual recipe links (not collections or categories)
                            if "/collection/" not in href and "/category/" not in href:
                                if href not in [r["href"] for r in recipe_links]:
                                    recipe_links.append({
                                        "href": href,
                                        "text": text
                                    })
                    except:
                        continue
            
            # If no links found with the above, try a more general approach
            if not recipe_links:
                print("🔄 No recipe links found with specific selectors, trying general search...")
                all_links = page.locator("a[href*='/recipes/']").all()
                for element in all_links:
                    try:
                        href = element.get_attribute("href")
                        text = element.text_content().strip()
                        # Filter out collection links
                        if href and "/recipes/" in href and "/collection/" not in href and "/category/" not in href:
                            # Check if it's a valid recipe (has a title and not empty)
                            if text and len(text) > 3:
                                if href not in [r["href"] for r in recipe_links]:
                                    recipe_links.append({
                                        "href": href,
                                        "text": text
                                    })
                    except:
                        continue
            
            count = len(recipe_links)
            print(f"🔗 Found {count} recipe links")
            
            # Get first 3 links as sample
            if count > 0:
                print("\n📝 First 3 recipe links:")
                for i in range(min(3, count)):
                    href = recipe_links[i]["href"]
                    text = recipe_links[i]["text"]
                    full_url = href if href.startswith("http") else f"https://www.bbcgoodfood.com{href}"
                    print(f"  {i+1}. {text[:50] if text else 'Untitled'}")
                    print(f"     URL: {full_url}")
            else:
                print("❌ No recipe links found")
                browser.close()
                return False
            
            # Check for JSON-LD
            scripts = page.locator("script[type='application/ld+json']").count()
            print(f"\n📊 Found {scripts} JSON-LD scripts")
            
            browser.close()
            
            # Determine if successful
            if count > 0:
                print(f"\n✅ Category '{category_name}' is accessible and has {count} recipes!")
                return True
            else:
                print(f"\n⚠️ Category '{category_name}' has no recipes")
                return False
                
        except Exception as e:
            print(f"❌ Error testing category: {e}")
            browser.close()
            return False


def test_vegetarian():
    """Test only the vegetarian category"""
    print("\n" + "="*80)
    print("🔍 TESTING VEGETARIAN CATEGORY")
    print("="*80)
    
    category_url = "https://www.bbcgoodfood.com/recipes/collection/vegetarian-recipes"
    
    result = test_category("vegetarian", category_url)
    
    if result:
        print("\n✅ Vegetarian category is working!")
    else:
        print("\n❌ Vegetarian category is not working")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_vegetarian()
    else:
        test_vegetarian()