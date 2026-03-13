from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# Sample Data
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 199, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True}
]

# Pydantic Model
class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool


# GET All Products
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# GET Single Product
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


# ADD Product
@app.post("/products", status_code=status.HTTP_201_CREATED)
def add_product(product: Product):
    new_id = max([p["id"] for p in products]) + 1 if products else 1
    new_product = product.dict()
    new_product["id"] = new_id
    products.append(new_product)
    return {"message": "Product added", "product": new_product}


# UPDATE Product
@app.put("/products/{product_id}")
def update_product(product_id: int, price: int):
    for product in products:
        if product["id"] == product_id:
            product["price"] = price
            return {"message": "Product updated", "product": product}
    raise HTTPException(status_code=404, detail="Product not found")


# DELETE Product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": f"Product '{product['name']}' deleted"}
    raise HTTPException(status_code=404, detail="Product not found")


# BONUS — Discount API
@app.get("/products/discount")
def discount_products(percent: int):
    discounted = []
    for product in products:
        new_price = int(product["price"] * (1 - percent / 100))
        discounted.append({
            "id": product["id"],
            "name": product["name"],
            "original_price": product["price"],
            "discounted_price": new_price
        })
    return {"discounted_products": discounted}


# Q5 — Audit API
@app.get("/products/audit")
def product_audit():
    total_products = len(products)
    in_stock_products = [p for p in products if p["in_stock"]]
    out_of_stock_products = [p["name"] for p in products if not p["in_stock"]]
    total_stock_value = sum(p["price"] for p in products)

    most_expensive = max(products, key=lambda x: x["price"]) if products else None

    return {
        "total_products": total_products,
        "in_stock_count": len(in_stock_products),
        "out_of_stock_names": out_of_stock_products,
        "total_stock_value": total_stock_value,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        } if most_expensive else None
    }