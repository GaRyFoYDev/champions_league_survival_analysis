from matches import fetch_page_content
import sqlite3
import logging
from tqdm import tqdm
from config import ANNEES, DB_FILE, LOG_FILE_VALO_AGES

logger = logging.getLogger("infos_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE_VALO_AGES)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s:%(levelname)s:%(message)s"))

logger.addHandler(file_handler)


def parse_teams_info(soup, teams_list, conn):
    """Extrait les équipes à partir de l'objet BeautifulSoup."""
    cursor = conn.cursor()

    teams = soup.find_all('td', class_="links no-border-links hauptlink")

    valos = soup.find_all("td", class_="rechts")
    headcounts_and_ages = [td for td in soup.find_all(
        'td') if td.get('class') == ['zentriert']]

    valos_grouped = list(zip(valos[::2], valos[1::2]))
    headcounts_and_ages_grouped = list(
        zip(headcounts_and_ages[::2], headcounts_and_ages[1::2]))

    for team, (v_tot, v_mean), (headcount, age_mean) in zip(teams, valos_grouped, headcounts_and_ages_grouped):
        team_name = team.find('a')['title']

        cursor.execute("SELECT id FROM teams WHERE team = ?", (team_name,))
        team_id = cursor.fetchone()

        if team_name not in teams_list:
            team_dict = {
                "team_id": team_id[0],
                "valo_tot": v_tot.text,
                "valo_mean": v_mean.text,
                "headcount": headcount.text,
                "age_mean": age_mean.text
            }
            teams_list.append(team_dict)

            logger.info(f"Nouvelle info ajoutée : Nom={team_name}")
    return teams_list


def save_teams_to_db(conn, teams, annee):
    """Enregistre les données des équipes dans la base de données SQLite."""
    cursor = conn.cursor()
    for team in teams:
        values = (annee,) + tuple(team.values())
        cursor.execute("""
            INSERT OR REPLACE INTO infos (annee,team_id, valo_tot, valo_mean, headcount, age_mean)
            VALUES (?, ?, ?, ?, ?, ?)
        """, values)
    conn.commit()


def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS infos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee INTEGER,
            team_id INTEGER,
            valo_tot TEXT,
            valo_mean TEXT,
            headcount TEXT,
            age_mean TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            UNIQUE (annee,team_id, valo_tot, valo_mean, headcount, age_mean)
        )
    """)
    conn.commit()
    for annee in tqdm(ANNEES, desc="Traitement des requêtes"):
        teams_list = []
        url = f'https://www.transfermarkt.fr/uefa-champions-league/teilnehmer/pokalwettbewerb/CL/saison_id/{
            annee}'
        soup = fetch_page_content(url)
        if soup:
            teams_list = parse_teams_info(soup, teams_list, conn)
            logger.info(f"Ajout des infos terminée pour l'année {annee}")
        else:
            logger.error(
                f"Erreur lors du chargement de la page pour l'année {annee}")

        save_teams_to_db(conn, teams_list, annee)


if __name__ == "__main__":
    main()
