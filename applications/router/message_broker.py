from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from applications.middleware.super_admin import is_super_admin
import libs.lb_config as lb_config
from modules.md_message_broker.dto import MessageBrokerDTO
import modules.md_message_broker.md_message_broker as md_message_broker

MAX_CERT_SIZE = 256 * 1024


class MessageBrokerRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('', self.getMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.setMessageBroker, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.deleteMessageBroker, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/test', self.testMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/retry-failed', self.retryFailed, methods=['POST'], dependencies=[Depends(is_super_admin)])

    def _response(self):
        module = md_message_broker.module_message_broker
        settings = md_message_broker.get_settings()
        broker = settings.get("broker")
        if broker:
            # La password non viene mai restituita
            broker = {k: v for k, v in broker.items() if k != "password"}
            broker["has_password"] = bool(settings["broker"].get("password"))
        return {
            "broker": broker,
            "client_id": module.client_id,
            "topic": module.client_id,
            "certificates": module.get_certificates_info(),
        }

    async def getMessageBroker(self):
        return self._response()

    async def setMessageBroker(
        self,
        host: str = Form(...),
        port: int = Form(8883),
        username: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
        remove_ca: bool = Form(False),
        remove_client_cert: bool = Form(False),
        include_images: bool = Form(True),
        include_pdf: bool = Form(True),
        include_csv: bool = Form(True),
        ca_file: Optional[UploadFile] = File(None),
        cert_file: Optional[UploadFile] = File(None),
        key_file: Optional[UploadFile] = File(None),
    ):
        # Password vuota/non inviata = mantiene quella già salvata (se l'utente non cambia)
        current = md_message_broker.get_settings().get("broker") or {}
        username = (username or "").strip() or None
        if not password and username and username == current.get("username"):
            password = current.get("password")
        if not username:
            password = None
        try:
            body = MessageBrokerDTO(
                host=host, port=port, username=username, password=password or None,
                include_images=include_images, include_pdf=include_pdf, include_csv=include_csv,
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.errors()[0]["msg"].replace("Value error, ", ""))

        # File TLS: quelli non caricati restano quelli già installati
        files = {}
        for kind, upload in (("ca", ca_file), ("cert", cert_file), ("key", key_file)):
            if upload is not None and upload.filename:
                content = await upload.read(MAX_CERT_SIZE + 1)
                if len(content) > MAX_CERT_SIZE:
                    raise HTTPException(status_code=400, detail=f"File {upload.filename} troppo grande")
                files[kind] = content

        module = md_message_broker.module_message_broker
        will_have_client_cert = bool(files.get("cert")) or (module.has_client_certificate() and not remove_client_cert)
        if not body.username and not will_have_client_cert:
            raise HTTPException(status_code=400, detail="Imposta username e password oppure carica certificato e chiave client")
        try:
            await run_in_threadpool(module.install_certificates, files, remove_ca, remove_client_cert)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        connected = await run_in_threadpool(module.set_config, body)
        md_message_broker.get_settings()["broker"] = body.model_dump()
        lb_config.saveconfig()
        return {
            **self._response(),
            "connected": connected,
            "status": module.get_status(),
        }

    async def deleteMessageBroker(self):
        await run_in_threadpool(md_message_broker.module_message_broker.set_config, None)
        md_message_broker.get_settings()["broker"] = None
        lb_config.saveconfig()
        return {"deleted": True}

    async def testMessageBroker(self):
        return md_message_broker.module_message_broker.get_status()

    async def retryFailed(self):
        count = md_message_broker.module_message_broker.retry_failed()
        return {"requeued": count}
