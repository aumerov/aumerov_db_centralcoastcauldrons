from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    #TODO: create logic statements in sql based on inventory, gold

    with db.engine.begin() as connection:
            sql_to_execute = \
                """SELECT * 
                FROM global_inventory
                
                """
            result = connection.execute(sqlalchemy.text(sql_to_execute))

    # hard coding for now
    data = result.fetchall() 
    print("Result: ", data) 
    num_green_potions = data[0][0]
    num_green_ml = data[0][1]
    gold = data[0][2]

    print("GOLD: ", gold) 
    for item in wholesale_catalog:
        print(item)
    
    
    # hard coded, only buy small green barrels
    if num_green_potions < 10: # if less than 10 green potions, buy small green barrels
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL":
                quant = barrel.quantity
                num_eligible_for_purchase = round(gold / barrel.price)

        # buy green barrels
        return {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": num_eligible_for_purchase
        }

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]
