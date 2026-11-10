"""Agente inteligente para el juego Clobber.

El agente controla al jugador B y utiliza Minimax con poda Alfa-Beta,
heurística de control territorial, aislamiento del rival y agrupación en bloques.
"""

from math import inf
from clobber import Clobber


# El agente corresponde al jugador MAX.
JUGADOR_AGENTE = Clobber.PLAYER_B

# El humano corresponde al jugador MIN.
JUGADOR_HUMANO = Clobber.PLAYER_A

# Contador de estados analizados.
tableros_revisados = 0


def clonar_tablero(tablero):
    """Crea una copia rápida del tablero sin la sobrecarga de deepcopy."""
    nuevo = Clobber.__new__(Clobber)
    nuevo._size = tablero._size
    nuevo._places = [fila[:] for fila in tablero._places]
    return nuevo


def estimacion(tablero):
    """Calcula la estimación heurística del estado del tablero.

    Criterios de evaluación:
    1. Agrupación sólida: Bonificación (+5) por cada subbloque de 2x2 del agente.
    2. Movilidad neta: Diferencia entre movimientos del agente y del rival.
    3. Aislamiento del rival: Bonificación (+3) por fichas del oponente sin fichas del agente adyacentes.
    4. Penalización por bordes/esquinas: Reducción moderada en bordes (-1) y esquinas (-3).

    Returns:
        Puntaje heurístico para el agente B (MAX).
    """
    places = tablero._places
    n = tablero._size
    
    score = 0.0

    # 1. EVALUACIÓN DE AGRUPACIÓN EN BLOQUES (2x2 Y RECTÁNGULOS)
    # Detecta cada subcuadro 2x2 compuesto únicamente por fichas del agente
    for r in range(n - 1):
        for c in range(n - 1):
            if (places[r][c] == JUGADOR_AGENTE and
                places[r+1][c] == JUGADOR_AGENTE and
                places[r][c+1] == JUGADOR_AGENTE and
                places[r+1][c+1] == JUGADOR_AGENTE):
                score += 5.0

    # 2. EVALUACIÓN DE MOVILIDAD NETA Y ATACANTES DEL RIVAL
    movs_agente = len(tablero.movimientos_legales(JUGADOR_AGENTE))
    movs_humano = tablero.movimientos_legales(JUGADOR_HUMANO)
    
    # La base de Clobber: a mayor diferencia a favor del agente, mejor posición
    score += (movs_agente - len(movs_humano)) * 2.0

    # 3. EVALUACIÓN POSICIONAL Y AISLAMIENTO DEL RIVAL
    direcciones = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for r in range(n):
        for c in range(n):
            pieza = places[r][c]
            
            # Penalización suave de bordes para evitar desventaja táctica involuntaria
            if pieza == JUGADOR_AGENTE:
                es_borde_r = (r == 0 or r == n - 1)
                es_borde_c = (c == 0 or c == n - 1)
                
                if es_borde_r and es_borde_c:
                    score -= 3.0
                elif es_borde_r or es_borde_c:
                    score -= 1.0

            # Aislar fichas enemigas (dejar sin fichas del agente a su alrededor)
            elif pieza == JUGADOR_HUMANO:
                tiene_agente_alrededor = False
                for dr, dc in direcciones:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        if places[nr][nc] == JUGADOR_AGENTE:
                            tiene_agente_alrededor = True
                            break
                
                if not tiene_agente_alrededor:
                    score += 3.0

    return score


def ordenar_movimientos(tablero, jugador, movimientos):
    """Ordena las jugadas según la heurística para favorecer podas Alfa-Beta tempranas."""
    movimientos_evaluados = []

    for movimiento in movimientos:
        simulacion = clonar_tablero(tablero)
        simulacion.play(*movimiento, player=jugador)
        valor = estimacion(simulacion)
        movimientos_evaluados.append((valor, movimiento))

    if jugador == JUGADOR_AGENTE:
        movimientos_evaluados.sort(key=lambda elemento: elemento[0], reverse=True)
    else:
        movimientos_evaluados.sort(key=lambda elemento: elemento[0])

    return [movimiento for _, movimiento in movimientos_evaluados]


def alfa_beta(tablero, le_toca_al_agente, alfa, beta, profundidad=5):
    """Calcula el valor Minimax con poda Alfa-Beta y límite de profundidad."""
    global tableros_revisados
    tableros_revisados += 1

    jugador_actual = JUGADOR_AGENTE if le_toca_al_agente else JUGADOR_HUMANO
    movimientos = tablero.movimientos_legales(jugador_actual)

    # ---------------------------------------------------------------
    # CASOS BASE
    # ---------------------------------------------------------------
    if not movimientos:
        return -10000.0 if le_toca_al_agente else 10000.0

    if profundidad == 0:
        return estimacion(tablero)

    movimientos = ordenar_movimientos(tablero, jugador_actual, movimientos)

    # ---------------------------------------------------------------
    # TURNO DEL AGENTE (MAX)
    # ---------------------------------------------------------------
    if le_toca_al_agente:
        mejor_puntaje = -inf

        for movimiento in movimientos:
            simulacion = clonar_tablero(tablero)
            simulacion.play(*movimiento, player=JUGADOR_AGENTE)

            puntaje = alfa_beta(simulacion, False, alfa, beta, profundidad - 1)
            mejor_puntaje = max(puntaje, mejor_puntaje)
            alfa = max(alfa, mejor_puntaje)

            if alfa >= beta:
                break

        return mejor_puntaje

    # ---------------------------------------------------------------
    # TURNO DEL HUMANO (MIN)
    # ---------------------------------------------------------------
    else:
        mejor_puntaje = inf

        for movimiento in movimientos:
            simulacion = clonar_tablero(tablero)
            simulacion.play(*movimiento, player=JUGADOR_HUMANO)

            puntaje = alfa_beta(simulacion, True, alfa, beta, profundidad - 1)
            mejor_puntaje = min(puntaje, mejor_puntaje)
            beta = min(beta, mejor_puntaje)

            if alfa >= beta:
                break

        return mejor_puntaje


def mejor_movimiento(tablero, profundidad=4):
    """Selecciona el movimiento óptimo para B dentro de la profundidad límite.

    Una profundidad de 5 ofrece un equilibrio entre fuerza de juego y
    rapidez de respuesta.
    """
    global tableros_revisados

    movimientos = tablero.movimientos_legales(JUGADOR_AGENTE)
    if not movimientos:
        return None

    mejor_puntaje = -inf
    movimiento_elegido = None
    tableros_revisados = 0

    movimientos = ordenar_movimientos(tablero, JUGADOR_AGENTE, movimientos)

    for movimiento in movimientos:
        simulacion = clonar_tablero(tablero)
        simulacion.play(*movimiento, player=JUGADOR_AGENTE)

        puntaje = alfa_beta(simulacion, False, mejor_puntaje, inf, profundidad - 1)

        print(f"Movimiento {movimiento} -> valor Minimax: {puntaje:.2f}")

        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            movimiento_elegido = movimiento

    print(f"Número de tableros revisados: {tableros_revisados}")
    print(f"Valor Minimax de la jugada elegida: {mejor_puntaje:.2f}")

    return movimiento_elegido