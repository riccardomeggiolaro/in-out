from applications.utils.web_socket import ConnectionManager

manager_anagrafics = {
    "subject": ConnectionManager(),
    "vector": ConnectionManager(),
    "driver": ConnectionManager(),
    "vehicle": ConnectionManager(),
    "material": ConnectionManager(),
    "reservation": ConnectionManager()
}