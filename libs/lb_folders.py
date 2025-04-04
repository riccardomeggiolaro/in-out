import os

def save_bytes_to_file(file_bytes, filename, folder_path):
    """
    Salva dei bytes in un file all'interno della cartella specificata.
    
    Parametri:
    file_bytes (bytes): I bytes del file da salvare
    filename (str): Il nome del file da creare (inclusa l'estensione)
    folder_path (str): Il percorso della cartella dove salvare il file
    
    Returns:
    str: Il percorso completo del file salvato
    """

    # Crea la cartella di destinazione se non esiste
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Costruisci il percorso completo del file
    file_path = os.path.join(folder_path, filename)

    # Scrivi i bytes nel file
    with open(file_path, 'wb') as file:
        file.write(file_bytes)

    return file_path

def search_file(filename, folder_path, search_subfolders=True):
    """
    Cerca un file con il nome specificato all'interno della cartella indicata.
    
    Parametri:
    filename (str): Il nome del file da cercare
    folder_path (str): Il percorso della cartella in cui cercare
    search_subfolders (bool, opzionale): Se True, cerca anche nelle sottocartelle (default: True)
    
    Returns:
    list: Lista di percorsi completi dei file trovati (vuota se nessun file è stato trovato)
    """
    # Verifica che la cartella esista
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"La cartella '{folder_path}' non esiste")
    
    # Lista per contenere i percorsi dei file trovati
    found_files = []
    
    # Cerca in modo diverso a seconda se è richiesta la ricerca nelle sottocartelle
    if search_subfolders:
        # Cerca in tutte le sottocartelle
        for root, _, files in os.walk(folder_path):
            if filename in files:
                found_file_path = os.path.join(root, filename)
                found_files.append(found_file_path)
    else:
        # Cerca solo nella cartella principale
        files_in_folder = os.listdir(folder_path)
        for file in files_in_folder:
            if file == filename and os.path.isfile(os.path.join(folder_path, file)):
                found_file_path = os.path.join(folder_path, file)
                found_files.append(found_file_path)
    
    return found_files

def search_file_with_pattern(pattern, folder_path, search_subfolders=True):
    """
    Cerca file che corrispondono a un pattern all'interno della cartella indicata.
    
    Parametri:
    pattern (str): Il pattern da cercare (può contenere wildcard come * e ?)
    folder_path (str): Il percorso della cartella in cui cercare
    search_subfolders (bool, opzionale): Se True, cerca anche nelle sottocartelle (default: True)
    
    Returns:
    list: Lista di percorsi completi dei file trovati (vuota se nessun file è stato trovato)
    """
    import fnmatch
    
    # Verifica che la cartella esista
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"La cartella '{folder_path}' non esiste")
    
    # Lista per contenere i percorsi dei file trovati
    found_files = []
    
    # Cerca in modo diverso a seconda se è richiesta la ricerca nelle sottocartelle
    if search_subfolders:
        # Cerca in tutte le sottocartelle
        for root, _, files in os.walk(folder_path):
            for filename in fnmatch.filter(files, pattern):
                found_file_path = os.path.join(root, filename)
                found_files.append(found_file_path)
    else:
        # Cerca solo nella cartella principale
        files_in_folder = os.listdir(folder_path)
        for file in files_in_folder:
            if fnmatch.fnmatch(file, pattern) and os.path.isfile(os.path.join(folder_path, file)):
                found_file_path = os.path.join(folder_path, file)
                found_files.append(found_file_path)
    
    return found_files