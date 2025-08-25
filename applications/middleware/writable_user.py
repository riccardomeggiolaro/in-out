from fastapi import HTTPException, status, Request
from applications.utils.utils_auth import is_writable_user as is_writable_level

async def is_writable_user(request: Request):
    # Verifica se l'utente ha il livello admin
    if hasattr(request.state, 'user') and request.state.user.level in is_writable_level:
        return True

    # Se non è un admin, solleva un'eccezione HTTPException per restituire errore
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not authorized to perform this action, you are not an writable user"
    )