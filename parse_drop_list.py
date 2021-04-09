import json

with open("drop.txt") as drop_list_file:
    drop_list_str = drop_list_file.read()

drop_list = [line.split(";")[0].strip() for line in drop_list_str.split("\n") if line.split(";")[0].strip() != "" ]

to_parse = {
    "ip_ranges": drop_list,
    "ip_addresses": {}
}

with open("data/BlackListFilter.json", "w") as blf_data_file:
    json.dump(to_parse, blf_data_file, sort_keys=True)
