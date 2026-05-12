import json

json_double = 
	{"user": {"name": "John", "age": 22}}

obj = json.loads(json_double)
print(obj)          				# prints entire nested dict: {'user': {'name': 'John', 'age': 22}}
print(obj["user"]["name"])  	    # prints: John
print(obj["user"]["age"])   		# prints: 22