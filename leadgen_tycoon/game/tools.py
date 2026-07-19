"""Tool marketplace and subscription effects."""

from copy import deepcopy

TOOLS = [
    {
        "id": "email_sending",
        "name": "Email sending tool",
        "monthly_cost": 69,
        "setup_cost": 40,
        "benefits": "Raises cold email sending capacity and consistency.",
        "downside": "More volume can still damage reputation if targeting is weak.",
        "effects": {"cold_email_leads_multiplier": 0.22, "cold_email_time_reduction": 0.10},
        "unlock_stage": 1,
    },
    {
        "id": "email_verification",
        "name": "Email verification tool",
        "monthly_cost": 49,
        "setup_cost": 25,
        "benefits": "Improves deliverability and protects sender reputation.",
        "downside": "Adds recurring cost before revenue is predictable.",
        "effects": {"cold_email_quality": 0.12, "reputation_protection": 0.20},
        "unlock_stage": 1,
    },
    {
        "id": "linkedin_automation",
        "name": "LinkedIn automation tool",
        "monthly_cost": 99,
        "setup_cost": 60,
        "benefits": "Increases LinkedIn outreach throughput.",
        "downside": "Adds account restriction risk when used aggressively.",
        "effects": {"linkedin_outreach_leads_multiplier": 0.35, "linkedin_risk": 0.06},
        "unlock_stage": 1,
    },
    {
        "id": "apify_credits",
        "name": "Apify credits",
        "monthly_cost": 79,
        "setup_cost": 0,
        "benefits": "Expands prospecting workflows and niche discovery.",
        "downside": "Can create noisy data without automation and targeting skill.",
        "effects": {"apify_workflows_leads_multiplier": 0.55, "targeting_quality": 0.08},
        "unlock_stage": 1,
    },
    {
        "id": "landing_page_builder",
        "name": "Landing page builder",
        "monthly_cost": 59,
        "setup_cost": 80,
        "benefits": "Improves conversion rates for ads, content, and direct response campaigns.",
        "downside": "Requires offer clarity; weak pages still convert poorly.",
        "effects": {"booking_rate": 0.08, "linkedin_ads_quality": 0.12, "landing_pages_leads_multiplier": 0.22},
        "unlock_stage": 1,
    },
    {
        "id": "crm",
        "name": "CRM",
        "monthly_cost": 89,
        "setup_cost": 120,
        "benefits": "Improves follow-up, reduces lost leads, and supports handoffs.",
        "downside": "Adds process overhead if operations are weak.",
        "effects": {"booking_rate": 0.05, "lost_leads_reduction": 0.25, "operations_quality": 0.06},
        "unlock_stage": 1,
    },
    {
        "id": "analytics_dashboard",
        "name": "Analytics dashboard",
        "monthly_cost": 119,
        "setup_cost": 100,
        "benefits": "Improves campaign optimization and reporting discipline.",
        "downside": "Data is only useful if reviewed consistently.",
        "effects": {"analytics_quality": 0.13, "qualified_rate": 0.04, "optimization": 0.08},
        "unlock_stage": 1,
    },
    {
        "id": "sales_call_recording",
        "name": "Sales call recording tool",
        "monthly_cost": 39,
        "setup_cost": 20,
        "benefits": "Improves sales learning and objection handling.",
        "downside": "Takes review time to convert recordings into better calls.",
        "effects": {"close_rate": 0.07, "sales_learning": 0.15},
        "unlock_stage": 1,
    },
    {
        "id": "data_enrichment",
        "name": "Data enrichment tool",
        "monthly_cost": 149,
        "setup_cost": 75,
        "benefits": "Improves targeting and qualification quality.",
        "downside": "Expensive early and can encourage over-segmentation.",
        "effects": {"qualified_rate": 0.07, "targeting_quality": 0.12},
        "unlock_stage": 2,
    },
    {
        "id": "scheduling",
        "name": "Scheduling tool",
        "monthly_cost": 29,
        "setup_cost": 15,
        "benefits": "Reduces booking friction and admin time.",
        "downside": "Does not fix weak demand or weak offers.",
        "effects": {"booking_rate": 0.06, "sales_time_reduction": 0.08},
        "unlock_stage": 1,
    },
    {
        "id": "proposal_software",
        "name": "Proposal software",
        "monthly_cost": 49,
        "setup_cost": 45,
        "benefits": "Improves proposal speed, clarity, and close rate.",
        "downside": "Templates can feel generic if the offer is weak.",
        "effects": {"close_rate": 0.05, "sales_time_reduction": 0.05},
        "unlock_stage": 1,
    },
    {
        "id": "ai_copywriting",
        "name": "AI copywriting assistant",
        "monthly_cost": 35,
        "setup_cost": 0,
        "benefits": "Saves time and improves iteration speed for copy.",
        "downside": "Overuse can produce generic messaging and reduce trust.",
        "effects": {"copy_quality": 0.08, "copy_time_reduction": 0.14, "generic_copy_risk": 0.05},
        "unlock_stage": 1,
    },
    {
        "id": "project_management",
        "name": "Project management tool",
        "monthly_cost": 79,
        "setup_cost": 70,
        "benefits": "Improves delivery capacity and reduces fulfillment mistakes.",
        "downside": "Needs operational discipline to be useful.",
        "effects": {"delivery_capacity": 7, "operations_quality": 0.08, "churn_reduction": 0.04},
        "unlock_stage": 2,
    },
]


def get_tool(tool_id):
    for tool in TOOLS:
        if tool["id"] == tool_id:
            return deepcopy(tool)
    return None


def owned_tool_ids(state):
    return {tool["id"] for tool in state.get("tools", [])}


def is_tool_owned(state, tool_id):
    return tool_id in owned_tool_ids(state)


def tool_effect_value(state, key):
    total = 0.0
    for tool in state.get("tools", []):
        total += float(tool.get("effects", {}).get(key, 0))
    return total


def monthly_tool_cost(state):
    return sum(float(tool.get("monthly_cost", 0)) for tool in state.get("tools", []))


def buy_tool(state, tool_id):
    tool = get_tool(tool_id)
    if not tool:
        return False, "Tool not found."
    if is_tool_owned(state, tool_id):
        return False, "You already subscribe to this tool."
    cost = float(tool.get("setup_cost", 0))
    if state.get("cash", 0) < cost:
        return False, f"You need ${cost:,.0f} for setup."
    state["cash"] -= cost
    state.setdefault("tools", []).append(tool)
    state.setdefault("last_feedback", []).append(
        f"Bought {tool['name']}. It adds ${tool['monthly_cost']:,.0f}/month, so it needs to improve conversion or save time to justify itself."
    )
    return True, f"{tool['name']} added."


def cancel_tool(state, tool_id):
    before = len(state.get("tools", []))
    state["tools"] = [tool for tool in state.get("tools", []) if tool["id"] != tool_id]
    if len(state["tools"]) == before:
        return False, "Subscription not found."
    return True, "Subscription cancelled."

