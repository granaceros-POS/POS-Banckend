import os
from functools import lru_cache

SYSTEM_DIR = os.environ.get("SYSTEMDIR", "textos") 

@lru_cache(maxsize=128)
def load_table(table_name: str, key_len: int) -> dict[str, str]:
    table_data = {}
    file_path = os.path.join(SYSTEM_DIR, table_name)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if len(line) > key_len:
                    key = line[:key_len]
                    data = line[key_len:]
                    table_data[key] = data
    except FileNotFoundError:
        print(f"ADVERTENCIA: Archivo de tabla no encontrado: {file_path}")
    except Exception as e:
        print(f"ERROR: No se pudo cargar la tabla {file_path}: {e}")

    return table_data

def gettxt(tab: str, key: str) -> str:
    table_name = tab.strip()
    if not table_name:
        return ""

    key_len = len(key)
    table_content = load_table(table_name, key_len)
    
    return table_content.get(key, "")