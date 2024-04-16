from fastapi import APIRouter
import sqlalchemy
from src import database as db
from .helper import global_status, potion_status

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 

    # semi-hard coded: red, green, blue potions, prices (for now)

    catalog = []
    if num_red_potions > 0:
        print(f"Selling {num_red_potions} red potions at {50} gold each.")
        catalog.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": {num_red_potions},
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        })
    if num_green_potions > 0:
        print(f"Selling {num_green_potions} green potions at {60} gold each.")
        catalog.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": {num_green_potions},
            "price": 60,
            "potion_type": [0, 100, 0, 0],
        })
    if num_blue_potions > 0:
        print(f"Selling {num_blue_potions} blue potions at {80} gold each.")
        catalog.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": {num_blue_potions},
            "price": 80,
            "potion_type": [0, 0, 100, 0],
        })

    return catalog

