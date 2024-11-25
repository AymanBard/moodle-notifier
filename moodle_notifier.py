import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Récupération des informations de connexion depuis les variables d'environnement
username = os.getenv("MOODLE_USERNAME")  # Nom d'utilisateur Moodle
password = os.getenv("MOODLE_PASSWORD")  # Mot de passe Moodle
url = "https://moodle.univ-lille.fr/course/view.php?id=34503"  # URL de la page Moodle à surveiller
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")  # URL du webhook Discord

if not username or not password or not webhook_url:
    print("Les variables d'environnement MOODLE_USERNAME, MOODLE_PASSWORD ou DISCORD_WEBHOOK_URL ne sont pas définies.")
    exit(1)

# Initialisation des options de Firefox pour le mode headless
firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--headless")  # Activer le mode headless

# Initialisation du navigateur Firefox pour Selenium en mode headless
driver = webdriver.Firefox(options=firefox_options)

try:
    # Étape 1 : Ouvrir la page de connexion CAS
    driver.get("https://cas.univ-lille.fr/login?service=https%3A%2F%2Fmoodle.univ-lille.fr%2Flogin%2Findex.php%3FauthCAS%3DCAS")

    # Attendre que le champ de nom d'utilisateur soit présent et entrer les identifiants de connexion
    username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    username_field.send_keys(username)

    password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
    password_field.send_keys(password)

    # Cliquer sur le bouton de connexion
    login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "submit")))
    login_button.click()

    # Étape 2 : Accéder à la page à surveiller
    driver.get(url)
    time.sleep(3)  # Attendre que la page se charge complètement

    # Extraire uniquement le contenu de la section à surveiller
    try:
        section_to_monitor = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "section-4")))
        content = section_to_monitor.get_attribute("outerHTML")
    except:
        content = "Section introuvable."

    # Charger le contenu précédent depuis le fichier
    try:
        with open("previous_content.txt", "r", encoding="utf-8") as file:
            previous_content = file.read()
    except FileNotFoundError:
        print("Fichier précédent introuvable, création d'un nouveau.")
        previous_content = ""

    def send_discord_notification():
        data = {
            "content": "La page Moodle que tu surveilles a changé ! Va vérifier les nouvelles informations."
        }
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("Notification envoyée sur Discord.")
        else:
            print(f"Erreur lors de l'envoi de la notification : {response.status_code}")

    # Si le contenu a changé, envoie une notification Discord
    if content != previous_content:
        print("La page a changé !")
        with open("previous_content.txt", "w", encoding="utf-8") as file:
            file.write(content)
        send_discord_notification()  # Envoie la notification sur Discord
    else:
        print("Pas de changement.")

finally:
    # Fermer le navigateur
    driver.quit()
