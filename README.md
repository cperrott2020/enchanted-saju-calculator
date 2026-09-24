# Enchanted Saju Calculator

An embeddable deterministic Korean Saju Palja / Four Pillars calculator for the **My Saju Journal** Notion workspace.

## Status

**v0.1 — deterministic engine, ForceTeller compatibility validation pending.**

The calculator deliberately separates:

1. birth-data normalisation;
2. astronomical/calendar calculation;
3. deterministic Saju derivation;
4. interpretation.

AI interpretation must never rewrite calculated chart data.

## Included

- Gregorian birth-date input
- exact / approximate / unknown birth time
- birthplace coordinates + IANA timezone
- historical timezone and DST resolution
- optional local/true-solar-time correction
- exact Ipchun year boundary
- solar-term month boundaries
- sexagenary Day Pillar from a fixed Julian-day anchor
- configurable midnight vs 23:00 Zi-hour day boundary
- Hour Pillar derived from Day Stem + Hour Branch
- Day Master
- Ten Gods
- fixed Hidden Stem existence table
- Five Element presence counts
- stem/branch relationship detection
- Twelve Growth Stages
- Void / Emptiness
- configurable Daewoon direction and start age
- boundary warnings
- civil-vs-solar comparison
- Notion save endpoint
- responsive pink/sage/cream/brown embed UI
- Docker + Render deployment files
- regression tests

## Accuracy philosophy

The engine does **not** fabricate:

- universal element-strength percentages;
- a universal Useful/Favourable/Unfavourable Element result;
- undocumented Symbolic Star rules;
- automatic transformation of every theoretical combination.

Those modules should only be enabled after a named methodology is selected and validated.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Test

```bash
pytest -q
```

## Deploy

This repository includes a Dockerfile and `render.yaml`.

Typical route:

1. connect this repository to Render;
2. deploy the Docker service;
3. copy its HTTPS URL;
4. in Notion, open **Chart Calculator**;
5. add `/embed`;
6. paste the deployed URL.

## Optional Notion save integration

Copy `.env.example` to `.env` and configure the server-side variables.

Never place a Notion token in frontend JavaScript.

## Validation before calling it ForceTeller-compatible

Add regression fixtures from trusted ForceTeller charts and compare:

- Year / Month / Day / Hour pillars
- Day Master
- Ten Gods
- Hidden Stems
- Daewoon direction
- Daewoon start

If results differ, diagnose the exact convention: timezone, solar correction, solar-term boundary, day boundary, or luck-cycle rule.