import os
import logging
from datetime import datetime
from supabase import create_client, Client

class SupabaseNewsManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            logging.warning("⚠️ Supabase credentials not found. Deduplication will be disabled.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(url, key)
                logging.info("✅ Supabase client initialized.")
            except Exception as e:
                logging.error(f"❌ Failed to initialize Supabase client: {e}")
                self.client = None
        
        self.table_name = "News"

    def check_if_exists(self, title: str) -> bool:
        """
        Checks if a news with the given title already exists.
        Returns True if exists (duplicate), False otherwise.
        """
        if not self.client:
            return False
            
        try:
            # Simple exact match check. Could be improved with vector similarity later.
            response = self.client.table(self.table_name).select("id").eq("title", title).execute()
            if response.data and len(response.data) > 0:
                return True
            return False
        except Exception as e:
            logging.error(f"⚠️ Error checking Supabase for duplicate '{title}': {e}")
            return False

    def save_news(self, article: dict):
        """
        Saves a news article to the database.
        Expected article dict keys: title, url, published_date, source, summary_feed (optional)
        """
        if not self.client:
            return

        try:
            data = {
                "title": article.get("title"),
                # "url": article.get("url"), # User didn't list this column
                "date": article.get("published_date") or article.get("date"),
                "source": article.get("source"),
                # "summary": article.get("summary_feed", "") # User didn't list this column
                "date_sent": datetime.now().isoformat()
            }
            
            # Using upsert to be safe
            self.client.table(self.table_name).insert(data).execute()
            logging.info(f"💾 Saved to Supabase: {article.get('title')}")
            
        except Exception as e:
            logging.error(f"❌ Error saving to Supabase: {e}")
