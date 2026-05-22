from pprint import pprint
from pymongo import MongoClient

def reset_db(db) -> None:
    db.users.drop()
    db.products.drop()
    db.orders.drop()

def seed_data(db) -> None:
    db.users.insert_many([
        {"_id": 1, "name": "Alex", "age": 30, "city": "San Francisco"},
        {"_id": 2, "name": "Maria", "age": 25, "city": "New York"},
        {"_id": 3, "name": "John", "age": 35, "city": "Chicago"},
        {"_id": 4, "name": "Lisa", "age": 28, "city": "San Francisco"},
    ])

    db.products.insert_many([
        {"_id": 101, "name": "Laptop", "category": "Electronics", "price": 1200.0},
        {"_id": 102, "name": "Phone", "category": "Electronics", "price": 800.0},
        {"_id": 103, "name": "Shoes", "category": "Fashion", "price": 120.0},
        {"_id": 104, "name": "Backpack", "category": "Fashion", "price": 90.0},
    ])

    db.orders.insert_many([
        {"_id": 1001, "user_id": 1, "product_id": 101, "quantity": 1},
        {"_id": 1002, "user_id": 1, "product_id": 104, "quantity": 2},
        {"_id": 1003, "user_id": 2, "product_id": 102, "quantity": 1},
        {"_id": 1004, "user_id": 3, "product_id": 103, "quantity": 2},
        {"_id": 1005, "user_id": 4, "product_id": 104, "quantity": 1},
    ])

def print_title(title: str) -> None:
    print(f"\n=== {title} ===")

def main() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["demo_nosql"]

    reset_db(db)
    seed_data(db)

    print_title("1. All users age > 27")
    for doc in db.users.find(
        {"age": {"$gt": 27}},
        {"_id": 1, "name": 1, "age": 1, "city": 1}
    ).sort("_id", 1):
        pprint(doc)

    print_title("2. Product count by category")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    for doc in db.products.aggregate(pipeline):
        pprint(doc)

    print_title("3. Revenue by user")
    pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {
            "$group": {
                "_id": "$user_id",
                "revenue": {
                    "$sum": {"$multiply": ["$quantity", "$product.price"]}
                }
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "user_id": "$user._id",
                "name": "$user.name",
                "revenue": 1
            }
        },
        {"$sort": {"user_id": 1}},
    ]
    for doc in db.orders.aggregate(pipeline):
        pprint(doc)

    print_title("4. Order details with lookup")
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {
            "$project": {
                "_id": 0,
                "order_id": "$_id",
                "user_name": "$user.name",
                "product_name": "$product.name",
                "category": "$product.category",
                "quantity": 1,
                "price": "$product.price",
                "line_total": {"$multiply": ["$quantity", "$product.price"]}
            }
        },
        {"$sort": {"order_id": 1}},
    ]
    for doc in db.orders.aggregate(pipeline):
        pprint(doc)

    client.close()

if __name__ == "__main__":
    main()
