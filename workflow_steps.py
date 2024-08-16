WORKFLOW_STEPS = [
    {"step_name": "Company Overview",
     "search_query": "company overview {company_url}",
     "prompt_to_analyse": "Provide a brief overview of the company.",
     "include_domains": ["{company_url}", "wikipedia.org"]
    },
    {"step_name": "Products and Services",
     "search_query": "products and services offered by {company_url}",
     "prompt_to_analyse": "List the main products and services offered by the company.",
     "include_domains": ["{company_url}"]
    }
]
