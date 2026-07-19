"""Random events for weekly simulation."""


RANDOM_EVENTS = [
    {
        "id": "client_referral",
        "name": "Client referral",
        "probability": 0.08,
        "condition": lambda state, context: len(state.get("clients", [])) > 0 and state.get("reputation", 0) >= 45,
    },
    {
        "id": "email_deliverability_issue",
        "name": "Email deliverability issue",
        "probability": 0.07,
        "condition": lambda state, context: context.get("campaigns_run", {}).get("cold_email", 0) >= 2,
    },
    {
        "id": "linkedin_restriction",
        "name": "LinkedIn account restriction",
        "probability": 0.06,
        "condition": lambda state, context: context.get("campaigns_run", {}).get("linkedin_outreach", 0) >= 2,
    },
    {
        "id": "ad_underperforms",
        "name": "Ad campaign underperforms",
        "probability": 0.07,
        "condition": lambda state, context: context.get("campaigns_run", {}).get("linkedin_ads", 0) > 0,
    },
    {
        "id": "viral_content",
        "name": "Viral content post",
        "probability": 0.05,
        "condition": lambda state, context: context.get("campaigns_run", {}).get("content_marketing", 0) > 0,
    },
    {
        "id": "great_sales_call",
        "name": "Great sales call",
        "probability": 0.06,
        "condition": lambda state, context: context.get("processed_calls", 0) > 0,
    },
    {
        "id": "bad_hire",
        "name": "Bad hire mistake",
        "probability": 0.05,
        "condition": lambda state, context: any(member.get("training_weeks_remaining", 0) > 0 for member in state.get("team", [])),
    },
    {
        "id": "tool_price_increase",
        "name": "Tool price increase",
        "probability": 0.04,
        "condition": lambda state, context: len(state.get("tools", [])) > 0,
    },
    {
        "id": "market_downturn",
        "name": "Market downturn",
        "probability": 0.035,
        "condition": lambda state, context: True,
    },
    {
        "id": "competitor_copies_offer",
        "name": "Competitor copies your offer",
        "probability": 0.045,
        "condition": lambda state, context: state.get("mrr", 0) >= 5000,
    },
    {
        "id": "accounting_expense",
        "name": "Unexpected accounting expense",
        "probability": 0.04,
        "condition": lambda state, context: state.get("week", 1) > 3,
    },
    {
        "id": "high_quality_inbound",
        "name": "High-quality inbound lead",
        "probability": 0.055,
        "condition": lambda state, context: state.get("reputation", 0) >= 40,
    },
    {
        "id": "apify_niche_discovery",
        "name": "Apify workflow discovers a valuable niche",
        "probability": 0.06,
        "condition": lambda state, context: context.get("campaigns_run", {}).get("apify_workflows", 0) > 0,
    },
]


def trigger_random_events(state, rng, context):
    triggered = []
    for event in RANDOM_EVENTS:
        if len(triggered) >= 2:
            break
        if not event["condition"](state, context):
            continue
        if rng.random() > event["probability"]:
            continue
        triggered.append(apply_event(state, rng, event["id"]))
    return [event for event in triggered if event]


def _add_booked_calls(state, channel_id, amount):
    pipeline = state.setdefault("pipeline", {})
    pipeline["booked_calls"] = pipeline.get("booked_calls", 0) + amount
    by_channel = pipeline.setdefault("booked_calls_by_channel", {})
    by_channel[channel_id] = by_channel.get(channel_id, 0) + amount
    state.setdefault("metrics", {}).setdefault("lifetime_booked_calls", 0)
    state["metrics"]["lifetime_booked_calls"] += amount
    performance = state.setdefault("channel_performance", {}).setdefault(
        channel_id, {"leads": 0, "qualified": 0, "booked": 0, "clients": 0, "spend": 0.0, "revenue": 0.0, "runs": 0}
    )
    performance["booked"] += amount


def apply_event(state, rng, event_id):
    if event_id == "client_referral":
        _add_booked_calls(state, "referrals", 1)
        state["reputation"] = min(100, state.get("reputation", 50) + 2)
        return {
            "name": "Client referral",
            "impact": "A satisfied client introduced a warm prospect. One referral call was added to the pipeline.",
            "lesson": "Referrals are a lagging indicator of delivery quality and trust, not a channel you can force instantly.",
        }
    if event_id == "email_deliverability_issue":
        state["reputation"] = max(0, state.get("reputation", 50) - 3)
        state.setdefault("active_modifiers", []).append(
            {"id": "email_deliverability_issue", "channel_id": "cold_email", "lead_multiplier": 0.75, "weeks_remaining": 1}
        )
        return {
            "name": "Email deliverability issue",
            "impact": "Cold email performance will be lower next week and reputation fell slightly.",
            "lesson": "Volume without verification, relevance, and reply handling can damage the asset you rely on.",
        }
    if event_id == "linkedin_restriction":
        state.setdefault("active_modifiers", []).append(
            {"id": "linkedin_restriction", "channel_id": "linkedin_outreach", "lead_multiplier": 0.55, "weeks_remaining": 1}
        )
        return {
            "name": "LinkedIn account restriction",
            "impact": "LinkedIn outreach capacity is reduced next week.",
            "lesson": "Personal channels scale through quality, process, and team capacity before automation volume.",
        }
    if event_id == "ad_underperforms":
        state["cash"] -= 250
        return {
            "name": "Ad campaign underperforms",
            "impact": "$250 of testing budget produced little signal.",
            "lesson": "Paid acquisition needs a testing budget and fast learning loops. Do not confuse spend with strategy.",
        }
    if event_id == "viral_content":
        _add_booked_calls(state, "content_marketing", 2)
        state["reputation"] = min(100, state.get("reputation", 50) + 4)
        return {
            "name": "Viral content post",
            "impact": "Two extra inbound calls entered the pipeline and reputation increased.",
            "lesson": "Content is volatile week to week, but consistent publishing creates more chances for upside.",
        }
    if event_id == "great_sales_call":
        state["reputation"] = min(100, state.get("reputation", 50) + 2)
        state.setdefault("temporary_close_bonus", 0)
        state["temporary_close_bonus"] += 0.03
        return {
            "name": "Great sales call",
            "impact": "Your positioning got sharper. Close rate gets a small temporary lift.",
            "lesson": "Good calls reveal customer language. Feed that back into offers, copy, and targeting.",
        }
    if event_id == "bad_hire":
        state["reputation"] = max(0, state.get("reputation", 50) - 2)
        state["founder_energy"] = max(0, state.get("founder_energy", 75) - 5)
        return {
            "name": "Bad hire mistake",
            "impact": "A ramping team member caused rework. Reputation and founder energy fell.",
            "lesson": "Hiring creates leverage only when onboarding, QA, and role clarity exist.",
        }
    if event_id == "tool_price_increase":
        tool = rng.choice(state.get("tools", []))
        increase = max(5, round(tool["monthly_cost"] * 0.10))
        tool["monthly_cost"] += increase
        return {
            "name": "Tool price increase",
            "impact": f"{tool['name']} increased by ${increase}/month.",
            "lesson": "Subscription sprawl quietly raises break-even revenue. Audit tools against measurable gains.",
        }
    if event_id == "market_downturn":
        state.setdefault("active_modifiers", []).append(
            {"id": "market_downturn", "channel_id": "all", "qualified_multiplier": 0.90, "weeks_remaining": 1}
        )
        return {
            "name": "Market downturn",
            "impact": "Qualification rates are slightly weaker next week.",
            "lesson": "In tougher markets, tighter targeting and stronger proof matter more than generic volume.",
        }
    if event_id == "competitor_copies_offer":
        state["reputation"] = max(0, state.get("reputation", 50) - 1)
        state.setdefault("active_modifiers", []).append(
            {"id": "competitor_copies_offer", "channel_id": "all", "booking_multiplier": 0.92, "weeks_remaining": 1}
        )
        return {
            "name": "Competitor copies your offer",
            "impact": "Prospects compare you more aggressively next week.",
            "lesson": "Offers need proof, positioning, and delivery quality. Copyable claims are not a moat.",
        }
    if event_id == "accounting_expense":
        expense = rng.randint(180, 650)
        state["cash"] -= expense
        return {
            "name": "Unexpected accounting expense",
            "impact": f"Cash fell by ${expense:,.0f}.",
            "lesson": "Cash flow planning needs a buffer for boring but real operating costs.",
        }
    if event_id == "high_quality_inbound":
        _add_booked_calls(state, "content_marketing", 1)
        return {
            "name": "High-quality inbound lead",
            "impact": "One warm inbound call was added to the pipeline.",
            "lesson": "Reputation and visible expertise can create demand that feels easier than cold outbound.",
        }
    if event_id == "apify_niche_discovery":
        state.setdefault("active_modifiers", []).append(
            {"id": "apify_niche_discovery", "channel_id": "apify_workflows", "qualified_multiplier": 1.25, "weeks_remaining": 2}
        )
        return {
            "name": "Apify workflow discovers a valuable niche",
            "impact": "Apify qualification rates improve for two weeks.",
            "lesson": "Automation is strongest when it uncovers sharper market segments, not just bigger lists.",
        }
    return None
