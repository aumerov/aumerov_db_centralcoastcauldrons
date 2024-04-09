from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

    # hard coding for now
    data = result.fetchall() 
    print("Catalog")
    print("Current table: ", data) 
    num_green_potions = data[0][0]
    gold = data[0][2]  # could use for dynamic pricing in future

    print(f"Selling {num_green_potions} green potions at {60} gold each.")

    # hard coded:
        # assumed to be all green potions
        # prices (for now), for small profit
    if num_green_potions > 0:
        return [{
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": {num_green_potions},
            "price": 60,
            "potion_type": [0, 0, 100, 0],
        }]

    return [{}] # return empty dictionary?

    # return [
    #         # {
    #         #     "sku": "GREEN_POTION_0",
    #         #     "name": "greeen potion",
    #         #     "quantity": 1,
    #         #     "price": 100,
    #         #     "potion_type": [0, 0, 100, 0],
    #         # },
    #         {
    #             "sku": "RED_POTION_0",
    #             "name": "red potion",
    #             "quantity": 1,
    #             "price": 50,
    #             "potion_type": [100, 0, 0, 0],
    #         }
    #     ]
