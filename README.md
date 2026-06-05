# crc3
Controle de Registros de Congregação - 3


## Desenvolvimento local

O ambiente local usa SQLite por padrão.

```bash
uv run --python .venv/bin/python python crc/manage.py runserver localhost:8000
```

## Produção no PythonAnywhere

O `wsgi.py` usa `crc.settings_pa` por padrão. Esse settings usa MySQL e lê
as credenciais por variáveis de ambiente, evitando editar arquivos no
PythonAnywhere.

Variáveis recomendadas:

```bash
CRC_DJANGO_SETTINGS_MODULE=crc.settings_pa
CRC_DB_PASSWORD=sua-senha-do-mysql
CRC_SECRET_KEY=sua-secret-key-de-producao
```

Variáveis opcionais, caso precise sobrescrever os valores padrão:

```bash
CRC_DB_NAME=rhsdoctors$crc
CRC_DB_USER=rhsdoctors
CRC_DB_HOST=rhsdoctors.mysql.pythonanywhere-services.com
CRC_DB_PORT=3306
CRC_ALLOWED_HOSTS=crc-rhsdoctors.pythonanywhere.com
```

Para coletar estáticos:

```bash
uv run --python .venv/bin/python python crc/manage.py collectstatic
```
