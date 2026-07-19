"""Shared seed data and constants for LeadGen Tycoon."""

SKILLS = [
    "Copywriting",
    "Targeting",
    "Offer Creation",
    "Sales",
    "Operations",
    "Client Delivery",
    "Analytics",
    "Automation",
]

BUSINESS_STAGES = [
    {"name": "Solo freelancer", "min_mrr": 0, "min_clients": 0, "min_reputation": 0},
    {"name": "Specialist", "min_mrr": 3000, "min_clients": 2, "min_reputation": 45},
    {"name": "Small agency", "min_mrr": 10000, "min_clients": 5, "min_reputation": 55},
    {"name": "Growing agency", "min_mrr": 25000, "min_clients": 10, "min_reputation": 65},
    {"name": "Established business", "min_mrr": 60000, "min_clients": 20, "min_reputation": 75},
    {"name": "Market leader", "min_mrr": 150000, "min_clients": 40, "min_reputation": 88},
]

CHANNEL_IDS = [
    "cold_email",
    "linkedin_outreach",
    "linkedin_ads",
    "apify_workflows",
    "landing_pages",
    "referrals",
    "content_marketing",
    "sales_calls",
]

CLIENT_NICHES = [
    "B2B SaaS",
    "Local services",
    "Recruiting firm",
    "Managed IT provider",
    "Commercial real estate",
    "Healthcare services",
    "Financial advisory",
    "Marketing consultancy",
    "Manufacturing supplier",
    "Training company",
    "Cybersecurity vendor",
    "Logistics firm",
]

CLIENT_NAME_PARTS = [
    "Northstar",
    "Brightline",
    "Summit",
    "Keystone",
    "Bluefield",
    "Redwood",
    "Signal",
    "Harbor",
    "Vector",
    "Pioneer",
    "Cobalt",
    "Apex",
]

BASE_FIXED_MONTHLY_EXPENSES = 250
WEEKS_PER_MONTH = 4.33
MAX_SKILL_LEVEL = 10

