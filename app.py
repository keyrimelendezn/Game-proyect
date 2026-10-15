"""KADB Casino Clash - versión web con Streamlit.
Cada jugador abre el link en su propio dispositivo; el Top 10 es compartido (ranking.json)."""
import html
import tempfile
import threading
import time
from pathlib import Path

import streamlit as st

import logica as L

st.set_page_config(page_title="KADB Casino Clash", page_icon="🃏", layout="centered")

COLORES = ["#5EEAD4", "#FB923C", "#F9A8D4", "#F87171", "#C4B5FD", "#60A5FA", "#FACC15", "#86EFAC"]

CSS = """
<style>
.timer{font-size:46px;font-weight:700;text-align:center;line-height:1.1}
.stage{width:150px;height:170px;margin:8px auto;border:5px solid var(--cc,#1F2A44);border-radius:16px;
 background:#0B0F19;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;text-align:center}
.stage b{font-size:26px}.stage small{font-size:12px;color:#C9D1D9;padding:0 6px}
.msg{min-height:1.5em;text-align:center;margin:6px 0 10px;font-weight:700}
.msg.ok{color:#39FF88}.msg.bad{color:#FF5C7A}.msg.hi{color:#58A6FF}.msg.lo{color:#FFB454}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:6px}
@media(min-width:640px){.grid{grid-template-columns:repeat(10,1fr)}}
.mc{border:2px solid #1F2A44;border-radius:8px;height:54px;display:flex;flex-direction:column;
 align-items:center;justify-content:center;color:#6B7A99;overflow:hidden}
.mc b{font-size:13px}.mc small{font-size:9px;color:#C9D1D9}.mc.on{background:#0B0F19}.mc.on b{color:#fff}
</style>
"""


# ---------------------------------------------------------------- recursos compartidos
@st.cache_resource
def candado():
    return threading.Lock()


@st.cache_resource
def ruta_ranking():
    base = Path(__file__).parent
    try:
        prueba = base / ".prueba_escritura"
        prueba.touch()
        prueba.unlink()
    except OSError:
        base = Path(tempfile.gettempdir())
    return base / "ranking.json"


# ---------------------------------------------------------------- estado de cada jugador
def init_estado():
    s = st.session_state
    s.setdefault("fase", "idle")          # idle | playing | over
    s.setdefault("nombre", "")
    s.setdefault("secret", 0)
    s.setdefault("ronda", 1)
    s.setdefault("tries", 0)
    s.setdefault("rtries", 0)
    s.setdefault("score", 0)
    s.setdefault("wins", 0)
    s.setdefault("fin", 0.0)
    s.setdefault("got", set())
    s.setdefault("ultima", None)
    s.setdefault("msg", ("> escribe tu nombre y pulsa jugar", "ok"))
    s.setdefault("resultado", None)


def iniciar(nombre):
    s = st.session_state
    s.fase = "playing"
    s.nombre = nombre
    s.secret = L.sorteo()
    s.ronda, s.tries, s.rtries, s.score, s.wins = 1, 0, 0, 0, 0
    s.fin = time.time() + L.DURACION
    s.got = set()
    s.ultima = None
    s.msg = ("> partida iniciada, ¡suerte!", "ok")
    s.resultado = None


def terminar():
    s = st.session_state
    if s.fase != "playing":
        return
    s.fase = "over"
    res = {"jugador": s.nombre, "puntaje": s.score, "intentos": s.tries, "wins": s.wins}
    try:
        L.guardar_resultado(ruta_ranking(), candado(), res)
    except OSError:
        pass
    s.resultado = res


def adivinar():
    """Se ejecuta al enviar el formulario 'guess( )'."""
    s = st.session_state
    if s.fase != "playing":
        return
    if s.fin - time.time() <= 0:
        terminar()
        return
    valor = s.get("guess_val")
    if valor is None:
        s.msg = ("✖ TypeError: escribe un número", "bad")
        return
    n = int(valor)
    s.tries += 1
    s.rtries += 1
    if n == s.secret:
        pts = L.puntos(s.rtries)
        idx = s.secret - 1
        s.score += pts
        s.wins += 1
        s.got.add(idx)
        s.ultima = idx
        s.msg = (f"✔ ¡Acierto! +{pts} pts · {L.CARDS[idx][0]}", "ok")
        s.ronda += 1
        s.rtries = 0
        s.secret = L.sorteo(s.secret)
    elif n < s.secret:
        s.msg = ("▲ Mayor", "hi")
    else:
        s.msg = ("▼ Menor", "lo")


# ---------------------------------------------------------------- piezas visuales
def carta_html(idx):
    if idx is None:
        return '<div class="stage"><b>?</b><small>secret = ?  # 1..20</small></div>'
    nombre, glifo = L.CARDS[idx]
    return (f'<div class="stage" style="--cc:{COLORES[idx % 8]}"><b>{html.escape(glifo)}</b>'
            f'<small>{html.escape(nombre.upper())}</small></div>')


def coleccion_html(got):
    celdas = []
    for i, (nombre, glifo) in enumerate(L.CARDS):
        if i in got:
            celdas.append(f'<div class="mc on" style="border-color:{COLORES[i % 8]}">'
                          f'<b>{html.escape(glifo)}</b><small>{html.escape(nombre)}</small></div>')
        else:
            celdas.append(f'<div class="mc"><b>{i + 1}</b></div>')
    return '<div class="grid">' + "".join(celdas) + "</div>"


@st.fragment(run_every=1)
def panel_juego():
    """Se actualiza solo cada segundo (temporizador). Los clics solo recargan este bloque."""
    s = st.session_state
    if s.fase != "playing":
        st.rerun()
        return
    restante = int(s.fin - time.time())
    if restante <= 0:
        terminar()
        st.rerun()
        return
    m, seg = divmod(restante, 60)
    color = "#FF5C7A" if restante <= 10 else "#39FF88"
    st.markdown(f'<div class="timer" style="color:{color}">{m:02d}:{seg:02d}</div>', unsafe_allow_html=True)
    st.caption(f"player = {s.nombre} · tries={s.tries} · pts={s.score} · wins={s.wins} · round={s.ronda}")
    st.markdown(carta_html(s.ultima), unsafe_allow_html=True)
    texto, tipo = s.msg
    st.markdown(f'<div class="msg {tipo}">{html.escape(texto)}</div>', unsafe_allow_html=True)
    with st.form("form_guess", clear_on_submit=True):
        st.number_input("guess( )", min_value=1, max_value=len(L.CARDS), step=1, value=None,
                        placeholder=f"1-{len(L.CARDS)}", key="guess_val")
        st.form_submit_button("run ▶", on_click=adivinar, type="primary")
    st.markdown(f"**colección.json** — {len(s.got)}/{len(L.CARDS)} cartas desbloqueadas")
    st.markdown(coleccion_html(s.got), unsafe_allow_html=True)


def pantalla_final():
    s = st.session_state
    r = s.resultado or {"jugador": s.nombre, "puntaje": 0, "wins": 0, "intentos": 0}
    st.markdown(carta_html(s.ultima), unsafe_allow_html=True)
    if r["wins"]:
        st.success(f"GAME OVER · {r['jugador']}: {r['puntaje']} pts · {r['wins']} wins · {r['intentos']} intentos")
    else:
        st.info("GAME OVER · nadie acertó esta vez. ¡Revancha!")
    st.markdown(f"**colección.json** — {len(s.got)}/{len(L.CARDS)} cartas desbloqueadas")
    st.markdown(coleccion_html(s.got), unsafe_allow_html=True)
    if st.button("↺ jugar de nuevo", type="primary"):
        s.fase = "idle"
        st.rerun()


@st.fragment(run_every=5)
def mostrar_ranking():
    """Top 10 compartido, ordenado con el insertion sort propio. Se refresca cada 5 s."""
    ranking = L.ordenar_ranking(L.cargar_ranking(ruta_ranking()))
    st.subheader("★ Top 10")
    if not ranking:
        st.caption("// aún no hay puntajes")
        return
    medallas = ["🥇", "🥈", "🥉"]
    filas = ["| # | Jugador | Pts | Wins | Intentos |", "|---|---|---:|---:|---:|"]
    for i, r in enumerate(ranking):
        pos = medallas[i] if i < 3 else str(i + 1)
        filas.append(f"| {pos} | {L.limpiar_nombre(r['jugador'])} | {r['puntaje']} | "
                     f"{r.get('wins', 0)} | {r['intentos']} |")
    st.markdown("\n".join(filas))


# ---------------------------------------------------------------- app
init_estado()
st.markdown(CSS, unsafe_allow_html=True)
st.title("kadb_casino_clash():")
st.caption("# adivina la carta de programación · 3 min · rango 1-20")

s = st.session_state
if s.fase == "idle":
    with st.form("form_nombre"):
        nombre = st.text_input("player =", value=s.nombre, max_chars=12, placeholder="tu nombre")
        jugar = st.form_submit_button("▶ jugar (3 min)", type="primary")
    if jugar:
        iniciar(L.limpiar_nombre(nombre))
        st.rerun()
elif s.fase == "playing":
    panel_juego()
else:
    pantalla_final()

st.divider()
mostrar_ranking()
