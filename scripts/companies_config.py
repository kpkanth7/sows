# Tech / software only (AI, ML, robotics, semis, SaaS, dev-tools, fintech-infra).
# region = continent/zone bucket for Market Map grouping (3.10). Private valuations
# web-researched 2026-05-29; public companies use live market_cap (no valuation field).
TIER1_COMPANIES = [
    {'name': 'NVIDIA', 'ticker': 'NVDA', 'is_private': False, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'NVIDIA', 'region': 'US'},
    {'name': 'Google', 'ticker': 'GOOGL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'google', 'region': 'US'},
    {'name': 'Microsoft', 'ticker': 'MSFT', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'microsoft', 'region': 'US'},
    {'name': 'Apple', 'ticker': 'AAPL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'apple', 'region': 'US'},
    {'name': 'OpenAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'openai', 'last_valuation': 852000000000, 'valuation_source': 'Private round (2026)', 'region': 'US'}
]

TIER2_COMPANIES = [
    # --- existing US/global large-cap ---
    {'name': 'Meta', 'ticker': 'META', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'facebook', 'region': 'US'},
    {'name': 'Amazon', 'ticker': 'AMZN', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'amzn', 'region': 'US'},
    {'name': 'Tesla', 'ticker': 'TSLA', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': 'teslamotors', 'region': 'US'},
    {'name': 'Anthropic', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'anthropics', 'last_valuation': 965000000000, 'valuation_source': 'Series H (May 2026)', 'region': 'US'},
    {'name': 'Mistral', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'mistralai', 'last_valuation': 14000000000, 'valuation_source': 'Series C (Sep 2025)', 'region': 'Europe'},
    {'name': 'xAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'xai', 'last_valuation': None, 'valuation_source': 'Merged into SpaceX (Feb 2026)', 'region': 'US'},
    {'name': 'Perplexity', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'perplexity-ai', 'last_valuation': 9000000000, 'valuation_source': 'Funding round (Jan 2025)', 'region': 'US'},
    {'name': 'Salesforce', 'ticker': 'CRM', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'salesforce', 'region': 'US'},
    {'name': 'Intel', 'ticker': 'INTC', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'intel', 'region': 'US'},
    {'name': 'AMD', 'ticker': 'AMD', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ROCm', 'region': 'US'},
    {'name': 'TSMC', 'ticker': 'TSM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None, 'region': 'Taiwan'},
    {'name': 'Palantir', 'ticker': 'PLTR', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'palantir', 'region': 'US'},
    {'name': 'Snowflake', 'ticker': 'SNOW', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'snowflakedb', 'region': 'US'},
    {'name': 'Databricks', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'databricks', 'last_valuation': 134000000000, 'valuation_source': 'Series L (Dec 2025)', 'region': 'US'},
    {'name': 'Arm', 'ticker': 'ARM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ARM-software', 'region': 'Europe'},
    {'name': 'Cloudflare', 'ticker': 'NET', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'cloudflare', 'region': 'US'},
    {'name': 'MongoDB', 'ticker': 'MDB', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'mongodb', 'region': 'US'},
    {'name': 'HuggingFace', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'huggingface', 'last_valuation': 4500000000, 'valuation_source': 'Series D (Aug 2023)', 'region': 'US'},
    {'name': 'Stability AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'Stability-AI', 'last_valuation': 1000000000, 'valuation_source': 'Seed round (Oct 2022)', 'region': 'Europe'},
    # --- added global large-cap (2026-05-29) ---
    {'name': 'Alibaba', 'ticker': 'BABA', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'alibaba', 'region': 'China'},
    {'name': 'Tencent', 'ticker': 'TCEHY', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'Tencent', 'region': 'China'},
    {'name': 'Baidu', 'ticker': 'BIDU', 'is_private': False, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'baidu', 'region': 'China'},
    {'name': 'PDD', 'ticker': 'PDD', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'China'},
    {'name': 'Samsung', 'ticker': '005930.KS', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'samsung', 'region': 'Korea'},
    {'name': 'SK Hynix', 'ticker': '000660.KS', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None, 'region': 'Korea'},
    {'name': 'SAP', 'ticker': 'SAP', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'SAP', 'region': 'Europe'},
    {'name': 'ASML', 'ticker': 'ASML', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None, 'region': 'Europe'},
    {'name': 'Broadcom', 'ticker': 'AVGO', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': True, 'github_org': 'Broadcom', 'region': 'US'},
    {'name': 'Qualcomm', 'ticker': 'QCOM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'qualcomm', 'region': 'US'},
    {'name': 'Adobe', 'ticker': 'ADBE', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'adobe', 'region': 'US'},
    {'name': 'ServiceNow', 'ticker': 'NOW', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'ServiceNow', 'region': 'US'},
    {'name': 'Sony', 'ticker': 'SONY', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'sony', 'region': 'Japan'},
    {'name': 'SoftBank', 'ticker': 'SFTBY', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': None, 'region': 'Japan'},
    {'name': 'Infineon', 'ticker': 'IFNNY', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'Infineon', 'region': 'Europe'},
    {'name': 'STMicroelectronics', 'ticker': 'STM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'STMicroelectronics', 'region': 'Europe'},
    {'name': 'CrowdStrike', 'ticker': 'CRWD', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'CrowdStrike', 'region': 'US'},
    {'name': 'Palo Alto Networks', 'ticker': 'PANW', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'PaloAltoNetworks', 'region': 'US'}
]

TIER3_COMPANIES = [
    # --- existing US public/private ---
    {'name': 'Oracle', 'ticker': 'ORCL', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'oracle', 'region': 'US'},
    {'name': 'IBM', 'ticker': 'IBM', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'IBM', 'region': 'US'},
    {'name': 'Shopify', 'ticker': 'SHOP', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Shopify', 'region': 'Canada'},
    {'name': 'Stripe', 'ticker': None, 'is_private': True, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'stripe', 'last_valuation': 91500000000, 'valuation_source': 'Tender offer (2025)', 'region': 'US'},
    {'name': 'Coinbase', 'ticker': 'COIN', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'coinbase', 'region': 'US'},
    {'name': 'Robinhood', 'ticker': 'HOOD', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'robinhood', 'region': 'US'},
    {'name': 'Unity', 'ticker': 'U', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Unity-Technologies', 'region': 'US'},
    {'name': 'Roblox', 'ticker': 'RBLX', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Roblox', 'region': 'US'},
    {'name': 'Discord', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'discord', 'last_valuation': 15000000000, 'valuation_source': 'Funding round (2021)', 'region': 'US'},
    {'name': 'Figma', 'ticker': 'FIG', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'figma', 'region': 'US'},
    {'name': 'Notion', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'makenotion', 'last_valuation': 10000000000, 'valuation_source': 'Series C (2021)', 'region': 'US'},
    {'name': 'Linear', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'linear', 'last_valuation': 400000000, 'valuation_source': 'Series A (2023)', 'region': 'US'},
    {'name': 'Vercel', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'vercel', 'last_valuation': 3200000000, 'valuation_source': 'Series D (2024)', 'region': 'US'},
    {'name': 'Supabase', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'supabase', 'last_valuation': 1000000000, 'valuation_source': 'Series B (2024)', 'region': 'US'},
    {'name': 'Replit', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'replit', 'last_valuation': 800000000, 'valuation_source': 'Series B extension (2023)', 'region': 'US'},
    {'name': 'Cursor', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'getcursor', 'last_valuation': 29300000000, 'valuation_source': 'Series D (Nov 2025)', 'region': 'US'},
    {'name': 'Cohere', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'cohere-ai', 'last_valuation': 5500000000, 'valuation_source': 'Series D (Jun 2024)', 'region': 'Canada'},
    {'name': 'AI21', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'AI21Labs', 'last_valuation': 1400000000, 'valuation_source': 'Series C (Nov 2023)', 'region': 'Middle East'},
    {'name': 'Runway', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'runwayml', 'last_valuation': 4000000000, 'valuation_source': 'Series C extension (2024)', 'region': 'US'},
    {'name': 'ElevenLabs', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'elevenlabs', 'last_valuation': 11000000000, 'valuation_source': 'Funding (Feb 2026)', 'region': 'US'},
    {'name': 'Harvey AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 1500000000, 'valuation_source': 'Series B (Jul 2024)', 'region': 'US'},
    {'name': 'Scale AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'scaleapi', 'last_valuation': 29000000000, 'valuation_source': 'Meta investment (Jun 2025)', 'region': 'US'},
    {'name': 'WandB', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'wandb', 'last_valuation': 1200000000, 'valuation_source': 'Series C (2021)', 'region': 'US'},
    {'name': 'Pinecone', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'pinecone-io', 'last_valuation': 1000000000, 'valuation_source': 'Series B (Apr 2023)', 'region': 'US'},
    {'name': 'Groq', 'ticker': None, 'is_private': True, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'groq', 'last_valuation': 2800000000, 'valuation_source': 'Series D (Aug 2024)', 'region': 'US'},
    {'name': 'Cerebras', 'ticker': None, 'is_private': True, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'Cerebras', 'last_valuation': 4000000000, 'valuation_source': 'Pre-IPO round (2024)', 'region': 'US'},
    {'name': 'Modal', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'modal-labs', 'last_valuation': 300000000, 'valuation_source': 'Series A (2023)', 'region': 'US'},
    {'name': 'Together AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'togethercomputer', 'last_valuation': 1300000000, 'valuation_source': 'Series A (Mar 2024)', 'region': 'US'},
    {'name': 'Qdrant', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'qdrant', 'last_valuation': 200000000, 'valuation_source': 'Series A (Jan 2024)', 'region': 'Europe'},
    {'name': 'LangChain', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'langchain-ai', 'last_valuation': 200000000, 'valuation_source': 'Series A (2024)', 'region': 'US'},
    # --- added global public: China ---
    {'name': 'JD.com', 'ticker': 'JD', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'China'},
    {'name': 'Xiaomi', 'ticker': '1810.HK', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'XiaoMi', 'region': 'China'},
    {'name': 'SMIC', 'ticker': '0981.HK', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None, 'region': 'China'},
    {'name': 'Kuaishou', 'ticker': '1024.HK', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': None, 'region': 'China'},
    {'name': 'Meituan', 'ticker': '3690.HK', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'meituan', 'region': 'China'},
    {'name': 'iFlytek', 'ticker': '002230.SZ', 'is_private': False, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'region': 'China'},
    {'name': 'SenseTime', 'ticker': '0020.HK', 'is_private': False, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'open-mmlab', 'region': 'China'},
    {'name': 'Zhipu AI', 'ticker': '2513.HK', 'is_private': False, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'THUDM', 'region': 'China'},
    {'name': 'Horizon Robotics', 'ticker': '9660.HK', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'region': 'China'},
    {'name': 'UBTech', 'ticker': '9880.HK', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'region': 'China'},
    # --- added global public: India ---
    {'name': 'Infosys', 'ticker': 'INFY', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'India'},
    {'name': 'TCS', 'ticker': 'TCS.NS', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'India'},
    {'name': 'Wipro', 'ticker': 'WIT', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'India'},
    {'name': 'HCLTech', 'ticker': 'HCLTECH.NS', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'India'},
    {'name': 'Persistent Systems', 'ticker': 'PERSISTENT.NS', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'India'},
    {'name': 'Freshworks', 'ticker': 'FRSH', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'freshworks', 'region': 'India'},
    # --- added global public: Europe ---
    {'name': 'Siemens', 'ticker': 'SIEGY', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'siemens', 'region': 'Europe'},
    {'name': 'Spotify', 'ticker': 'SPOT', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'spotify', 'region': 'Europe'},
    {'name': 'Nokia', 'ticker': 'NOK', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'nokia', 'region': 'Europe'},
    {'name': 'Ericsson', 'ticker': 'ERIC', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'Ericsson', 'region': 'Europe'},
    {'name': 'Adyen', 'ticker': 'ADYEY', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'Adyen', 'region': 'Europe'},
    {'name': 'UiPath', 'ticker': 'PATH', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'UiPath', 'region': 'Europe'},
    {'name': 'ABB', 'ticker': 'ABB', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'region': 'Europe'},
    # --- added global public: Korea / Japan ---
    {'name': 'Naver', 'ticker': '035420.KS', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'naver', 'region': 'Korea'},
    {'name': 'Coupang', 'ticker': 'CPNG', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'Korea'},
    {'name': 'Rakuten', 'ticker': 'RKUNY', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'rakuten', 'region': 'Japan'},
    {'name': 'Fanuc', 'ticker': 'FANUY', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'region': 'Japan'},
    # --- added global public: SE Asia / LatAm / Australia ---
    {'name': 'Sea Ltd', 'ticker': 'SE', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'SE Asia'},
    {'name': 'Grab', 'ticker': 'GRAB', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'SE Asia'},
    {'name': 'MercadoLibre', 'ticker': 'MELI', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': None, 'region': 'LatAm'},
    {'name': 'Nubank', 'ticker': 'NU', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': None, 'region': 'LatAm'},
    {'name': 'Atlassian', 'ticker': 'TEAM', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'atlassian', 'region': 'Australia'},
    {'name': 'WiseTech Global', 'ticker': 'WTC.AX', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': None, 'region': 'Australia'},
    # --- added US dark-horse / robotics public ---
    {'name': 'Intuitive Surgical', 'ticker': 'ISRG', 'is_private': False, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'region': 'US'},
    {'name': 'Super Micro', 'ticker': 'SMCI', 'is_private': False, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': None, 'region': 'US'},
    # --- added global private (valuations web-researched 2026-05-29) ---
    {'name': 'DeepSeek', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'deepseek-ai', 'last_valuation': 45000000000, 'valuation_source': 'Reported round (Q2 2026)', 'region': 'China'},
    {'name': 'Moonshot AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'MoonshotAI', 'last_valuation': 20000000000, 'valuation_source': 'Funding (May 2026)', 'region': 'China'},
    {'name': 'MiniMax', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'MiniMax-AI', 'last_valuation': 13200000000, 'valuation_source': 'HK IPO debut (Jan 2026)', 'region': 'China'},
    {'name': 'Safe Superintelligence', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 32000000000, 'valuation_source': 'Funding (2025)', 'region': 'US'},
    {'name': 'Figure AI', 'ticker': None, 'is_private': True, 'sector': 'Robotics', 'is_ai_company': True, 'github_org': None, 'last_valuation': 39000000000, 'valuation_source': 'Series C (2025)', 'region': 'US'},
    {'name': 'Canva', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'canva', 'last_valuation': 42000000000, 'valuation_source': 'Employee tender (2025)', 'region': 'Australia'},
    {'name': 'Helsing', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 4000000000, 'valuation_source': 'Funding (2025, approx)', 'region': 'Europe'},
    {'name': 'DeepL', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 2000000000, 'valuation_source': 'Funding (2024)', 'region': 'Europe'},
    {'name': 'Celonis', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'celonis', 'last_valuation': 13000000000, 'valuation_source': 'Series D (2022)', 'region': 'Europe'},
    {'name': 'Synthesia', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 2100000000, 'valuation_source': 'Series D (2025)', 'region': 'Europe'},
    {'name': 'Sarvam AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'sarvamai', 'last_valuation': 1500000000, 'valuation_source': 'Round (2026, reported)', 'region': 'India'},
    {'name': 'Krutrim', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 1500000000, 'valuation_source': 'Round (2025)', 'region': 'India'},
    {'name': 'Zoho', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'zoho', 'last_valuation': None, 'valuation_source': 'Bootstrapped (private)', 'region': 'India'}
]

ALL_COMPANIES = [c['name'] for c in TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES]

YOUTUBE_CHANNELS = [
    {'name': 'Fireship', 'channel_id': 'UCsBjURrPoezykLs9EqgamOA', 'category': 'dev', 'playlist_id': 'UUsBjURrPoezykLs9EqgamOA'},
    {'name': 'Two Minute Papers', 'channel_id': 'UCbfYPyITQ-7l4upoX8nvctg', 'category': 'ai_ml', 'playlist_id': 'UUbfYPyITQ-7l4upoX8nvctg'},
    {'name': 'Yannic Kilcher', 'channel_id': 'UCZHmQk67mSJgfCCTn7xBfew', 'category': 'ai_ml', 'playlist_id': 'UUZHmQk67mSJgfCCTn7xBfew'},
    {'name': 'AI Explained', 'channel_id': 'UCNJ1Ymd5yFuUPtn21xtRbbw', 'category': 'ai_ml', 'playlist_id': 'UUNJ1Ymd5yFuUPtn21xtRbbw'},
    {'name': 'Matt Wolfe', 'channel_id': 'UChpleBmo18P08aKCIgti38g', 'category': 'ai_ml', 'playlist_id': 'UUhpleBmo18P08aKCIgti38g'},
    {'name': 'World of AI', 'channel_id': 'UC2WmuBuFq6gL08QYG-JjXKw', 'category': 'ai_ml', 'playlist_id': 'UU2WmuBuFq6gL08QYG-JjXKw'},
    {'name': 'MKBHD', 'channel_id': 'UCBJycsmduvYEL83R_U4JriQ', 'category': 'tech_general', 'playlist_id': 'UUBJycsmduvYEL83R_U4JriQ'},
    {'name': 'Linus Tech Tips', 'channel_id': 'UCXuqSBlHAE6Xw-yeJA0Tunw', 'category': 'tech_general', 'playlist_id': 'UUXuqSBlHAE6Xw-yeJA0Tunw'},
    {'name': 'Mrwhosetheboss', 'channel_id': 'UCMiJRAwDNSNzuYeN2uWa0pA', 'category': 'tech_general', 'playlist_id': 'UUMiJRAwDNSNzuYeN2uWa0pA'},
    {'name': 'Varun Mayya', 'channel_id': 'UCsQoiOrh7jzKmE8NBofhTnQ', 'category': 'startup', 'playlist_id': 'UUsQoiOrh7jzKmE8NBofhTnQ'},
    {'name': 'Y Combinator', 'channel_id': 'UCcefcZRL2oaA_uBNeo5UOWg', 'category': 'startup', 'playlist_id': 'UUcefcZRL2oaA_uBNeo5UOWg'},
    {'name': 'Garry Tan', 'channel_id': 'UCIBgYfDjtWlbJhg--Z4sOgQ', 'category': 'startup', 'playlist_id': 'UUIBgYfDjtWlbJhg--Z4sOgQ'},
    {'name': 'Meet Kevin', 'channel_id': 'UCUvvj5lwue7PspotMDjk5UA', 'category': 'finance', 'playlist_id': 'UUUvvj5lwue7PspotMDjk5UA'},
    {'name': 'The Plain Bagel', 'channel_id': 'UCFCEuCsyWP0YkP3CZ3Mr01Q', 'category': 'finance', 'playlist_id': 'UUFCEuCsyWP0YkP3CZ3Mr01Q'},
    {'name': 'ThePrimeagen', 'channel_id': 'UCUyeluBRhGPCW4rPe_UvBZQ', 'category': 'dev', 'playlist_id': 'UUUyeluBRhGPCW4rPe_UvBZQ'},
    {'name': 'NetworkChuck', 'channel_id': 'UC9x0AN7BWHpCDHSm9NiJFJQ', 'category': 'dev', 'playlist_id': 'UU9x0AN7BWHpCDHSm9NiJFJQ'},
    {'name': 'Joseph Carlson', 'channel_id': 'UCfCT7SSFEWyG4th9ZmaGYqQ', 'category': 'finance', 'playlist_id': 'UUfCT7SSFEWyG4th9ZmaGYqQ'},
    {'name': 'BG2 Pod', 'channel_id': 'UC-yRDvpR99LUc5l7i7jLzew', 'category': 'finance', 'playlist_id': 'UU-yRDvpR99LUc5l7i7jLzew'},
    {'name': 'Ticker Symbol: YOU', 'channel_id': 'UC7kCeZ53sli_9XwuQeFxLqw', 'category': 'finance', 'playlist_id': 'UU7kCeZ53sli_9XwuQeFxLqw'},
    {'name': 'Andrej Karpathy', 'channel_id': 'UCXUPKJO5MZQN11PqgIvyuvQ', 'category': 'dev', 'playlist_id': 'UUXUPKJO5MZQN11PqgIvyuvQ'},
    {'name': 'ByteByteGo', 'channel_id': 'UCZgt6AzoyjslHTC9dz0UoTw', 'category': 'dev', 'playlist_id': 'UUZgt6AzoyjslHTC9dz0UoTw'},
    {'name': 'Web Dev Simplified', 'channel_id': 'UCFbNIlppjAuEX4znoulh0Cw', 'category': 'dev', 'playlist_id': 'UUFbNIlppjAuEX4znoulh0Cw'},
    {'name': 'Traversy Media', 'channel_id': 'UC29ju8bIPH5as8OGnQzwJyA', 'category': 'dev', 'playlist_id': 'UU29ju8bIPH5as8OGnQzwJyA'},
    {'name': 'TechLead', 'channel_id': 'UC4xKdmAXFh4ACyhpiQ_3qBw', 'category': 'dev', 'playlist_id': 'UU4xKdmAXFh4ACyhpiQ_3qBw'},
    {'name': 'All-In Podcast', 'channel_id': 'UCESLZhusAkFfsNsApnjF_Cg', 'category': 'finance', 'playlist_id': 'UUESLZhusAkFfsNsApnjF_Cg'},
    {'name': 'HyperChange', 'channel_id': 'UC1LAjODfg7dnSSrrPGGPPMw', 'category': 'finance', 'playlist_id': 'UU1LAjODfg7dnSSrrPGGPPMw'},
    {'name': 'ARK Invest', 'channel_id': 'UCK-zlnUfoDHzUwXcbddtnkg', 'category': 'finance', 'playlist_id': 'UUK-zlnUfoDHzUwXcbddtnkg'},
    {'name': 'Modern Software Engineering', 'channel_id': 'UCCfqyGl3nq_V0bo64CjZh8g', 'category': 'dev', 'playlist_id': 'UUCfqyGl3nq_V0bo64CjZh8g'}
]

BLUESKY_ACCOUNTS = [
    'yann-lecun.bsky.social',
    'karpathy.bsky.social',
    'swyx.io',
    'gdb.bsky.social',
    'sama.bsky.social',
    'clem.hf.co'
]

RSS_FEEDS = [
    'https://techcrunch.com/feed/',
    'https://www.theverge.com/rss/index.xml',
    'https://arstechnica.com/feed/',
    'https://venturebeat.com/feed/',
    'https://www.technologyreview.com/feed/',
    'https://www.wired.com/feed/rss',
    'https://news.ycombinator.com/rss',
    'https://www.techmeme.com/feed.xml',
    'https://www.infoq.com/feed/',
    'https://dev.to/feed'
]

REDDIT_SUBREDDITS = [
    'MachineLearning',
    'singularity',
    'LocalLLaMA',
    'OpenAI',
    'SaaS',
    'devops',
    'softwaredevelopment',
    'ClaudeAI',
    'Anthropic'
]
