from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math
import random
from .helper import global_status, itemize, capacity_status

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


### notes 4.17
# can use barrel_delivered.price

# "INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')",
#     [{"order_id": order_id}]
# }
# except IntegrityError as e:
#     return "OK"

# "order_id": order_id)]


# use: 
# elif barrel_delivered.potion_type == [1,0,0,0] for different barrels
# ...
# else: raise Exception("Invalid potion type")
####### better to fail fast -> be code to be more explicit about what it's expecting (throw errors if not)

# dont have to call db again: values are updated (assume update is right)
# print("gold paid: {gold_paid} red_ml: {red_ml} ...")

# parameterize SQL

# can bulk INSERT by putting parameterized dictionary in more than once. Makes sense for insert but not update



@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):  # hard coded to 1 small green barrel for now
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    if not barrels_delivered:
        return "OK"

    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        
        # Assuming barrel plan is valid.
        purchase_plan = itemize(barrels_delivered)
        print("Purchase plan: ", purchase_plan)

        # Modularizing SQL UPDATE code
        update_commands = []
        ml_inventory = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
        initial_gold = gold

        # check each type of barrel
        for i, ml in enumerate(ml_inventory):
            inventory_barrel_type = [int(j == i) for j in range(4)]
            print("Type of barrel to purchase: ", inventory_barrel_type)


            for barrel_key in purchase_plan:
                barrel = purchase_plan[barrel_key] 
                if barrel.potion_type == inventory_barrel_type: # bought that type of barrel
                    gold -= barrel.quantity * barrel.price
                    update_commands.append(f"""UPDATE global_inventory 
                                           SET quantity = quantity + {barrel.quantity * barrel.ml_per_barrel} 
                                           WHERE id = {i + 2}""")   # no time to parameterize

        update_commands.append(f"UPDATE global_inventory SET quantity = {gold} WHERE name = 'gold'") # update gold last

        # execute all
        for command in update_commands:
            connection.execute(sqlalchemy.text(command))

        # check updated table
        global_status()

    return "OK"




### notes 4.17
# not one right way to do it, can be creative here

# control variables - to control logic, so don;t have to redeploy to tweak value
    # static variable in db
    # threshold_normal, threshold_large, ml_capacity

# different logic for large vs normal size barrels

# inventory scheme -> lookup
# ((PHOTO))

# threshold = ml_threshold_large if selling_large else ml_threshold_normal
# for i, ml in enumerate(ml_inventory):
# if ml < threshold:
    # buy up to get back to threshold

# calculate_barrel_to_purchase 
###



# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("Barrel plan / Barrels plan called")
    print("CATALOG")
    print(wholesale_catalog)

    potion_capacity, ml_capacity  = capacity_status()

    gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status()
    catalog = itemize(wholesale_catalog)
    # print("Itemized catalog: ", catalog)

    ml_inventory = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
    current_total_ml = sum(ml_inventory)
    threshold = ml_capacity / 4
    # initial_gold = gold            # copy of gold just in case
    barrels_to_purchase = []    # final purchase plan


    for i, ml in enumerate(ml_inventory):
        # print (i, ml)
        if ml <= threshold:
            barrel_type_to_buy = [int(j == i) for j in range(4)]
            print("Potion type below threshold: ", barrel_type_to_buy)

            # check catalog for barrel of that type
            for key, barrel in catalog.items():
                current_total_ml = sum(ml_inventory)
                # if key.startswith('SMALL'): 
                # print("entry: ", key)
                if barrel_type_to_buy == barrel.potion_type:
                    if gold >= barrel.price:                            
                        max_affordable_quant = math.floor(gold / barrel.price)
                        threshold_quant = math.ceil(threshold / barrel.ml_per_barrel)
                        capacity_quant = math.floor((ml_capacity - current_total_ml) / barrel.ml_per_barrel)
                        quant = min(max_affordable_quant, barrel.quantity, threshold_quant, capacity_quant)

                        if quant > 0:
                            gold -= barrel.price * quant
                            ml += quant * barrel.ml_per_barrel
                            # current_total_ml += quant * barrel.ml_per_barrel
                            barrels_to_purchase.append({
                                "sku": key,
                                "quantity": quant
                            })

    print(f"Plan: {barrels_to_purchase}")
    return barrels_to_purchase
