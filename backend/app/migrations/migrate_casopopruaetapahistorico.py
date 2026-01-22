import sqlite3
from pathlib import Path

DB_PATH = Path("poprua.db")

COLS = [
    ("responsavel_funcao", "TEXT"),
    ("responsavel_servico", "TEXT"),
    ("responsavel_contato", "TEXT"),
]

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("PRAGMA table_info(casopopruaetapahistorico)")
    existing = {row[1] for row in cur.fetchall()}

    for name, ddl in COLS:
        if name in existing:
            print(f"OK: {name} já existe")
            continue
        sql = f"ALTER TABLE casopopruaetapahistorico ADD COLUMN {name} {ddl}"
        print("Applying:", sql)
        cur.execute(sql)

    con.commit()
    con.close()
    print("✅ Migração concluída.")

if __name__ == "__main__":
    main()