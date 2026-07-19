"""Achievement definitions and unlock logic."""

ACHIEVEMENTS = [
    {"id": "first_client", "name": "First Client", "description": "Close your first paying client.", "xp": 80},
    {"id": "first_10k_mrr", "name": "First $10k MRR", "description": "Reach $10,000 in monthly recurring revenue.", "xp": 150},
    {"id": "profitable_month", "name": "Profitable Month", "description": "Finish four consecutive weeks with positive total profit.", "xp": 120},
    {"id": "referral_engine", "name": "Referral Engine", "description": "Generate at least three referral opportunities.", "xp": 120},
    {"id": "cold_email_machine", "name": "Cold Email Machine", "description": "Generate 250 lifetime cold email leads.", "xp": 100},
    {"id": "linkedin_ads_operator", "name": "LinkedIn Ads Operator", "description": "Close a client sourced from LinkedIn ads.", "xp": 120},
    {"id": "automation_builder", "name": "Automation Builder", "description": "Use Apify or hire automation talent to generate 200 workflow leads.", "xp": 120},
    {"id": "team_builder", "name": "Team Builder", "description": "Build a team of at least three people.", "xp": 100},
    {"id": "cash_buffer", "name": "Cash Buffer", "description": "Hold at least three months of expenses in cash.", "xp": 100},
    {"id": "market_leader", "name": "Market Leader", "description": "Reach the Market leader business stage.", "xp": 250},
]


def _channel_leads(state, channel_id):
    return state.get("channel_performance", {}).get(channel_id, {}).get("leads", 0)


def _has_client_from(state, source):
    return any(client.get("source") == source for client in state.get("clients", []))


def _profitable_month(state):
    history = state.get("history", [])
    if len(history) < 4:
        return False
    return sum(row.get("profit", 0) for row in history[-4:]) > 0


def _cash_buffer(state):
    expenses = max(1, state.get("monthly_expenses", 0))
    return state.get("cash", 0) >= expenses * 3 and expenses > 500


def condition_met(achievement, state):
    achievement_id = achievement["id"]
    if achievement_id == "first_client":
        return state.get("metrics", {}).get("lifetime_clients_closed", 0) >= 1
    if achievement_id == "first_10k_mrr":
        return state.get("mrr", 0) >= 10000
    if achievement_id == "profitable_month":
        return _profitable_month(state)
    if achievement_id == "referral_engine":
        return state.get("metrics", {}).get("lifetime_referrals", 0) >= 3
    if achievement_id == "cold_email_machine":
        return _channel_leads(state, "cold_email") >= 250
    if achievement_id == "linkedin_ads_operator":
        return _has_client_from(state, "linkedin_ads")
    if achievement_id == "automation_builder":
        return _channel_leads(state, "apify_workflows") >= 200 or any(
            member.get("role_id") == "automation_specialist" for member in state.get("team", [])
        )
    if achievement_id == "team_builder":
        return len(state.get("team", [])) >= 3
    if achievement_id == "cash_buffer":
        return _cash_buffer(state)
    if achievement_id == "market_leader":
        return state.get("stage") == "Market leader"
    return False


def check_achievements(state):
    unlocked = set(state.setdefault("achievements", []))
    new_unlocks = []
    for achievement in ACHIEVEMENTS:
        if achievement["id"] in unlocked:
            continue
        if condition_met(achievement, state):
            state["achievements"].append(achievement["id"])
            state["xp"] = state.get("xp", 0) + achievement.get("xp", 0)
            state["reputation"] = min(100, state.get("reputation", 50) + 1)
            new_unlocks.append(achievement)
    return new_unlocks

