from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from .helper import global_status, potion_status, itemize


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
    print("Capacity plan called")
    gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status()
    potion_cap = 0
    ml_cap = 0
    if gold > 5000:
        ml_cap = 1
        potion_cap = 1
    if gold > 10000:
        ml_cap = 2
        potion_cap = 2
    print(f"Purchasing {potion_cap} potion capacity and {ml_cap} ml capacity")
    return {
        "potion_capacity": potion_cap,
        "ml_capacity": ml_cap
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
    print("Capacity deliver called")
    potion_cap = capacity_purchase.potion_capacity
    ml_cap = capacity_purchase.ml_capacity
    gold_spent = potion_cap * 1000 + ml_cap * 1000

    if potion_cap > 0 or ml_cap > 0:
        with db.engine.begin() as connection:
            # update capacity
            sql = """
                UPDATE capacity_inventory 
                SET potion_capacity = potion_capacity + :potion_capacity,
                    ml_capacity = ml_capacity + :ml_capacity"""
            connection.execute(sqlalchemy.text(sql),
                {
                    'potion_capacity': potion_cap * 50,
                    'ml_capacity': ml_cap * 10000
                })
            # update gold
            sql = """
                UPDATE global_inventory 
                SET quantity = quantity - :gold_spent"""
            connection.execute(sqlalchemy.text(sql),
                {
                    'gold_spent': gold_spent
                })
    print(f"Potion capacity\t+{potion_cap * 50}\nMl capacity\t+{ml_cap * 10000}")

    return "OK"
