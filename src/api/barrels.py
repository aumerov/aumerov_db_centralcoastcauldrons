from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math
import random
from .helper import global_status, potion_status, itemize

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int






@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):  # hard coded to 1 small green barrel for now
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    if not barrels_delivered:
        return "OK"

    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status()  

        if gold == 0:   # for testing purposes
            return "OK"

        # Semi-hard coded to purchase small red, green, blue barrels.
        # Assuming barrel plan is valid.

        curr_gold = gold    # copy of gold just in case
        purchase_plan = itemize(barrels_delivered)
        red_purchasing = 0
        green_purchasing = 0
        blue_purchasing = 0
        red_price = 0
        green_price = 0
        blue_price = 0
        
        # # Update quantities based on purchase plan. Initialized above to reduce risk of errors.
        # red_purchasing = purchase_plan['SMALL_RED_BARREL'].quantity
        # green_purchasing = purchase_plan['SMALL_GREEN_BARREL'].quantity
        # blue_purchasing = purchase_plan['SMALL_BLUE_BARREL'].quantity
        # red_price = purchase_plan['SMALL_RED_BARREL'].price
        # green_price = purchase_plan['SMALL_GREEN_BARREL'].price
        # blue_price = purchase_plan['SMALL_BLUE_BARREL'].price


        # Modularizing SQL UPDATE code
        update_commands = []

        for barrel in barrels_delivered:
            if barrel.sku == 'SMALL_RED_BARREL': # if bought red barrels
                red_purchasing = purchase_plan['SMALL_RED_BARREL'].quantity
                red_price = purchase_plan['SMALL_RED_BARREL'].price
                curr_gold -= red_purchasing * red_price
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_red_ml} + {red_purchasing * purchase_plan['SMALL_RED_BARREL'].ml_per_barrel} WHERE item = 'red_ml'")

            elif barrel.sku == 'SMALL_GREEN_BARREL': # if bought green barrels
                green_purchasing = purchase_plan['SMALL_GREEN_BARREL'].quantity
                green_price = purchase_plan['SMALL_GREEN_BARREL'].price
                curr_gold -= green_purchasing * green_price
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_green_ml} + {green_purchasing * purchase_plan['SMALL_GREEN_BARREL'].ml_per_barrel} WHERE item = 'green_ml'")

            elif barrel.sku == 'SMALL_BLUE_BARREL': # if bought blue barrels
                blue_purchasing = purchase_plan['SMALL_BLUE_BARREL'].quantity
                blue_price = purchase_plan['SMALL_BLUE_BARREL'].price
                curr_gold -= blue_purchasing * blue_price
                update_commands.append(f"UPDATE global_inventory SET quantity = {num_blue_ml} + {blue_purchasing * purchase_plan['SMALL_BLUE_BARREL'].ml_per_barrel} WHERE item = 'blue_ml'")

        update_commands.append(f"UPDATE global_inventory SET quantity = {curr_gold} WHERE item = 'gold'") # update gold last

        # if red_purchasing > 0: # if bought red barrels
        #     curr_gold -= red_purchasing * red_price
        #     update_commands.append(f"num_red_ml = {num_red_ml} + {red_purchasing * purchase_plan['SMALL_RED_BARREL'].ml_per_barrel}")
        
        # if green_purchasing > 0: # if bought green barrels
        #     curr_gold -= green_purchasing * green_price
        #     update_commands.append(f"num_green_ml = {num_green_ml} + {green_purchasing * purchase_plan['SMALL_GREEN_BARREL'].ml_per_barrel}")

        # if blue_purchasing > 0: # if bought blue barrels
        #     curr_gold -= blue_purchasing * blue_price
        #     update_commands.append(f"num_blue_ml = {num_blue_ml} + {blue_purchasing * purchase_plan['SMALL_BLUE_BARREL'].ml_per_barrel}")
        

        # execute all
        for command in update_commands:
            connection.execute(sqlalchemy.text(command))

        # check updated table
        global_status()

    return "OK"









# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("CATALOG")
    print(wholesale_catalog)

    gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status()
    num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status()
    catalog = itemize(wholesale_catalog)
    
    # Semi-hard coded to purchase small red, green, blue barrels.
    # logic: 
        # buy as many blue barrels as possible.
        # buy one red barrel.
        # buy as many green barrels as possible with gold left.

    barrels_to_purchase = []    # final purchase plan
    curr_gold = gold            # copy of gold just in case
    available_red = catalog['SMALL_RED_BARREL'].quantity
    available_green = catalog['SMALL_GREEN_BARREL'].quantity
    available_blue = catalog['SMALL_BLUE_BARREL'].quantity
    red_price = catalog['SMALL_RED_BARREL'].price
    green_price = catalog['SMALL_GREEN_BARREL'].price
    blue_price = catalog['SMALL_BLUE_BARREL'].price
    red_purchasing = 0
    green_purchasing = 0
    blue_purchasing = 0

    if (curr_gold >= blue_price) & (available_blue >= 1): # buy as many blue barrels as possible
        blue_purchasing = math.floor(curr_gold / blue_price)
        if blue_purchasing > available_blue:
            blue_purchasing = available_blue
        barrels_to_purchase.append({
            "sku": "SMALL_BLUE_BARREL",
            "quantity": blue_purchasing
        })
        curr_gold -= blue_price * blue_purchasing  # locally update gold

    if (curr_gold >= red_price) & (available_red >= 1): # buy one red barrel, if possible
        red_purchasing = 1
        barrels_to_purchase.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": red_purchasing
        })
        curr_gold -= red_price * red_purchasing # locally update gold

    if (curr_gold >= green_price) & (available_green >= 1): # buy as many green barrels as possible
        green_purchasing = math.floor(curr_gold / green_price)
        if green_purchasing > available_green:
            green_purchasing = available_green
        barrels_to_purchase.append({
            "sku": "SMALL_GREEN_BARREL",
            "quantity": green_purchasing
        })
        curr_gold -= green_price * green_purchasing  # locally update gold
    
    print(f"Plan: {barrels_to_purchase}")
    return barrels_to_purchase
