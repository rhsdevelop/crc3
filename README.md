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
CRC_ENV=production
CRC_DJANGO_SETTINGS_MODULE=crc.settings_pa
CRC_DB_PASSWORD=sua-senha-do-mysql
CRC_SECRET_KEY=sua-secret-key-de-producao
```

No arquivo WSGI do PythonAnywhere, aponte explicitamente para produção antes
de carregar a aplicação:

```python
import os
import sys

path = '/home/rhsdoctors/crc3/crc'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['CRC_ENV'] = 'production'
os.environ['DJANGO_SETTINGS_MODULE'] = 'crc.settings_pa'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
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
