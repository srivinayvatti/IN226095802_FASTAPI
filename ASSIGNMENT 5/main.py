from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FastAPI Day 6 — Search, Sort & Pagination")

# ─────────────────────────────────────────────
# In-memory data
# ─────────────────────────────────────────────

products = [
    {"product_id": 1, "name": "Wireless Mouse",  "price": 499,  "category": "Electronics"},
    {"product_id": 2, "name": "USB Hub",          "price": 799,  "category": "Electronics"},
    {"product_id": 3, "name": "Notebook",         "price": 99,   "category": "Stationery"},
    {"product_id": 4, "name": "Pen Set",          "price": 49,   "category": "Stationery"},
]

orders = []
order_id_counter = {"value": 1}


# ─────────────────────────────────────────────
# Pydantic model for Order
# ─────────────────────────────────────────────

class OrderRequest(BaseModel):
    customer_name: str
    product_id: int
    quantity: int


# ─────────────────────────────────────────────
# POST /orders  (helper to seed order data)
# ─────────────────────────────────────────────

@app.post("/orders", tags=["Orders"])
def place_order(order: OrderRequest):
    product = next((p for p in products if p["product_id"] == order.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {order.product_id} not found")

    new_order = {
        "order_id":      order_id_counter["value"],
        "customer_name": order.customer_name,
        "product_id":    order.product_id,
        "product_name":  product["name"],
        "quantity":      order.quantity,
        "total_price":   product["price"] * order.quantity,
    }
    orders.append(new_order)
    order_id_counter["value"] += 1
    return {"message": "Order placed successfully", "order": new_order}


# ─────────────────────────────────────────────
# Q1 — GET /products/search  (case-insensitive keyword search)
# ─────────────────────────────────────────────

@app.get("/products/search", tags=["Q1 - Search Products"])
def search_products(keyword: str = Query(..., description="Keyword to search in product names")):
    """
    Q1: Search products by keyword (case-insensitive).
    Test URLs:
      /products/search?keyword=mouse   → Wireless Mouse, total_found: 1
      /products/search?keyword=MOUSE   → same result (case-insensitive)
      /products/search?keyword=e       → 3 products contain 'e'
      /products/search?keyword=laptop  → no-results friendly message
    """
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {
        "keyword":     keyword,
        "total_found": len(results),
        "products":    results,
    }


# ─────────────────────────────────────────────
# Q2 — GET /products/sort  (sort by field + order)
# ─────────────────────────────────────────────

VALID_SORT_FIELDS = ["price", "name"]

@app.get("/products/sort", tags=["Q2 - Sort Products"])
def sort_products(
    sort_by: str = Query("price", description="Field to sort by: 'price' or 'name'"),
    order:   str = Query("asc",   description="Sort direction: 'asc' or 'desc'"),
):
    """
    Q2: Sort products by price or name, ascending or descending.
    Test URLs:
      /products/sort?sort_by=price&order=asc
      /products/sort?sort_by=price&order=desc
      /products/sort?sort_by=name&order=asc
      /products/sort?sort_by=name&order=desc
      /products/sort?sort_by=category  → error message
    """
    if sort_by not in VALID_SORT_FIELDS:
        return {"error": f"Invalid sort_by '{sort_by}'. Allowed values: {VALID_SORT_FIELDS}"}

    reverse = (order == "desc")
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    return {
        "sort_by":  sort_by,
        "order":    order,
        "products": sorted_products,
    }


# ─────────────────────────────────────────────
# Q3 — GET /products/page  (pagination)
# ─────────────────────────────────────────────

@app.get("/products/page", tags=["Q3 - Paginate Products"])
def get_products_paged(
    page:  int = Query(1, ge=1,  description="Page number (starts at 1)"),
    limit: int = Query(2, ge=1, le=20, description="Items per page"),
):
    """
    Q3: Paginate the products list.
    Test URLs:
      /products/page?page=1&limit=2   → products 1-2
      /products/page?page=2&limit=2   → products 3-4
      /products/page?page=3&limit=2   → empty (no products on page 3)
      /products/page?page=1&limit=1   → total_pages should be 4
    """
    total = len(products)
    start = (page - 1) * limit
    paged = products[start: start + limit]

    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": -(-total // limit),   # ceiling division
        "products":    paged,
    }


# ─────────────────────────────────────────────
# Q4 — GET /orders/search  (search orders by customer name)
# ─────────────────────────────────────────────

@app.get("/orders/search", tags=["Q4 - Search Orders"])
def search_orders(
    customer_name: str = Query(..., description="Customer name keyword to search")
):
    """
    Q4: Search all orders by customer name (case-insensitive, partial match).
    First POST a few orders, then:
      /orders/search?customer_name=rahul  → returns all orders with 'rahul' in customer_name
      /orders/search?customer_name=xyz    → friendly no-results message
    """
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {
        "customer_name": customer_name,
        "total_found":   len(results),
        "orders":        results,
    }


# ─────────────────────────────────────────────
# Q5 — GET /products/sort-by-category  (multi-key sort)
# ─────────────────────────────────────────────

@app.get("/products/sort-by-category", tags=["Q5 - Sort by Category"])
def sort_by_category():
    """
    Q5: Sort products first by category (A→Z), then by price (cheapest first) within each category.
    Expected order:
      Electronics → Wireless Mouse (₹499), USB Hub (₹799)
      Stationery  → Pen Set (₹49),  Notebook (₹99)
    """
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {
        "sort":     "category asc, price asc",
        "total":    len(result),
        "products": result,
    }


# ─────────────────────────────────────────────
# Q6 — GET /products/browse  (search + sort + paginate combined)
# ─────────────────────────────────────────────

@app.get("/products/browse", tags=["Q6 - Browse (Search+Sort+Page)"])
def browse_products(
    keyword: str = Query(None,    description="Optional keyword filter on product name"),
    sort_by: str = Query("price", description="Sort field: 'price' or 'name'"),
    order:   str = Query("asc",   description="Sort direction: 'asc' or 'desc'"),
    page:    int = Query(1, ge=1, description="Page number"),
    limit:   int = Query(4, ge=1, le=20, description="Items per page"),
):
    """
    Q6: Search + Sort + Paginate in one endpoint.
    Pipeline order: filter → sort → paginate.

    Test URLs:
      /products/browse                                              → all 4, price asc, page 1
      /products/browse?keyword=e&sort_by=price&order=asc&page=1&limit=2
      /products/browse?sort_by=name&order=desc&page=1&limit=2
    """
    # Step 1: Filter by keyword
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Step 2: Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Step 3: Paginate
    total = len(result)
    start = (page - 1) * limit
    paged = result[start: start + limit]

    return {
        "keyword":     keyword,
        "sort_by":     sort_by,
        "order":       order,
        "page":        page,
        "limit":       limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products":    paged,
    }


# ─────────────────────────────────────────────
# BONUS — GET /orders/page  (paginate orders)
# ─────────────────────────────────────────────

@app.get("/orders/page", tags=["Bonus - Paginate Orders"])
def get_orders_paged(
    page:  int = Query(1, ge=1,  description="Page number"),
    limit: int = Query(3, ge=1, le=20, description="Orders per page"),
):
    """
    Bonus: Paginate the orders list.
    First POST 5+ orders, then:
      /orders/page?page=1&limit=3  → orders 1-3
      /orders/page?page=2&limit=3  → orders 4-5 (and so on)
    """
    total = len(orders)
    start = (page - 1) * limit
    paged = orders[start: start + limit]

    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": -(-total // limit) if total > 0 else 0,
        "orders":      paged,
    }


# ─────────────────────────────────────────────
# GET /products/{product_id}  (existing helper)
# ─────────────────────────────────────────────

@app.get("/products/{product_id}", tags=["Products"])
def get_product(product_id: int):
    product = next((p for p in products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


# ─────────────────────────────────────────────
# GET /products  (list all)
# ─────────────────────────────────────────────

@app.get("/products", tags=["Products"])
def list_products():
    return {"total": len(products), "products": products}


# ─────────────────────────────────────────────
# GET /orders  (list all)
# ─────────────────────────────────────────────

@app.get("/orders", tags=["Orders"])
def list_orders():
    return {"total": len(orders), "orders": orders}
