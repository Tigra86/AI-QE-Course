import json

json_single = 
   {"name": "John", "age": 22}

obj = json.loads(json_single)
print(obj)          				# prints entire flat dict: {'name': 'John', 'age': 22}
print(obj["name"])      		    # prints: John
print(obj["age"])       			# prints: 22