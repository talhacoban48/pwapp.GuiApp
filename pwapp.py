import os
import sys
import random
import pandas as pd
from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QListWidget, 
        QLabel, 
        QLineEdit, 
        QPushButton, 
        QTextEdit,
        QVBoxLayout, 
        QHBoxLayout, 
        QGroupBox, 
        QMessageBox,
        QFileDialog,
        QCheckBox
    )
from PyQt5.QtGui import QIcon, QFont
from pathlib import Path
import sqlite3
import locale
locale.setlocale(locale.LC_ALL, "tr_TR.utf8")




class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("password app")
        self.setGeometry(400, 200, 960, 648)
        self.setWindowIcon(QIcon("Password.ico"))
        
        basepath = Path(os.path.expanduser("~/pwapp"))
        if not basepath.exists():
            basepath.mkdir(parents=True)
        self.db_name = os.path.join(basepath, "database.db")
        
        self.control = False
        self.menubar()
        self.widgets()
        self.layouts()
        try:
            self.create_table()
            self.cursor.close()
            self.conn.close()
        except:
            self.get_objects()
        self.show()


    def menubar(self):
        
        bar = self.menuBar()
        
        file = bar.addMenu("file")
        file.addAction("save as excel")
        file.addAction("save as csv")
        file.triggered.connect(self.file_progressTrig)
        
        edit = bar.addMenu("import")
        edit.addAction("import excel")
        edit.addAction("import csv")
        edit.triggered.connect(self.import_progressTrig)
        

    def file_progressTrig(self, q):

        process = q.text()
        if process == "save as excel":
            filename, _ = QFileDialog.getSaveFileName(self, "Open file", "", "Excel files (*.xlsx)")
            if filename != "":
                self.connect_database()
                query = "SELECT * FROM passwords;"
                rows = self.cursor.execute(query)
                df = pd.DataFrame()
                for row in rows:
                    row = [ None if r == "None" else r for r in row ]
                    df = pd.concat([
                        df, 
                        pd.DataFrame({
                            "appname" : [row[0]], 
                            "username" : [row[1]],
                            "email" : [row[2]],
                            "password" : [row[3]], 
                            "url" : [row[4]],
                            "aktifpasif" : [row[5]]
                        })
                    ])
                    df.to_excel(filename, index=False)
                self.cursor.close()
                self.conn.close()
                
        elif process == "save as csv":
            filename, _ = QFileDialog.getSaveFileName(self, "Open file", "", "csv files (*.csv)")
            if filename != "":
                self.connect_database()
                query = "SELECT * FROM passwords;"
                rows = self.cursor.execute(query)
                df = pd.DataFrame()
                for row in rows:
                    row = [ None if r == "None" else r for r in row ]
                    df = pd.concat([
                        df, 
                        pd.DataFrame({
                            "appname" : [row[0]], 
                            "username" : [row[1]],
                            "email" : [row[2]],
                            "password" : [row[3]], 
                            "url" : [row[4]],
                            "aktifpasif" : [row[5]]
                        })
                    ])
                    df.to_csv(filename, index=False)
                self.cursor.close()
                self.conn.close()
        else:
            pass

    def import_progressTrig(self, q):

        def insert_objects(df):
            
            columns = list(df.columns)
            column_names = ["appname", "username", "email", "password", "url", "aktifpasif"]
            for column_name in column_names:
                if column_name not in columns:
                    message = f"Column name '{column_name}' does not exist in table. Provided table should contain all following columns:"
                    for c_name in column_names:
                        message += f"\n\t'{c_name}'"
                    QMessageBox.warning(self, "warning", message)
                    return
            
            self.connect_database()
            index = 0
            for _, row in df.iterrows():
                app_name = str(row["appname"])
                if app_name == "nan":
                    app_name = None
                query1 = f"SELECT appname FROM passwords WHERE appname = '{app_name}';"
                resp = self.cursor.execute(query1)
                resp = resp.fetchone()
                if resp == None:
                    user_name = str(row["username"])
                    if user_name == "nan":
                        user_name = None
                    email = str(row["email"])
                    if email == "nan":
                        email = None
                    pass_word = str(row["password"])
                    if pass_word == "nan":
                        pass_word = None
                    url = str(row["url"])
                    if url == "nan":
                        url = None
                    aktifpasif = str(row["aktifpasif"])
                    if str(aktifpasif) not in ["aktif", "pasif"]:
                        aktifpasif = "aktif"
                    query2 = f"""INSERT INTO passwords (appname, username, email, password, url, aktifpasif)
                                    VALUES ('{app_name}', '{user_name}', '{email}', '{pass_word}', '{url}', '{aktifpasif}');"""
                    self.cursor.execute(query2)
                else:
                    index += 1
            self.conn.commit()
            
            if index == 0:
                message = "All object added to database."
            else:
                message = f"{index} number of objects already exists in database. Rest of them were inserted to database."
            
            self.cursor.close()
            self.conn.close()
            self.get_objects()
            QMessageBox.information(self, "success", message)
            
            
        process = q.text()
        if process == "import excel":
            filename, _ = QFileDialog.getOpenFileName(self,"Open File", "","Excel files (*.xlsx)")
            if filename:
                df = pd.read_excel(filename)
                insert_objects(df=df)
        elif process == "import csv":
            filename, _ = QFileDialog.getOpenFileName(self,"Open File", "","csv files (*.csv)")
            if filename:
                df = pd.read_csv(filename)
                insert_objects(df=df)
        else:
            pass
        
        
    def connect_database(self):
        
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()


    def create_table(self):
        
        self.connect_database()
        query = """
            CREATE TABLE passwords (
                appname varchar(255) PRIMARY KEY,
                username varchar(255),
                email varchar(255),
                password varchar(255),
                url varchar(255),
                aktifpasif varchar(255)
            );                 
        """
        self.cursor.execute(query)
        self.conn.commit()


    def widgets(self):
        
        self.show_pasive_objects = QCheckBox("Show pasive objects", self)
        self.show_pasive_objects.setFont(QFont("Times", 11))
        self.show_pasive_objects.clicked.connect(self.hide_show_passive_objects)
        # left side widgets
        self.objects_list = QListWidget(self)
        self.objects_list.setMinimumHeight(500)
        self.objects_list.setMinimumWidth(200)
        self.objects_list.setFont(QFont("Times", 11))
        self.objects_list.mouseDoubleClickEvent = self.open_selected_object
        
        # right side widgets
        self.app_name_label = QLabel("App Name : ", self)
        self.app_name_label.setFont(QFont("Times", 10))
        self.app_name = QLineEdit()
        self.app_name.setFont(QFont("Times", 10))
        self.app_name.setMinimumWidth(275)
        self.app_name.setMinimumHeight(40)
        
        self.user_name_label = QLabel("UserName : ", self)
        self.user_name_label.setFont(QFont("Times", 10))
        self.user_name = QLineEdit()
        self.user_name.setFont(QFont("Times", 10))
        self.user_name.setMinimumWidth(275)
        self.user_name.setMinimumHeight(40)
        
        self.email_label = QLabel("Email : ", self)
        self.email_label.setFont(QFont("Times", 10))
        self.email = QLineEdit()
        self.email.setFont(QFont("Times", 10))
        self.email.setMinimumWidth(275)
        self.email.setMinimumHeight(40)
        
        self.password_label = QLabel("Password : ", self)
        self.password_label.setFont(QFont("Times", 10))
        self.password = QLineEdit()
        self.password.setFont(QFont("Times", 10))
        self.password.setMinimumWidth(275)
        self.password.setMinimumHeight(40)
        
        self.url_label = QLabel("Url : ", self)
        self.url_label.setFont(QFont("Times", 10))
        self.url = QTextEdit()
        self.url.setFont(QFont("Times", 10))
        self.url.setMinimumWidth(275)
        self.url.setMaximumHeight(120)
        
        self.change_visibility_label = QLabel("Visibility : ", self)
        self.change_visibility_label.setFont(QFont("Times", 10))
        self.change_visibility = QCheckBox()
        self.change_visibility.setFont(QFont("Times", 10))
        self.change_visibility.setChecked(True)
        self.change_visibility.clicked.connect(self.visibility_function)
        self.visible = QLabel("True", self)
        self.visible.setFont(QFont("Times", 10))
        
        self.empty_space = QLabel()
        self.empty_space.setMinimumHeight(40)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setMinimumHeight(40)
        self.clear_button.setMinimumWidth(100)
        self.clear_button.clicked.connect(self.clear_function)
        
        self.insert_button = QPushButton("Insert")
        self.insert_button.setMinimumHeight(40)
        self.insert_button.setMinimumWidth(100)
        self.insert_button.clicked.connect(self.insert_function)
        
        self.update_button = QPushButton("Update")
        self.update_button.setMinimumHeight(40)
        self.update_button.setMinimumWidth(100)
        self.update_button.clicked.connect(self.update_function)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setMinimumHeight(40)
        self.delete_button.setMinimumWidth(100)
        self.delete_button.clicked.connect(self.delete_funtion)
    
        self.create_password_button = QPushButton("Create")
        self.create_password_button.setMinimumHeight(40)
        self.create_password_button.setMinimumWidth(100)
        self.create_password_button.clicked.connect(self.create_password_function)
        
        self.random_password = QLineEdit()
        self.random_password.setFont(QFont("Times", 10))
        self.random_password.setMinimumWidth(275)
        self.random_password.setMinimumHeight(40)
    
    
    def create_password_function(self):
        
        self.random_password.clear()
        lower_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","r","s","t","u","v","x","y","z"]
        upper_letters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","R","S","T","U","V","X","Y","Z"]
        numbers = ["0","1","2","3","4","5","6","7","8","9"]
        others = ["<",">","?","!","}","{","[","]","(",")",".",",",":",";"]
        characters = lower_letters + upper_letters + numbers + others
        random_password = ""
        for _ in range(15):
            random_char = random.choice(characters)
            random_password += random_char
        self.random_password.setText(random_password)
        
    
    def visibility_function(self):
        
        visible = self.change_visibility.isChecked()
        if visible:
            self.visible.clear()
            self.visible.setText("True")
        else:
            self.visible.clear()
            self.visible.setText("False")
            
            
    def hide_show_passive_objects(self):
        
        self.control = self.show_pasive_objects.isChecked()
        self.get_objects()
    
    
    def open_selected_object(self, event):

        object_name = self.objects_list.currentItem().text().strip()
        self.connect_database()
        query = f"SELECT * FROM passwords WHERE appname = '{object_name}';"
        row = self.cursor.execute(query)
        row = row.fetchone()
        row = [ None if r == "None" else r for r in row ]
        self.cursor.close()
        self.conn.close()

        self.app_name.setText(row[0])
        self.user_name.setText(row[1])
        self.email.setText(row[2])
        self.password.setText(row[3])
        self.url.setText(row[4])
        if row[5] == "aktif":
            self.visible.clear()
            self.visible.setText("True")
            self.change_visibility.setChecked(True)
        else:
            self.visible.clear()
            self.visible.setText("False")
            self.change_visibility.setChecked(False)

    
    def get_objects(self):
        
        self.connect_database()
        self.objects_list.clear()
        query = "SELECT appname, aktifpasif FROM passwords;"
        rows = self.cursor.execute(query)
        rows = rows.fetchall()

        if self.control:
            appnames = [ "   " + row[0] for row in rows ]
            appnames.sort(key=locale.strxfrm)
            self.objects_list.addItems(appnames)
        else:
            appnames = []
            for appname, aktifpasif in rows:
                if aktifpasif == "aktif":
                    appnames.append("   " + appname)
            appnames.sort(key=locale.strxfrm)
            self.objects_list.addItems(appnames)
        self.cursor.close()
        self.conn.close()
        

    def clear_function(self):

        self.app_name.clear()
        self.user_name.clear()
        self.email.clear()
        self.password.clear()
        self.url.clear()
        self.visible.clear()
        self.visible.setText("True")
        self.change_visibility.setChecked(True)
        self.random_password.clear()
        

    def insert_function(self):
        
        app_name = self.app_name.text().strip()
        user_name = self.user_name.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        url = self.url.toPlainText().strip()
        aktifpasif = self.change_visibility.isChecked()
        if aktifpasif:
            aktifpasif = "aktif"
        else:
            aktifpasif = "pasif"
            
        if app_name == "" or password == "":
            QMessageBox.warning(self, "warning", "App name and password must be given")
            return
        
        self.connect_database()
        
        try:
            query1 = f"SELECT appname FROM passwords WHERE appname = '{app_name}';"
            row = self.cursor.execute(query1)
            row = row.fetchone()
            
        except:
            QMessageBox.warning(self, "failure", "An unknown error occured")
            return
        
        if row == None:
            try:
                query2 = f"""INSERT INTO passwords (appname, username, email, password, url, aktifpasif) 
                            VALUES ('{app_name}', '{user_name}', '{email}', '{password}', '{url}', '{aktifpasif}');"""
                self.cursor.execute(query2)

                answer = QMessageBox.question(
                    self, 
                    "Final warning", 
                    f"""Are you sure you want to insert a new value with app name '{app_name}'. The following values will be inserted\n\tuser name = '{user_name}'\n\temail = '{email}'\n\tpassword = '{password}'\n\turl = '{url}'\n\tvisibility = '{aktifpasif}'""",
                    buttons=QMessageBox.Yes | QMessageBox.No                         
                )
                if answer == QMessageBox.Yes:
                    self.conn.commit()
                    self.cursor.close()
                    self.conn.close()
                    self.get_objects()
                    if aktifpasif == "pasif" and self.show_pasive_objects.isChecked() == False:
                        self.clear_function()
                    QMessageBox.information(self, "success", "new object has added to database")
                elif answer == QMessageBox.No:
                    self.cursor.close()
                    self.conn.close()
                else:
                    pass
                
            except:
                QMessageBox.warning(self, "failure", "An unknown error occured")
        else:
            QMessageBox.warning(self, "warning", "The givin app name already exists in database")
        
    
    def update_function(self):
       
        app_name = self.app_name.text().strip()
        user_name = self.user_name.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        url = self.url.toPlainText().strip()
        aktifpasif = self.change_visibility.isChecked()
        if aktifpasif:
            aktifpasif = "aktif"
        else:
            aktifpasif = "pasif"
            
        if app_name == "" or password == "":
            QMessageBox.warning(self, "warning", "App name must be given")
            return
        
        self.connect_database()
        
        try:
            query1 = f"SELECT appname FROM passwords WHERE appname = '{app_name}';"
            row = self.cursor.execute(query1)
            row = row.fetchone()
            
        except:
            QMessageBox.warning(self, "failure", "An unknown error occured")
            return
        
        if row == None:
            QMessageBox.warning(self, "warning", "The givin app name does not exists in database")
            
        else:
            query2 = f"""UPDATE passwords 
                        SET username = '{user_name}', email = '{email}', password = '{password}', url = '{url}', aktifpasif = '{aktifpasif}' 
                        WHERE appname = '{app_name}';"""
            self.cursor.execute(query2)
            
            answer = QMessageBox.question(
                self, 
                "Final warning", 
                f"""Are you sure you want to update '{app_name}'. The following values will be replaced with\n\tuser name = '{user_name}'\n\temail = '{email}'\n\tpassword = '{password}'\n\turl = '{url}'\n\tvisibility = '{aktifpasif}'""",
                    buttons=QMessageBox.Yes | QMessageBox.No                         
            )
            if answer == QMessageBox.Yes:
                self.conn.commit()
                self.cursor.close()
                self.conn.close()
                self.get_objects()
                if aktifpasif == "pasif" and self.show_pasive_objects.isChecked() == False:
                    self.clear_function()
                QMessageBox.information(self, "success", "Object has updated to database")
            elif answer == QMessageBox.No:
                self.cursor.close()
                self.conn.close()
            else:
                pass


    def delete_funtion(self):
        
        app_name = self.app_name.text().strip()
        if app_name == "":
            QMessageBox.warning(self, "warning", "App name must be givin")
            return
        
        self.connect_database()
        
        try:
            query1 = f"SELECT appname FROM passwords WHERE appname = '{app_name}';"
            row = self.cursor.execute(query1)
            row = row.fetchone()
        except:
            QMessageBox.warning(self, "failure", "An unknown error occured")
            return
        
        if row == None:
            QMessageBox.warning(self, "warning", "The givin app name does not exists in database")
        else:
            try:
                query2 = f"DELETE FROM passwords WHERE appname = '{app_name}';"
                self.cursor.execute(query2)
                
                answer = QMessageBox.question(
                    self, 
                    "Final warning", 
                    f"Are you sure you want to delete '{app_name}'?",
                    buttons=QMessageBox.Yes | QMessageBox.No                         
                )
                if answer == QMessageBox.Yes:
                    self.conn.commit()
                    self.cursor.close()
                    self.conn.close()
                    self.get_objects()
                    self.clear_function()
                    QMessageBox.information(self, "success", "Object has deleted from database")
                elif answer == QMessageBox.No:
                    self.cursor.close()
                    self.conn.close()
                else:
                    pass
                
            except:
                QMessageBox.warning(self, "failure", "An unknown error occured")
                
        
    def layouts(self):
        
        left_groupbox = QGroupBox("apps, sites, etc", self)
        show_passive_objects_layout = QHBoxLayout()
        show_passive_objects_layout.addStretch()
        show_passive_objects_layout.addWidget(self.show_pasive_objects)
        show_passive_objects_layout.addStretch()
        
        left_layout = QVBoxLayout()
        left_layout.addStretch()
        left_layout.addLayout(show_passive_objects_layout)
        left_layout.addWidget(self.objects_list)
        left_layout.addStretch()
        left_groupbox.setLayout(left_layout)
        
        right_groupbox = QGroupBox("selected object information", self)
        right_layout = QVBoxLayout()  
        
        app_name_layout = QHBoxLayout()
        app_name_label_layout = QHBoxLayout()
        app_name_label_layout.addStretch()
        app_name_label_layout.addWidget(self.app_name_label)
        
        app_name_value_layout = QHBoxLayout()
        app_name_value_layout.addWidget(self.app_name)
        app_name_value_layout.addStretch()
        
        app_name_layout.addLayout(app_name_label_layout, 30)
        app_name_layout.addLayout(app_name_value_layout, 70)
        
        user_name_layout = QHBoxLayout()
        user_name_label_layout = QHBoxLayout()
        user_name_label_layout.addStretch()
        user_name_label_layout.addWidget(self.user_name_label)
        
        user_name_value_layout = QHBoxLayout()
        user_name_value_layout.addWidget(self.user_name)
        user_name_value_layout.addStretch()
        
        user_name_layout.addLayout(user_name_label_layout, 30)
        user_name_layout.addLayout(user_name_value_layout, 70)
        
        email_layout = QHBoxLayout()
        email_label_layout = QHBoxLayout()
        email_label_layout.addStretch()
        email_label_layout.addWidget(self.email_label)
        
        email_value_layout = QHBoxLayout()
        email_value_layout.addWidget(self.email)
        email_value_layout.addStretch()
        
        email_layout.addLayout(email_label_layout, 30)
        email_layout.addLayout(email_value_layout, 70)
        
        pass_word_layout = QHBoxLayout()
        pass_word_label_layout = QHBoxLayout()
        pass_word_label_layout.addStretch()
        pass_word_label_layout.addWidget(self.password_label)
        
        pass_word_value_layout = QHBoxLayout()
        pass_word_value_layout.addWidget(self.password)
        pass_word_value_layout.addStretch()
        
        pass_word_layout.addLayout(pass_word_label_layout, 30)
        pass_word_layout.addLayout(pass_word_value_layout, 70)
        
        url_layout = QHBoxLayout()
        url_label_layout = QHBoxLayout()
        url_label_layout.addStretch()
        url_label_layout.addWidget(self.url_label)
        
        url_value_layout = QHBoxLayout()
        url_value_layout.addWidget(self.url)
        url_value_layout.addStretch()
        
        url_layout.addLayout(url_label_layout, 30)
        url_layout.addLayout(url_value_layout, 70)
        
        visibility_layout = QHBoxLayout()
        visibility_label_layout = QHBoxLayout()
        visibility_label_layout.addStretch()
        visibility_label_layout.addWidget(self.change_visibility_label)
        
        visibility_value_layout = QHBoxLayout()
        visibility_value_layout.addWidget(self.change_visibility)
        visibility_value_layout.addWidget(self.visible)
        visibility_value_layout.addStretch()
        
        visibility_layout.addLayout(visibility_label_layout, 30)
        visibility_layout.addLayout(visibility_value_layout, 70)      

        button_layouts = QHBoxLayout()
        button_layouts.addStretch()
        button_layouts.addWidget(self.clear_button)
        button_layouts.addWidget(self.insert_button)
        button_layouts.addWidget(self.update_button)
        button_layouts.addWidget(self.delete_button)
        button_layouts.addStretch()
        
        password_button_layout = QHBoxLayout()
        password_button_layout.addStretch()
        password_button_layout.addWidget(self.create_password_button)
        password_button_layout.addStretch()
        
        random_password_layout = QHBoxLayout()
        random_password_layout.addStretch()
        random_password_layout.addWidget(self.random_password)
        random_password_layout.addStretch()

        right_layout.addStretch()
        right_layout.addLayout(app_name_layout)
        right_layout.addLayout(user_name_layout)
        right_layout.addLayout(email_layout)
        right_layout.addLayout(pass_word_layout)
        right_layout.addLayout(url_layout)
        right_layout.addLayout(visibility_layout)
        right_layout.addWidget(self.empty_space)
        right_layout.addLayout(button_layouts)
        right_layout.addLayout(password_button_layout)
        right_layout.addLayout(random_password_layout)
        right_layout.addStretch()
        
        right_groupbox.setLayout(right_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(left_groupbox, 45)
        main_layout.addWidget(right_groupbox, 55)
        
        main_widget = QGroupBox()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
