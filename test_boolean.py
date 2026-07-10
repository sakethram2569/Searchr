import pickle
from boolean_query import intersect, union, subtract, multi_and

with open("index.pkl", "rb") as f:
    data = pickle.load(f)
inverted_index = data["inverted_index"]

oil = inverted_index.get("oil", [])
price = inverted_index.get("price", [])
rise = inverted_index.get("rise", [])

and_result = intersect(oil, price)
or_result = union(oil, price)
not_result = subtract(oil, price)

print(f"'oil' postings: {len(oil)}")
print(f"'price' postings: {len(price)}")
print(f"'oil' AND 'price': {len(and_result)}")
print(f"'oil' OR 'price': {len(or_result)}")
print(f"'oil' NOT 'price': {len(not_result)}")

and_ids = {p["doc_id"] for p in and_result}
oil_ids = {p["doc_id"] for p in oil}
price_ids = {p["doc_id"] for p in price}
assert and_ids == (oil_ids & price_ids), "AND result mismatch!"
assert {p["doc_id"] for p in or_result} == (oil_ids | price_ids), "OR result mismatch!"
assert {p["doc_id"] for p in not_result} == (oil_ids - price_ids), "NOT result mismatch!"
print("\nAll set-equivalence checks passed (AND=intersection, OR=union, NOT=difference)")

triple_and = multi_and([oil, price, rise])
print(f"\n'oil' AND 'price' AND 'rise': {len(triple_and)} docs")