import json

with open("drop.txt") as drop_list_file:
    drop_list_str = drop_list_file.read()

drop_list = [line.split(";")[0].strip() for line in drop_list_str.split("\n")]
drop_dict = {ip_range: 10000 for ip_range in drop_list if ip_range != ""}

with open("data/BlackListFilter.json", "w") as blf_data_file:
    json.dump(drop_dict, blf_data_file, sort_keys=True)
