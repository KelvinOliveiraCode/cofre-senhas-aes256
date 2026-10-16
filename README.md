# cofre-senhas-aes256

Cofre local de senhas cifrado com AES-256. Deriva a chave com PBKDF2-HMAC-SHA256 a partir de uma senha mestra e cifra um JSON de senhas com AES-256-GCM (biblioteca `cryptography`), tudo num único arquivo local.

## Descrição

O programa cadastra e acessa senhas protegidas por senha mestra. Toda entrada fica cifrada no disco; sem a senha mestra correta, o arquivo é ininteligível. AES-256-GCM autentica o conteúdo, então qualquer adulteração do arquivo é detectada ao abrir.

## Stack

- Python 3.10+
- `cryptography` (PBKDF2-HMAC-SHA256 + AES-256-GCM)
- `tkinter` (interface gráfica)

## Como usar

Instale o pacote em modo editável:

```
uv pip install -e .
```

ou

```
pip install -e .
```

Inicie a interface gráfica:

```
python -m cofre_senhas_aes256
```

Fluxo:

1. Primeira execução: informe uma senha mestra e clique em **Criar cofre**. Isso gera o arquivo `cofre-senhas-aes256.enc` no seu diretório de usuário.
2. Execuções seguintes: informe a mesma senha mestra e clique em **Desbloquear**.
3. Preencha Serviço, Usuário e Senha, depois clique em **Adicionar / Atualizar**.
4. Selecione uma entrada e clique em **Copiar senha** para copiá-la à área de transferência.
5. Clique em **Bloquear** para limpar a chave da memória.

### Camada de cifragem sem interface

```
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

Formato do arquivo: `salt (16 bytes) || nonce (12 bytes) || ciphertext + tag (AES-256-GCM)`. O payload cifrado é JSON com chaves ordenadas.

## Testes

```
uv run pytest -q
```

ou

```
python -m pytest -q
```

São 20 testes. Cobrem derivação de chave, cifra/decifra, persistência em arquivo, senha mestra incorreta, adulteração do arquivo (tag do GCM), entradas inexistentes, bloqueio e validação de campos. A interface tkinter não é coberta por teste (funciona sem display).

## Segurança

- Nunca commite o arquivo `.enc` com senhas reais num repositório.
- A senha mestra não fica armazenada em lugar nenhum: existe só na memória enquanto o cofre está desbloqueado.
- PBKDF2 com 480_000 iterações por padrão (ajustável pelo parâmetro `iteracoes`).
- AES-256-GCM detecta qualquer modificação do arquivo antes de devolver dados.

## Licença

MIT

## Autor

Kelvin Oliveira

---

# cofre-senhas-aes256

Local password vault encrypted with AES-256. Derives the key with PBKDF2-HMAC-SHA256 from a master password and encrypts a JSON of passwords with AES-256-GCM (library `cryptography`), all in a single local file.

## Description

The program registers and retrieves passwords protected by a master password. Every entry is encrypted on disk; without the correct master password, the file is unintelligible. AES-256-GCM authenticates the content, so any tampering with the file is detected on open.

## Stack

- Python 3.10+
- `cryptography` (PBKDF2-HMAC-SHA256 + AES-256-GCM)
- `tkinter` (GUI)

## How to use

Install the package in editable mode:

```
uv pip install -e .
```

or

```
pip install -e .
```

Start the graphical interface:

```
python -m cofre_senhas_aes256
```

Flow:

1. First run: enter a master password and click **Create vault**. This creates the file `cofre-senhas-aes256.enc` in your user directory.
2. Later runs: enter the same master password and click **Unlock**.
3. Fill in Service, User, and Password, then click **Add / Update**.
4. Select an entry and click **Copy password** to copy it to the clipboard.
5. Click **Lock** to clear the key from memory.

### Encryption layer without UI

```
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

File format: `salt (16 bytes) || nonce (12 bytes) || ciphertext + tag (AES-256-GCM)`. The encrypted payload is JSON with sorted keys.

## Tests

```
uv run pytest -q
```

or

```
python -m pytest -q
```

There are 20 tests. They cover key derivation, encrypt/decrypt, file persistence, wrong master password, file tampering (GCM tag), missing entries, lock, and field validation. The tkinter GUI is not covered by tests (works without a display).

## Security

- Never commit the `.enc` file with real passwords to a repository.
- The master password is never stored anywhere: it exists only in memory while the vault is unlocked.
- PBKDF2 with 480_000 iterations by default (adjustable via the `iteracoes` parameter).
- AES-256-GCM detects any file modification before returning data.

## License

MIT

## Author

Kelvin Oliveira
