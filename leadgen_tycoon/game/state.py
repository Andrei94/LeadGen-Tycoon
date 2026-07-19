"""Game state factory and normalization helpers."""

from copy import deepcopy
from datetime import datetime

from .channels import CHANNELS
from .data import BASE_FIXED_MONTHLY_EXPENSES, BUSINESS_STAGES, MAX_SKILL_LEVEL, SKILLS, WEEKS_PER_MONTH
from .hiring import monthly_payroll
from .tools import monthly_tool_cost


def new_game():
    now = datetime.utcnow().isoformat(timespec="seconds")
    return {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "seed": 137,
        "week": 1,
        "xp": 0,
        "level": 1,
        "stage": "Solo freelancer",
        "cash": 5000.0,
        "mrr": 0.0,
        "one_time_revenue": 0.0,
        "monthly_expenses": BASE_FIXED_MONTHLY_EXPENSES,
        "weekly_profit": 0.0,
        "reputation": 42.0,
        "founder_energy": 82.0,
        "founder_time_capacity": 45.0,
        "skills": {skill: 1 for skill in SKILLS},
        "skill_xp": {skill: 0.0 for skill in SKILLS},
        "tools": [],
        "team": [],
        "clients": [],
        "pipeline": {
            "leads": 0,
            "qualified_leads": 0,
            "booked_calls": 0,
            "booked_calls_by_channel": {},
        },
        "channel_performance": {
            channel_id: {
                "leads": 0,
                "qualified": 0,
                "booked": 0,
                "clients": 0,
                "spend": 0.0,
                "revenue": 0.0,
                "runs": 0,
            }
            for channel_id in CHANNELS
        },
        "metrics": {
            "lifetime_leads": 0,
            "lifetime_qualified_leads": 0,
            "lifetime_booked_calls": 0,
            "lifetime_clients_closed": 0,
            "lifetime_churned_clients": 0,
            "lifetime_referrals": 0,
            "total_revenue": 0.0,
            "total_expenses": 0.0,
            "total_campaign_spend": 0.0,
        },
        "history": [],
        "last_results": {},
        "last_feedback": [
            "You are starting as a solo founder. Your first constraint is not scale; it is finding a repeatable channel without burning cash or reputation."
        ],
        "last_events": [],
        "last_achievements": [],
        "achievements": [],
        "active_modifiers": [],
    }


def normalize_state(state):
    base = new_game()
    merged = deepcopy(base)
    merged.update(state or {})
    for key, value in base.items():
        if isinstance(value, dict):
            merged.setdefault(key, {})
            for sub_key, sub_value in value.items():
                merged[key].setdefault(sub_key, deepcopy(sub_value))
    merged["skills"] = {skill: int(merged.get("skills", {}).get(skill, 1)) for skill in SKILLS}
    merged["skill_xp"] = {skill: float(merged.get("skill_xp", {}).get(skill, 0)) for skill in SKILLS}
    merged.setdefault("pipeline", {}).setdefault("booked_calls_by_channel", {})
    for channel_id in CHANNELS:
        merged.setdefault("channel_performance", {}).setdefault(
            channel_id,
            {"leads": 0, "qualified": 0, "booked": 0, "clients": 0, "spend": 0.0, "revenue": 0.0, "runs": 0},
        )
    refresh_business_metrics(merged)
    return merged


def refresh_business_metrics(state):
    active_clients = [client for client in state.get("clients", []) if client.get("status") == "active"]
    state["mrr"] = sum(float(client.get("monthly_value", 0)) for client in active_clients)
    state["monthly_expenses"] = BASE_FIXED_MONTHLY_EXPENSES + monthly_tool_cost(state) + monthly_payroll(state)
    state["level"] = compute_level(state.get("xp", 0))
    state["stage"] = compute_stage(state)
    return state


def compute_level(xp):
    return max(1, min(30, int(xp // 250) + 1))


def compute_stage(state):
    selected = BUSINESS_STAGES[0]["name"]
    active_clients = len([client for client in state.get("clients", []) if client.get("status") == "active"])
    for stage in BUSINESS_STAGES:
        if (
            state.get("mrr", 0) >= stage["min_mrr"]
            and active_clients >= stage["min_clients"]
            and state.get("reputation", 0) >= stage["min_reputation"]
        ):
            selected = stage["name"]
    return selected


def add_skill_xp(state, skill, amount):
    if skill not in SKILLS:
        return []
    messages = []
    state.setdefault("skill_xp", {}).setdefault(skill, 0.0)
    state.setdefault("skills", {}).setdefault(skill, 1)
    state["skill_xp"][skill] += amount
    while state["skills"][skill] < MAX_SKILL_LEVEL:
        needed = 70 + state["skills"][skill] * 35
        if state["skill_xp"][skill] < needed:
            break
        state["skill_xp"][skill] -= needed
        state["skills"][skill] += 1
        messages.append(f"{skill} improved to level {state['skills'][skill]}.")
    return messages


def weekly_expense_run_rate(state):
    return refresh_business_metrics(state)["monthly_expenses"] / WEEKS_PER_MONTH
