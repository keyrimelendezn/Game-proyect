"""
Adivina el Número - versión CASINO
===================================
- GUI hecha con Tkinter (mismos colores rosado/lila de antes).
- El jugador empieza con 100 fichas y apuesta en cada ronda.
- Tiene un número limitado de intentos para adivinar (según la dificultad).
- Mientras menos intentos use, más gana:
      premio = apuesta x (2 + intentos_que_le_sobraron // 2)
- Si se queda sin intentos, pierde la apuesta.
- Se puede pedir una pista (par/impar) que cuesta 5 fichas.
- Al retirarse (o quedarse sin fichas) el puntaje se guarda en un JSON.
- El ranking (Top 10, por fichas) se ordena con un algoritmo propio
  (Insertion Sort), sin usar sorted() ni list.sort().

Se usa desde el menú principal (menu.py): la clase JuegoAdivinanza
hereda de tk.Frame y recibe (parent, volver_menu).
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import random
from datetime import datetime

from estilo_casino import (
    COLOR_FONDO, COLOR_PANEL, COLOR_PANEL_2, COLOR_TEXTO, COLOR_TEXTO_SUAVE,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_EXITO, COLOR_EXITO_HOVER,
    COLOR_ALERTA, COLOR_ALERTA_HOVER, COLOR_INFO, COLOR_INFO_HOVER,
    COLOR_ORO, COLOR_ORO_HOVER, BotonEstilizado, LetreroLuces,
)

# -------------------------------------------------------------------
# Configuración general
# -------------------------------------------------------------------
ARCHIVO_PUNTAJES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "puntajes_casino_adivina.json")
TOP_N = 10

FICHAS_INICIALES = 100
APUESTA_MINIMA = 10
COSTO_PISTA = 5
APUESTAS = ["10", "20", "50"]

# nombre: (mínimo, máximo, intentos permitidos)
DIFICULTADES = {
    "Fácil (1-50)": (1, 50, 7),
    "Normal (1-100)": (1, 100, 8),
    "Difícil (1-500)": (1, 500, 10),
}


# -------------------------------------------------------------------
# Manejo de datos (leer y escribir el JSON de puntajes)
# -------------------------------------------------------------------
def cargar_puntajes():
    if not os.path.exists(ARCHIVO_PUNTAJES):
        return []
    try:
        with open(ARCHIVO_PUNTAJES, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def guardar_puntajes(lista_puntajes):
    with open(ARCHIVO_PUNTAJES, "w", encoding="utf-8") as f:
        json.dump(lista_puntajes, f, indent=4, ensure_ascii=False)


def agregar_puntaje(nombre, fichas, ganadas, dificultad):
    puntajes = cargar_puntajes()
    puntajes.append({
        "nombre": nombre,
        "fichas": fichas,
        "ganadas": ganadas,
        "dificultad": dificultad,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    guardar_puntajes(puntajes)


# -------------------------------------------------------------------
# ALGORITMO DE ORDENAMIENTO PROPIO: Insertion Sort
# -------------------------------------------------------------------
def insertion_sort_por_fichas(lista):
    """Ordena de MAYOR a MENOR cantidad de fichas (Insertion Sort manual)."""
    datos = lista.copy()
    for i in range(1, len(datos)):
        actual = datos[i]
        j = i - 1
        while j >= 0 and datos[j]["fichas"] < actual["fichas"]:
            datos[j + 1] = datos[j]
            j -= 1
        datos[j + 1] = actual
    return datos


def obtener_top_n(n=TOP_N):
    puntajes = cargar_puntajes()
    return insertion_sort_por_fichas(puntajes)[:n]


# -------------------------------------------------------------------
# Interfaz gráfica principal
# -------------------------------------------------------------------
class JuegoAdivinanza(tk.Frame):
    def __init__(self, parent, volver_menu):
        super().__init__(parent, bg=COLOR_FONDO)
        self.volver_menu = volver_menu

        # Estado del juego
        self.saldo = FICHAS_INICIALES
        self.ganadas = 0
        self.ronda_activa = False
        self.apuesta_ronda = 0
        self.numero_secreto = None
        self.intentos = 0
        self.max_intentos = 0
        self.rango_ronda = (1, 100)

        self.rango_actual = tk.StringVar(value="Normal (1-100)")
        self.jugador_actual = tk.StringVar(value="Jugador1")
        self.apuesta_var = tk.StringVar(value=APUESTAS[0])

        self._crear_widgets()
        self._actualizar_saldo()

    # ---------------- construcción de la interfaz ----------------
    def _crear_widgets(self):
        # ---- Encabezado con luces de casino ----
        LetreroLuces(self, 480, 70, "🎰 CASINO ADIVINA 🎰", 18).pack()

        # ---- Panel principal ----
        panel = tk.Frame(self, bg=COLOR_FONDO)
        panel.pack(fill="both", expand=True, padx=20, pady=10)

        # -- Tarjeta: jugador, dificultad y apuesta --
        tarjeta_config = tk.Frame(panel, bg=COLOR_PANEL)
        tarjeta_config.pack(fill="x", pady=(0, 8))
        interior_config = tk.Frame(tarjeta_config, bg=COLOR_PANEL)
        interior_config.pack(fill="x", padx=15, pady=10)
        interior_config.columnconfigure((0, 1), weight=1)

        tk.Label(interior_config, text="👤 Jugador", font=("Helvetica", 10, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE).grid(row=0, column=0, sticky="w")
        entry_nombre = tk.Entry(
            interior_config, textvariable=self.jugador_actual, font=("Helvetica", 12),
            bg=COLOR_PANEL_2, fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO,
            relief="flat", justify="center"
        )
        entry_nombre.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8), ipady=5)

        tk.Label(interior_config, text="🎚️ Dificultad", font=("Helvetica", 10, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE).grid(row=2, column=0, sticky="w")
        tk.Label(interior_config, text="💵 Apuesta", font=("Helvetica", 10, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE).grid(row=2, column=1, sticky="w", padx=(8, 0))

        menu_dificultad = tk.OptionMenu(interior_config, self.rango_actual,
                                        *DIFICULTADES.keys())
        menu_dificultad.config(
            bg=COLOR_PANEL_2, fg=COLOR_TEXTO, font=("Helvetica", 11), relief="flat",
            highlightthickness=0, activebackground=COLOR_ACENTO, bd=0
        )
        menu_dificultad["menu"].config(bg=COLOR_PANEL_2, fg=COLOR_TEXTO)
        menu_dificultad.grid(row=3, column=0, sticky="ew", pady=(4, 0), ipady=3)

        menu_apuesta = tk.OptionMenu(interior_config, self.apuesta_var, *APUESTAS)
        menu_apuesta.config(
            bg=COLOR_PANEL_2, fg=COLOR_TEXTO, font=("Helvetica", 11), relief="flat",
            highlightthickness=0, activebackground=COLOR_ACENTO, bd=0
        )
        menu_apuesta["menu"].config(bg=COLOR_PANEL_2, fg=COLOR_TEXTO)
        menu_apuesta.grid(row=3, column=1, sticky="ew", pady=(4, 0), padx=(8, 0), ipady=3)

        # -- Tarjeta: fichas --
        tarjeta_saldo = tk.Frame(panel, bg=COLOR_PANEL)
        tarjeta_saldo.pack(fill="x", pady=(0, 8))
        self.label_saldo = tk.Label(tarjeta_saldo, text="", font=("Helvetica", 18, "bold"),
                                    bg=COLOR_PANEL, fg=COLOR_ACENTO)
        self.label_saldo.pack(pady=(8, 0))
        self.label_ganadas = tk.Label(tarjeta_saldo, text="", font=("Helvetica", 10),
                                      bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE)
        self.label_ganadas.pack(pady=(0, 8))

        # -- Tarjeta: juego --
        tarjeta_juego = tk.Frame(panel, bg=COLOR_PANEL)
        tarjeta_juego.pack(fill="x", pady=(0, 8))
        interior_juego = tk.Frame(tarjeta_juego, bg=COLOR_PANEL)
        interior_juego.pack(fill="x", padx=15, pady=10)

        self.label_rango = tk.Label(
            interior_juego, text="Haz tu apuesta y pulsa APOSTAR",
            font=("Helvetica", 11), bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE
        )
        self.label_rango.pack(pady=(0, 6))

        self.entry_guess = tk.Entry(
            interior_juego, font=("Helvetica", 20, "bold"), justify="center",
            bg=COLOR_PANEL_2, fg=COLOR_ACENTO, insertbackground=COLOR_TEXTO, relief="flat"
        )
        self.entry_guess.pack(fill="x", ipady=6, pady=(0, 8))
        self.entry_guess.bind("<Return>", lambda event: self._adivinar())

        BotonEstilizado(
            interior_juego, COLOR_ACENTO, COLOR_ACENTO_HOVER,
            text="🎲 ADIVINAR", command=self._adivinar
        ).pack(fill="x")

        # -- Retroalimentación --
        self.label_feedback = tk.Label(
            panel, text="¡Bienvenido al casino! 🍀", font=("Helvetica", 13, "bold"),
            bg=COLOR_FONDO, fg=COLOR_ACENTO, wraplength=400, height=2
        )
        self.label_feedback.pack(pady=(4, 0))

        self.label_intentos = tk.Label(
            panel, text="Intentos: 0", font=("Helvetica", 11),
            bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE
        )
        self.label_intentos.pack()

        # -- Botones inferiores --
        frame_botones = tk.Frame(panel, bg=COLOR_FONDO)
        frame_botones.pack(fill="x", pady=(8, 0))
        frame_botones.columnconfigure((0, 1), weight=1)

        BotonEstilizado(
            frame_botones, COLOR_ACENTO, COLOR_ACENTO_HOVER,
            text="🎰 APOSTAR", command=self._apostar
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=4)

        BotonEstilizado(
            frame_botones, COLOR_EXITO, COLOR_EXITO_HOVER,
            text=f"💡 Pista (-{COSTO_PISTA})", command=self._dar_pista
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=4)

        BotonEstilizado(
            frame_botones, COLOR_ORO, COLOR_ORO_HOVER,
            text="🏆 Ver ranking", command=self._mostrar_ranking
        ).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)

        BotonEstilizado(
            frame_botones, COLOR_INFO, COLOR_INFO_HOVER,
            text="💰 Retirarme", command=self._retirarse
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        BotonEstilizado(
            frame_botones, COLOR_ALERTA, COLOR_ALERTA_HOVER,
            text="🚪 Volver al menú", command=self.volver_menu
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)

    # ---------------- lógica del juego ----------------
    def _actualizar_saldo(self):
        self.label_saldo.config(text=f"🪙 Fichas: {self.saldo}")
        self.label_ganadas.config(text=f"Rondas ganadas: {self.ganadas}")

    def _apostar(self):
        """Empieza una ronda: descuenta la apuesta y genera el número secreto."""
        if self.ronda_activa:
            messagebox.showinfo("Ronda en curso",
                                "Termina la ronda actual antes de apostar de nuevo.")
            return

        apuesta = int(self.apuesta_var.get())
        if apuesta > self.saldo:
            messagebox.showwarning("Fichas insuficientes",
                                   f"Solo tienes {self.saldo} fichas. Elige una apuesta menor.")
            return

        minimo, maximo, max_intentos = DIFICULTADES[self.rango_actual.get()]
        self.saldo -= apuesta
        self.apuesta_ronda = apuesta
        self.numero_secreto = random.randint(minimo, maximo)
        self.rango_ronda = (minimo, maximo)
        self.max_intentos = max_intentos
        self.intentos = 0
        self.ronda_activa = True

        self._actualizar_saldo()
        self.label_rango.config(text=f"Adivina un número entre {minimo} y {maximo}")
        self.label_feedback.config(
            text=f"Apostaste {apuesta} fichas. ¡Suerte! 🍀", fg=COLOR_ACENTO)
        self.label_intentos.config(text=f"Intentos: 0 / {max_intentos}")
        self.entry_guess.delete(0, tk.END)
        self.entry_guess.focus()

    def _adivinar(self):
        if not self.ronda_activa:
            self.label_feedback.config(text="Primero haz tu apuesta 🎰", fg=COLOR_ALERTA)
            return

        valor = self.entry_guess.get().strip()
        minimo, maximo = self.rango_ronda

        if not valor.lstrip("-").isdigit():
            messagebox.showwarning("Entrada inválida", "Por favor ingresa un número entero.")
            return

        guess = int(valor)
        if guess < minimo or guess > maximo:
            messagebox.showwarning("Fuera de rango",
                                   f"El número debe estar entre {minimo} y {maximo}.")
            return

        self.intentos += 1
        self.label_intentos.config(text=f"Intentos: {self.intentos} / {self.max_intentos}")
        self.entry_guess.delete(0, tk.END)
        self.entry_guess.focus()

        if guess == self.numero_secreto:
            self._ganar_ronda()
        elif self.intentos >= self.max_intentos:
            self._perder_ronda()
        elif guess < self.numero_secreto:
            self.label_feedback.config(text="⬆️ Muy bajo, intenta más alto", fg=COLOR_INFO)
        else:
            self.label_feedback.config(text="⬇️ Muy alto, intenta más bajo", fg=COLOR_ALERTA)

    def _ganar_ronda(self):
        sobraron = self.max_intentos - self.intentos
        multiplicador = 2 + sobraron // 2
        premio = self.apuesta_ronda * multiplicador
        self.saldo += premio
        self.ganadas += 1
        self.ronda_activa = False
        self._actualizar_saldo()
        self.label_feedback.config(
            text=f"🎉 ¡Correcto! Ganas {premio} fichas (x{multiplicador})", fg=COLOR_EXITO)

    def _perder_ronda(self):
        self.ronda_activa = False
        self.label_feedback.config(
            text=f"😢 Sin intentos. El número era {self.numero_secreto}", fg=COLOR_ALERTA)
        self._revisar_quiebra()

    def _revisar_quiebra(self):
        """Si ya no alcanza ni para la apuesta mínima, termina la sesión."""
        if self.saldo < APUESTA_MINIMA:
            messagebox.showinfo("Sin fichas",
                                "Te quedaste sin fichas. Tu puntaje se guardará en el ranking.")
            self._guardar_y_reiniciar()

    def _dar_pista(self):
        """Pista: dice si el número es par o impar. Cuesta fichas."""
        if not self.ronda_activa:
            self.label_feedback.config(text="Las pistas se piden durante una ronda", fg=COLOR_ALERTA)
            return
        if self.saldo < COSTO_PISTA:
            messagebox.showwarning("Fichas insuficientes",
                                   f"Una pista cuesta {COSTO_PISTA} fichas.")
            return
        self.saldo -= COSTO_PISTA
        self._actualizar_saldo()
        paridad = "par" if self.numero_secreto % 2 == 0 else "impar"
        self.label_feedback.config(text=f"💡 Pista: el número es {paridad}", fg=COLOR_EXITO)

    def _retirarse(self):
        if self.ronda_activa:
            messagebox.showinfo("Ronda en curso", "Termina la ronda antes de retirarte.")
            return
        nombre = self.jugador_actual.get().strip() or "Anónimo"
        messagebox.showinfo("Te retiras",
                            f"{nombre}, te retiras con {self.saldo} fichas.\n"
                            "Tu puntaje quedó guardado en el ranking.")
        self._guardar_y_reiniciar()

    def _guardar_y_reiniciar(self):
        nombre = self.jugador_actual.get().strip() or "Anónimo"
        agregar_puntaje(nombre, self.saldo, self.ganadas, self.rango_actual.get())
        self.saldo = FICHAS_INICIALES
        self.ganadas = 0
        self.ronda_activa = False
        self._actualizar_saldo()
        self.label_rango.config(text="Haz tu apuesta y pulsa APOSTAR")
        self.label_feedback.config(text="¡Nueva partida! 🍀", fg=COLOR_ACENTO)
        self.label_intentos.config(text="Intentos: 0")
        self.entry_guess.delete(0, tk.END)

    # ---------------- ventana de ranking ----------------
    def _mostrar_ranking(self):
        top = obtener_top_n(TOP_N)

        ventana = tk.Toplevel(self)
        ventana.title("🏆 Ranking - Top 10")
        ventana.geometry("440x460")
        ventana.configure(bg=COLOR_FONDO)
        ventana.resizable(False, False)

        header = tk.Frame(ventana, bg=COLOR_ACENTO, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="🏆 MEJORES PUNTAJES 🏆", font=("Helvetica", 15, "bold"),
            bg=COLOR_ACENTO, fg="white"
        ).pack(expand=True)

        contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
        contenedor.pack(fill="both", expand=True, padx=15, pady=15)

        if not top:
            tk.Label(
                contenedor, text="Todavía no hay puntajes registrados.",
                font=("Helvetica", 12), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE
            ).pack(pady=30)
            return

        encabezados = ["#", "Jugador", "Fichas", "Ganadas", "Dificultad"]
        anchos = [3, 9, 6, 7, 12]
        fila_encabezado = tk.Frame(contenedor, bg=COLOR_PANEL_2)
        fila_encabezado.pack(fill="x", pady=(0, 4))
        for col in range(len(encabezados)):
            tk.Label(
                fila_encabezado, text=encabezados[col], font=("Helvetica", 10, "bold"),
                bg=COLOR_PANEL_2, fg=COLOR_ACENTO, width=anchos[col], anchor="w"
            ).grid(row=0, column=col, padx=3, pady=6)

        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        for i, registro in enumerate(top, start=1):
            color_fila = COLOR_PANEL if i % 2 == 0 else COLOR_PANEL_2
            fila = tk.Frame(contenedor, bg=color_fila)
            fila.pack(fill="x")

            valores = [
                medallas.get(i, str(i)),
                registro["nombre"],
                str(registro["fichas"]),
                str(registro.get("ganadas", 0)),
                registro.get("dificultad", "-"),
            ]
            for col in range(len(valores)):
                tk.Label(fila, text=valores[col], font=("Helvetica", 10),
                         bg=color_fila, fg=COLOR_TEXTO, width=anchos[col],
                         anchor="w").grid(row=0, column=col, padx=3, pady=5)


# -------------------------------------------------------------------
# Para probar el juego solo (el menú ignora este bloque)
# -------------------------------------------------------------------
if __name__ == "__main__":
    ventana = tk.Tk()
    ventana.title("🎰 Casino Adivina")
    ventana.geometry("480x760")
    ventana.resizable(False, False)
    juego = JuegoAdivinanza(ventana, volver_menu=ventana.destroy)
    juego.pack(fill="both", expand=True)
    ventana.mainloop()
