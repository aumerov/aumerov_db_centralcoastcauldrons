from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
import os
from .helper import global_status, potion_status

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    
    # using a global log.txt file to count. Code from Stack Overflow
    with open('src/log.txt','r') as f:
        counter = int(f.read())
        counter += 1 
    with open('src/log.txt','w') as f:
        f.write(str(counter))

    print(counter)
    return {"cart_id": counter}


class CartItem(BaseModel):
    quantity: int





@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 
        
        # hard coding to 1 item per visit, for now
        if cart_item.quantity > 1:
            cart_item.quantity = 1
        

        # if item_sku == 'RED_POTION_0':
        #     num_red = cart_item.quantity
        #     return
        # elif item_sku == 'GREEN_POTION_0':
        #     num_green = cart_item.quantity
        #     return
        # elif item_sku == 'BLUE_POTION_0':
        #     num_blue = cart_item.quantity
        #     return

    return "OK"





class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # profit = int(cart_checkout.payment)

    with db.engine.begin() as connection:
        gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 

        # Double checking
        if num_green_potions == 0:
            print("Out of potions! Come back later.")
            return "Out of potions! Come back later."


        # UPDATE
        # price still hard coded at 50/60/80.
        sql_to_execute = \
            f"""UPDATE global_inventory
            SET num_green_potions = {num_green_potions - 1},
            gold = {gold + 60};
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # check updated table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory;
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        print("Checkout Result: ", data) 

    return {"total_potions_bought": 1, "total_gold_paid": 60}
