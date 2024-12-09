from fastapi import Request, HTTPException, status
from applications.utils.utils_auth import is_super_admin as is_super_admin_level

async def is_super_admin(request: Request):
    # Verifica se l'utente ha il livello admin
    if hasattr(request.state, 'user') and request.state.user.level in is_super_admin_level:
        return True

    # Se non è un admin, solleva un'eccezione HTTPException per restituire errore
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not authorized to perform this action, you are not a super admin"
    )