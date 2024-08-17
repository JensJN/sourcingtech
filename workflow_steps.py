SUMMARY_BEGINNING_OF_PROMPT = """I'm a VC. I want to draft an email to an entrepreneur that conveys that I'm knowledgeable about:
        - his business
        - the market and industry context his business operates in
        - how his business differentiates vs. its competitors
        - what customers are saying about his business
        - any recent news or key developments around his business I might congratulate him on
        I'll write greeting and sign-off separately; only provide email body to copy/paste, nothing else.
        Use the following information about the company:
        \n**********"""

SUMMARY_END_OF_PROMPT = """\n**********\n
        For drafting the email body, it's important that you write it as follows:
        - Length: concise; max. 3 short paragraphs.
        - Tone: conversational, direct, to the point.
        - Language: factual, analytical, no flattery.
        """

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
    },
    {
        "step_name": "Funding History",
        "search_query": "{company_url} funding rounds investment series total raised investors",
        "prompt_to_analyse": "Summarize the company's funding history, including total amount raised, key investors, and details of the most recent funding round if available. Include any information on the company's current valuation or financial status if publicly available.",
        "include_domains": ["crunchbase.com", "pitchbook.com", "dealroom.co"]
    }
]

# For testing purposes
TEST_ONLY = False

if TEST_ONLY:
    WORKFLOW_STEPS = [
        {
            "step_name": "Company Overview",
            "search_query": "{company_url} about OR mission OR products OR services",
            "prompt_to_analyse": "Summarize the key information about the company from its official website, including its mission, products/services, and any unique selling points.",
            "include_domains": ["{company_url}"]
        }
    ]
