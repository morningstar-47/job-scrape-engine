import requests
import pycountry 
from dotenv import load_dotenv

load_dotenv()

def get_country_code_pycountry(country_name_or_code):
    # 1. Vérification si c'est déjà un code (2 lettres, majuscules)
    potential_code = country_name_or_code.strip().upper()
    if len(potential_code) == 2 and potential_code.isalpha():
        # Vérifie si c'est un code ISO 3166-1 alpha-2 valide
        try:
            pycountry.countries.lookup(potential_code)
            return potential_code
        except LookupError:
            pass # Continuer pour tenter la recherche par nom

    # 2. Conversion par nom
    try:
        country = pycountry.countries.lookup(country_name_or_code)
        return country.alpha_2
    except LookupError:
        print(f"Avertissement : Pays non reconnu : {country_name_or_code}")
        return country_name_or_code # Retourne l'original si non trouvé


def geocode_city(api_key, city_name, country_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    address = city_name
    country_code = get_country_code_pycountry(country_name)
    address += f", {country_code}"

    params = {
        "address": address,
        "key": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    if response.status_code != 200 or not data["results"]:
        raise Exception("Ville introuvable.")

    # Filtrer pour ne garder que les villes (locality)
    cities = [
        r for r in data["results"]
        if "locality" in r["types"]
    ]

    if len(cities) == 0:
        raise Exception("Aucune ville exacte trouvée.")

    if len(cities) > 1:
        print("⚠️ Plusieurs villes trouvées :")
        for idx, c in enumerate(cities):
            print(f"{idx+1}. {c['formatted_address']}")
        print("➡️ La première sera utilisée par défaut.")

    city = cities[0]
    loc = city["geometry"]["location"]

    return loc["lat"], loc["lng"]


def get_travel_time(api_key, origin_lat, origin_lng, dest_lat, dest_lng, travel_mode):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration"  # On récupère uniquement la durée
    }

    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_lng
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": dest_lat,
                    "longitude": dest_lng
                }
            }
        },
        "travelMode": travel_mode
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Erreur API : {response.text}")

    data = response.json()
    if data:
        duration_str = data["routes"][0]["duration"]

        # Conversion en minutes
        seconds = int(duration_str.replace("s", ""))
        minutes = seconds // 60

        return minutes
    else:
        return 1000

def travel_time_from_cities(api_key, origin_city, origin_country, destination_city, destination_country, travel_mode):
    # Étape 1 : géocodage
    origin_lat, origin_lng = geocode_city(api_key, origin_city, origin_country)
    dest_lat, dest_lng = geocode_city(api_key, destination_city, destination_country)
    
    # Étape 2 : appel à Google Routes
    return get_travel_time(api_key, origin_lat, origin_lng, dest_lat, dest_lng, travel_mode)

def select_from_job(job):
    cles_a_garder = ["job_id", "job_title", "employer_name", "job_publisher", "job_description", "job_posted_at", "job_location", "job_city", "job_country", "job_apply_link"]
    # Création du sous-dictionnaire
    sous_dictionnaire = {
        cle: job[cle]
        for cle in cles_a_garder
    }
    return sous_dictionnaire