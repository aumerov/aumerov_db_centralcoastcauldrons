from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math
from .helper import global_status, potion_status, capacity_status

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int






@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print("Potions delivered / bottler deliver called")
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        # num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 

        ml_used = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
        # update_commands = []

        # it's late...                ...             ... and chatGPT recommended I combine my 16 different SQL color inventory queries into one. I did it, of course, because if AI told me to jump off a bridge I would.
        for potion in potions_delivered:
            ml_used['red_ml'] += potion.potion_type[0] * potion.quantity  # has to be hard coded this way because of what we pass in... Can we change this to give ourselves more info?
            ml_used['green_ml'] += potion.potion_type[1] * potion.quantity 
            ml_used['blue_ml'] += potion.potion_type[2] * potion.quantity 
            ml_used['dark_ml'] += potion.potion_type[3] * potion.quantity 

            find_potion_query = """
                SELECT sku FROM potion_inventory
                WHERE red_content = :red
                  AND green_content = :green
                  AND blue_content = :blue
                  AND dark_content = :dark
            """
            potion_sku = connection.execute(            # find the sku, to update potion_inventory
                sqlalchemy.text(find_potion_query),
                {
                    'red': potion.potion_type[0],
                    'green': potion.potion_type[1],
                    'blue': potion.potion_type[2],
                    'dark': potion.potion_type[3]
                }
            ).fetchone()
            print("potion_sku: ", potion_sku)
            
            if potion_sku:  # should always find the potion... right?
                update_potion_inventory = """
                        UPDATE potion_inventory
                        SET quantity = quantity + :quantity
                        WHERE sku = :sku
                    """
                connection.execute(
                    sqlalchemy.text(update_potion_inventory),
                    {
                        'quantity': potion.quantity,
                        'sku': potion_sku.sku
                    })
            
            else:   # just in case
                print(f"Error: No potion found")
                return "OK"

        # update global_inventory
        for color, ml_deducted in ml_used.items():
            update_command = """
                UPDATE global_inventory
                SET quantity = quantity - :deducted
                WHERE name = :color
            """
            connection.execute(sqlalchemy.text(update_command), {'deducted': ml_deducted, 'color': color})


        # # execute all   
        # for command in update_commands:
        #     connection.execute(sqlalchemy.text(command))
    
    # check updated global table
    global_status()

    return "OK"








@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    print("Potions plan / bottler plan called")
    gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status()
    # num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status()

    potions_brewed = []
    potion_capacity, ml_capacity  = capacity_status()

    with db.engine.begin() as connection:
        # sql = "SELECT potion_capacity FROM capacity_inventory"
        # res = connection.execute(sqlalchemy.text(sql)).fetchone()
        # potion_capacity = int(res[0]) if res else 100
        # print(f"current potion capacity: {potion_capacity}")

        sql = "SELECT quantity FROM potion_inventory"
        res = connection.execute(sqlalchemy.text(sql)).fetchall()
        total_potions = sum(quantity[0] for quantity in res)
        print(f"Currently have {total_potions} potions")
        potion_capacity -= total_potions 

        # Step 2: Retrieve available potion recipes and sort by complexity
        potion_query = """
            SELECT sku, name, quantity, red_content, green_content, blue_content, dark_content
            FROM potion_inventory
            ORDER BY (red_content > 0)::int + (green_content > 0)::int +
                     (blue_content > 0)::int + (dark_content > 0)::int DESC,
                     red_content + green_content + blue_content + dark_content DESC
        """
        potion_recipes = connection.execute(sqlalchemy.text(potion_query)).fetchall()
        print("Potion recipes: ", potion_recipes)


        # Step 3: Iterate through potions and check if they can be created
        for potion in potion_recipes:
            print("checking potion: ", potion)
            quantity_brewed = 0
            # Check if the potion can be created with the current ml_inventory. If so, create as many as possible.
            while (num_red_ml >= potion.red_content and
                num_green_ml >= potion.green_content and
                num_blue_ml >= potion.blue_content and
                num_dark_ml >= potion.dark_content):

                if potion.quantity >= 15:
                    break
                
                # Create the potion and update ml_inventory
                num_red_ml -= potion.red_content
                num_green_ml -= potion.green_content
                num_blue_ml -= potion.blue_content
                num_dark_ml -= potion.dark_content
                quantity_brewed += 1
            
            if (quantity_brewed > 0) & (potion_capacity > 0):
                if quantity_brewed > potion_capacity:
                    quantity_brewed = potion_capacity
                potion_capacity -= quantity_brewed
                # Add the brewed potion to the list
                potions_brewed.append({
                        "potion_type": [potion.red_content, potion.green_content, potion.blue_content, potion.dark_content],
                        "quantity": quantity_brewed,
                    })

    print("Potions brewed: ", potions_brewed)
    return potions_brewed




if __name__ == "__main__":
    print(get_bottle_plan())
