import streamlit as st
import random
import json
import os
from datetime import datetime

# ==========================
# CONFIGURACIÓN
# ==========================

ARCHIVO_PUNTAJES = "puntajes_casino_adivina.json"

FICHAS_INICIALES = 100
COSTO_PISTA = 5

DIFICULTADES = {
    "Fácil (1-50)": (1, 50, 7),
    "Normal (1-100)": (1, 100, 8),
    "Difícil (1-500)": (1, 500, 10)
}


# ==========================
# FUNCIONES JSON
# ==========================

def cargar_puntajes():
    if not os.path.exists(ARCHIVO_PUNTAJES):
        return []

    try:
        with open(ARCHIVO_PUNTAJES, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def guardar_puntajes(lista):
    with open(ARCHIVO_PUNTAJES, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)


def agregar_puntaje(nombre, fichas, ganadas, dificultad):

    datos = cargar_puntajes()

    datos.append({
        "nombre": nombre,
        "fichas": fichas,
        "ganadas": ganadas,
        "dificultad": dificultad,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    guardar_puntajes(datos)


# ==========================
# INSERTION SORT
# ==========================

def insertion_sort_por_fichas(lista):

    datos = lista.copy()

    for i in range(1, len(datos)):
        actual = datos[i]
        j = i - 1

        while j >= 0 and datos[j]["fichas"] < actual["fichas"]:
            datos[j + 1] = datos[j]
            j -= 1

        datos[j + 1] = actual

    return datos


# ==========================
# SESSION STATE
# ==========================

if "saldo" not in st.session_state:
    st.session_state.saldo = FICHAS_INICIALES

if "ganadas" not in st.session_state:
    st.session_state.ganadas = 0

if "numero_secreto" not in st.session_state:
    st.session_state.numero_secreto = None

if "ronda_activa" not in st.session_state:
    st.session_state.ronda_activa = False

if "intentos" not in st.session_state:
    st.session_state.intentos = 0

if "max_intentos" not in st.session_state:
    st.session_state.max_intentos = 0

if "apuesta_actual" not in st.session_state:
    st.session_state.apuesta_actual = 0


# ==========================
# INTERFAZ
# ==========================

st.set_page_config(
    page_title="Casino Adivina",
    page_icon="🎰",
    layout="centered"
)

st.title("🎰 CASINO ADIVINA")

nombre = st.text_input("👤 Jugador", "Jugador1")

dificultad = st.selectbox(
    "🎚️ Dificultad",
    list(DIFICULTADES.keys())
)

apuesta = st.selectbox(
    "💵 Apuesta",
    [10, 20, 50]
)

st.markdown("---")

st.metric("🪙 Fichas", st.session_state.saldo)
st.metric("🏆 Rondas ganadas", st.session_state.ganadas)

st.markdown("---")

# ==========================
# APOSTAR
# ==========================

if st.button("🎰 APOSTAR"):

    if st.session_state.ronda_activa:
        st.warning("Ya hay una ronda activa")
    else:

        if apuesta > st.session_state.saldo:
            st.error("No tienes suficientes fichas")
        else:

            minimo, maximo, max_int = DIFICULTADES[dificultad]

            st.session_state.saldo -= apuesta
            st.session_state.apuesta_actual = apuesta
            st.session_state.numero_secreto = random.randint(
                minimo,
                maximo
            )

            st.session_state.max_intentos = max_int
            st.session_state.intentos = 0
            st.session_state.ronda_activa = True
            st.session_state.minimo = minimo
            st.session_state.maximo = maximo

            st.success(
                f"Adivina un número entre {minimo} y {maximo}"
            )

# ==========================
# JUEGO
# ==========================

if st.session_state.ronda_activa:

    st.info(
        f"Número entre {st.session_state.minimo} y "
        f"{st.session_state.maximo}"
    )

    numero = st.number_input(
        "Tu número",
        min_value=int(st.session_state.minimo),
        max_value=int(st.session_state.maximo),
        step=1
    )

    col1, col2 = st.columns(2)

    # ADIVINAR

    with col1:

        if st.button("🎲 ADIVINAR"):

            st.session_state.intentos += 1

            if numero == st.session_state.numero_secreto:

                sobraron = (
                    st.session_state.max_intentos
                    - st.session_state.intentos
                )

                multiplicador = 2 + (sobraron // 2)

                premio = (
                    st.session_state.apuesta_actual
                    * multiplicador
                )

                st.session_state.saldo += premio
                st.session_state.ganadas += 1
                st.session_state.ronda_activa = False

                st.success(
                    f"🎉 Correcto. Ganaste {premio} fichas."
                )

            elif st.session_state.intentos >= st.session_state.max_intentos:

                st.session_state.ronda_activa = False

                st.error(
                    f"😢 Perdiste. El número era "
                    f"{st.session_state.numero_secreto}"
                )

            elif numero < st.session_state.numero_secreto:
                st.warning("⬆️ Más alto")

            else:
                st.warning("⬇️ Más bajo")

    # PISTA

    with col2:

        if st.button("💡 PISTA"):

            if st.session_state.saldo < COSTO_PISTA:
                st.error("No tienes fichas para una pista")

            else:

                st.session_state.saldo -= COSTO_PISTA

                paridad = (
                    "PAR"
                    if st.session_state.numero_secreto % 2 == 0
                    else "IMPAR"
                )

                st.success(
                    f"💡 El número es {paridad}"
                )

    st.write(
        f"Intentos: "
        f"{st.session_state.intentos}/"
        f"{st.session_state.max_intentos}"
    )

# ==========================
# RETIRARSE
# ==========================

st.markdown("---")

if st.button("💰 RETIRARME"):

    agregar_puntaje(
        nombre,
        st.session_state.saldo,
        st.session_state.ganadas,
        dificultad
    )

    st.success(
        f"Puntaje guardado con "
        f"{st.session_state.saldo} fichas."
    )

# ==========================
# RANKING
# ==========================

st.markdown("---")

if st.button("🏆 VER RANKING"):

    ranking = insertion_sort_por_fichas(
        cargar_puntajes()
    )

    if ranking:

        st.subheader("🏆 TOP JUGADORES")

        for i, jugador in enumerate(ranking[:10], start=1):

            st.write(
                f"{i}. "
                f"{jugador['nombre']} | "
                f"{jugador['fichas']} fichas | "
                f"{jugador['ganadas']} victorias"
            )

    else:
        st.info("Todavía no hay puntajes registrados.")
