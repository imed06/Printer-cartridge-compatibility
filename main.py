import sys
import os
import sqlite3
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget, QAction, 
    QPushButton, QFormLayout, QDialog, QMessageBox, QListWidgetItem, QFrame, QMainWindow
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

def get_db_connection():
    if getattr(sys, 'frozen', False):
        # Chemin vers la base de données dans le dossier temporaire
        db_path = os.path.join(sys._MEIPASS, 'printers.db')
        # Vérifier si la base de données existe déjà dans le répertoire temporaire
        if not os.path.exists(db_path):
            # Copier la base de données initiale depuis le dossier des ressources
            initial_db_path = os.path.join(sys._MEIPASS, 'data', 'printers.db')
            shutil.copy(initial_db_path, db_path)
    else:
        # Si non gelé, utilisez le chemin local
        db_path = 'printers.db'
    
    conn = sqlite3.connect(db_path)
    return conn

def set_global_font(size):
    font = QFont("Verdana", size)  # Vous pouvez changer "Arial" pour une autre police
    QApplication.setFont(font)

def enforce_uppercase(widget):
    """
    Force un champ de saisie (QLineEdit) à convertir automatiquement son contenu en majuscules.
    """
    def to_uppercase(text):
        widget.blockSignals(True)  # Empêche la récursion infinie
        widget.setText(text.upper())
        widget.blockSignals(False)
    
    widget.textChanged.connect(to_uppercase)  # Connecte le signal de changement de texte

class AjouterWindow(QDialog):
    data_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Ajouter une Marque, Modèle et Consommable")
        self.resize(800, 400)

        # Style commun pour les widgets d'entrée
        input_style = """
            font-size: 18px;
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        """
        button_style = """
            font-size: 18px;
        """
        list_style = """
            font-size: 18px;
        """

    # **Colonne 1 : Marque**
        marque_layout = QVBoxLayout()

        marque_label_existing = QLabel("Marque existante :", self)
        self.marque_dropdown = QComboBox(self)
        self.marque_dropdown.setStyleSheet(input_style)
        self.load_marques()

        marque_label_new = QLabel("Ajouter une nouvelle marque :", self)
        self.marque_input = QLineEdit(self)
        self.marque_input.setPlaceholderText("Nouvelle marque")
        self.marque_input.setStyleSheet(input_style)
        enforce_uppercase(self.marque_input)

        marque_layout.addWidget(marque_label_existing)
        marque_layout.addWidget(self.marque_dropdown)
        marque_layout.addWidget(QLabel("ou", self))
        marque_layout.addWidget(marque_label_new)
        marque_layout.addWidget(self.marque_input)
        marque_layout.addStretch()
        marque_layout.addWidget(QFrame())  # Ligne de séparation

        # **Colonne 2 : Modèle**
        modele_layout = QVBoxLayout()

        modele_layout_input = QHBoxLayout()
        
        self.model_input = QLineEdit(self)
        self.model_input.setPlaceholderText("ex: SX218")
        self.model_input.setStyleSheet(input_style)
        enforce_uppercase(self.model_input)

        add_model_button = QPushButton("+", self)
        add_model_button.setStyleSheet(button_style)
        add_model_button.clicked.connect(self.add_model)
        
        modele_layout_input.addWidget(self.model_input)
        modele_layout_input.addWidget(add_model_button)

        self.models_list = QListWidget(self)
        self.models_list.setStyleSheet(list_style)
        
        modele_layout.addWidget(QLabel("Nom du modèle :", self))
        modele_layout.addLayout(modele_layout_input)
        modele_layout.addWidget(self.models_list)
        
        # **Colonne 3 : Consommable**
        consommable_layout = QVBoxLayout()

        self.consommable_input = QComboBox(self)
        self.consommable_input.addItems(["TONER", "CARTOUCHE", "RESERVOIR"])
        self.consommable_input.setStyleSheet(input_style)

        self.reference_input = QLineEdit(self)
        self.reference_input.setPlaceholderText("ex: CH435")
        self.reference_input.setStyleSheet(input_style)
        enforce_uppercase(self.reference_input)

        save_button = QPushButton("Sauvegarder", self)
        save_button.setStyleSheet("""
            padding: 10px;
        """)
        save_button.clicked.connect(self.save_data)
        save_button.setCursor(Qt.PointingHandCursor)

        consommable_layout.addWidget(QLabel("Type :", self))
        consommable_layout.addWidget(self.consommable_input)
        consommable_layout.addWidget(QLabel("Référence :", self))
        consommable_layout.addWidget(self.reference_input)
        consommable_layout.addStretch()
        consommable_layout.addWidget(save_button)

        # **Disposition générale : 3 colonnes avec séparateurs**
        main_layout = QHBoxLayout()
        main_layout.addLayout(marque_layout)
        main_layout.addLayout(modele_layout)
        main_layout.addLayout(consommable_layout)
        main_layout.setSpacing(10)  # Espacement entre les colonnes

        self.setLayout(main_layout)

    def load_marques(self):
        """Load existing brands into the dropdown"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM marques")
        marques = cursor.fetchall()
        conn.close()

        self.marque_dropdown.clear()
        self.marque_dropdown.addItem("Sélectionnez une marque", -1)  # Default option
        for marque in marques:
            self.marque_dropdown.addItem(marque[1], marque[0])

    def add_model(self):
        """Ajoute un modèle à la liste avec un bouton 'X' pour suppression."""
        model_name = self.model_input.text().strip().upper()

        if not model_name:
            QMessageBox.warning(self, "!!", "Veuillez entrer un modèle valide.")
            return

        if any(model_name == self.models_list.itemWidget(self.models_list.item(i)).model_label.text()
               for i in range(self.models_list.count())):
            QMessageBox.warning(self, "!!", "Ce modèle existe déjà dans la liste.")
            return

        # Créer un widget avec un label (nom du modèle) et un bouton "X"
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)

        model_label = QLabel(model_name)
        model_label.setStyleSheet("font-size: 14px;")
        item_layout.addWidget(model_label)
        
        item_widget.model_label = model_label

        delete_button = QPushButton("X")
        delete_button.setStyleSheet("color: red; font-weight: bold;")
        delete_button.setFixedSize(20, 20)
        delete_button.clicked.connect(lambda: self.delete_model(item_widget))
        item_layout.addWidget(delete_button)

        item_widget.setLayout(item_layout)

        # Ajouter le widget à la liste
        list_item = QListWidgetItem(self.models_list)
        list_item.setSizeHint(item_widget.sizeHint())
        self.models_list.addItem(list_item)
        self.models_list.setItemWidget(list_item, item_widget)

        # Effacer le champ de saisie après ajout
        self.model_input.clear()

    def delete_model(self, item_widget):
        """Supprime un modèle spécifique de la liste."""
        for i in range(self.models_list.count()):
            list_item = self.models_list.item(i)
            if self.models_list.itemWidget(list_item) == item_widget:
                self.models_list.takeItem(i)
                break
            
    def save_data(self):
        """Save the data (Marque, Models, and Consumables) to the database"""
        # Get the marque
        marque_id = self.marque_dropdown.currentData()
        new_marque = self.marque_input.text().strip()

        if marque_id == -1 and not new_marque:
            QMessageBox.warning(self, "!!", "Veuillez sélectionner ou ajouter une marque.")
            return

        if new_marque:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO marques (nom) VALUES (?)", (new_marque,))
                conn.commit()
                marque_id = cursor.lastrowid
                self.load_marques()  # Reload the updated marques list
                QMessageBox.information(self, "!!", f"La marque '{new_marque}' a été ajoutée.")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "!!", f"La marque '{new_marque}' existe déjà.")
                conn.close()
                return
            conn.close()

        # Get the models
        models = [
            self.models_list.itemWidget(self.models_list.item(i)).layout().itemAt(0).widget().text()
            for i in range(self.models_list.count())
        ]
        if not models:
            QMessageBox.warning(self, "!!", "Veuillez ajouter au moins un modèle.")
            return

        # Get the consumable type and reference
        consumable_type = self.consommable_input.currentText()
        reference = self.reference_input.text().strip()
        if not reference:
            QMessageBox.warning(self, "!!", "Veuillez entrer une référence pour l'encre.")
            return

        # Save data to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Insert models and consumables
            for model in models:
                cursor.execute("INSERT INTO modeles (nom, id_marque) VALUES (?, ?)", (model, marque_id))
                model_id = cursor.lastrowid

                # Insert consumable
                cursor.execute(
                    "INSERT OR IGNORE INTO consommables (reference, type) VALUES (?, ?)",
                    (reference, consumable_type),
                )
                cursor.execute("SELECT id FROM consommables WHERE reference = ?", (reference,))
                consumable_id = cursor.fetchone()[0]

                # Link model and consumable
                cursor.execute(
                    "INSERT OR IGNORE INTO modeles_consommables (id_modele, id_consommable) VALUES (?, ?)",
                    (model_id, consumable_id),
                )

            conn.commit()
            QMessageBox.information(self, "!!", "Les données ont été sauvegardées avec succès.")
            self.data_added.emit()
            self.accept()  # Close the window
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "!!", f"Une erreur est survenue : {e}")
        finally:
            self.parent.reset_search()  # Appeler la méthode de la fenêtre principale
            conn.close()

class ModifierWindow(QWidget):
    def __init__(self, model_name, consumable_data, parent=None):
        super().__init__()
        self.parent = parent
        self.model_name = model_name
        self.consumable_id = consumable_data[0]  # ID of the consumable
        self.initUI(consumable_data)

    def initUI(self, consumable_data):
        self.setWindowTitle(f"Modifier le consommable du modèle {self.model_name}")
        self.resize(500, 250)

        # Style commun pour les champs et les boutons
        input_style = """
            font-size: 18px;
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        """
        button_style = """
            font-size: 18px;
            color: #fff;
            background-color: #007bff;
            padding: 8px;
            border: none;
            border-radius: 5px;
        """

        # Disposition du formulaire
        layout = QFormLayout()

        # **Modèle affiché**
        model_label = QLabel("Modèle :", self)
        model_display = QLabel(self.model_name, self)
        model_display.setStyleSheet("""
            font-size: 18px;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #fff;
        """)
        layout.addRow(model_label, model_display)

        # **Type de consommable**
        consommable_label = QLabel("Type de consommable :", self)
        self.consommable_input = QComboBox(self)
        self.consommable_input.addItems(["TONER", "CARTOUCHE", "RESERVOIR"])
        self.consommable_input.setCurrentText(consumable_data[1])  # Type actuel
        self.consommable_input.setStyleSheet(input_style)
        layout.addRow(consommable_label, self.consommable_input)

        # **Référence du consommable**
        reference_label = QLabel("Référence :", self)
        self.reference_input = QLineEdit(self)
        self.reference_input.setText(consumable_data[2])  # Référence actuelle
        self.reference_input.setStyleSheet(input_style)
        enforce_uppercase(self.reference_input)
        layout.addRow(reference_label, self.reference_input)

        # **Bouton Enregistrer**
        save_button = QPushButton("Sauvegarder", self)
        save_button.setStyleSheet("""
            padding: 10px;
        """)
        save_button.clicked.connect(self.save_modifications)
        save_button.setCursor(Qt.PointingHandCursor) 
        layout.addRow(save_button)

        self.setLayout(layout)

    def save_modifications(self):
        """
        Met à jour l'association modèle-consommable :
        - Si le consommable existe déjà : associer.
        - Si le consommable n'existe pas : ajouter et associer.
        """
        new_type = self.consommable_input.currentText()
        new_reference = self.reference_input.text().strip().upper()

        if not new_reference:
            # Validation : Référence vide
            print("La référence ne peut pas être vide.")  # Vous pouvez afficher un message d'erreur ici
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifier si le consommable existe déjà
        cursor.execute("""
            SELECT id FROM consommables WHERE reference = ?
        """, (new_reference,))
        existing_consumable = cursor.fetchone()

        if existing_consumable:
            # Consommable existe déjà, récupérer son ID
            consumable_id = existing_consumable[0]
        else:
            # Consommable non existant, l'ajouter
            cursor.execute("""
                INSERT INTO consommables (type, reference)
                VALUES (?, ?)
            """, (new_type, new_reference))
            consumable_id = cursor.lastrowid

        # Récupérer l'ID du modèle
        cursor.execute("""
            SELECT id FROM modeles WHERE nom = ?
        """, (self.model_name,))
        model_id = cursor.fetchone()

        if model_id:
            model_id = model_id[0]

            # Supprimer l'association existante pour ce modèle
            cursor.execute("""
                DELETE FROM modeles_consommables WHERE id_modele = ?
            """, (model_id,))

            # Ajouter la nouvelle association
            cursor.execute("""
                INSERT INTO modeles_consommables (id_modele, id_consommable)
                VALUES (?, ?)
            """, (model_id, consumable_id))

        conn.commit()
        conn.close()
        
        self.parent.reset_search()  # Appeler la méthode de la fenêtre principale

        # Fermer la fenêtre après sauvegarde
        self.close()

class ModifierConsumableWindow(QWidget):
    
    all_consumables = []  # Liste de tous les consommables
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.initUI()
        self.selected_reference = None  # Référence sélectionnée depuis la liste

    def initUI(self):
        self.setWindowTitle("Modifier un Consommable")
        self.resize(600, 400)

        # Style commun pour les champs et les boutons
        input_style = """
            font-size: 18px;
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        """
        button_style = """
            font-size: 18px;
            color: #fff;
            background-color: #007bff;
            padding: 10px;
            border: none;
            border-radius: 5px;
        """
        list_style = """
            font-size: 18px;
            padding: 5px;
            border: 1px solid #ddd;
            background-color: #fff;
        """

        # **Disposition générale**
        main_layout = QVBoxLayout()

        # **Recherche de consommable**
        search_layout = QFormLayout()
        search_label = QLabel("Rechercher Consommable :", self)
        self.consumable_search_input = QLineEdit(self)
        self.consumable_search_input.setPlaceholderText("Entrez la référence de l'encre")
        self.consumable_search_input.setStyleSheet(input_style)
        enforce_uppercase(self.consumable_search_input)
        self.consumable_search_input.textChanged.connect(self.search_consumable)
        search_layout.addRow(search_label, self.consumable_search_input)

        # **Résultats de la recherche**
        self.consumable_results = QListWidget(self)
        self.consumable_results.setStyleSheet(list_style)
        self.consumable_results.itemClicked.connect(self.select_consumable)
        results_label = QLabel("Résultats :", self)
        search_layout.addRow(results_label, self.consumable_results)

        # Ajout du bloc de recherche au layout principal
        main_layout.addLayout(search_layout)

        # **Modification du consommable**
        modify_layout = QFormLayout()

        # Champ Type de consommable
        type_label = QLabel("Type :", self)
        self.type_input = QComboBox(self)
        self.type_input.addItems(["TONER", "CARTOUCHE", "RESERVOIR"])
        self.type_input.setStyleSheet(input_style)
        modify_layout.addRow(type_label, self.type_input)

        # Champ Référence du consommable
        reference_label = QLabel("Nouvelle Référence :", self)
        self.reference_input = QLineEdit(self)
        self.reference_input.setPlaceholderText("Entrez la nouvelle référence")
        self.reference_input.setStyleSheet(input_style)
        enforce_uppercase(self.reference_input)
        modify_layout.addRow(reference_label, self.reference_input)

        # Ajout du bloc de modification au layout principal
        main_layout.addLayout(modify_layout)

        # **Bouton Sauvegarder**
        save_button = QPushButton("Sauvegarder", self)
        save_button.setStyleSheet("""
            padding: 10px;
        """)
        save_button.clicked.connect(self.update_consumable)
        save_button.setCursor(Qt.PointingHandCursor)

        # Ajout du bouton au layout principal
        main_layout.addWidget(save_button, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        # Charger tous les consommables
        self.load_all_consumables()

    def load_all_consumables(self):
        """Charger tous les consommables dans la liste."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, reference FROM consommables")
        results = cursor.fetchall()
        conn.close()

        self.all_consumables = results  # Stocker tous les consommables
        self.update_consumable_list(self.all_consumables)  # Afficher tous les consommables

    
    def search_consumable(self):
        """Filtrer les consommables en fonction de la recherche de l'utilisateur."""
        reference = self.consumable_search_input.text().strip()  # Convertir en minuscules pour ignorer la casse

        if not reference:
            self.update_consumable_list(self.all_consumables)  # Si vide, réafficher tous les consommables
            return

        # Filtrer les résultats
        filtered_consumables = [
            (consumable_id, consumable_type, consumable_ref)
            for consumable_id, consumable_type, consumable_ref in self.all_consumables
            if reference in consumable_ref  # Comparaison insensible à la casse
        ]
        
        # Mettre à jour la liste avec les résultats filtrés
        self.update_consumable_list(filtered_consumables)

    def update_consumable_list(self, consumables):
        """Mettre à jour la liste des consommables affichée."""
        self.consumable_results.clear()  # Vider la liste existante

        for consumable_id, consumable_type, consumable_ref in consumables:
            self.consumable_results.addItem(f"{consumable_ref} ({consumable_type})")


    def select_consumable(self, item):
        """Remplir les champs après la sélection d'un consommable."""
        text = item.text()
        reference, consumable_type = text.split(" (")
        consumable_type = consumable_type.strip(")")

        # Sauvegarder la référence sélectionnée
        self.selected_reference = reference

        self.reference_input.setText(reference)
        self.type_input.setCurrentText(consumable_type)

    def update_consumable(self):
        """Mettre à jour uniquement les champs du consommable sélectionné."""
        if not self.selected_reference:
            return  # Aucun consommable sélectionné

        new_reference = self.reference_input.text().strip()
        consumable_type = self.type_input.currentText()

        if not new_reference:
            QMessageBox.warning(self, "!!", "Veuillez entrer une référence pour l'encre.")
            return  # Ne pas poursuivre si le champ est vide

        conn = get_db_connection()
        cursor = conn.cursor()

        # Mettre à jour le consommable existant
        cursor.execute("""
            UPDATE consommables
            SET type = ?, reference = ?
            WHERE reference = ?
        """, (consumable_type, new_reference, self.selected_reference))
        conn.commit()
        conn.close()

        self.parent.reset_search()
        self.close()  # Fermer la fenêtre après la mise à jour

# Main Application
class PrinterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Consultation Cartouches")
        self.resize(800, 500)

        # Styling window with a modern look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)

        # Dropdown for brands with MacBook-like styling
        self.brand_dropdown = QComboBox(self)
        self.load_brands()
        self.brand_dropdown.setStyleSheet("""
            font-size: 16px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fff;
            color: #333;
        """)

        # Input field for the model
        self.model_input = QLineEdit(self)
        self.model_input.setPlaceholderText("Entrez le modèle ici...")
        enforce_uppercase(self.model_input)
        self.model_input.textChanged.connect(self.suggest_models)
        self.model_input.setStyleSheet("""
            font-size: 16px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 8px;
        """)

        # Suggestion list with hover effects
        self.suggestions_list = QListWidget(self)
        self.suggestions_list.setStyleSheet("""
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fff;
            color: #333;
            padding: 5px;
            selection-background-color: #0078D7;
            selection-color: #fff;
        """)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)

        # Result display at the bottom
        self.result_label = QLabel(self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #0078D7;
            padding: 10px;
            background-color: #eef;
            border-radius: 8px;
        """)
        self.result_label.setText("Aucun résultat trouvé")
        self.result_label.hide()  # Hidden by default

        # Layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Marque:", self))
        input_layout.addWidget(self.brand_dropdown)
        input_layout.addWidget(QLabel("Modèle:", self))
        input_layout.addWidget(self.model_input)
        input_layout.setSpacing(10)

        final_layout = QVBoxLayout()
        final_layout.addLayout(input_layout)
        final_layout.addWidget(self.suggestions_list)
        final_layout.addWidget(self.result_label)
        final_layout.setSpacing(20)

        # Central widget and layout
        central_widget = QWidget(self)
        central_widget.setLayout(final_layout)
        self.setCentralWidget(central_widget)

        # Menu bar
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #f5f5f5;
                padding: 5px;
                font-size: 16px;
                border-bottom: 1px solid #ddd;
            }
            QMenuBar::item {
                padding: 5px 15px;
                margin: 2px;
                background-color: transparent;
                border-radius: 5px;
            }
            QMenuBar::item:selected {
                background-color: #0078D7;
                color: #fff;
            }
        """)

        options_menu = menu_bar.addMenu('Options')
        options_menu.setStyleSheet("""
            QMenu {
                background-color: #d3d3d3;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
            QMenu::item {
                font-size: 14px;
                padding: 8px 20px;
                background-color: transparent;
                color: #000;
            }
            QMenu::item:selected {
                background-color: #0078D7;
                color: #fff;
                border-radius: 5px;
            }
        """)

        # Actions for the dropdown
        new_model_action = QAction("Nouveau Modèle d'imprimante", self)
        modify_ink_action = QAction("Modifier encre d'imprimante", self)
        details_modify_ink_action = QAction("Détails/modifier encre", self)

        # Connect actions to their functions
        new_model_action.triggered.connect(self.open_ajouter_window)
        modify_ink_action.triggered.connect(self.open_modifier_window)
        details_modify_ink_action.triggered.connect(self.open_modifier_consumable_window)

        # Add actions to the menu
        options_menu.addAction(new_model_action)
        options_menu.addAction(modify_ink_action)
        options_menu.addAction(details_modify_ink_action)

           
    # Load brands into the dropdown
    def load_brands(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM marques")
        brands = cursor.fetchall()
        self.brand_dropdown.clear()
        self.brand_dropdown.addItem("Sélectionnez une marque", -1)
        for brand in brands:
            self.brand_dropdown.addItem(brand[1], brand[0])
        conn.close()

    # Suggest models dynamically based on input
    def suggest_models(self):
        brand_id = self.brand_dropdown.currentData()
        model_name = self.model_input.text().strip()

        if not brand_id or not model_name:
            self.suggestions_list.clear()
            self.result_label.hide()
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nom FROM modeles
            WHERE id_marque = ? AND nom LIKE ?
            LIMIT 10
        """, (brand_id, f"%{model_name}%"))
        models = cursor.fetchall()
        conn.close()

        self.suggestions_list.clear()
        if models:
            for model in models:
                self.suggestions_list.addItem(model[0])
            self.suggestions_list.show()

    # Select a suggestion and display its consumables
    def select_suggestion(self, item):
        selected_model = item.text()
        self.model_input.setText(selected_model)
        #self.suggestions_list.hide()
        self.search_consumables()

    # Search consumables based on brand and model
    def search_consumables(self):
        brand_id = self.brand_dropdown.currentData()
        model_name = self.model_input.text().strip()

        if not brand_id or not model_name:
            self.result_table.setRowCount(0)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.type, c.reference
            FROM modeles m
            JOIN modeles_consommables mc ON m.id = mc.id_modele
            JOIN consommables c ON mc.id_consommable = c.id
            WHERE m.id_marque = ? AND m.nom = ?
        """, (brand_id, model_name))
        results = cursor.fetchall()
        conn.close()

        if results:
            # Format the results as a string
            result_text = "<br>".join(
                f"<b>{ctype}:</b> {cref}" for ctype, cref in results
            )
            self.result_label.setText(result_text)
            self.result_label.show()
        else:
            self.result_label.setText("Aucun consommable trouvé pour ce modèle.")
            self.result_label.show()

    # Open a new window to add marque, model, and consumable
    def open_ajouter_window(self):
        """Open the Ajouter window"""
        ajouter_window = AjouterWindow(parent=self)
        ajouter_window.data_added.connect(self.refresh_data)
        ajouter_window.exec_()  # Open the window in a modal way
      
    def open_modifier_window(self):
        """
        Open the ModifierWindow to modify the consumable of a selected model.
        """
        brand_id = self.brand_dropdown.currentData()
        model_name = self.model_input.text().strip()

        # Ensure that a valid brand and model are selected
        if not brand_id or not model_name:
            return  # Optionally, show a message to the user

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.type, c.reference
            FROM modeles m
            JOIN modeles_consommables mc ON m.id = mc.id_modele
            JOIN consommables c ON mc.id_consommable = c.id
            WHERE m.id_marque = ? AND m.nom = ?
        """, (brand_id, model_name))
        consumable_data = cursor.fetchone()
        conn.close()

        # Ensure consumable data is found
        if not consumable_data:
            return  # Optionally, show a message to the user

        # Open the modifier window with the fetched data
        self.modifier_window = ModifierWindow(model_name, consumable_data, parent=self)
        self.modifier_window.show()
  
    # Define the function to open the new window for modifying a consumable
    def open_modifier_consumable_window(self):
        self.modifier_consumable_window = ModifierConsumableWindow(parent=self)
        self.modifier_consumable_window.show()

    def refresh_data(self):
        self.load_brands()
        self.suggestions_list.clear()
        self.result_label.clear()

    def reset_search(self):
        """
        Réinitialise les champs de recherche et les résultats affichés.
        """
        self.brand_dropdown.setCurrentIndex(0)  # Réinitialiser le dropdown des marques
        self.model_input.clear()               # Effacer le champ du modèle
        self.suggestions_list.clear()          # Vider les suggestions
        self.result_label.clear()       # Réinitialiser la table des résultats

       
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    set_global_font(12)  # Changez "12" pour la taille de texte souhaitée
    window = PrinterApp()
    window.show()
    sys.exit(app.exec_())
