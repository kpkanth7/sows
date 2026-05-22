TIER1_COMPANIES = [
    {'name': 'NVIDIA', 'ticker': 'NVDA', 'is_private': False, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'NVIDIA'},
    {'name': 'Google', 'ticker': 'GOOGL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'google'},
    {'name': 'Microsoft', 'ticker': 'MSFT', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'microsoft'},
    {'name': 'Apple', 'ticker': 'AAPL', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'apple'},
    {'name': 'OpenAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'openai'}
]

TIER2_COMPANIES = [
    {'name': 'Meta', 'ticker': 'META', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'facebook'},
    {'name': 'Amazon', 'ticker': 'AMZN', 'is_private': False, 'sector': 'Technology', 'is_ai_company': True, 'github_org': 'amzn'},
    {'name': 'Tesla', 'ticker': 'TSLA', 'is_private': False, 'sector': 'Automotive', 'is_ai_company': True, 'github_org': 'teslamotors'},
    {'name': 'Anthropic', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'anthropics'},
    {'name': 'Mistral', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'mistralai'},
    {'name': 'xAI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'xai'},
    {'name': 'Perplexity', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'perplexity-ai'},
    {'name': 'Salesforce', 'ticker': 'CRM', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'salesforce'},
    {'name': 'Intel', 'ticker': 'INTC', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'intel'},
    {'name': 'AMD', 'ticker': 'AMD', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ROCm'},
    {'name': 'TSMC', 'ticker': 'TSM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': None},
    {'name': 'Palantir', 'ticker': 'PLTR', 'is_private': False, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'palantir'},
    {'name': 'Snowflake', 'ticker': 'SNOW', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'snowflakedb'},
    {'name': 'Databricks', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'databricks'},
    {'name': 'Arm', 'ticker': 'ARM', 'is_private': False, 'sector': 'Semiconductors', 'is_ai_company': False, 'github_org': 'ARM-software'},
    {'name': 'Cloudflare', 'ticker': 'NET', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'cloudflare'},
    {'name': 'MongoDB', 'ticker': 'MDB', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'mongodb'},
    {'name': 'HuggingFace', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'huggingface'},
    {'name': 'Stability AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'Stability-AI'}
]

TIER3_COMPANIES = [
    {'name': 'Oracle', 'ticker': 'ORCL', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'oracle'},
    {'name': 'IBM', 'ticker': 'IBM', 'is_private': False, 'sector': 'Technology', 'is_ai_company': False, 'github_org': 'IBM'},
    {'name': 'Shopify', 'ticker': 'SHOP', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Shopify'},
    {'name': 'Stripe', 'ticker': None, 'is_private': True, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'stripe'},
    {'name': 'Coinbase', 'ticker': 'COIN', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'coinbase'},
    {'name': 'Robinhood', 'ticker': 'HOOD', 'is_private': False, 'sector': 'Fintech', 'is_ai_company': False, 'github_org': 'robinhood'},
    {'name': 'Unity', 'ticker': 'U', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Unity-Technologies'},
    {'name': 'Roblox', 'ticker': 'RBLX', 'is_private': False, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'Roblox'},
    {'name': 'Discord', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'discord'},
    {'name': 'Figma', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'figma'},
    {'name': 'Notion', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'makenotion'},
    {'name': 'Linear', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'linear'},
    {'name': 'Vercel', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'vercel'},
    {'name': 'Supabase', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'supabase'},
    {'name': 'Replit', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'replit'},
    {'name': 'Cursor', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': True, 'github_org': 'getcursor'},
    {'name': 'Cohere', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'cohere-ai'},
    {'name': 'AI21', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'AI21Labs'},
    {'name': 'Runway', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'runwayml'},
    {'name': 'ElevenLabs', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'elevenlabs'},
    {'name': 'Harvey AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': None},
    {'name': 'Scale AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'scaleapi'},
    {'name': 'WandB', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'wandb'},
    {'name': 'Pinecone', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'pinecone-io'},
    {'name': 'Groq', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'groq'},
    {'name': 'Cerebras', 'ticker': None, 'is_private': True, 'sector': 'AI Hardware', 'is_ai_company': True, 'github_org': 'Cerebras'},
    {'name': 'Modal', 'ticker': None, 'is_private': True, 'sector': 'Software', 'is_ai_company': False, 'github_org': 'modal-labs'},
    {'name': 'Together AI', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'togethercomputer'},
    {'name': 'Qdrant', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'qdrant'},
    {'name': 'LangChain', 'ticker': None, 'is_private': True, 'sector': 'AI', 'is_ai_company': True, 'github_org': 'langchain-ai'}
]

ALL_COMPANIES = [c['name'] for c in TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES]

YOUTUBE_CHANNELS = [
    {'name': 'Fireship', 'channel_id': 'UCsBjURrPoezykLs9EqgamOA', 'category': 'dev', 'playlist_id': 'UUsBjURrPoezykLs9EqgamOA'},
    {'name': 'Two Minute Papers', 'channel_id': 'UCbfYPyITQ-7l4upoX8nvctg', 'category': 'ai_ml', 'playlist_id': 'UUbfYPyITQ-7l4upoX8nvctg'},
    {'name': 'Yannic Kilcher', 'channel_id': 'UCzhmTeWuF61jRhptzcVBRsQ', 'category': 'ai_ml', 'playlist_id': 'UUzhmTeWuF61jRhptzcVBRsQ'},
    {'name': 'AI Explained', 'channel_id': 'UCNJ1Ymd5yWuZZPNAXm3Skg', 'category': 'ai_ml', 'playlist_id': 'UUNJ1Ymd5yWuZZPNAXm3Skg'},
    {'name': 'Matt Wolfe', 'channel_id': 'UCmN2w9tPj5kH5E4D1tI4Hbw', 'category': 'ai_ml', 'playlist_id': 'UUmN2w9tPj5kH5E4D1tI4Hbw'},
    {'name': 'World of AI', 'channel_id': 'UC4OZbT3r7D1A9e12v_K6vqw', 'category': 'ai_ml', 'playlist_id': 'UU4OZbT3r7D1A9e12v_K6vqw'},
    {'name': 'MKBHD', 'channel_id': 'UCBJycsmduvYEL83R_U4JriQ', 'category': 'tech_general', 'playlist_id': 'UUBJycsmduvYEL83R_U4JriQ'},
    {'name': 'Linus Tech Tips', 'channel_id': 'UCXuqSBlHAE6Xw-yeJA0Tunw', 'category': 'tech_general', 'playlist_id': 'UUXuqSBlHAE6Xw-yeJA0Tunw'},
    {'name': 'Mrwhosetheboss', 'channel_id': 'UCVYamHliCI9W1NcRSiWpD-g', 'category': 'tech_general', 'playlist_id': 'UUVYamHliCI9W1NcRSiWpD-g'},
    {'name': 'Varun Mayya', 'channel_id': 'UCjHDEgR3QZ9HqBfV-6D6VpQ', 'category': 'startup', 'playlist_id': 'UUjHDEgR3QZ9HqBfV-6D6VpQ'},
    {'name': 'Y Combinator', 'channel_id': 'UCcefcZRL2oaA_uBNeo5UOWg', 'category': 'startup', 'playlist_id': 'UUcefcZRL2oaA_uBNeo5UOWg'},
    {'name': 'Garry Tan', 'channel_id': 'UCbUoR-pE_kK9g1_h1y3r1Bw', 'category': 'startup', 'playlist_id': 'UUbUoR-pE_kK9g1_h1y3r1Bw'},
    {'name': 'Meet Kevin', 'channel_id': 'UC3D_V780B8N-d5a2I6D2-bQ', 'category': 'finance', 'playlist_id': 'UU3D_V780B8N-d5a2I6D2-bQ'},
    {'name': 'The Plain Bagel', 'channel_id': 'UC2D9b9_9ZJ1zH-yI2v9w3A', 'category': 'finance', 'playlist_id': 'UU2D9b9_9ZJ1zH-yI2v9w3A'},
    {'name': 'ThePrimeagen', 'channel_id': 'UC8ENHEh5W8iQ5N98dM8-dCQ', 'category': 'dev', 'playlist_id': 'UU8ENHEh5W8iQ5N98dM8-dCQ'},
    {'name': 'NetworkChuck', 'channel_id': 'UC9x0AN7BWHp0dp5vA2oB0_A', 'category': 'dev', 'playlist_id': 'UU9x0AN7BWHp0dp5vA2oB0_A'}
]

BLUESKY_ACCOUNTS = [
    'pmarca.com',
    'ylecun.com',
    'karpathy.ai',
    'swyx.io',
    'gdb.bsky.social',
    'sama.bsky.social',
    'elonmusk.bsky.social',
    'clem.huggingface.co'
]

RSS_FEEDS = [
    'https://techcrunch.com/feed/',
    'https://www.theverge.com/rss/index.xml',
    'https://arstechnica.com/feed/',
    'https://venturebeat.com/feed/',
    'https://www.technologyreview.com/feed/',
    'https://www.wired.com/feed/rss'
]

REDDIT_SUBREDDITS = ['technology', 'MachineLearning', 'programming', 'artificial', 'investing']
