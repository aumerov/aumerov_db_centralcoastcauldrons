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
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):  # hard coded to 1 small green barrel for now
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection: # SELECT step may be unnecessary
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # hard coding for now
        data = result.fetchall() 
        num_green_potions = data[0][0]
        num_green_ml = data[0][1]
        gold = data[0][2]

        # parse order
        for barrel in barrels_delivered:
                if barrel.sku == "SMALL_GREEN_BARREL":
                    quant = barrel.quantity
                    price = barrel.price
                    ml = barrel.ml_per_barrel

        if int(price) * int(quant) > gold:
             print("Insufficient gold to complete order!")
             return "Insufficient gold to complete order"

        # else UPDATE
        sql_to_execute = \
            f"""UPDATE global_inventory
            SET num_green_ml = {num_green_ml + ml},
            gold = {gold - int(quant) * int(price)};
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # print(result.fetchall)

        # check updated table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        print("Deliver Result: ", data) 

    return "OK"






# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("CATALOG")
    print(wholesale_catalog)

    with db.engine.begin() as connection:
            sql_to_execute = \
                """SELECT * 
                FROM global_inventory
                
                """
            result = connection.execute(sqlalchemy.text(sql_to_execute))

    # hard coding for now
    data = result.fetchall() 
    print("Plan Result: ", data) 
    num_green_potions = data[0][0]
    num_green_ml = data[0][1]
    gold = data[0][2]

    # print("GOLD: ", gold) 
    # print("CATALOG")
    # for item in wholesale_catalog:
    #     print(item)
    
    
    # hard coded, only buy small green barrels
    if num_green_potions < 10: # if less than 10 green potions, buy small green barrels
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL":
                stock = barrel.quantity
                num_eligible_for_purchase = 0
                if gold >= barrel.price:
                    num_eligible_for_purchase = round(gold / barrel.price)  
                    # if we try to buy more barrels than stock  
                    if num_eligible_for_purchase > stock:  # better way to do this using ':' but I forgot and don't want to look it up rn
                        num_eligible_for_purchase = stock
                print(f"Buying {num_eligible_for_purchase} green barrels")

        # buy green barrels
        return {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": num_eligible_for_purchase
        }
    
    # else
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]
