def update_list(i, lst):
    name, status = i["name"], i["status"]
    found = False

    for item in lst:
        if name in item:
            item[name] = status
            found = True
            break

    if not found:
        lst.append({name: status})

# Esempio di utilizzo
i = {
    "name": "1s",
    "status": 1
}

lst = [
    {"1": 0},
    {"2": 0},
    {"3": 0}
]

update_list(i, lst)
print(lst)  # La lista verrà aggiornata correttamente
