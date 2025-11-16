import os
from amadeus import Client
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)

def search_flights(origin, destination, departure_date, return_date=None, adults=1):
    """
    Recherche simple d'un vol aller/retour via l'API Amadeus.
    """
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=adults,
            currencyCode="EUR"
        )
        return response.data
    except Exception as e:
        return {"error": str(e)}
          
