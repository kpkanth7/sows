TIER1_COMPANIES = [
    {'name': 'NVIDIA', 'ticker': 'NVDA', 'is_private': False, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'NVIDIA'},
    {'name': 'Google', 'ticker': 'GOOGL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'google'},
    {'name': 'Microsoft', 'ticker': 'MSFT', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'microsoft'},
    {'name': 'Apple', 'ticker': 'AAPL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'apple'},
    {'name': 'OpenAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'openai', 'last_valuation': 157000000000, 'valuation_source': 'Series H (Oct 2024)'}
]

TIER2_COMPANIES = [
    {'name': 'Meta', 'ticker': 'META', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'facebook'},
    {'name': 'Amazon', 'ticker': 'AMZN', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'amzn'},
    {'name': 'Tesla', 'ticker': 'TSLA', 'is_private': False, 'sector': 'Automotive', 'is_ai_company': True, 'github_org': 'teslamotors'},
    {'name': 'Anthropic', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'anthropics', 'last_valuation': 40000000000, 'valuation_source': 'Amazon/Google round (May 2024)'},
    {'name': 'Mistral', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'mistralai', 'last_valuation': 6000000000, 'valuation_source': 'Series B (Jun 2024)'},
    {'name': 'xAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'xai', 'last_valuation': 45000000000, 'valuation_source': 'Series C (Dec 2024)'},
    {'name': 'Perplexity', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'perplexity-ai', 'last_valuation': 9000000000, 'valuation_source': 'Funding round (Jan 2025)'},
    {'name': 'Salesforce', 'ticker': 'CRM', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'salesforce'},
    {'name': 'Intel', 'ticker': 'INTC', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'intel'},
    {'name': 'AMD', 'ticker': 'AMD', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ROCm'},
    {'name': 'TSMC', 'ticker': 'TSM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None},
    {'name': 'Palantir', 'ticker': 'PLTR', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'palantir'},
    {'name': 'Snowflake', 'ticker': 'SNOW', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'snowflakedb'},
    {'name': 'Databricks', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'databricks', 'last_valuation': 43000000000, 'valuation_source': 'Series I (Sep 2023)'},
    {'name': 'Arm', 'ticker': 'ARM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ARM-software'},
    {'name': 'Cloudflare', 'ticker': 'NET', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'cloudflare'},
    {'name': 'MongoDB', 'ticker': 'MDB', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'mongodb'},
    {'name': 'HuggingFace', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'huggingface', 'last_valuation': 4500000000, 'valuation_source': 'Series D (Aug 2023)'},
    {'name': 'Stability AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'Stability-AI', 'last_valuation': 1000000000, 'valuation_source': 'Seed round (Oct 2022)'}
]

TIER3_COMPANIES = [
    {'name': 'Oracle', 'ticker': 'ORCL', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'oracle'},
    {'name': 'IBM', 'ticker': 'IBM', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'IBM'},
    {'name': 'Shopify', 'ticker': 'SHOP', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Shopify'},
    {'name': 'Stripe', 'ticker': None, 'is_private': True, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'stripe', 'last_valuation': 70000000000, 'valuation_source': 'Tender offer (Feb 2024)'},
    {'name': 'Coinbase', 'ticker': 'COIN', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'coinbase'},
    {'name': 'Robinhood', 'ticker': 'HOOD', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'robinhood'},
    {'name': 'Unity', 'ticker': 'U', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Unity-Technologies'},
    {'name': 'Roblox', 'ticker': 'RBLX', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Roblox'},
    {'name': 'Discord', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'discord', 'last_valuation': 15000000000, 'valuation_source': 'Funding round (2021)'},
    {'name': 'Figma', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'figma', 'last_valuation': 10000000000, 'valuation_source': 'Secondary market (2024)'},
    {'name': 'Notion', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'makenotion', 'last_valuation': 10000000000, 'valuation_source': 'Series C (2021)'},
    {'name': 'Linear', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'linear', 'last_valuation': 400000000, 'valuation_source': 'Series A (2023)'},
    {'name': 'Vercel', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'vercel', 'last_valuation': 3200000000, 'valuation_source': 'Series D (2024)'},
    {'name': 'Supabase', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'supabase', 'last_valuation': 1000000000, 'valuation_source': 'Series B (2024)'},
    {'name': 'Replit', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'replit', 'last_valuation': 800000000, 'valuation_source': 'Series B extension (2023)'},
    {'name': 'Cursor', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'getcursor', 'last_valuation': 2500000000, 'valuation_source': 'Series A (Aug 2024)'},
    {'name': 'Cohere', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'cohere-ai', 'last_valuation': 5500000000, 'valuation_source': 'Series D (Jun 2024)'},
    {'name': 'AI21', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'AI21Labs', 'last_valuation': 1400000000, 'valuation_source': 'Series C (Nov 2023)'},
    {'name': 'Runway', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'runwayml', 'last_valuation': 4000000000, 'valuation_source': 'Series C extension (2024)'},
    {'name': 'ElevenLabs', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'elevenlabs', 'last_valuation': 3000000000, 'valuation_source': 'Series B (Jan 2024)'},
    {'name': 'Harvey AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None, 'last_valuation': 1500000000, 'valuation_source': 'Series B (Jul 2024)'},
    {'name': 'Scale AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'scaleapi', 'last_valuation': 14000000000, 'valuation_source': 'Series F (May 2024)'},
    {'name': 'WandB', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'wandb', 'last_valuation': 1200000000, 'valuation_source': 'Series C (2021)'},
    {'name': 'Pinecone', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'pinecone-io', 'last_valuation': 1000000000, 'valuation_source': 'Series B (Apr 2023)'},
    {'name': 'Groq', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'groq', 'last_valuation': 2800000000, 'valuation_source': 'Series D (Aug 2024)'},
    {'name': 'Cerebras', 'ticker': None, 'is_private': True, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'Cerebras', 'last_valuation': 4000000000, 'valuation_source': 'Pre-IPO round (2024)'},
    {'name': 'Modal', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'modal-labs', 'last_valuation': 300000000, 'valuation_source': 'Series A (2023)'},
    {'name': 'Together AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'togethercomputer', 'last_valuation': 1300000000, 'valuation_source': 'Series A (Mar 2024)'},
    {'name': 'Qdrant', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'qdrant', 'last_valuation': 200000000, 'valuation_source': 'Series A (Jan 2024)'},
    {'name': 'LangChain', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'langchain-ai', 'last_valuation': 200000000, 'valuation_source': 'Series A (2024)'}
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
    'technology', 'MachineLearning', 'programming', 'artificial', 'investing',
    'singularity', 'LocalLLaMA', 'OpenAI', 'SaaS', 'devops',
    'softwaredevelopment', 'tech', 'compsci', 'ClaudeAI', 'Anthropic'
]
