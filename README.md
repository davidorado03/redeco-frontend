# Frontend REDECO (Django)

Proyecto mínimo para visualizar una interfaz inicial que consumirá el API REDECO de CONDUSEF.

Objetivo de este repositorio: levantar rápidamente un servidor Django con una vista inicial (plantilla) y estructura básica.

Requisitos
- Python 3.10+ (recomendado)
- virtualenv / venv

Instalación rápida (PowerShell)

```powershell
cd 'c:\Users\david\Documents\Universidad\Negocios\redeco\frontend_REDECO'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Variables de entorno
- Copia `.env.example` a `.env` y añade los valores necesarios (SECRET_KEY, TOKEN_PLACEHOLDER si aplica).

Ejecutar el servidor

```powershell
cd 'c:\Users\david\Documents\Universidad\Negocios\redeco\frontend_REDECO'
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

El servidor quedará escuchando en http://127.0.0.1:8000/ y verás la página inicial con un formulario de ejemplo.

Siguientes pasos sugeridos
- Implementar autenticación hacia el API (server-side proxy).  
- Añadir llamadas a los endpoints REDECO y manejo de tokens en el backend.  
- Mejorar el diseño y agregar test básicos.
