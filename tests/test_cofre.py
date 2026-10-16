"""Testes da camada de cifragem do cofre (sem tkinter).

Executa so contra :mod:`cofre_senhas_aes256.cofre`: deriva de chave,
cifra/decifra AES-256-GCM, persistencia em arquivo local e validacoes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cofre_senhas_aes256.cofre import CofreError, CofreSenhas, Senha

ITERACOES_TESTES = 10_000


@pytest.fixture
def caminho_cofre(tmp_path: Path) -> Path:
    """Caminho de arquivo de cofre num diretorio temporario."""
    return tmp_path / "cofre.enc"


def _cofre_criado(caminho: Path, senha_mestra: str = "mestra-123") -> CofreSenhas:
    """Cria um cofre vazio e o deixa desbloqueado (apenas nos testes)."""
    cofre = CofreSenhas(caminho, iteracoes=ITERACOES_TESTES)
    cofre.criar(senha_mestra)
    return cofre


# ------------------------------------------------------------------- chave

def test_derivar_chave_retorna_32_bytes() -> None:
    chave = CofreSenhas.derivar_chave("senha", b"saltfixo12345678", 10_000)
    assert isinstance(chave, bytes)
    assert len(chave) == 32


def test_derivar_chave_eh_determinista() -> None:
    mesma = CofreSenhas.derivar_chave("senha", b"saltfixo12345678", 10_000)
    outra = CofreSenhas.derivar_chave("senha", b"saltfixo12345678", 10_000)
    assert mesma == outra


def test_derivar_chave_senhas_diferentes_geram_chaves_diferentes() -> None:
    chave_a = CofreSenhas.derivar_chave("senha-a", b"saltfixo12345678", 10_000)
    chave_b = CofreSenhas.derivar_chave("senha-b", b"saltfixo12345678", 10_000)
    assert chave_a != chave_b


def test_derivar_chave_senha_vazia_rejeita() -> None:
    with pytest.raises(ValueError, match="Senha mestra nao pode ser vazia"):
        CofreSenhas.derivar_chave("", b"saltfixo12345678", 10_000)


# ----------------------------------------------------- ciclo de vida / arquivo

def test_criar_desbloquear_obter_roundtrip(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("exemplo.com", "usuario", "senha-secreta")
    cofre.adicionar("outro.com", "admin", "outra-senha")

    # Nova instancia lendo o mesmo arquivo: prova persistencia local.
    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    cofre2.desbloquear("mestra-123")
    assert cofre2.obter("exemplo.com", "usuario") == "senha-secreta"
    assert cofre2.obter("outro.com", "admin") == "outra-senha"


def test_adicionar_atualiza_mesma_entrada(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("servico", "usuario", "senha-1")
    cofre.adicionar("servico", "usuario", "senha-2")

    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    cofre2.desbloquear("mestra-123")
    assert cofre2.obter("servico", "usuario") == "senha-2"
    assert cofre2.listar_servicos() == ["servico"]


def test_listar_servicos_ordenado_sem_duplicatas(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("zebra.com", "u", "s")
    cofre.adicionar("alpha.com", "u", "s")
    cofre.adicionar("zebra.com", "outro", "s")

    assert cofre.listar_servicos() == ["alpha.com", "zebra.com"]


def test_listar_entradas_ordenadas(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("b.com", "usuario", "senha-b")
    cofre.adicionar("a.com", "usuario", "senha-a")

    entradas = cofre.listar_entradas()
    assert isinstance(entradas[0], Senha)
    assert [e.servico for e in entradas] == ["a.com", "b.com"]


def test_senha_mestra_errada_erro(caminho_cofre: Path) -> None:
    _cofre_criado(caminho_cofre)

    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    with pytest.raises(CofreError, match="Senha mestra incorreta"):
        cofre2.desbloquear("senha-errada")


def test_arquivo_adulterado_erro(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("x", "y", "z")

    dados = bytearray(caminho_cofre.read_bytes())
    dados[-1] ^= 0xFF  # corrompe o tag de autenticacao do GCM
    caminho_cofre.write_bytes(bytes(dados))

    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    with pytest.raises(CofreError):
        cofre2.desbloquear("mestra-123")


def test_arquivo_nao_existente_erro(tmp_path: Path) -> None:
    cofre = CofreSenhas(tmp_path / "naoexiste.enc", iteracoes=ITERACOES_TESTES)
    with pytest.raises(CofreError, match="nao encontrado"):
        cofre.desbloquear("qualquer")


def test_obter_senha_inexistente_erro(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    with pytest.raises(CofreError, match="nao encontrada"):
        cofre.obter("naoexiste", "qualquer")


def test_remover_senha(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("servico", "usuario", "senha")
    cofre.remover("servico", "usuario")

    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    cofre2.desbloquear("mestra-123")
    assert cofre2.listar_servicos() == []


def test_bloquear_impede_acesso(caminho_cofre: Path) -> None:
    cofre = _cofre_criado(caminho_cofre)
    cofre.adicionar("servico", "usuario", "senha")
    cofre.bloquear()

    assert not cofre.esta_desbloqueado()
    with pytest.raises(CofreError, match="bloqueado"):
        cofre.obter("servico", "usuario")
    with pytest.raises(CofreError, match="bloqueado"):
        cofre.adicionar("x", "y", "z")


# ------------------------------------------------------------- validacoes

@pytest.mark.parametrize(
    "servico,usuario,senha",
    [
        ("", "usuario", "senha"),
        ("servico", "", "senha"),
        ("servico", "usuario", ""),
        ("   ", "usuario", "senha"),
        ("servico", "   ", "senha"),
    ],
)
def test_adicionar_campos_vazios_rejeitados(
    caminho_cofre: Path, servico: str, usuario: str, senha: str
) -> None:
    cofre = _cofre_criado(caminho_cofre)
    with pytest.raises(ValueError):
        cofre.adicionar(servico, usuario, senha)


def test_criar_cofre_ja_existente_rejeita(caminho_cofre: Path) -> None:
    _cofre_criado(caminho_cofre)
    cofre2 = CofreSenhas(caminho_cofre, iteracoes=ITERACOES_TESTES)
    with pytest.raises(CofreError, match="ja existe"):
        cofre2.criar("outra-senha")
