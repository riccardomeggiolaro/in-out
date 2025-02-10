oggetti = [
    {"1": "valore1"},
    {"2": "valore2"},
    {"3": "valore3"}
]

numeri_successivi = []

for oggetto in oggetti:
    for chiave in oggetto:
        numero = int(chiave)  # Converte la chiave in intero
        numero_successivo = str(numero + 1)  # Aggiunge 1 e converte di nuovo in stringa
        numeri_successivi.append(numero_successivo)

print(numeri_successivi)