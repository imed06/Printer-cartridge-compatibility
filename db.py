import sqlite3

def create_database():
    conn = sqlite3.connect('printers.db')
    cursor = conn.cursor()
    
    # Table des marques
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS marques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Table des modèles
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS modeles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL,
            id_marque INTEGER NOT NULL,
            FOREIGN KEY (id_marque) REFERENCES marques (id) ON DELETE CASCADE
        )
    ''')

    # Table des consommables (cartouches, toners, réservoirs)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS consommables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            type TEXT CHECK(type IN ("TONER", "CARTOUCHE", "RESERVOIR")) NOT NULL
        )
    ''')

    # Table d'association entre modèles et consommables
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS modeles_consommables (
            id_modele INTEGER,
            id_consommable INTEGER,
            FOREIGN KEY (id_modele) REFERENCES modeles (id) ON DELETE CASCADE,
            FOREIGN KEY (id_consommable) REFERENCES consommables (id) ON DELETE CASCADE,
            PRIMARY KEY (id_modele, id_consommable)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
