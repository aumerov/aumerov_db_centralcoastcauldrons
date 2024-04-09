from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int






@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):   # Execution hard coded in docs for now. 5 green potions
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:

        # SELECT to grab table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # hard coding for now
        data = result.fetchall() 
        print("Bottler delivery")
        print("Table contents: ", data) 
        num_green_potions = data[0][0]
        num_green_ml = data[0][1]
        gold = data[0][2]

        for potion in potions_delivered:  # assuming 1 (hard coded)
            potions_brewed = potion.quantity

        if num_green_ml <= 100:  # return if cannot brew more potions
            print("Insufficient ml to brew new potions")
            return "Insufficient ml to brew new potions"

        # UPDATE
        sql_to_execute = \
            f"""UPDATE global_inventory
            SET num_green_ml = {num_green_ml - (potions_brewed * 100)},
            num_green_potions = {num_green_potions + potions_brewed};
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # check updated table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        print("Potion brew result: ", data) 

    return "OK"








@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    with db.engine.begin() as connection:
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # hard coding for now
        data = result.fetchall() 
        print("Bottler plan")
        print("Table contents: ", data) 
        num_green_potions = data[0][0]
        num_green_ml = data[0][1]
        gold = data[0][2]

        # V1 logic: bottle all barrels into green potions.
        potions_brewed = 0
        if num_green_ml > 0:
            potions_brewed = math.floor(num_green_ml / 100) # 100ml per potion
        

        print(f"Brewing {potions_brewed} green potions")

        return [{
            "potion_type": [0, 0, 100, 0],
            "quantity": potions_brewed,
        }]

    # # Initial logic: bottle all barrels into red potions.
    # return [
    #         {
    #             "potion_type": [100, 0, 0, 0],
    #             "quantity": 5,
    #         }
    #     ]


if __name__ == "__main__":
    print(get_bottle_plan())
