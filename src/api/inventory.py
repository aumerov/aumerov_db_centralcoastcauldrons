from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

# TODO: implement. Format:
    # "number_of_potions": 0,
    #   "ml_in_barrels": 0,
    #   "gold": 0
@router.get("/audit")
def get_inventory():
    """ """
    print("Audit called")
    with db.engine.connect() as connection:

        # num potions
        sql_to_execute = """
            SELECT quantity
            FROM potion_inventory
        """
        potions_result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        # print(potions_result)
        if potions_result is not None:
            total_potions = sum(potion.quantity for potion in potions_result)
            # print(f"Total potions: {total_potions}")



        # Retrieve all entries for potion ingredients and gold from global_inventory
        sql_to_execute = sqlalchemy.text("""
            SELECT name, quantity
            FROM global_inventory
        """)
        inventory_results = connection.execute(sql_to_execute).fetchall()
        
        total_ml = 0
        gold = 0

        # semi-hard coded?
        for item in inventory_results:
            if item.name == 'gold':
                gold = item.quantity
            else:
                total_ml += item.quantity

        print(f"Inventory result: {total_potions} potions, {total_ml} ml, and {gold} gold.")
        return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}




# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold. (multiples of above)
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int



# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
