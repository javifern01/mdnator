# Mdnator

Convierte documentos a Markdown desde la línea de comandos. Procesa ficheros individuales o carpetas enteras mostrando progreso en tiempo real.

**Formatos soportados:** PDF, DOCX, XLSX, PPTX, HTML, HTM, CSV, JSON, XML, ZIP, EPUB, TXT

## Requisitos

- Python 3.10 o superior

## Instalación

```bash
git clone <url-del-repositorio>
cd Mdnator
pip install .
```

Tras la instalación el comando `mdnator` queda disponible en el terminal.

## Uso

```
mdnator <ruta> --output-dir <carpeta_salida> [--recursive] [--dry-run]
```

| Argumento | Descripción |
|---|---|
| `ruta` | Fichero o directorio de entrada (obligatorio) |
| `--output-dir` / `-o` | Carpeta donde se guardan los `.md` (obligatorio) |
| `--recursive` / `-r` | Procesa también las subcarpetas |
| `--dry-run` | Muestra qué se procesaría sin escribir nada |

### Ejemplos

```bash
# Convertir un único fichero
mdnator informe.pdf --output-dir ./markdown

# Convertir todos los ficheros de una carpeta
mdnator ./documentos --output-dir ./markdown

# Incluir subcarpetas
mdnator ./documentos --output-dir ./markdown --recursive

# Ver qué se procesaría sin convertir nada
mdnator ./documentos --output-dir ./markdown --dry-run
```
