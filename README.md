# szakdolgozat-tower-defense-ppo
# Mesterséges intelligencia alapú ágens fejlesztése játékokhoz

A szakdolgozathoz készült forráskód: egy pygame-ben írt tower defense játék,
egy egyedi Gymnasium-környezet és egy Stable-Baselines3 PPO ügynök.

Szakdolgozat: Debreceni Egyetem, Informatikai Kar, 2026.
Szerző: Signorelli Marco Giacomo. Témavezető: Dr. Harangi Balázs.

## Telepítés
    pip install -r requirements.txt

## Fájlok
- main.py – a játék emberi játékosnak
- env.py – a Gymnasium tanító környezet
- train.py – a PPO ügynök tanítása
- evaluate.py – kiértékelés (véletlenszerű, heurisztikus és PPO ügynök)
- watch_agent.py – a betanított ügynök élő lejátszása
- heuristic_agent.py, random_agent.py – viszonyítási ügynökök

## Licenc és forrás
A játék alapszerkezete a „Coding With Russ" oktatóanyagra épül.
