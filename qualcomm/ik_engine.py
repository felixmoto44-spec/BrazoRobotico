"""
Motor de cinemática inversa: MediaPipe landmarks → ángulos de servos

Usa los ángulos reales de las articulaciones (MCP, PIP) para calcular 
la flexión de cada dedo y mapearla al rango 0-180° del servo.

Landmarks MediaPipe (índices):
  0: WRIST        5: INDEX_MCP      9: MIDDLE_MCP    13: RING_MCP    17: PINKY_MCP
  1: THUMB_CMC     6: INDEX_PIP     10: MIDDLE_PIP    14: RING_PIP    18: PINKY_PIP
  2: THUMB_MCP     7: INDEX_DIP     11: MIDDLE_DIP    15: RING_DIP    19: PINKY_DIP
  3: THUMB_IP      8: INDEX_TIP     12: MIDDLE_TIP    16: RING_TIP    20: PINKY_TIP
  4: THUMB_TIP
"""

import math
from typing import List, Dict


def landmarks_to_angles_pro(
    landmarks: List[Dict[str, float]],
    min_angle: int = 0,
    max_angle: int = 180
) -> List[float]:
    """
    Calcula los ángulos de 5 servos a partir de los 21 landmarks de MediaPipe.
    """
    if not landmarks or len(landmarks) < 21:
        return [90.0] * 5

    lm = landmarks
    angles = []

    # Pulgar: combinación de ángulo MCP y distancia al índice
    try:
        thumb_angle = angle_at_joint(lm, 0, 2, 4)
        dist_to_index = math.dist(
            (lm[4]["x"], lm[4]["y"]),
            (lm[5]["x"], lm[5]["y"])
        )
        thumb_servo = thumb_angle * 0.4 + (1.0 - dist_to_index * 10) * 180 * 0.6
        thumb_servo = max(min_angle, min(max_angle, thumb_servo))
    except (IndexError, KeyError):
        thumb_servo = 90.0
    angles.append(thumb_servo)

    # 4 dedos largos: ángulo en articulación PIP → servo
    fingers = [
        (5, 6, 8, "Índice"),
        (9, 10, 12, "Corazón"),
        (13, 14, 16, "Anular"),
        (17, 18, 20, "Meñique"),
    ]

    for mcp, pip, tip, name in fingers:
        try:
            flexion = angle_at_joint(lm, mcp, pip, tip)
            servo = max(min_angle, min(max_angle, 180 - flexion))
        except (IndexError, KeyError):
            servo = 90.0
        angles.append(servo)

    return angles


def angle_at_joint(lm, a, b, c) -> float:
    """
    Ángulo en el punto B formado por los vectores B→C y B→A.
    Retorna grados (0° = completamente cerrado, 180° = completamente abierto).
    """
    v1 = (lm[c]["x"] - lm[b]["x"], lm[c]["y"] - lm[b]["y"])
    v2 = (lm[a]["x"] - lm[b]["x"], lm[a]["y"] - lm[b]["y"])

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    m1 = math.sqrt(v1[0]**2 + v1[1]**2)
    m2 = math.sqrt(v2[0]**2 + v2[1]**2)

    if m1 < 1e-9 or m2 < 1e-9:
        return 180.0

    cos_val = max(-1.0, min(1.0, dot / (m1 * m2)))
    return math.degrees(math.acos(cos_val))
