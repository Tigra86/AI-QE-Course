import json

json_array = 
[
	{"name": "John", "age": 22},
	{"name": "Mike", "age": 24},
	{"name": "Nik", "age": 26}
]

obj = json.loads(json_array)
print(obj) 	# [{'name': 'John', 'age': 22}, {'name': 'Mike', 'age': 24}, {'name': 'Nik', 'age': 26}]
for person in obj:
  print(person["name"], person["age"]) # prints: John, Mike, Nik and 22, 24, 26