import json

test = {
    "bool-key": True,
    "none-key": None

}

with open("parse-test.json", "w") as f:
    json.dump(test, f, sort_keys=True)
