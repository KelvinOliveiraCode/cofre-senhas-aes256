# cofre-senhas-aes256

Cofre local de senhas cifrado com AES-256. Deriva a chave com PBKDF2-HMAC-SHA256 a partir de uma senha mestra e cifra um JSON de senhas com AES-256-GCM (biblioteca `cryptography`), tudo num único arquivo local.

## Sobre o projeto

O programa cadastra e acessa senhas protegidas por uma senha mestra. Toda entrada fica cifrada no disco; sem a senha mestra correta, o arquivo é ininteligível. AES-256-GCM autentica o conteúdo, então qualquer adulteração do arquivo é detectada ao abrir. Não há servidor nem nuvem: o cofre é um único arquivo local, no diretório do usuário por padrão (`cofre-senhas-aes256.enc`).

A senha mestra nunca é armazenada em disco: existe apenas na memória enquanto o cofre está desbloqueado. Se for perdida, não há como recuperar as senhas salvas.

## Stack

- Python 3.10+
- `cryptography` (PBKDF2-HMAC-SHA256 + AES-256-GCM)
- `tkinter` (interface gráfica)

## Instalação

Instale o pacote em modo editável:

```
uv pip install -e .
```

ou

```
pip install -e .
```

Após a instalação, o comando `cofre-senhas` também fica disponível.

## Uso

Inicie a interface gráfica:

```
python -m cofre_senhas_aes256
```

O programa segue este fluxo:

1. Primeira execução: informe uma senha mestra e clique em Criar cofre. Isso gera o arquivo `cofre-senhas-aes256.enc` no seu diretório de usuário.
2. Execuções seguintes: informe a mesma senha mestra e clique em Desbloquear.
3. Preencha Serviço, Usuário e Senha, depois clique em Adicionar / Atualizar.
4. Selecione uma entrada e clique em Copiar senha para copiá-la à área de transferência.
5. Clique em Bloquear para limpar a chave da memória.

O botão Criar cofre falha se o arquivo já existir, evitando sobrescrever um cofre existente por engano.

### Camada de cifragem sem interface

Use a classe `CofreSenhas` diretamente em Python:

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

### Formato do arquivo

`salt (16 bytes) || nonce (12 bytes) || ciphertext + tag (AES-256-GCM)`. O payload cifrado é JSON com chaves ordenadas. O nonce é aleatório a cada gravação, então o mesmo conteúdo gera cifrados diferentes em gravações distintas.

## Segurança

- Nunca commite o arquivo `.enc` com senhas reais num repositório.
- A senha mestra não fica armazenada em lugar nenhum: existe só na memória enquanto o cofre está desbloqueado.
- PBKDF2 com 480.000 iterações por padrão (ajustável pelo parâmetro `iteracoes`).
- AES-256-GCM detecta qualquer modificação do arquivo antes de devolver dados.
- Se a senha mestra for perdida, as senhas não podem ser recuperadas.

## Testes

```
uv run pytest -q
```

ou

```
python -m pytest -q
```

São 20 testes. Cobrem derivação de chave, cifra/decifra, persistência em arquivo, senha mestra incorreta, adulteração do arquivo (tag do GCM), entradas inexistentes, bloqueio e validação de campos. A interface tkinter não é coberta por teste.

## Licença

MIT

## Autor

Kelvin Oliveira
