import sqlite3
from pathlib import Path

DB_PATH = Path("poprua.db")

COLS_TO_ADD = [
    ("data_prevista_proxima_acao", "TEXT"),
    ("data_ultima_acao", "TEXT"),
    ("flag_estagnado", "INTEGER NOT NULL DEFAULT 0"),
    ("dias_estagnado", "INTEGER NOT NULL DEFAULT 0"),
    ("tipo_estagnacao", "TEXT"),
    ("motivo_estagnacao", "TEXT"),
]

def main():
    if not DB_PATH.exists():
        print("ERRO: poprua.db não existe na pasta atual.")
        return

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    cur.execute("PRAGMA table_info(casopoprua)")
    existing = {r[1] for r in cur.fetchall()}

    for name, coltype in COLS_TO_ADD:
        if name in existing:
            print(f"OK: {name} já existe")
            continue
        sql = f"ALTER TABLE casopoprua ADD COLUMN {name} {coltype}"
        print("Applying:", sql)
        cur.execute(sql)

    con.commit()
    con.close()
    print("✅ Migração concluída.")

if __name__ == "__main__":
    main()
