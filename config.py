
ANNEES = range(2013, 2023)

DB_FILE = 'db/survival_football.db'

LOG_FILE_TEAMS = 'logs/teams.log'
LOG_FILE_MATCHES = 'logs/matches.log'

HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

PHASES_TOURNOI = {
    **{key: f"Phase de poules" for key in "ABCDEFGH"},
    'AFH': "Huitièmes de finale Aller",
    'AFR': "Huitièmes de finale Retour",
    'VFH': "Quart de finale Aller",
    'VFR': "Quart de finale Retour",
    'HFH': "Demi finale Aller",
    'HFR': "Demi finale Retour",
    'FF': "Final"
}
