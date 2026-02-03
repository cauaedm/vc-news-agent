import sys
import os
import re
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()

from src.supabase_client import SupabaseNewsManager

raw_text = """
🇧🇷 Fiemg Anjos - Seed Investment
The Deal: Fiemg Anjos makes its first investment in a software startup for the industrial sector.
Business: The startup develops software solutions aimed at enhancing the industrial processes.
Founders: Not disclosed.
Investors: Fiemg Anjos.
Valuation: Not disclosed.
Why it matters: This marks a significant step for Fiemg Anjos as it enters the venture funding space, emphasizing the importance of technology in industrial growth.
Read Source
🇧🇷 Juspay - Series D
The Deal: Juspay raises $50M in Series D funding to accelerate global expansion.
Business: Juspay provides payment solutions tailored for online shops and platforms.
Founders: Not disclosed.
Investors: Not disclosed.
Valuation: Not disclosed.
Why it matters: The funding is a strong indication of increasing demand for reliable payment solutions in the fast-growing fintech sector in Brazil.
Read Source
🇧🇷 Caf - Series A
The Deal: Caf rebrands after securing R$ 50M from L4, marking its new phase.
Business: Dedicated to integrating ID technologies for businesses.
Founders: Not disclosed.
Investors: L4.
Valuation: Not disclosed.
Why it matters: This funding signifies potential growth within the ID technology market in Brazil, pushing innovation and service expansion.
Read Source
🇧🇷 Magie - Fundraising
The Deal: Magie raises R$ 27 million.
Business: Aimed at developing innovative digital solutions.
Founders: Not disclosed.
Investors: Not disclosed.
Valuation: Not disclosed.
Why it matters: The investment highlights the sustained investor interest in technology startups that offer creative and scalable digital solutions.
Read Source
🇧🇷 Passabot - Seed Funding
The Deal: Passabot raises R$ 1.2 million.
Business: Passabot provides automated customer service solutions.
Founders: Not disclosed.
Investors: Not disclosed.
Valuation: Not disclosed.
Why it matters: The growth in customer service automation indicates a shift towards more efficient business operations among Brazilian startups.
Read Source
🇧🇷 Frete.com - Fundraising
The Deal: Frete.com raises R$ 150 million with a FIDC.
Business: Provides transportation and logistics solutions.
Founders: Not disclosed.
Investors: Not disclosed.
Valuation: Not disclosed.
Why it matters: This funding showcases the potential of the logistics sector as demand for efficient delivery services continues to increase in e-commerce.
Read Source
🇧🇷 CRMBonus - Minority Acquisition
The Deal: iFood's minority acquisition of CRMBonus is approved by Cade.
Business: CRMBonus provides customer loyalty and reward programs.
Founders: Not disclosed.
Investors: iFood.
Valuation: Not disclosed.
Why it matters: This acquisition allows iFood to enhance its customer engagement strategies, highlighting the growing competitive landscape of loyalty programs in food tech.
Read Source
🇧🇷 PicPay - IPO Announcement
The Deal: PicPay initiates the process of going public (IPO).
Business: Provides a mobile payments platform.
Founders: Not disclosed.
Investors: Not disclosed.
Valuation: Not disclosed.
Why it matters: The move towards an IPO demonstrates confidence in market conditions and commitment to expanding its financial services reach.
Read Source
"""

def parse_and_seed():
    manager = SupabaseNewsManager()
    if not manager.client:
        print("❌ Supabase client not initialized.")
        return

    # Split by the Brazilian flag
    items = raw_text.strip().split("🇧🇷")
    
    count = 0
    for item in items:
        if not item.strip():
            continue
            
        lines = item.strip().split('\n')
        # Title is the first line
        title = lines[0].strip()
        
        # Try to find source from content or default
        # Since text doesn't explicitly have source name other than inferred from title or 'Read Source' which is empty
        # We will use "Manual Import"
        source = "Manual Import"
        
        # Date: User didn't provide dates in text, assuming today or Unknown
        date_str = datetime.now().strftime("%Y-%m-%d")

        print(f"Processing: {title}")
        
        article = {
            "title": title,
            "source": source,
            "date": date_str,
            # date_sent is handled by save_news
        }
        
        if not manager.check_if_exists(title):
            manager.save_news(article)
            count += 1
        else:
            print(f"Skipping duplicate: {title}")

    print(f"✅ Finished. Seeded {count} articles.")

if __name__ == "__main__":
    parse_and_seed()
