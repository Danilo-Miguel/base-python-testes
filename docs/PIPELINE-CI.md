# Pipeline de testes automatizados — Burguer App

Arquivo do pipeline: [`.github/workflows/ci-test-main.yml`](../.github/workflows/ci-test-main.yml)
Branch alvo: **`test-main`**

O pipeline roda no **GitHub Actions**: a cada `push` o GitHub cria uma máquina Linux
limpa, baixa o código, instala tudo e executa os testes. Se algo quebrar, o commit fica
com um ❌ vermelho; se tudo passar, fica com um ✅ verde.

```
 push na test-main
        │
        ├──► 1 · Smoke (sobe cada serviço) ──┐   (4 jobs em paralelo)
        │                                    ├──► 3 · Testes unitários ──► 4 · Selenium (E2E)
        └──► 2 · Lint (flake8) ──────────────┘       (6 jobs: 2 serviços × 3 Pythons)
```

---

## Passo 0 — Conceitos rápidos

| Termo | O que é |
|---|---|
| **Workflow** | O arquivo `.yml` dentro de `.github/workflows/`. Cada arquivo é um pipeline. |
| **Trigger (`on:`)** | O evento que dispara o pipeline (push, pull request, manual, horário...). |
| **Job** | Um bloco de trabalho que roda em **uma máquina virtual própria**. Jobs rodam em paralelo, a menos que você use `needs:`. |
| **Step** | Um passo dentro do job: um comando (`run:`) ou uma ação pronta (`uses:`). |
| **Runner** | A máquina que executa (`runs-on: ubuntu-latest`). |
| **Matrix** | Repete o mesmo job variando parâmetros (serviço, versão do Python...). |
| **Service container** | Um container Docker rodando ao lado do job (usamos para o **MongoDB**). |
| **Artifact** | Arquivo gerado pelo job que fica disponível para download (relatórios). |

---

## Passo 1 — O pipeline mínimo ("será que roda?")

Antes de qualquer teste, prove que o GitHub Actions executa seu arquivo.
Crie `.github/workflows/ci-test-main.yml` só com isto:

```yaml
name: CI - Burguer App (test-main)

on:
  push:
    branches: [ "test-main" ]

jobs:
  ola:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Pipeline funcionando!" && ls burguer-app
```

```powershell
git checkout test-main
git add .github/workflows/ci-test-main.yml
git commit -m "ci: pipeline mínimo"
git push -u origin test-main
```

Abra o repositório no GitHub → aba **Actions** → veja o job rodando e o `echo` no log.

---

## Passo 2 — Gatilhos (`on:`)

```yaml
on:
  push:                          # roda a cada push...
    branches: [ "test-main" ]    # ...somente na branch test-main
  pull_request:                  # roda quando abrem/atualizam um PR...
    branches: [ "test-main" ]    # ...que tenha como destino a test-main
  workflow_dispatch:             # botão "Run workflow" manual na aba Actions
```

| Gatilho | Quando dispara | Uso típico |
|---|---|---|
| `push` | Alguém fez push na branch | Validar todo commit |
| `pull_request` | PR aberto/atualizado **para** a branch | Barrar código quebrado **antes** do merge |
| `workflow_dispatch` | Clique manual na aba Actions | Rodar de novo sem commit (ótimo para aula) |
| `schedule` | Horário (cron), ex.: `- cron: "0 3 * * *"` | Teste noturno |

> **Variações para mostrar:** retire o `pull_request` para rodar só no push; troque
> `branches: [ "test-main" ]` por `branches: [ "main", "develop" ]`; use
> `paths: [ "burguer-app/auth-service/**" ]` para rodar só quando aquela pasta mudar.

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```
Se você der dois pushes seguidos, o GitHub cancela a execução antiga e roda só a nova.

---

## Passo 3 — Variáveis globais e o problema do banco

```yaml
env:
  PYTHON_VERSION: "3.12"
  MONGO_URI: "mongodb://localhost:27017"
  SECRET_KEY: "chave-so-para-ci"
  JWT_SECRET: "jwt-so-para-ci"
```

**Por que o projeto não funcionava localmente?** Só o `auth-service` tinha `.env`. Os outros
serviços ficavam sem `MONGO_URI` e tentavam um MongoDB em `localhost`, que não existia.

**No CI é a mesma coisa:** o `.env` **não vai para o GitHub** (está no `.gitignore`, porque
tem senha). Então:

1. As variáveis são definidas no próprio pipeline (`env:`). O `load_dotenv()` não sobrescreve
   variáveis que já existem, então o código funciona sem mudança.
2. O banco é um **MongoDB descartável** que sobe junto com o job:

```yaml
    services:
      mongo:
        image: mongo:7                    # imagem oficial do MongoDB no Docker Hub
        ports: [ "27017:27017" ]          # expõe a porta para o job
        options: >-                       # o job só começa quando o Mongo responder ao ping
          --health-cmd "mongosh --quiet --eval 'db.runCommand({ping:1})'"
          --health-interval 5s --health-timeout 5s --health-retries 10
```

> **Boa prática:** nunca coloque a URI do MongoDB Atlas (com senha) no `.yml`. Se precisar
> do banco real, use **Settings → Secrets and variables → Actions** e leia com
> `${{ secrets.MONGO_URI }}`. Para testes, o banco descartável é melhor: começa sempre vazio.

---

## Passo 4 — Etapa 1: subir todos os serviços (smoke test)

Objetivo: **antes de testar, provar que cada microsserviço sobe e responde HTTP 200.**

```yaml
  smoke-servicos:
    name: "1 · Sobe ${{ matrix.service }}"
    runs-on: ubuntu-latest
    timeout-minutes: 10                # mata o job se travar
    strategy:
      fail-fast: false                 # um serviço quebrado não cancela os outros
      matrix:
        include:                       # 4 jobs em paralelo, um por serviço
          - { service: auth-service,    port: 5000, path: /auth/login }
          - { service: user-service,    port: 5001, path: /user/create }
          - { service: order-service,   port: 5002, path: /order/list }
          - { service: product-service, port: 5003, path: /product/list }
    defaults:
      run:
        working-directory: burguer-app/${{ matrix.service }}   # "cd" automático
```

Passos do job, linha a linha:

| Step | O que faz |
|---|---|
| `actions/checkout@v4` | Baixa o código do repositório para a máquina do CI. |
| `actions/setup-python@v5` | Instala a versão do Python pedida. `cache: pip` reaproveita downloads entre execuções. |
| `pip install -r requirements.txt` | Instala as dependências **do serviço**. |
| `nohup python app.py > app.log 2>&1 &` | Sobe o Flask **em segundo plano** (`&`) e manda a saída para `app.log`. |
| Health check com `curl` | Tenta acessar a URL por até 30s. `curl -sf` falha se o status não for 2xx. |
| `if: always()` + `cat app.log` | Mostra o log do serviço **mesmo se falhar**, para você investigar. |

👉 **Commit sugerido para a aula:** suba só esta etapa e mostre os 4 jobs verdes.

---

## Passo 5 — Etapa 2: lint

```yaml
flake8 burguer-app --select=E9,F63,F7,F82 ...           # quebra o build
flake8 burguer-app --exit-zero --max-line-length=120 ... # só mostra avisos
```
- `E9` erro de sintaxe, `F63` comparação inválida, `F7` erro de estrutura, `F82` nome indefinido.
- `--exit-zero` = mostra os problemas de estilo, mas **não reprova** o pipeline.

---

## Passo 6 — Etapa 3: testes unitários (e por que a versão do Python importa)

Testes que já existem no projeto:

| Serviço | Pasta | O que testa |
|---|---|---|
| auth-service | `tests/test_user_model.py` | `serialize_user` com campos completos/ausentes |
| auth-service | `tests/test_user_model_parametrize.py` | os mesmos casos com `@pytest.mark.parametrize` |
| auth-service | `tests/test_database.py` | `get_db()` com `MongoClient` **mockado** (não usa banco) |
| user-service | `tests/test_user_model.py` | `serialize_user` do user-service |

```yaml
  testes-unitarios:
    needs: [ smoke-servicos, lint ]          # dependência: só roda se 1 e 2 passarem
    strategy:
      matrix:
        python-version: [ "3.11", "3.12", "3.13" ]
        service: [ auth-service, user-service ]
        include:
          - { service: auth-service, cov-min: 20 }
          - { service: user-service, cov-min: 3 }
```

A matrix gera **2 serviços × 3 versões = 6 jobs**.

**Por que testar em várias versões do Python?**
- O código ou uma biblioteca pode funcionar em uma versão e quebrar em outra.
- As versões fixadas no `requirements.txt` (ex.: `cffi==1.17.1`, `cryptography==45.0.4`)
  só têm pacote pronto (wheel) para algumas versões do Python. Em uma versão nova demais
  o `pip install` pode falhar ou precisar compilar.
- O seu computador roda **Python 3.14**, o pipeline antigo usava **3.12.4**. Se a máquina do
  dev e o CI usam versões diferentes, aparece o famoso "na minha máquina funciona".

> **Experimento para a aula:** acrescente `"3.14"` na lista e veja o que acontece.
> Depois troque para `"3.8"`: versões antigas também quebram (o Flask 3.1 exige Python ≥ 3.9).

O comando de teste:

```bash
pytest tests -v -o addopts="" \
  --cov=models --cov=services --cov=controllers --cov=config \   # mede cobertura dessas pastas
  --cov-report=term-missing \      # mostra no log quais linhas não foram testadas
  --cov-report=xml \               # gera coverage.xml (para ferramentas como Codecov/Sonar)
  --cov-fail-under=${{ matrix.cov-min }} \   # REPROVA se a cobertura ficar abaixo do mínimo
  --junitxml=report.xml            # relatório padrão JUnit
```

- `pytest tests` roda **só a pasta de testes unitários** (a pasta `tests_selenium` fica para a etapa 4).
- `-o addopts=""` ignora o `pytest.ini` local, para o CI ter regras próprias.
- **Cobertura atual:** auth-service **20%**, user-service **3%** (controllers e services
  ainda não têm teste). O `cov-min` está nesse piso: suba o número conforme criar testes.
  O pipeline antigo (`auth-service.yml`) pedia 90% e por isso reprovaria.

`actions/upload-artifact@v4` guarda `report.xml` e `coverage.xml`: no fim da execução,
eles aparecem na página do run, em **Artifacts**, para download.

---

## Passo 7 — Etapa 4: Selenium (usabilidade / E2E)

Aqui sobe **o sistema inteiro** (4 serviços + MongoDB) e o Chrome executa o teste de login.

| Step | O que faz |
|---|---|
| `services: mongo` | Banco vazio só para esse job. |
| Instala os 4 `requirements.txt` + `selenium` | O runner `ubuntu-latest` já tem o Google Chrome; o Selenium 4 baixa o driver sozinho. |
| Sobe os 4 serviços com `nohup ... &` | Todos em segundo plano, nas portas 5000–5003. |
| Health check em todas as URLs | Garante que tudo está no ar antes de testar. |
| **Seed** com `curl -X POST /user/create` | Como o banco começa vazio, cria o usuário `ci@teste.com` pelo próprio user-service. |
| `pytest tests_selenium` | Roda os testes de login. |
| `if: failure()` + logs | Só mostra os logs se algo falhar. |

Variáveis que o teste lê (veja `tests_selenium/test_login_usabilidade.py`):

| Variável | Local (aula) | No CI |
|---|---|---|
| `HEADLESS` | `0` (abre a janela) | `1` (não existe tela no servidor) |
| `PAUSA` | `1.5` s entre ações | `0` |
| `BASE_URL` | `http://127.0.0.1:5000/auth` | igual |
| `TEST_EMAIL` / `TEST_SENHA` | usuário da aula | `ci@teste.com` / `123456` |

Para rodar localmente igual ao CI:
```powershell
$env:HEADLESS="1"; $env:PAUSA="0"
pytest tests_selenium -v
```

---

## Passo 8 — Subir e acompanhar

```powershell
git checkout test-main
git add .github/workflows/ci-test-main.yml docs/PIPELINE-CI.md burguer-app
git commit -m "ci: pipeline completo de testes"
git push origin test-main
```

No GitHub: **Actions → CI - Burguer App (test-main)** → clique no run e veja:
1. o grafo dos jobs (smoke e lint em paralelo, depois unitários, depois Selenium);
2. o log de cada step (clique para expandir);
3. os **Artifacts** no fim da página.

### Para mostrar uma falha de propósito
- Quebre um teste: mude `"cliente"` para `"admin"` no `esperado` de um teste → etapa 3 fica vermelha
  e a etapa 4 é **pulada** (por causa do `needs`).
- Mude a porta no smoke (`port: 5999`) → o health check falha e mostra o `app.log`.
- Coloque `--cov-fail-under=90` → reprova por cobertura baixa.

---

## Próximos passos
- Testes para `controllers/` e `services/` usando o `app.test_client()` do Flask + `mongomock`.
- Pasta `tests/` para `order-service` e `product-service`, e incluí-los na matrix.
- Badge de status no README:
  `![CI](https://github.com/<usuario>/<repo>/actions/workflows/ci-test-main.yml/badge.svg?branch=test-main)`
- Proteção de branch: em **Settings → Branches**, exigir que o pipeline passe antes do merge na `main`.
