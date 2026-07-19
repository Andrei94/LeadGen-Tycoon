"""Hiring and team management."""

from copy import deepcopy
from uuid import uuid4

ROLE_DATA = {
    "sdr": {
        "role": "SDR",
        "base_salary": 2600,
        "productivity_effect": {"cold_email_leads_multiplier": 0.18, "linkedin_outreach_leads_multiplier": 0.10, "call_capacity": 2},
        "quality_effect": {"targeting_quality": 0.04},
        "time_relief": 5,
        "delivery_capacity": 0,
        "training_requirement": 2,
        "mistakes": "Can send poorly researched outreach if ramped too quickly.",
    },
    "copywriter": {
        "role": "Copywriter",
        "base_salary": 3200,
        "productivity_effect": {"copy_quality": 0.12, "content_marketing_leads_multiplier": 0.16},
        "quality_effect": {"booking_rate": 0.03},
        "time_relief": 4,
        "delivery_capacity": 1,
        "training_requirement": 2,
        "mistakes": "Can drift off positioning without clear briefs.",
    },
    "linkedin_specialist": {
        "role": "LinkedIn outreach specialist",
        "base_salary": 3000,
        "productivity_effect": {"linkedin_outreach_leads_multiplier": 0.24},
        "quality_effect": {"linkedin_quality": 0.05},
        "time_relief": 5,
        "delivery_capacity": 0,
        "training_requirement": 2,
        "mistakes": "Can trigger restriction risk if activity spikes.",
    },
    "media_buyer": {
        "role": "Media buyer",
        "base_salary": 4500,
        "productivity_effect": {"linkedin_ads_leads_multiplier": 0.30},
        "quality_effect": {"linkedin_ads_quality": 0.08, "analytics_quality": 0.04},
        "time_relief": 3,
        "delivery_capacity": 0,
        "training_requirement": 3,
        "mistakes": "Can burn budget before enough signal is available.",
    },
    "sales_closer": {
        "role": "Sales closer",
        "base_salary": 5200,
        "productivity_effect": {"call_capacity": 7},
        "quality_effect": {"close_rate": 0.10},
        "time_relief": 6,
        "delivery_capacity": 0,
        "training_requirement": 3,
        "mistakes": "Can overpromise if incentives are not aligned.",
    },
    "virtual_assistant": {
        "role": "Virtual assistant",
        "base_salary": 1800,
        "productivity_effect": {"lost_leads_reduction": 0.08},
        "quality_effect": {"operations_quality": 0.03},
        "time_relief": 7,
        "delivery_capacity": 2,
        "training_requirement": 1,
        "mistakes": "Can mis-handle follow-up without checklists.",
    },
    "automation_specialist": {
        "role": "Automation specialist",
        "base_salary": 4300,
        "productivity_effect": {"apify_workflows_leads_multiplier": 0.34, "automation_quality": 0.08},
        "quality_effect": {"targeting_quality": 0.05},
        "time_relief": 4,
        "delivery_capacity": 2,
        "training_requirement": 3,
        "mistakes": "Can build brittle workflows if specs are vague.",
    },
    "strategist": {
        "role": "Strategist",
        "base_salary": 6500,
        "productivity_effect": {"offer_quality": 0.12, "qualified_rate": 0.06},
        "quality_effect": {"reputation_gain": 0.04},
        "time_relief": 3,
        "delivery_capacity": 3,
        "training_requirement": 4,
        "mistakes": "Expensive before there is enough client volume.",
    },
    "account_manager": {
        "role": "Account manager",
        "base_salary": 4200,
        "productivity_effect": {"churn_reduction": 0.06},
        "quality_effect": {"client_satisfaction": 0.06},
        "time_relief": 6,
        "delivery_capacity": 2,
        "training_requirement": 2,
        "mistakes": "Can hide delivery problems if reporting is weak.",
    },
    "operations_manager": {
        "role": "Operations manager",
        "base_salary": 5800,
        "productivity_effect": {"operations_quality": 0.10},
        "quality_effect": {"churn_reduction": 0.05},
        "time_relief": 8,
        "delivery_capacity": 3,
        "training_requirement": 4,
        "mistakes": "Too early, this creates fixed cost without enough process volume.",
    },
}

SENIORITY = {
    "Junior": {"salary": 0.72, "productivity": 0.72, "quality": 0.70, "mistake": 0.18, "training": 1},
    "Mid": {"salary": 1.0, "productivity": 1.0, "quality": 1.0, "mistake": 0.10, "training": 0},
    "Senior": {"salary": 1.45, "productivity": 1.30, "quality": 1.35, "mistake": 0.05, "training": -1},
}


def role_options():
    return deepcopy(ROLE_DATA)


def create_hire(role_id, seniority, current_week):
    role = ROLE_DATA[role_id]
    seniority_data = SENIORITY[seniority]
    salary = round(role["base_salary"] * seniority_data["salary"])
    training_weeks = max(0, role["training_requirement"] + seniority_data["training"])
    return {
        "id": str(uuid4()),
        "role_id": role_id,
        "role": role["role"],
        "seniority": seniority,
        "salary": salary,
        "hired_week": current_week,
        "training_weeks_remaining": training_weeks,
        "mistake_chance": seniority_data["mistake"],
        "mistakes": role["mistakes"],
    }


def hire_member(state, role_id, seniority):
    if role_id not in ROLE_DATA or seniority not in SENIORITY:
        return False, "Unknown role or seniority."
    candidate = create_hire(role_id, seniority, state.get("week", 1))
    onboarding_cost = round(candidate["salary"] * 0.25)
    if state.get("cash", 0) < onboarding_cost:
        return False, f"You need ${onboarding_cost:,.0f} for onboarding."
    state["cash"] -= onboarding_cost
    state.setdefault("team", []).append(candidate)
    state.setdefault("last_feedback", []).append(
        f"Hired a {candidate['seniority']} {candidate['role']}. Payroll rose by ${candidate['salary']:,.0f}/month; watch cash runway."
    )
    active_client_count = sum(1 for client in state.get("clients", []) if client.get("status") == "active")
    if role_id in {"account_manager", "operations_manager"} and active_client_count < 5:
        state.setdefault("last_feedback", []).append(
            f"{candidate['role']} leverage is limited with only {active_client_count} active client(s). Management hires pay off after there is enough delivery volume to manage."
        )
    return True, f"{candidate['seniority']} {candidate['role']} hired."


def fire_member(state, member_id):
    member = next((item for item in state.get("team", []) if item["id"] == member_id), None)
    if not member:
        return False, "Team member not found."
    severance = round(member["salary"] * 0.15)
    state["cash"] -= severance
    state["team"] = [item for item in state.get("team", []) if item["id"] != member_id]
    state["reputation"] = max(0, state.get("reputation", 0) - 1)
    return True, f"{member['role']} removed. Severance cost ${severance:,.0f}."


def monthly_payroll(state):
    return sum(float(member.get("salary", 0)) for member in state.get("team", []))


def _clamp(value, low, high):
    return max(low, min(high, value))


def team_effects(state):
    team = state.get("team", [])
    active_client_count = sum(1 for client in state.get("clients", []) if client.get("status") == "active")
    management_roles = {"account_manager", "operations_manager"}
    manager_count = sum(1 for member in team if member.get("role_id") in management_roles)
    manager_utilization = 1.0
    if manager_count:
        manager_utilization = _clamp(active_client_count / max(1, manager_count * 5), 0.0, 1.0)
    manager_effectiveness = 0.35 + 0.65 * manager_utilization

    effects = {
        "time_relief": 0.0,
        "delivery_capacity": 0.0,
        "mistake_risk": 0.0,
        "team_quality": 0.0,
        "management_utilization": manager_utilization,
        "coordination_overhead": 0.0,
    }
    count = 0
    role_counts = {}
    ops_leadership = 0.0
    for member in team:
        role = ROLE_DATA.get(member.get("role_id"))
        seniority = SENIORITY.get(member.get("seniority"), SENIORITY["Mid"])
        if not role:
            continue
        role_id = member.get("role_id")
        count += 1
        previous_same_role = role_counts.get(role_id, 0)
        role_counts[role_id] = previous_same_role + 1
        duplicate_efficiency = 1 / (1 + previous_same_role * 0.35)
        role_efficiency = duplicate_efficiency
        if role_id in management_roles:
            role_efficiency *= manager_effectiveness
        if role_id == "operations_manager":
            ops_leadership += seniority["quality"] * (0.55 if member.get("training_weeks_remaining", 0) > 0 else 1.0) * role_efficiency

        ramp = 0.55 if member.get("training_weeks_remaining", 0) > 0 else 1.0
        prod_factor = seniority["productivity"] * ramp * role_efficiency
        quality_factor = seniority["quality"] * ramp * role_efficiency

        effects["time_relief"] += role.get("time_relief", 0) * prod_factor
        effects["delivery_capacity"] += role.get("delivery_capacity", 0) * prod_factor
        effects["mistake_risk"] += member.get("mistake_chance", 0) * (1.35 if ramp < 1 else 1.0)
        effects["team_quality"] += quality_factor

        for key, value in role.get("productivity_effect", {}).items():
            effects[key] = effects.get(key, 0.0) + value * prod_factor
        for key, value in role.get("quality_effect", {}).items():
            effects[key] = effects.get(key, 0.0) + value * quality_factor

    if count:
        effects["team_quality"] = effects["team_quality"] / count
        effects["mistake_risk"] = min(0.35, effects["mistake_risk"] / max(1, count))
        operations_skill = state.get("skills", {}).get("Operations", 1)
        manageable_team_size = 2 + operations_skill * 1.2 + ops_leadership * 3.5
        excess_team = max(0, count - manageable_team_size)
        coordination_overhead = min(0.30, excess_team * 0.035)
        if coordination_overhead:
            effects["coordination_overhead"] = coordination_overhead
            effects["delivery_capacity"] *= 1 - coordination_overhead
            effects["time_relief"] *= 1 - coordination_overhead * 0.8
            effects["operations_quality"] = effects.get("operations_quality", 0.0) - coordination_overhead * 0.25
            effects["mistake_risk"] = min(0.45, effects["mistake_risk"] + coordination_overhead * 0.5)
    if manager_count:
        effects["management_bloat"] = max(0.0, 1.0 - manager_utilization)
        effects["manager_count"] = manager_count
        effects["active_client_count"] = active_client_count
    return effects


def advance_training(state):
    ramping = 0
    for member in state.get("team", []):
        if member.get("training_weeks_remaining", 0) > 0:
            member["training_weeks_remaining"] -= 1
            ramping += 1
    return ramping
