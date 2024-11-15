import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from tqdm import tqdm
from config import HEADERS, ANNEES, DB_FILE, PHASES_TOURNOI, LOG_FILE_MATCHES


logger = logging.getLogger("matches_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE_MATCHES)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s:%(levelname)s:%(message)s"))

logger.addHandler(file_handler)


def fetch_page_content(url):
    """Effectue une requête HTTP pour récupérer le contenu de la page."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la requête pour l'URL {url}: {e}")
        return None


def parse_match_data(soup, conn):
    """Extrait les données de chaque match à partir de l'objet BeautifulSoup."""
    matches = []
    cursor = conn.cursor()

    team1_list = soup.find_all(
        'td', class_="rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname")
    team2_list = soup.find_all(
        'td', class_="hauptlink no-border-links no-border-rechts hide-for-small spieltagsansicht-vereinsname")
    scores = soup.find_all('span', class_="matchresult finished")
    

    for t1, t2, score in zip(team1_list, team2_list, scores):
        t1_name = t1.find_all('a')[1]['title'] if len(
            t1.find_all('a')) > 1 else t1.find('a')['title']
        t2_name = t2.find('a')['title'] if t2.find('a') else "N/A"
        sc1, sc2 = score.text.split(':')
        

        # Récupère les IDs des équipes depuis la table `teams`
        cursor.execute("SELECT id FROM teams WHERE team = ?", (t1_name,))
        t1_id = cursor.fetchone()
        cursor.execute("SELECT id FROM teams WHERE team = ?", (t2_name,))
        t2_id = cursor.fetchone()

        # Ajoute les IDs d'équipes et scores dans la liste des matches
        if t1_id and t2_id:
            matches.append((t1_id[0], sc1.strip(), t2_id[0], sc2.strip()))
        else:
            logger.warning(f"Équipe non trouvée : {t1_name} ou {t2_name}")


    return matches


def save_matches_to_db(conn, annee, groupe, matches):
    """Enregistre les données des matchs dans la base de données SQLite."""
    cursor = conn.cursor()
    for t1_id, sc1, t2_id, sc2 in matches:
        cursor.execute("""
            INSERT OR REPLACE INTO matches (annee, phase_tournoi, t1_id, score1, t2_id, score2)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (annee, groupe, t1_id, sc1, t2_id, sc2))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee INTEGER,
            phase_tournoi TEXT,
            t1_id INTEGER,
            score1 INTEGER,
            t2_id INTEGER,
            score2 INTEGER,
            FOREIGN KEY (t1_id) REFERENCES teams(id),
            FOREIGN KEY (t2_id) REFERENCES teams(id),
            UNIQUE (annee, phase_tournoi, t1_id, t2_id)
        )
    """)
    conn.commit()

    for annee in tqdm(ANNEES, desc="Traitement des années"):
        for key, phase_tournoi in tqdm(PHASES_TOURNOI.items(), desc=f"Traitement des matchs pour {annee}", leave=False):
            url = f'https://www.transfermarkt.fr/uefa-champions-league/spieltag/pokalwettbewerb/CL/plus/0?saison_id={
                annee}&gruppe={key}'
            soup = fetch_page_content(url)
            if soup:
                matches = parse_match_data(soup, conn)
                save_matches_to_db(conn, annee, phase_tournoi, matches)
                if key in 'ABCDEFGH':
                    logger.info(f"Matches pour {annee}, groupe {
                                key} enregistrés dans la base de données.")
                else:
                    logger.info(f"Matches pour {annee}, {
                                phase_tournoi} enregistrés dans la base de données.")
            else:
                if key in 'ABCDEFGH':
                    logger.error(f"Erreur pour l'année {
                                 annee} et le groupe {key}")
                else:
                    logger.error(f"Erreur pour l'année {
                                 annee} et les {phase_tournoi}")

    conn.close()
    logger.info("Traitement terminé et base de données mise à jour.")


if __name__ == "__main__":
    main()
