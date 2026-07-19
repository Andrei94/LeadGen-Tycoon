"""Weekly turn simulation."""

from copy import deepcopy
import math
import random

from .achievements import check_achievements
from .channels import CHANNELS
from .clients import create_client, service_clients
from .data import WEEKS_PER_MONTH
from .events import trigger_random_events
from .hiring import advance_training, team_effects
from .state import add_skill_xp, normalize_state, refresh_business_metrics
from .tools import tool_effect_value


def clamp(value, low, high):
    return max(low, min(high, value))


def random_count(rng, attempts, probability):
    attempts = int(max(0, attempts))
    probability = clamp(probability, 0, 1)
    return sum(1 for _ in range(attempts) if rng.random() < probability)


def skill_multiplier(state, weights):
    score = 0
    total = sum(weights.values()) or 1
    for skill, weight in weights.items():
        level = state.get("skills", {}).get(skill, 1)
        score += ((level - 1) / 9) * (weight / total)
    return 0.78 + score * 0.58


def active_modifier_multiplier(state, channel_id, key, default=1.0):
    multiplier = default
    for modifier in state.get("active_modifiers", []):
        if modifier.get("channel_id") not in (channel_id, "all"):
            continue
        modifier_key = f"{key}_multiplier"
        if modifier_key in modifier:
            multiplier *= modifier[modifier_key]
    return multiplier


def channel_tool_team_bonus(state, team, channel_id, suffix):
    return tool_effect_value(state, f"{channel_id}_{suffix}") + team.get(f"{channel_id}_{suffix}", 0)


def estimate_campaign_cost(channel_id, intensity, budget):
    channel = CHANNELS[channel_id]
    return channel["base_cost"] * intensity + max(0, budget)


def run_channel(state, rng, channel_id, plan, team):
    channel = CHANNELS[channel_id]
    intensity = int(plan.get("intensity", 1))
    budget = float(plan.get("budget", 0))
    spend = estimate_campaign_cost(channel_id, intensity, budget)
    time_reduction = (
        tool_effect_value(state, "copy_time_reduction")
        + tool_effect_value(state, f"{channel_id}_time_reduction")
        + team.get(f"{channel_id}_time_reduction", 0)
    )
    time_cost = max(1.0, channel["time_cost"] * intensity * (1 - clamp(time_reduction, 0, 0.45)))

    base = channel["base_leads"] * intensity
    recommended = max(1, channel["recommended_budget"])
    budget_factor = 1 + min(0.85, math.log1p(max(0, budget) / recommended) * 0.55)
    skill_factor = skill_multiplier(state, channel["skills"])
    reputation_factor = 0.82 + state.get("reputation", 45) / 180
    energy_factor = 0.82 + state.get("founder_energy", 75) / 240
    lead_bonus = 1 + channel_tool_team_bonus(state, team, channel_id, "leads_multiplier")
    if channel_id == "content_marketing":
        previous_runs = state.get("channel_performance", {}).get(channel_id, {}).get("runs", 0)
        lead_bonus += min(0.45, previous_runs * 0.025)

    lead_multiplier = active_modifier_multiplier(state, channel_id, "lead")
    noise = rng.uniform(0.72, 1.28)
    leads = round(base * budget_factor * skill_factor * reputation_factor * energy_factor * lead_bonus * lead_multiplier * noise)
    leads = max(0, leads)

    quality_bonus = (
        tool_effect_value(state, "qualified_rate")
        + tool_effect_value(state, "targeting_quality")
        + tool_effect_value(state, f"{channel_id}_quality")
        + team.get("qualified_rate", 0)
        + team.get("targeting_quality", 0)
        + team.get(f"{channel_id}_quality", 0)
    )
    if channel_id == "cold_email":
        quality_bonus += tool_effect_value(state, "cold_email_quality")
    qualified_rate = channel["qualified_rate"] + quality_bonus
    qualified_rate += (state["skills"].get("Targeting", 1) - 1) * 0.012
    qualified_rate *= active_modifier_multiplier(state, channel_id, "qualified")
    qualified = random_count(rng, leads, clamp(qualified_rate, 0.05, 0.82))

    booking_bonus = (
        tool_effect_value(state, "booking_rate")
        + team.get("booking_rate", 0)
        + (state["skills"].get("Offer Creation", 1) - 1) * 0.008
        + (state["skills"].get("Sales", 1) - 1) * 0.006
    )
    if channel_id in ("linkedin_ads", "landing_pages", "content_marketing"):
        booking_bonus += tool_effect_value(state, "landing_conversion")
    booking_rate = (channel["booking_rate"] + booking_bonus) * active_modifier_multiplier(state, channel_id, "booking")
    booked = random_count(rng, qualified, clamp(booking_rate, 0.03, 0.62))

    protection = tool_effect_value(state, "reputation_protection")
    generic_copy_risk = tool_effect_value(state, "generic_copy_risk")
    risk = max(0, channel["risk"] + team.get("mistake_risk", 0) * 0.20 + generic_copy_risk - protection * 0.10)
    reputation_delta = 0
    if intensity >= 3 and rng.random() < risk:
        reputation_delta -= rng.choice([1, 2, 3])
    if qualified >= max(3, leads * 0.45) and leads:
        reputation_delta += 1
    state["reputation"] = clamp(state.get("reputation", 50) + reputation_delta, 0, 100)

    for skill in channel.get("learning", []):
        add_skill_xp(state, skill, 5 * intensity + booked * 2)

    pipeline = state.setdefault("pipeline", {})
    pipeline["leads"] = pipeline.get("leads", 0) + leads
    pipeline["qualified_leads"] = pipeline.get("qualified_leads", 0) + qualified
    pipeline["booked_calls"] = pipeline.get("booked_calls", 0) + booked
    by_channel = pipeline.setdefault("booked_calls_by_channel", {})
    by_channel[channel_id] = by_channel.get(channel_id, 0) + booked

    performance = state.setdefault("channel_performance", {}).setdefault(
        channel_id, {"leads": 0, "qualified": 0, "booked": 0, "clients": 0, "spend": 0.0, "revenue": 0.0, "runs": 0}
    )
    performance["leads"] += leads
    performance["qualified"] += qualified
    performance["booked"] += booked
    performance["spend"] += spend
    performance["runs"] += 1

    return {
        "channel_id": channel_id,
        "name": channel["name"],
        "leads": leads,
        "qualified": qualified,
        "booked": booked,
        "spend": spend,
        "time": time_cost,
        "reputation_delta": reputation_delta,
        "qualified_rate": qualified / leads if leads else 0,
        "booking_rate": booked / qualified if qualified else 0,
    }


def process_sales_calls(state, rng, sales_focus_intensity, team):
    pipeline = state.setdefault("pipeline", {})
    available = int(pipeline.get("booked_calls", 0))
    base_capacity = 3 + state["skills"].get("Sales", 1) * 1.4
    capacity = round(base_capacity + team.get("call_capacity", 0) + sales_focus_intensity * 4)
    processed = min(available, max(0, capacity))
    if processed <= 0:
        return {"processed": 0, "clients": [], "setup_revenue": 0, "lost": 0, "close_rate": 0}

    close_bonus = (
        tool_effect_value(state, "close_rate")
        + team.get("close_rate", 0)
        + (state["skills"].get("Sales", 1) - 1) * 0.018
        + (state["skills"].get("Offer Creation", 1) - 1) * 0.012
        + state.pop("temporary_close_bonus", 0)
    )
    close_rate = clamp(0.13 + close_bonus + state.get("reputation", 50) / 650, 0.05, 0.62)

    by_channel = pipeline.setdefault("booked_calls_by_channel", {})
    clients = []
    setup_revenue = 0
    processed_remaining = processed
    for channel_id, calls in list(by_channel.items()):
        if processed_remaining <= 0:
            break
        source_calls = min(calls, processed_remaining)
        closed = random_count(rng, source_calls, close_rate)
        value_multiplier = CHANNELS.get(channel_id, {}).get("lead_value", 1.0)
        for _ in range(closed):
            client = create_client(channel_id, state.get("week", 1), rng, value_multiplier=value_multiplier)
            clients.append(client)
            setup_revenue += client["setup_fee"]
            perf = state["channel_performance"].setdefault(
                channel_id, {"leads": 0, "qualified": 0, "booked": 0, "clients": 0, "spend": 0.0, "revenue": 0.0, "runs": 0}
            )
            perf["clients"] += 1
            perf["revenue"] += client["setup_fee"]
        by_channel[channel_id] = max(0, calls - source_calls)
        processed_remaining -= source_calls

    lost_reduction = clamp(tool_effect_value(state, "lost_leads_reduction") + team.get("lost_leads_reduction", 0), 0, 0.65)
    unprocessed = max(0, available - processed)
    lost = random_count(rng, unprocessed, 0.18 * (1 - lost_reduction))
    pipeline["booked_calls"] = max(0, available - processed - lost)
    if lost:
        for channel_id in list(by_channel.keys()):
            if lost <= 0:
                break
            removed = min(by_channel[channel_id], lost)
            by_channel[channel_id] -= removed
            lost -= removed
    state.setdefault("clients", []).extend(clients)
    state["metrics"]["lifetime_clients_closed"] += len(clients)
    state["one_time_revenue"] = state.get("one_time_revenue", 0) + setup_revenue
    add_skill_xp(state, "Sales", processed * 4 + len(clients) * 10)
    add_skill_xp(state, "Offer Creation", len(clients) * 5)

    return {
        "processed": processed,
        "clients": clients,
        "setup_revenue": setup_revenue,
        "lost": max(0, unprocessed - pipeline["booked_calls"]),
        "close_rate": close_rate,
    }


def compute_delivery_capacity(state, team):
    base = 8 + state["skills"].get("Client Delivery", 1) * 2.4 + state["skills"].get("Operations", 1) * 1.4
    return base + team.get("delivery_capacity", 0) + tool_effect_value(state, "delivery_capacity")


def simulate_week(current_state, actions):
    state = normalize_state(deepcopy(current_state))
    week = state["week"]
    rng = random.Random(state.get("seed", 137) + week * 7919 + len(state.get("history", [])) * 97)
    feedback = []
    campaign_results = []
    campaigns_run = {}
    campaign_spend = 0.0
    time_used = 0.0
    sales_focus = 0

    team = team_effects(state)
    ramping_hires = advance_training(state)
    if ramping_hires:
        time_used += ramping_hires * 1.5
        feedback.append(f"{ramping_hires} team member(s) needed onboarding attention this week, reducing founder leverage.")
    if team.get("management_bloat", 0) >= 0.35:
        feedback.append(
            "Management-heavy hiring is underutilized. Account and operations managers create leverage only when there are enough clients and operators for them to manage."
        )
    if team.get("coordination_overhead", 0) >= 0.08:
        feedback.append(
            f"Team coordination overhead absorbed about {team['coordination_overhead']:.0%} of capacity. More people now require stronger process, not just more payroll."
        )

    starting_modifiers = deepcopy(state.get("active_modifiers", []))
    state["active_modifiers"] = starting_modifiers

    for channel_id, plan in actions.get("campaigns", {}).items():
        if not plan.get("enabled") or int(plan.get("intensity", 0)) <= 0:
            continue
        if channel_id not in CHANNELS:
            continue
        intensity = int(plan.get("intensity", 1))
        campaigns_run[channel_id] = intensity
        if channel_id == "sales_calls":
            sales_focus = intensity
            time_used += CHANNELS[channel_id]["time_cost"] * intensity * (1 - clamp(tool_effect_value(state, "sales_time_reduction"), 0, 0.35))
            continue
        result = run_channel(state, rng, channel_id, plan, team)
        campaign_results.append(result)
        campaign_spend += result["spend"]
        time_used += result["time"]

    training_cost = 0.0
    for skill, hours in actions.get("training", {}).items():
        hours = float(hours)
        if hours <= 0:
            continue
        time_used += hours
        training_cost += hours * 65
        feedback.extend(add_skill_xp(state, skill, hours * 22))

    sales_result = process_sales_calls(state, rng, sales_focus, team)
    if sales_result["processed"]:
        feedback.append(
            f"Sales processed {sales_result['processed']} booked call(s) at an estimated {sales_result['close_rate']:.0%} close rate."
        )
    if sales_result["clients"]:
        feedback.append(
            f"Closed {len(sales_result['clients'])} client(s) and collected ${sales_result['setup_revenue']:,.0f} in setup revenue."
        )
    if sales_result.get("lost"):
        feedback.append("Some booked calls went stale. CRM, scheduling, and sales capacity reduce pipeline leakage.")

    refresh_business_metrics(state)
    delivery_capacity = compute_delivery_capacity(state, team)
    operations_quality = (
        (state["skills"].get("Operations", 1) - 1) * 0.025
        + tool_effect_value(state, "operations_quality")
        + team.get("operations_quality", 0)
    )
    operations_quality = clamp(operations_quality, -0.15, 0.45)
    churn_reduction = clamp(tool_effect_value(state, "churn_reduction") + team.get("churn_reduction", 0), 0, 0.55)
    service_result = service_clients(state, rng, delivery_capacity, operations_quality, churn_reduction)
    feedback.extend(service_result["feedback"])
    state["metrics"]["lifetime_churned_clients"] += len(service_result["churned"])
    if service_result["referral_calls"]:
        state["pipeline"]["booked_calls"] += service_result["referral_calls"]
        state["pipeline"]["booked_calls_by_channel"]["referrals"] = (
            state["pipeline"]["booked_calls_by_channel"].get("referrals", 0) + service_result["referral_calls"]
        )
        state["metrics"]["lifetime_referrals"] += service_result["referral_calls"]
        state["metrics"]["lifetime_booked_calls"] += service_result["referral_calls"]
        state["channel_performance"].setdefault(
            "referrals", {"leads": 0, "qualified": 0, "booked": 0, "clients": 0, "spend": 0.0, "revenue": 0.0, "runs": 0}
        )["booked"] += service_result["referral_calls"]

    context = {
        "campaigns_run": campaigns_run,
        "processed_calls": sales_result["processed"],
    }
    events = trigger_random_events(state, rng, context)
    state["last_events"] = events
    for event in events:
        feedback.append(f"{event['name']}: {event['impact']} Lesson: {event['lesson']}")

    remaining_modifiers = []
    for modifier in starting_modifiers:
        modifier["weeks_remaining"] = modifier.get("weeks_remaining", 1) - 1
        if modifier["weeks_remaining"] > 0:
            remaining_modifiers.append(modifier)
    new_modifiers = [modifier for modifier in state.get("active_modifiers", []) if modifier not in starting_modifiers]
    state["active_modifiers"] = remaining_modifiers + new_modifiers

    refresh_business_metrics(state)
    recurring_revenue = state["mrr"] / WEEKS_PER_MONTH
    one_time_revenue = sales_result["setup_revenue"]
    weekly_expenses = state["monthly_expenses"] / WEEKS_PER_MONTH
    total_costs = weekly_expenses + campaign_spend + training_cost
    total_revenue = recurring_revenue + one_time_revenue
    profit = total_revenue - total_costs
    state["cash"] += profit
    state["weekly_profit"] = profit

    total_leads = sum(result["leads"] for result in campaign_results)
    total_qualified = sum(result["qualified"] for result in campaign_results)
    total_booked = sum(result["booked"] for result in campaign_results)
    state["metrics"]["lifetime_leads"] += total_leads
    state["metrics"]["lifetime_qualified_leads"] += total_qualified
    state["metrics"]["lifetime_booked_calls"] += total_booked
    state["metrics"]["total_revenue"] += total_revenue
    state["metrics"]["total_expenses"] += weekly_expenses + training_cost
    state["metrics"]["total_campaign_spend"] += campaign_spend

    if campaign_results:
        best = max(campaign_results, key=lambda item: (item["booked"], item["qualified"], item["leads"]))
        feedback.append(
            f"{best['name']} was the strongest acquisition action this week. Track booked calls and clients, not only lead volume."
        )
    else:
        feedback.append("No lead generation campaigns ran. Cash burn may be lower, but pipeline growth will stall.")

    if campaign_spend > 0 and total_booked:
        feedback.append(f"Cost per booked call was about ${campaign_spend / total_booked:,.0f}. Use this to compare channels.")
    if state["cash"] < 0:
        feedback.append("Cash is negative. The business is alive in the simulator, but payroll and subscriptions are now a major survival risk.")

    founder_capacity = state.get("founder_time_capacity", 45) + min(14, team.get("time_relief", 0))
    overload = max(0, time_used - founder_capacity)
    if overload:
        state["founder_energy"] = clamp(state.get("founder_energy", 75) - 8 - overload * 0.65, 0, 100)
        feedback.append(f"Founder time was over capacity by {overload:.1f} hours. Energy fell, which will reduce future execution quality.")
    elif time_used < founder_capacity * 0.65:
        state["founder_energy"] = clamp(state.get("founder_energy", 75) + 5, 0, 100)
    else:
        state["founder_energy"] = clamp(state.get("founder_energy", 75) - 2, 0, 100)

    xp_gain = 20 + len(sales_result["clients"]) * 25 + total_booked * 2 + max(0, profit) / 500
    state["xp"] += xp_gain
    refresh_business_metrics(state)
    unlocked = check_achievements(state)
    state["last_achievements"] = [
        {
            "id": achievement["id"],
            "name": achievement["name"],
            "description": achievement["description"],
            "xp": achievement.get("xp", 0),
        }
        for achievement in unlocked
    ]
    for achievement in unlocked:
        feedback.append(f"Achievement unlocked: {achievement['name']} - {achievement['description']}")
    refresh_business_metrics(state)

    history_row = {
        "week": week,
        "cash": round(state["cash"], 2),
        "mrr": round(state["mrr"], 2),
        "revenue": round(total_revenue, 2),
        "expenses": round(total_costs, 2),
        "profit": round(profit, 2),
        "leads": total_leads,
        "qualified_leads": total_qualified,
        "booked_calls": total_booked,
        "clients_closed": len(sales_result["clients"]),
        "active_clients": len([client for client in state.get("clients", []) if client.get("status") == "active"]),
        "reputation": round(state["reputation"], 1),
        "founder_energy": round(state["founder_energy"], 1),
    }
    state.setdefault("history", []).append(history_row)
    state["last_results"] = {
        "week": week,
        "campaign_results": campaign_results,
        "sales": sales_result,
        "service": service_result,
        "revenue": total_revenue,
        "expenses": total_costs,
        "profit": profit,
        "time_used": time_used,
        "founder_capacity": founder_capacity,
    }
    state["last_feedback"] = feedback[:14]
    state["week"] = week + 1
    return normalize_state(state)
