from matches import fetch_page_content
import sqlite3
import logging
from tqdm import tqdm
from config import ANNEES, DB_FILE, LOG_FILE_TEAMS

logger = logging.getLogger("teams_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE_TEAMS)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s:%(levelname)s:%(message)s"))

logger.addHandler(file_handler)


def parse_teams_data(soup, teams_list):
    """Extrait les équipes à partir de l'objet BeautifulSoup."""
    teams = soup.find_all('td', class_="links no-border-links hauptlink")

    for team in teams:
        team_name = team.find('a')['title']
        if team_name not in teams_list:
            teams_list.append(team_name)
            logger.info(f"Nouvelle équipe ajoutée : Nom={team_name}")
    return teams_list


def save_teams_to_db(conn, teams):
    """Enregistre les données des équipes dans la base de données SQLite."""
    cursor = conn.cursor()
    for team in teams:
        cursor.execute("""
            INSERT OR REPLACE INTO teams (team)
            VALUES (?)
        """, (team,))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT UNIQUE
        )
    """)
    conn.commit()
    teams_list = []
    for annee in tqdm(ANNEES, desc="Traitement des requêtes"):
        url = f'https://www.transfermarkt.fr/uefa-champions-league/teilnehmer/pokalwettbewerb/CL/saison_id/{
            annee}'
        soup = fetch_page_content(url)
        if soup:
            teams_list = parse_teams_data(soup, teams_list)
            logger.info(f"Ajout des équipes terminée pour l'année {annee}")
        else:
            logger.error(
                f"Erreur lors du chargement de la page pour l'année {annee}")

    save_teams_to_db(conn, teams_list)


if __name__ == "__main__":
    main()
