import json
import cv2
import numpy as np
import face_recognition
import mysql.connector
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.list import OneLineListItem

# Configura tu conexión MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'reconocimiento'
}

def conectar():
    return mysql.connector.connect(**DB_CONFIG)

def capturar_rostro():
    cap = cv2.VideoCapture(0)
    rostro_codificado = None

    print("[INFO] Escanea tu rostro... Presiona 'q' para capturar")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detectar rostros
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        caras = face_recognition.face_locations(rgb)

        for (top, right, bottom, left) in caras:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.imshow("Presiona 'q' para capturar", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') and caras:
            rostro_codificado = face_recognition.face_encodings(rgb, caras)[0]
            break

    cap.release()
    cv2.destroyAllWindows()

    if rostro_codificado is not None:
        return json.dumps(rostro_codificado.tolist())  # convertir a JSON
    else:
        return None

def verificar_rostro(encoding_guardado):
    cap = cv2.VideoCapture(0)
    resultado = False
    print("[INFO] Verificando rostro...")

    try:
        encoding_guardado = np.array(json.loads(encoding_guardado))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            caras = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, caras)

            for encoding_actual in encodings:
                matches = face_recognition.compare_faces([encoding_guardado], encoding_actual)
                if matches[0]:
                    resultado = True
                    break

            cv2.imshow("Verificación Facial - Presiona 'q' para salir", frame)

            if resultado or cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        return resultado


class RegistroScreen(MDScreen):
    dialog = None

    def registrar_usuario(self):
        usuario = self.ids.reg_usuario.text.strip()
        contrasena = self.ids.reg_contrasena.text.strip()

        if not usuario or not contrasena:
            self.mostrar_dialogo("Error", "Completa todos los campos.")
            return

        rostro = capturar_rostro()
        if not rostro:
            self.mostrar_dialogo("Error", "No se pudo capturar rostro.")
            return

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (usuario, contrasena, rostro_encoding) VALUES (%s, %s, %s)",
                           (usuario, contrasena, rostro))
            conn.commit()
            self.ids.reg_usuario.text = ""
            self.ids.reg_contrasena.text = ""
            self.mostrar_dialogo("Éxito", "Usuario registrado correctamente.")
        except mysql.connector.IntegrityError:
            self.mostrar_dialogo("Error", "El usuario ya existe.")
        finally:
            cursor.close()
            conn.close()

    def mostrar_dialogo(self, titulo, mensaje):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(title=titulo, text=mensaje,
                               buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

class LoginScreen(MDScreen):
    dialog = None

    def iniciar_sesion(self):
        usuario = self.ids.login_usuario.text.strip()
        contrasena = self.ids.login_contrasena.text.strip()

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT rostro_encoding FROM usuarios WHERE usuario=%s AND contrasena=%s",
                           (usuario, contrasena))
            resultado = cursor.fetchone()
            if resultado:
                encoding_guardado = resultado[0]
                if verificar_rostro(encoding_guardado):
                    self.manager.current = 'usuarios'
                    self.manager.get_screen('usuarios').mostrar_usuarios()
                    self.ids.login_usuario.text = ""
                    self.ids.login_contrasena.text = ""
                else:
                    self.mostrar_dialogo("Error", "Rostro no coincide.")
            else:
                self.mostrar_dialogo("Error", "Usuario o contraseña incorrectos.")
        finally:
            cursor.close()
            conn.close()

    def mostrar_dialogo(self, titulo, mensaje):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(title=titulo, text=mensaje,
                               buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

class UsuariosScreen(MDScreen):
    def mostrar_usuarios(self):
        self.ids.lista_usuarios.clear_widgets()
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios")
        for (usuario,) in cursor.fetchall():
            self.ids.lista_usuarios.add_widget(OneLineListItem(text=usuario))
        cursor.close()
        conn.close()

class AppFacial(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return Builder.load_file("ui.kv")

if __name__ == '__main__':
    AppFacial().run()
