# BRIEF — cofre-senhas-aes256

Projeto: cofre local de senhas cifrado AES-256 (área: Cibersegurança).
Diretório de entrega: `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\cofre-senhas-aes256\`

## Entregas

| Arquivo | Conteúdo |
|---|---|
| `pyproject.toml` | Projeto Python (setuptools, src-layout), dependência `cryptography`, entry point `cofre-senhas` |
| `src/cofre_senhas_aes256/__init__.py` | Exporta `CofreSenhas`, `CofreError`, `Senha` |
| `src/cofre_senhas_aes256/cofre.py` | Camada de cifragem: PBKDF2-HMAC-SHA256 + AES-256-GCM, persistência em arquivo local |
| `src/cofre_senhas_aes256/gui.py` | Interface tkinter: criar/desbloquear/bloquear cofre, adicionar/atualizar/remover senhas, copiar senha |
| `src/cofre_senhas_aes256/__main__.py` | Ponto de entrada `python -m cofre_senhas_aes256` |
| `tests/test_cofre.py` | 20 testes da camada de cifragem (sem tkinter) |
| `README.md` | Documentação completa bilíngue PT-BR + EN |
| `BRIEF.md` | Este arquivo |

## Especificação implementada

- Chave derivada com PBKDF2-HMAC-SHA256 (SHA-256, 256 bits, 480_000 iterações padrão, salt de 16 bytes).
- Cifra de senhas em JSON com AES-256-GCM (nonce 12 bytes, tag 16 bytes).
- Arquivo local: `salt || nonce || ciphertext+tag`; qualquer adulteração é rejeitada (InvalidTag → `CofreError`).
- Desbloqueio valida senha mestra; arquivo ausente, corrompido ou com senha errada lançam `CofreError`.
- Campos de entrada vazios lançam `ValueError`.
- Determinístico: mesma entrada + mesmo nonce gera mesmo ciphertext (nonce aleatório por gravação).

## Como verificar

No diretório do projeto:

```powershell
uv run ruff check .
uv run pytest -q
```

Resultado obtido na validação:

- `ruff check .`: **All checks passed!**
- `pytest -q`: **20 passed in 0.61s**

Comando de teste usado: `uv run pytest -q` (equivalente a `python -m pytest -q`).

## Caminhos dos documentos

- README: `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\cofre-senhas-aes256\README.md`
- BRIEF: `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\cofre-senhas-aes256\BRIEF.md`
