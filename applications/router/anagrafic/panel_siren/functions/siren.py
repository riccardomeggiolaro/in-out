import httpx

async def send_message(ip, port, username, password, timeout, endpoint):
    # Richiesta HTTP asincrona con autenticazione digest
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                endpoint,
                auth=httpx.DigestAuth(username, password)
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ConnectionError(f"Errore HTTP da {ip}:{port} - {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise ConnectionError(f"Errore di richiesta HTTP a {ip}:{port}: {e}")
    except Exception as e:
        raise ConnectionError(f"Errore sconosciuto durante la richiesta a {ip}:{port}: {e}")