# Crear entorno virtual
py -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Desactivar entorno virtual
deactivate

# Levantar servicio uvicorn
python -m uvicorn api:app --reload

# URL Uvicorn
http://127.0.0.1:8000/docs

# Prueba de compilación de Código
python -m py_compile api.py

# Correr Main.py
python main.py

# Gitlab
## Branch actual
git branch

## Agregar archivos
git add .

## Commit
git commit -m "text"

## Push
git push origin [branch]

## Duplicar branch como nueva branch
git pull origin [branch-original]
git switch -c [nueva-branch]
git push -u origin [nueva-branch]