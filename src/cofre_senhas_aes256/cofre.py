"""Camada de cifragem do cofre de senhas.

Deriva a chave com PBKDF2-HMAC-SHA256 a partir da senha mestra e cifra um
JSON de senhas com AES-256-GCM (biblioteca ``cryptography``), persistindo
tudo num unico arquivo local.

Formato do arquivo (binario):
    salt (16 bytes) || nonce (12 bytes) || ciphertext + tag (AES-256-GCM)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_LENGTH = 16
NONCE_LENGTH = 12
TAG_LENGTH = 16
KEY_LENGTH = 32
DEFAULT_ITERATIONS = 480_000


class CofreError(Exception):
    """Erro de operacao do cofre (senha errada, arquivo corrompido, cofre bloqueado, etc.)."""


@dataclass
class Senha:
    """Uma entrada de senha armazenada no cofre."""

    servico: str
    usuario: str
    senha: str


class CofreSenhas:
    """Cofre local cifrado com AES-256-GCM.

    Parametros:
        caminho_arquivo: caminho do arquivo local onde o cofre persiste.
        iteracoes: numero de iteracoes do PBKDF2 (padrao 480_000).
    """

    def __init__(self, caminho_arquivo: str | Path, iteracoes: int = DEFAULT_ITERATIONS) -> None:
        self.caminho_arquivo = Path(caminho_arquivo)
        self.iteracoes = iteracoes
        self._chave: bytes | None = None
        self._salt: bytes | None = None
        self._senhas: dict[tuple[str, str], Senha] = {}
        self._desbloqueado = False

    # ------------------------------------------------------------------ chave

    @staticmethod
    def derivar_chave(
        senha_mestra: str, salt: bytes, iteracoes: int = DEFAULT_ITERATIONS
    ) -> bytes:
        """Deriva uma chave de 256 bits com PBKDF2-HMAC-SHA256."""
        if not senha_mestra:
            raise ValueError("Senha mestra nao pode ser vazia.")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=iteracoes,
        )
        return kdf.derive(senha_mestra.encode("utf-8"))

    # ------------------------------------------------- cifragem / decifragem

    @staticmethod
    def _cifrar(dados: dict[str, Any], chave: bytes) -> bytes:
        """Cifra dados JSON com AES-256-GCM. Retorna nonce + ciphertext + tag."""
        aesgcm = AESGCM(chave)
        nonce = os.urandom(NONCE_LENGTH)
        payload = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return nonce + aesgcm.encrypt(nonce, payload, None)

    @staticmethod
    def _decifrar(blob: bytes, chave: bytes) -> dict[str, Any]:
        """Decifra blob (nonce + ciphertext + tag) e valida o JSON."""
        if len(blob) < NONCE_LENGTH + TAG_LENGTH:
            raise CofreError(
                "Arquivo do cofre muito curto para conter dados cifrados."
            )
        aesgcm = AESGCM(chave)
        nonce = blob[:NONCE_LENGTH]
        cifrado = blob[NONCE_LENGTH:]
        try:
            payload = aesgcm.decrypt(nonce, cifrado, None)
        except InvalidTag as exc:
            raise CofreError(
                "Senha mestra incorreta ou arquivo adulterado."
            ) from exc
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CofreError("Conteudo decifrado nao e JSON valido.") from exc

    # ------------------------------------------------------- ciclo de vida

    def criar(self, senha_mestra: str) -> None:
        """Cria um cofre vazio cifrado pela senha mestra."""
        if self.caminho_arquivo.exists():
            raise CofreError(f"Cofre ja existe: {self.caminho_arquivo}")
        salt = os.urandom(SALT_LENGTH)
        chave = self.derivar_chave(senha_mestra, salt, self.iteracoes)
        dados = {"senhas": []}
        blob = salt + self._cifrar(dados, chave)
        self.caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_arquivo.write_bytes(blob)
        self._salt = salt
        self._chave = chave
        self._senhas = {}
        self._desbloqueado = True

    def desbloquear(self, senha_mestra: str) -> None:
        """Le o arquivo, deriva a chave e decifra/valida o conteudo."""
        if not self.caminho_arquivo.is_file():
            raise CofreError(
                f"Arquivo do cofre nao encontrado: {self.caminho_arquivo}"
            )
        blob = self.caminho_arquivo.read_bytes()
        if len(blob) < SALT_LENGTH:
            raise CofreError("Arquivo do cofre esta corrompido (sem salt).")
        salt = blob[:SALT_LENGTH]
        chave = self.derivar_chave(senha_mestra, salt, self.iteracoes)
        dados = self._decifrar(blob[SALT_LENGTH:], chave)
        self._salt = salt
        self._chave = chave
        self._senhas = {
            (item["servico"], item["usuario"]): Senha(**item)
            for item in dados.get("senhas", [])
        }
        self._desbloqueado = True

    def bloquear(self) -> None:
        """Limpa a chave em memoria e as senhas decifradas."""
        self._chave = None
        self._salt = None
        self._senhas = {}
        self._desbloqueado = False

    def esta_desbloqueado(self) -> bool:
        """Retorna True se o cofre esta desbloqueado em memoria."""
        return self._desbloqueado

    def _exigir_desbloqueado(self) -> None:
        if not self._desbloqueado:
            raise CofreError("Cofre bloqueado. Desbloqueie com a senha mestra.")

    def _exigir_campos(self, servico: str, usuario: str, senha: str) -> None:
        for nome, valor in (("servico", servico), ("usuario", usuario), ("senha", senha)):
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"Campo '{nome}' nao pode ser vazio.")

    # ------------------------------------------------------------- operacoes

    def adicionar(self, servico: str, usuario: str, senha: str) -> None:
        """Adiciona (ou atualiza) uma entrada e persiste o cofre cifrado."""
        self._exigir_desbloqueado()
        assert self._chave is not None and self._salt is not None
        self._exigir_campos(servico, usuario, senha)
        entrada = Senha(servico=servico.strip(), usuario=usuario.strip(), senha=senha)
        self._senhas[(entrada.servico, entrada.usuario)] = entrada
        self._salvar()

    def obter(self, servico: str, usuario: str) -> str:
        """Retorna a senha de uma entrada existente."""
        self._exigir_desbloqueado()
        chave = (servico.strip(), usuario.strip())
        if chave not in self._senhas:
            raise CofreError(f"Senha nao encontrada para {servico}/{usuario}.")
        return self._senhas[chave].senha

    def remover(self, servico: str, usuario: str) -> None:
        """Remove uma entrada e persiste o cofre cifrado."""
        self._exigir_desbloqueado()
        assert self._chave is not None and self._salt is not None
        chave = (servico.strip(), usuario.strip())
        if chave not in self._senhas:
            raise CofreError(f"Senha nao encontrada para {servico}/{usuario}.")
        del self._senhas[chave]
        self._salvar()

    def listar_servicos(self) -> list[str]:
        """Retorna nomes de servicos cadastrados, em ordem alfabetica."""
        self._exigir_desbloqueado()
        return sorted({servico for servico, _ in self._senhas})

    def listar_entradas(self) -> list[Senha]:
        """Retorna todas as entradas cadastradas."""
        self._exigir_desbloqueado()
        return sorted(self._senhas.values(), key=lambda e: (e.servico, e.usuario))

    # ----------------------------------------------------------- persistencia

    def _salvar(self) -> None:
        """Reescreve o arquivo local com as senhas decifradas (novo nonce)."""
        assert self._chave is not None and self._salt is not None
        dados = {"senhas": [vars(entrada) for entrada in self._senhas.values()]}
        blob = self._salt + self._cifrar(dados, self._chave)
        self.caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_arquivo.write_bytes(blob)
