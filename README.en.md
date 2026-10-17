# cofre-senhas-aes256

Local password vault encrypted with AES-256. Derives the key with PBKDF2-HMAC-SHA256 from a master password and encrypts a JSON of passwords with AES-256-GCM (library `cryptography`), all in a single local file.

## About the project

The program registers and retrieves passwords protected by a master password. Every entry is encrypted on disk; without the correct master password, the file is unintelligible. AES-256-GCM authenticates the content, so any tampering with the file is detected on open. There is no server or cloud: the vault is a single local file, in the user's home directory by default (`cofre-senhas-aes256.enc`).

The master password is never stored on disk: it exists only in memory while the vault is unlocked. If it is lost, the saved passwords cannot be recovered.

## Stack

- Python 3.10+
- `cryptography` (PBKDF2-HMAC-SHA256 + AES-256-GCM)
- `tkinter` (GUI)

## Installation

Install the package in editable mode:

```
uv pip install -e .
```

or

```
pip install -e .
```

After installation, the `cofre-senhas` command is also available.

## Usage

Start the graphical interface:

```
python -m cofre_senhas_aes256
```

The program follows this flow:

1. First run: enter a master password and click Create vault. This creates the file `cofre-senhas-aes256.enc` in your user directory.
2. Later runs: enter the same master password and click Unlock.
3. Fill in Service, User, and Password, then click Add / Update.
4. Select an entry and click Copy password to copy it to the clipboard.
5. Click Lock to clear the key from memory.

The Create vault button fails if the file already exists, so an existing vault is not overwritten by mistake.

### Encryption layer without UI

Use the `CofreSenhas` class directly in Python:

```python
from pathlib import Path
from cofre_senhas_aes256 import CofreSenhas

cofre = CofreSenhas(Path("cofre.enc"), iteracoes=480_000)
cofre.criar("minha-senha-mestra")
cofre.adicionar("exemplo.com", "usuario", "senha-secreta")

cofre2 = CofreSenhas(Path("cofre.enc"), iteracoes=480_000)
cofre2.desbloquear("minha-senha-mestra")
print(cofre2.obter("exemplo.com", "usuario"))  # senha-secreta
cofre2.bloquear()
```

### File format

`salt (16 bytes) || nonce (12 bytes) || ciphertext + tag (AES-256-GCM)`. The encrypted payload is JSON with sorted keys. The nonce is random on each write, so the same content produces different ciphertexts across writes.

## Security

- Never commit the `.enc` file with real passwords to a repository.
- The master password is never stored anywhere: it exists only in memory while the vault is unlocked.
- PBKDF2 with 480,000 iterations by default (adjustable via the `iteracoes` parameter).
- AES-256-GCM detects any file modification before returning data.
- If the master password is lost, the passwords cannot be recovered.

## Tests

```
uv run pytest -q
```

or

```
python -m pytest -q
```

There are 20 tests. They cover key derivation, encrypt/decrypt, file persistence, wrong master password, file tampering (GCM tag), missing entries, lock, and field validation. The tkinter GUI is not covered by tests.

## License

MIT

## Author

Kelvin Oliveira
