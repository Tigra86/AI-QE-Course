db.users.drop();

db.users.insertMany([
  { first_name: "John", last_name: "Smith", phone: "415 234-5678", email: "john_smith@gmail.com" },
  { first_name: "Mike", last_name: "Loomis", phone: "408 875-5033", email: "mike_loomis@gmail.com" }
]);

print(EJSON.stringify(db.users.find({ first_name: "Mike" }).toArray(), null, 2));
