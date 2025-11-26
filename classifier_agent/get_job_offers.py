import http.client
import urllib.parse

def search_jobs(role, city, num_pages=1, country="fr", date_posted="all"):
    conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

    params = {
        "query": f"{role} jobs in {city}",
        "num_pages": num_pages,
        "country": country,
        "date_posted": date_posted
    }

    query_string = urllib.parse.urlencode(params)

    headers = {
        'x-rapidapi-key': "c8b31874f8mshbf18214c60669dep1483fajsnbd95099cd31f",
        'x-rapidapi-host': "jsearch.p.rapidapi.com"
    }

    conn.request("GET", f"/search?{query_string}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")