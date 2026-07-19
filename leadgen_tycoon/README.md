# LeadGen Tycoon

LeadGen Tycoon is a local-first weekly business simulator for practicing B2B lead generation, cash flow, hiring, delivery capacity, and agency growth decisions.

The MVP runs entirely on your computer with Python, Streamlit, and SQLite. It does not use paid APIs or external services.

## Run Locally

From the `leadgen_tycoon` folder:

```bash
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0
```

Streamlit will show a local URL such as `http://localhost:8501`.

## Open From Your Phone

1. Make sure your computer and phone are on the same WiFi network.
2. Start the app with:

```bash
streamlit run app.py --server.address 0.0.0.0
```

3. Find your computer's local IP address.
   - On Windows, run `ipconfig` and look for the IPv4 address on your WiFi adapter.
   - It usually looks like `192.168.x.x` or `10.0.x.x`.
4. On your phone, open:

```text
http://YOUR-COMPUTER-IP:8501
```

Example:

```text
http://192.168.1.25:8501
```

If the page does not load, allow Python or Streamlit through your computer firewall and confirm both devices are on the same WiFi network.

## Gameplay Loop

Each simulated week:

1. Review the dashboard.
2. Choose campaign channels and intensity.
3. Buy or cancel tools.
4. Hire carefully when capacity becomes a bottleneck.
5. Train skills.
6. Run the week.
7. Review results, random events, educational feedback, and updated reports.

The simulator tracks:

- Cash, MRR, expenses, weekly profit/loss
- Leads, qualified leads, booked calls, close rate, clients
- Client satisfaction, delivery workload, churn risk, referrals
- Founder energy, team size, tool stack, delivery capacity
- Channel performance and unit economics
- Skills, levels, business stages, achievements

## Local Persistence

Progress autosaves to SQLite after every turn and major action.

Save file:

```text
leadgen_tycoon/saves/leadgen_tycoon.sqlite
```

If SQLite cannot open because of local file permissions, the app falls back to:

```text
leadgen_tycoon/saves/leadgen_tycoon_fallback.json
```

Use **Settings / Save Game** inside the app to manually save, continue, or reset.

## Project Structure

```text
leadgen_tycoon/
  app.py
  requirements.txt
  README.md
  game/
    state.py
    simulation.py
    channels.py
    tools.py
    hiring.py
    clients.py
    events.py
    achievements.py
    persistence.py
    data.py
```

## Extending The Game

- Add or rebalance channels in `game/channels.py`
- Add marketplace items in `game/tools.py`
- Tune roles and seniority in `game/hiring.py`
- Add events in `game/events.py`
- Add achievements in `game/achievements.py`
- Tune weekly outcomes in `game/simulation.py`
