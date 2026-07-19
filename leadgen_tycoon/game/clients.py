"""Client creation and portfolio simulation."""

from copy import deepcopy

from .data import CLIENT_NAME_PARTS, CLIENT_NICHES


def create_client(source, current_week, rng, value_multiplier=1.0):
    name = f"{rng.choice(CLIENT_NAME_PARTS)} {rng.choice(['Labs', 'Group', 'Partners', 'Systems', 'Works', 'Growth'])}"
    niche = rng.choice(CLIENT_NICHES)
    source_multiplier = {
        "referrals": 1.18,
        "content_marketing": 1.10,
        "linkedin_ads": 1.08,
        "landing_pages": 1.06,
        "linkedin_outreach": 1.02,
        "cold_email": 0.96,
        "apify_workflows": 0.94,
    }.get(source, 1.0)
    monthly_value = round(rng.randint(1200, 3200) * source_multiplier * value_multiplier / 50) * 50
    delivery_workload = round(monthly_value / 520, 1)
    satisfaction = rng.randint(68, 82)
    return {
        "id": f"client-{current_week}-{rng.randint(10000, 99999)}",
        "name": name,
        "niche": niche,
        "source": source,
        "monthly_value": monthly_value,
        "setup_fee": round(monthly_value * rng.uniform(0.30, 0.75) / 50) * 50,
        "satisfaction": satisfaction,
        "delivery_workload": delivery_workload,
        "churn_risk": max(5, 28 - satisfaction * 0.18),
        "referral_potential": rng.randint(20, 75),
        "age_weeks": 0,
        "status": "active",
    }


def active_clients(state):
    return [client for client in state.get("clients", []) if client.get("status") == "active"]


def portfolio_mrr(state):
    return sum(float(client.get("monthly_value", 0)) for client in active_clients(state))


def portfolio_workload(state):
    return sum(float(client.get("delivery_workload", 0)) for client in active_clients(state))


def service_clients(state, rng, delivery_capacity, operations_quality, churn_reduction):
    feedback = []
    churned = []
    referral_calls = 0
    clients = active_clients(state)
    workload = portfolio_workload(state)
    pressure = workload / max(1.0, delivery_capacity)
    energy = state.get("founder_energy", 70)

    for client in clients:
        client["age_weeks"] = client.get("age_weeks", 0) + 1
        satisfaction_delta = 0
        if pressure > 1:
            satisfaction_delta -= min(12, (pressure - 1) * 10)
        else:
            satisfaction_delta += min(3, (1 - pressure) * 2.5)
        satisfaction_delta += operations_quality * 5
        if energy < 35:
            satisfaction_delta -= 3
        if client.get("age_weeks", 0) <= 2:
            satisfaction_delta -= 1.5
        client["satisfaction"] = round(max(0, min(100, client.get("satisfaction", 75) + satisfaction_delta)), 1)

        non_performance_risk = 0.25 if client["satisfaction"] >= 90 else 0.6 if client["satisfaction"] >= 80 else 1.2
        service_risk = max(0, 76 - client["satisfaction"]) * 0.62
        capacity_risk = max(0, pressure - 1) * 12
        energy_risk = 1.5 if energy < 35 else 0
        churn_risk = non_performance_risk + service_risk + capacity_risk + energy_risk
        churn_risk *= max(0.55, 1 - churn_reduction)
        client["churn_risk"] = round(max(0.2, min(85, churn_risk)), 1)

        weekly_churn_probability = client["churn_risk"] / 100 / 4.33
        if client.get("age_weeks", 0) > 2 and rng.random() < weekly_churn_probability:
            client["status"] = "churned"
            churned.append(deepcopy(client))

        referral_probability = (client.get("referral_potential", 30) / 100) * (client["satisfaction"] / 100) / 9
        referral_probability *= 1 + state.get("reputation", 50) / 180
        if client.get("status") == "active" and rng.random() < referral_probability:
            referral_calls += 1

    if pressure > 1.15 and clients:
        feedback.append(
            f"Delivery workload is {pressure:.1f}x capacity. Satisfaction fell because the business sold more than it can comfortably fulfill."
        )
    elif clients:
        feedback.append("Client delivery stayed within capacity, which protected satisfaction and churn risk.")

    if churned:
        lost_mrr = sum(client["monthly_value"] for client in churned)
        high_satisfaction_churn = [client for client in churned if client.get("satisfaction", 0) >= 85]
        if high_satisfaction_churn:
            feedback.append(
                f"{len(high_satisfaction_churn)} high-satisfaction client(s) still churned for budget or priority reasons. This is rare, but client risk is never zero."
            )
        feedback.append(f"{len(churned)} client(s) churned, removing ${lost_mrr:,.0f} MRR. Capacity and satisfaction are the early warning metrics.")
    if referral_calls:
        feedback.append(f"Happy clients created {referral_calls} referral call(s). Referrals compound when satisfaction and reputation stay high.")

    return {
        "feedback": feedback,
        "churned": churned,
        "referral_calls": referral_calls,
        "pressure": pressure,
    }
