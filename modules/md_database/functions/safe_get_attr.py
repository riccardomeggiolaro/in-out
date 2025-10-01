from sqlalchemy import inspect as sa_inspect

# Funzione helper per accedere agli attributi in modo sicuro
def safe_get_attr(obj, attr, default=None):
    try:
        if obj is None:
            return default
        # Verifica se l'attributo è stato caricato
        state = sa_inspect(obj)
        if attr in state.unloaded:
            return default
        return getattr(obj, attr, default)
    except:
        return default