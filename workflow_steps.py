WORKFLOW_STEPS = [
    {
        "step_name": "Company Overview",
        "search_query": "{company_url} about OR mission OR products OR services",
        "prompt_to_analyse": "Summarize the key information about the company from its official website, including its mission, products/services, and any unique selling points.",
        "include_domains": ["{company_url}"]
    },
    {
        "step_name": "Founder Information",
        "search_query": "{company_url} founder OR CEO biography leadership team",
        "prompt_to_analyse": "Identify the founder(s) or CEO of the company and summarize their professional background, key achievements, and vision for the company.",
        "include_domains": ["{company_url}", "linkedin.com", "crunchbase.com"]
    },
    {
        "step_name": "Industry Analysis",
        "search_query": "{company_url} industry market report size growth trends 2024",
        "prompt_to_analyse": "Analyze the industry in which the company operates. Summarize key statistics, growth projections, market size, and emerging trends for 2024 and beyond.",
        "include_domains": ["statista.com", "marketresearch.com", "ibisworld.com", "grandviewresearch.com"]
    },
    {
        "step_name": "Competitor Analysis",
        "search_query": "{company_url} top competitors comparison market share",
        "prompt_to_analyse": "Identify the top 3-5 competitors of the company. For each competitor, summarize their key offerings and unique selling points. Then, compare and contrast with the target company, highlighting key differentiators and relative market positions.",
        "include_domains": []
    },
    {
        "step_name": "Customer Sentiment",
        "search_query": "{company_url} customer reviews testimonials case studies",
        "prompt_to_analyse": "Analyze customer reviews and testimonials for the company. Summarize the overall sentiment and extract common themes from both positive and negative reviews. Include any notable case studies or success stories if available.",
        "include_domains": ["trustpilot.com", "g2.com", "capterra.com", "{company_url}"]
    },
    {
        "step_name": "Recent Developments",
        "search_query": "{company_url} recent news announcements partnerships product launches achievements",
        "prompt_to_analyse": "Summarize the most significant recent news articles about the company, focusing on major announcements, partnerships, product launches, or achievements from the past 3 months.",
        "include_domains": ["{company_url}", "techcrunch.com", "crunchbase.com", "businesswire.com", "prnewswire.com"]
    }
]

SUMMARY_BEGINNING_OF_PROMPT = """You're an analyst and think step-by-step.
        
        Task: you'll be given information about a company to extract key insights from and to summarize:
        - what the company does
        - what products or services it offers (be more expansive here)
        - the market and industry context the company operates
        - what's been driving the market and what are recent industry trends and developments
        - how the company and its offering differentiates vs. its competitors
        - what customers are saying about the company and its products
        - any recent key news or developments around the company
        
        Objective: you're doing this for your director who wants to email the founder of this company and impress him with his in-depth knowledge about his business;
        therefore focus on insights and developments that an industry expert would pick up on.

        Only provide the summary; no need for commentary on the task, a pre-amble or closing language.
        
        You've now been given the below information:
        \n**********"""

SUMMARY_END_OF_PROMPT = """\n**********\n
        Remember your task and objective.
        """

DRAFT_EMAIL_PROMPT = """Objective: you're trying to get in touch with the founder and CEO of a company.
        You therefore need to write an email that demonstrates your in-depth knowledge about their business and industry.
        
        Task: write an email based on the information you'll be given.
        Only provide the email body; no greeting, no sign-off, nothing else.
        
        Content: should vary depending on the information you're given on this particular company; 
        select any themes that particularly stand out from the information, for example:
        - why the company's offering and product is a great idea
        - how the company offering differentiates from others' in the market
        - what's to like about this market (but don't cite any specific market figures)
        - any particularly positive customer feedback
        - any important more nuanced insights about the company, its market position or relevant industry trend
        - particularly noteworthy recent developments or achievements (very important if any)
        - do not comment on their revenue or headcount growth or their funding

        It's important that you phrase this as follows:
        - Length: concise; max. 3 short paragraphs.
        - Tone: conversational, direct, to the point.
        - Language/vocabulary: mature, factual, analytical, no flattery, not sales-y, simple language.
        - Do not use flowery language: innovative, revolutationary, rapid growth, market validation, underscores, relevance, rapidly, robust, aligns, recognition, noteworthy, demonstrates, critical, overlooked, crucial;
          instead of such flowerly language, prefer straight-forward language (important, nice, good, strong, differentiated, seems/sounds/feels like, makes sense, great to see, congrats on, I saw, etc.).
        - Prefer language such as 'I like company_name's xyz' or 'I like the xyz' or 'I saw xyz' to 'your xyz'.
        - Remember you're emailing the founder/CEO so don't speak about them in third-person (don't use: their, its, his, her, etc.).
        - Don't point out obvious things or lecture; remember while you did your research this is only your initial interpretation of things.
        - Start with 'I've recently come across company_name'

        You've now been given the below information on the company:
        \n**********\n"""
