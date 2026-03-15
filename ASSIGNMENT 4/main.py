from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Cart System API", description="FastAPI Day 5 — Shopping Cart Practice")

# ─────────────────────────────────────────────
# In-memory product catalog
# ─────────────────────────────────────────────
products = [
    {"product_id": 1, "name": "Wireless Mouse",  "price": 499, "in_stock": True},
    {"product_id": 2, "name": "Notebook",         "price": 99,  "in_stock": True},
    {"product_id": 3, "name": "USB Hub",           "price": 349, "in_stock": False},
    {"product_id": 4, "name": "Pen Set",           "price": 49,  "in_stock": True},
    {"product_id": 5, "name": "HDMI Cable",        "price": 199, "in_stock": True},
]

# In-memory cart and orders store (reset on server restart — expected)
cart: List[dict] = []
orders: List[dict] = []
order_id_counter = 1  # global auto-increment for order IDs


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def get_product(product_id: int) -> dict:
    for p in products:
        if p["product_id"] == product_id:
            return p
    return None


def calculate_subtotal(product: dict, quantity: int) -> int:
    return product["price"] * quantity


# ─────────────────────────────────────────────
# Pydantic model for checkout body
# ─────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# ─────────────────────────────────────────────
# Root
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to the Cart System API 🛒", "docs": "/docs"}


# ─────────────────────────────────────────────
# Q1 & Q4  — POST /cart/add
# Add a product to the cart (or update quantity if already present)
# ─────────────────────────────────────────────
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    # Validate product exists
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    # Validate product is in stock  (Q3)
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # Check if product already in cart  (Q4)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = calculate_subtotal(product, item["quantity"])
            return {"message": "Cart updated", "cart_item": item}

    # New item — append to cart
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_subtotal(product, quantity),
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}


# ─────────────────────────────────────────────
# Q2  — GET /cart
# View current cart with grand total
# ─────────────────────────────────────────────
@app.get("/cart")
def get_cart():
    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)
    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total,
    }


# ─────────────────────────────────────────────
# Q5  — DELETE /cart/{product_id}
# Remove a specific product from the cart
# ─────────────────────────────────────────────
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    global cart
    original_len = len(cart)
    cart = [item for item in cart if item["product_id"] != product_id]

    if len(cart) == original_len:
        raise HTTPException(status_code=404, detail=f"Product id {product_id} not found in cart")

    return {"message": f"Product {product_id} removed from cart", "item_count": len(cart)}


# ─────────────────────────────────────────────
# Q5 & Q6 & Bonus — POST /cart/checkout
# Checkout the cart: create orders, clear cart
# ─────────────────────────────────────────────
@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    global order_id_counter

    # Bonus — reject empty cart with 400
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    orders_placed = []
    grand_total = 0

    for item in cart:
        order = {
            "order_id": order_id_counter,
            "customer_name": request.customer_name,
            "delivery_address": request.delivery_address,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item["subtotal"],
        }
        orders.append(order)
        orders_placed.append(order)
        grand_total += item["subtotal"]
        order_id_counter += 1

    # Clear cart after checkout
    cart.clear()

    return {
        "message": "Checkout successful! 🎉",
        "customer_name": request.customer_name,
        "delivery_address": request.delivery_address,
        "orders_placed": orders_placed,
        "grand_total": grand_total,
    }


# ─────────────────────────────────────────────
# Q5 & Q6  — GET /orders
# View all placed orders
# ─────────────────────────────────────────────
@app.get("/orders")
def get_orders():
    if not orders:
        return {"message": "No orders yet", "orders": [], "total_orders": 0}

    return {
        "orders": orders,
        "total_orders": len(orders),
    }
