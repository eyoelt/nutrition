import streamlit as st
import pandas as pd
import json
from services.article_service import article_service

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Nutrition Intelligence Platform",
    page_icon="🥗",
    layout="wide"
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🥗 Nutrition Intelligence")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🍽️ Recipes",
        "📊 Analytics",
        "⚙ Settings"
    ]
)

st.sidebar.markdown("---")

# =========================================================
# SCRAPER
# =========================================================

def run_recipe_scraper():
    """Run the comprehensive BBC Good Food scraper"""
    try:
        from scraper.bbc_goodfood_all import run_all_bbc_scraper
        
        # Use a status container for messages
        status_container = st.sidebar.container()
        status_container.info("🔄 Scraping recipes from BBC Good Food...")
        status_container.info("📚 This may take a few seconds...")
        
        # Run the scraper (no spinner to avoid blocking)
        recipes = run_all_bbc_scraper()
        
        if not recipes:
            status_container.warning("No recipes scraped.")
            return
        
        # Save to database
        saved = article_service.save_recipes(recipes)
        
        if saved > 0:
            status_container.success(f"✅ {saved} recipe(s) saved to database!")
            status_container.info(f"📊 Total recipes collected: {len(recipes)}")
            
            # Show some stats
            sources = set(r.get("source", "") for r in recipes)
            if sources:
                status_container.write(f"📌 Sources: {', '.join(list(sources)[:3])}...")
        else:
            status_container.warning("No new recipes were saved (duplicates?).")
                
    except ImportError as e:
        st.sidebar.error(f"❌ Scraper module not found: {e}")
        st.sidebar.info("💡 Make sure 'bbc_goodfood_all.py' exists in the scraper folder.")
    except Exception as e:
        st.sidebar.error(f"❌ Scraping failed: {e}")
        st.sidebar.info(f"🔍 Error details: {str(e)}")

# Scraper options in sidebar
st.sidebar.subheader("🍽️ Scraping Options")

# Option 1: Scrape all recipes
if st.sidebar.button("🔄 Scrape All Recipes", use_container_width=True):
    run_recipe_scraper()
    # REMOVED st.rerun() - No page refresh

# Option 2: Scrape specific recipe URLs
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Or Scrape Specific URLs")

custom_urls = st.sidebar.text_area(
    "Enter recipe URLs (one per line)",
    placeholder="https://www.bbcgoodfood.com/recipes/chicken-tikka-masala\nhttps://www.bbcgoodfood.com/recipes/spaghetti-carbonara",
    height=100
)

if st.sidebar.button("🍽️ Scrape Custom URLs", use_container_width=True):
    if custom_urls.strip():
        try:
            from scraper.bbc_goodfood_scraper import BBCGoodFoodScraper
            
            urls = [url.strip() for url in custom_urls.split("\n") if url.strip()]
            
            with st.spinner(f"Scraping {len(urls)} recipes..."):
                scraper = BBCGoodFoodScraper(urls)
                recipes = scraper.scrape()
                
                if recipes:
                    saved = article_service.save_recipes(recipes)
                    st.sidebar.success(f"✅ {saved} recipe(s) saved.")
                else:
                    st.sidebar.warning("No recipes scraped.")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error: {e}")
    else:
        st.sidebar.warning("Please enter at least one URL.")

# Add a manual refresh button
if st.sidebar.button("🔄 Refresh Page", use_container_width=True):
    st.rerun()

# =========================================================
# LOAD ARTICLES
# =========================================================

@st.cache_data(ttl=10)  # Cache for 10 seconds, refresh quickly
def load_articles():
    try:
        rows = article_service.get_articles()
        if not rows:
            return pd.DataFrame()
        
        # Convert rows to dictionaries
        data = []
        for row in rows:
            if isinstance(row, dict):
                data.append(row)
            else:
                # Convert to dict if it's a tuple or sqlite3.Row
                try:
                    data.append(dict(row))
                except:
                    # Fallback for sqlite3.Row objects
                    data.append({key: row[key] for key in row.keys()})
        
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"❌ Failed to load articles: {e}")
        return pd.DataFrame()

# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":
    st.title("🥗 Nutrition Intelligence Platform")
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Articles",
            article_service.get_total_articles()
        )
    
    with col2:
        st.metric(
            "Sources",
            article_service.get_total_sources()
        )
    
    with col3:
        st.metric(
            "Categories",
            article_service.get_total_categories()
        )
    
    with col4:
        # Get recipe count
        recipes = article_service.get_recipes()
        st.metric(
            "Recipes",
            len(recipes)
        )
    
    st.divider()
    
    # Recent recipes
    st.subheader("🍽️ Recent Recipes")
    
    try:
        recipes = article_service.get_recipes()
        
        if recipes:
            # Show last 5 recipes
            recent = recipes[:5]
            
            # Display as cards
            cols = st.columns(min(3, len(recent)))
            for idx, col in enumerate(cols):
                if idx < len(recent):
                    recipe = recent[idx]
                    with col:
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:5px; margin:5px 0;">
                            <h4>{recipe.get('title', 'Untitled')[:50]}</h4>
                            <p><small>Source: {recipe.get('source', 'Unknown')}</small></p>
                            <p><small>Published: {recipe.get('published_date', 'N/A')}</small></p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("📭 No recipes found. Try scraping some recipes!")
            
    except Exception as e:
        st.error(f"❌ Error loading recent recipes: {e}")
    
    st.divider()
    
    # Recipe management table
    st.subheader("📋 Recipe Management Table")
    
    try:
        table = article_service.get_recipe_table()
        
        if table:
            df = pd.DataFrame(table)
            st.dataframe(
                df,
                width="stretch",
                hide_index=True
            )
        else:
            st.info("📭 No recipes found in the database.")
            
    except Exception as e:
        st.error(f"❌ Error loading recipe table: {e}")

# =========================================================
# RECIPES
# =========================================================

elif page == "🍽️ Recipes":
    st.title("🍽️ Recipe Explorer")
    
    try:
        recipes = article_service.get_recipes()
        
        if not recipes:
            st.info("📭 No recipes found. Go to Dashboard and scrape some recipes first!")
            st.stop()
        
        # Convert to DataFrame
        df = pd.DataFrame(recipes)
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        
        with col1:
            keyword = st.text_input("🔍 Search recipe...", placeholder="Type a recipe name...")
        
        with col2:
            # Source filter
            sources = ["All"] + sorted(df["source"].unique().tolist())
            selected_source = st.selectbox("📌 Filter by source", sources)
        
        # Apply filters
        filtered_df = df.copy()
        
        if keyword:
            filtered_df = filtered_df[
                filtered_df["title"].str.contains(keyword, case=False, na=False)
            ]
        
        if selected_source != "All":
            filtered_df = filtered_df[filtered_df["source"] == selected_source]
        
        if filtered_df.empty:
            st.info(f"No recipes found matching your criteria")
            st.stop()
        
        st.subheader(f"📋 Found {len(filtered_df)} recipe(s)")
        
        # Display recipe list with selection
        display_cols = ["title", "source", "published_date", "author"]
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_cols],
            width="stretch",
            hide_index=True
        )
        
        st.divider()
        
        # Recipe detail view
        selected = st.selectbox(
            "📖 Select a recipe to view details",
            filtered_df["title"].tolist()
        )
        
        if selected:
            row = filtered_df[filtered_df["title"] == selected].iloc[0]
            
            st.header(f"🍳 {row['title']}")
            
            # Recipe image if available
            if row.get("image_url"):
                st.image(row["image_url"], width=300)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Ingredients
                st.subheader("📝 Ingredients")
                ingredients = row.get("ingredients", [])
                if ingredients:
                    if isinstance(ingredients, str):
                        try:
                            # Try to parse as JSON if stored as JSON string
                            ingredients = json.loads(ingredients)
                        except:
                            ingredients = ingredients.split("\n")
                    for item in ingredients:
                        if item and str(item).strip():
                            st.markdown(f"- {item}")
                else:
                    st.warning("No ingredients listed")
                
                # Instructions
                st.subheader("👨‍🍳 Instructions")
                instructions = row.get("instructions", [])
                if instructions:
                    if isinstance(instructions, str):
                        try:
                            instructions = json.loads(instructions)
                        except:
                            instructions = instructions.split("\n")
                    for i, step in enumerate(instructions, start=1):
                        if step and str(step).strip():
                            st.write(f"**Step {i}:** {step}")
                else:
                    st.warning("No instructions available")
            
            with col2:
                # Nutrition
                st.subheader("📊 Nutrition Facts")
                nutrition_fields = {
                    "calories": "Calories",
                    "protein": "Protein (g)",
                    "fat": "Fat (g)",
                    "carbohydrates": "Carbs (g)",
                    "fiber": "Fiber (g)",
                    "sugar": "Sugar (g)",
                    "cholesterol": "Cholesterol (mg)",
                    "sodium": "Sodium (mg)"
                }
                
                has_nutrition = False
                for field, label in nutrition_fields.items():
                    value = row.get(field)
                    if value and value != "None" and value != "null":
                        st.write(f"**{label}:** {value}")
                        has_nutrition = True
                
                if not has_nutrition:
                    st.warning("No nutrition data available")
                
                st.divider()
                
                # Recipe Information
                st.subheader("ℹ️ Recipe Information")
                info = {
                    "Source": row.get("source"),
                    "Author": row.get("author"),
                    "Published": row.get("published_date"),
                    "Prep Time": row.get("prep_time"),
                    "Cook Time": row.get("cook_time"),
                    "Total Time": row.get("total_time"),
                    "Yield": row.get("recipe_yield"),
                }
                
                for key, value in info.items():
                    if value and value != "None" and value != "null":
                        st.write(f"**{key}:** {value}")
                
                st.divider()
                
                if row.get("url"):
                    st.link_button(
                        "🔗 Open Original Recipe",
                        row["url"],
                        width="stretch"
                    )
                    
    except Exception as e:
        st.error(f"❌ Error loading recipes: {e}")
        st.info("💡 Try scraping some recipes first!")

# =========================================================
# ANALYTICS
# =========================================================

elif page == "📊 Analytics":
    st.title("📊 Analytics Dashboard")
    
    try:
        table = article_service.get_recipe_table()
        
        if not table:
            st.info("📭 No recipe data available for analytics.")
        else:
            df = pd.DataFrame(table)
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Recipes", len(df))
            
            with col2:
                # Average calories
                if "Calories" in df.columns:
                    cal_series = pd.to_numeric(df["Calories"], errors="coerce")
                    avg_cal = cal_series.mean() if not cal_series.isna().all() else 0
                    st.metric("Avg Calories", f"{avg_cal:.0f}" if avg_cal > 0 else "N/A")
                else:
                    st.metric("Avg Calories", "N/A")
            
            with col3:
                # Average protein
                if "Protein" in df.columns:
                    protein_series = pd.to_numeric(df["Protein"], errors="coerce")
                    avg_protein = protein_series.mean() if not protein_series.isna().all() else 0
                    st.metric("Avg Protein (g)", f"{avg_protein:.1f}" if avg_protein > 0 else "N/A")
                else:
                    st.metric("Avg Protein (g)", "N/A")
            
            with col4:
                sources = df["Source"].nunique() if "Source" in df.columns else 0
                st.metric("Unique Sources", sources)
            
            st.divider()
            
            # Charts
            st.subheader("📈 Data Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Source distribution
                if "Source" in df.columns:
                    source_counts = df["Source"].value_counts()
                    st.bar_chart(source_counts)
                    st.caption("Recipe Sources Distribution")
            
            with col2:
                # Calories distribution
                if "Calories" in df.columns:
                    cal_data = pd.to_numeric(df["Calories"], errors="coerce").dropna()
                    if not cal_data.empty:
                        st.bar_chart(cal_data.sort_values().reset_index(drop=True))
                        st.caption("Calories Distribution")
            
            st.divider()
            
            # Full data table
            st.subheader("📊 Recipe Data Table")
            
            display_cols = [
                "Title", "Source", "Category", "Author",
                "Calories", "Protein", "Carbs", "Fat",
                "Prep Time", "Cook Time", "Total Time"
            ]
            
            available_cols = [col for col in display_cols if col in df.columns]
            
            st.dataframe(
                df[available_cols],
                width="stretch",
                hide_index=True
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Recipe Data (CSV)",
                data=csv,
                file_name=f"recipe_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch"
            )
            
    except Exception as e:
        st.error(f"❌ Analytics error: {e}")

# =========================================================
# SETTINGS
# =========================================================

else:  # Settings page
    st.title("⚙ Settings")
    
    st.subheader("🗄️ Database Management")
    
    total = article_service.get_total_articles()
    st.write(f"**Current database:** {total} total articles")
    
    if total > 0:
        sources = article_service.get_total_sources()
        categories = article_service.get_total_categories()
        recipes = article_service.get_recipes()
        st.write(f"**Sources:** {sources} | **Categories:** {categories} | **Recipes:** {len(recipes)}")
    
    st.divider()
    
    # Export data
    st.subheader("📤 Export Data")
    
    if st.button("📥 Export All Recipes to JSON"):
        try:
            recipes = article_service.get_recipes()
            if recipes:
                with open("exported_recipes.json", "w") as f:
                    json.dump(recipes, f, indent=2, default=str)
                st.success(f"✅ Exported {len(recipes)} recipes to exported_recipes.json")
                
                # Create download button
                with open("exported_recipes.json", "r") as f:
                    data = f.read()
                    st.download_button(
                        label="Download JSON File",
                        data=data,
                        file_name="exported_recipes.json",
                        mime="application/json",
                        width="stretch"
                    )
            else:
                st.warning("No recipes to export.")
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
    
    st.divider()
    
    # Danger zone
    st.subheader("⚠️ Danger Zone")
    
    st.warning("⚠️ This action will permanently delete all data from the database!")
    
    confirm = st.text_input("Type 'DELETE' to confirm database clear:", placeholder="Type DELETE here...")
    
    if confirm == "DELETE":
        if st.button("🗑️ Clear Database", type="primary"):
            try:
                article_service.clear_articles()
                st.success("✅ Database cleared successfully!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to clear database: {e}")
    elif confirm and confirm != "DELETE":
        st.warning("Please type 'DELETE' exactly to confirm")
    
    st.divider()
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()