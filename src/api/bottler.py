from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math
from .helper import global_status, potion_status

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

    # Semi-hard coded to bottle red, green, blue potions.

    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 

        update_commands = []

        for potion in potions_delivered:
            if potion.potion_type == [100,0,0,0]: # if brewed red potions
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_red_ml} - {100 * potion.quantity} WHERE item = 'red_ml'")
                update_commands.append(f"UPDATE potion_inventory SET quantity = {num_red_potions} + {potion.quantity} WHERE item = 'red_potion'")

            elif potion.potion_type == [0,100,0,0]: # if brewed green potions
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_green_ml} - {100 * potion.quantity} WHERE item = 'green_ml'")
                update_commands.append(f"UPDATE potion_inventory SET quantity = {num_green_potions} + {potion.quantity} WHERE item = 'green_potion'")

            elif potion.potion_type == [0,0,100,0]: # if brewed blue potions
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_blue_ml} - {100 * potion.quantity} WHERE item = 'blue_ml'")
                update_commands.append(f"UPDATE potion_inventory SET quantity = {num_blue_potions} + {potion.quantity} WHERE item = 'blue_potion'")

        # execute all   
        for command in update_commands:
            connection.execute(sqlalchemy.text(command))
    
    # check updated table
    global_status()

    return "OK"









@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status()
    num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status()

    potions_brewed = []
    num_red_brewed = 0
    num_green_brewed = 0
    num_blue_brewed = 0
    # num_dark_brewed = 0

    # Semi-hard coded to bottle red, green, blue potions.
    # For now, bottling everything possible (no worry about inventory cap yet)
    
    if num_red_ml >= 100:
        num_red_brewed = math.floor(num_red_ml / 100)
        potions_brewed.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": num_red_brewed,
            })
    if num_green_ml >= 100:
        num_green_brewed = math.floor(num_green_ml / 100)
        potions_brewed.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": num_green_brewed,
            })
    if num_blue_ml >= 100:
        num_blue_brewed = math.floor(num_blue_ml / 100)
        potions_brewed.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": num_blue_brewed,
            })
    # if num_dark_ml >= 100:
    #     num_dark_brewed = math.floor(num_dark_ml / 100)
    #     potions_brewed.append({
    #             "potion_type": [0, 0, 0, 100],
    #             "quantity": num_dark_brewed,
    #         })

    print(potions_brewed)
    return potions_brewed


if __name__ == "__main__":
    print(get_bottle_plan())
