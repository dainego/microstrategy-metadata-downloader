# Crear entorno virtual
py -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Desactivar entorno virtual
deactivate

# Levantar servicio uvicorn
python -m uvicorn api:app --reload

# Prueba de compilación de Código
python -m py_compile api.py