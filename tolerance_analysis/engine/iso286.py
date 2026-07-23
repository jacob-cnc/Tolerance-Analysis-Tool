"""ISO 286 tolerance grade and fit class lookup tables.

Provides standard tolerance grades (IT01–IT18) and fundamental deviations
for common hole and shaft basis fits. Given a nominal size and a fit code
(e.g., H7, g6, js5), returns the upper and lower deviations in inches.

Reference: ISO 286-1:2010, ANSI B4.2

All internal values stored in millimeters, converted to inches on output.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class FitResult:
    """Result of a fit class lookup."""
    upper_deviation_mm: float   # Upper deviation from nominal (mm)
    lower_deviation_mm: float   # Lower deviation from nominal (mm)
    grade: int                  # IT grade number
    code: str                   # Full code (e.g., "H7")

    @property
    def upper_deviation_inch(self) -> float:
        return self.upper_deviation_mm / 25.4

    @property
    def lower_deviation_inch(self) -> float:
        return self.lower_deviation_mm / 25.4


# ISO 286 size ranges (mm): (over, up_to_including)
_SIZE_RANGES = [
    (0, 3),
    (3, 6),
    (6, 10),
    (10, 18),
    (18, 30),
    (30, 50),
    (50, 80),
    (80, 120),
    (120, 180),
    (180, 250),
    (250, 315),
    (315, 400),
    (400, 500),
]

# Standard tolerance grades IT01 through IT18 in micrometers
# Indexed by size range, then by IT grade (0=IT01, 1=IT0, 2=IT1, ... 20=IT18)
# For simplicity, we store IT1 through IT18 (indices 0-17)
# Values from ISO 286-1 tables
_IT_GRADES_UM = [
    # IT1, IT2, IT3, IT4, IT5, IT6, IT7, IT8, IT9, IT10, IT11, IT12, IT13, IT14, IT15, IT16, IT17, IT18
    [0.8, 1.2, 2, 3, 4, 6, 10, 14, 25, 40, 60, 100, 140, 250, 400, 600, 1000, 1400],      # 0-3
    [1.0, 1.5, 2.5, 4, 5, 8, 12, 18, 30, 48, 75, 120, 180, 300, 480, 750, 1200, 1800],     # 3-6
    [1.0, 1.5, 2.5, 4, 6, 9, 15, 22, 36, 58, 90, 150, 220, 360, 580, 900, 1500, 2200],     # 6-10
    [1.2, 2.0, 3, 5, 8, 11, 18, 27, 43, 70, 110, 180, 270, 430, 700, 1100, 1800, 2700],    # 10-18
    [1.5, 2.5, 4, 6, 9, 13, 21, 33, 52, 84, 130, 210, 330, 520, 840, 1300, 2100, 3300],    # 18-30
    [1.5, 2.5, 4, 7, 11, 16, 25, 39, 62, 100, 160, 250, 390, 620, 1000, 1600, 2500, 3900], # 30-50
    [2.0, 3.0, 5, 8, 13, 19, 30, 46, 74, 120, 190, 300, 460, 740, 1200, 1900, 3000, 4600], # 50-80
    [2.5, 4.0, 6, 10, 15, 22, 35, 54, 87, 140, 220, 350, 540, 870, 1400, 2200, 3500, 5400],# 80-120
    [3.5, 5.0, 8, 12, 18, 25, 40, 63, 100, 160, 250, 400, 630, 1000, 1600, 2500, 4000, 6300],# 120-180
    [4.5, 7.0, 10, 14, 20, 29, 46, 72, 115, 185, 290, 460, 720, 1150, 1850, 2900, 4600, 7200],# 180-250
    [6.0, 8.0, 12, 16, 23, 32, 52, 81, 130, 210, 320, 520, 810, 1300, 2100, 3200, 5200, 8100],# 250-315
    [7.0, 9.0, 13, 18, 25, 36, 57, 89, 140, 230, 360, 570, 890, 1400, 2300, 3600, 5700, 8900],# 315-400
    [8.0, 10.0, 15, 20, 27, 40, 63, 97, 155, 250, 400, 630, 970, 1550, 2500, 4000, 6300, 9700],# 400-500
]

# Fundamental deviations for holes (uppercase letters) in micrometers
# Key: letter, value: function(size_range_index) -> lower_deviation in um
# For holes, the fundamental deviation is typically the lower deviation
# We store common ones: H, G, F, E, D, C, JS, J, K, M, N, P, R, S
_HOLE_LOWER_DEV_UM = {
    'H': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # H basis: lower dev = 0
    'G': [2, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 18, 20],
    'F': [6, 10, 13, 16, 20, 25, 30, 36, 43, 50, 56, 62, 68],
    'E': [14, 20, 25, 32, 40, 50, 60, 72, 85, 100, 110, 125, 135],
    'D': [20, 30, 40, 50, 65, 80, 100, 120, 145, 170, 190, 210, 230],
}

# Fundamental deviations for shafts (lowercase letters) in micrometers
# For shafts, the fundamental deviation is typically the upper deviation
_SHAFT_UPPER_DEV_UM = {
    'h': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # h basis: upper dev = 0
    'g': [-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20],
    'f': [-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68],
    'e': [-14, -20, -25, -32, -40, -50, -60, -72, -85, -100, -110, -125, -135],
    'd': [-20, -30, -40, -50, -65, -80, -100, -120, -145, -170, -190, -210, -230],
    'c': [-60, -70, -80, -95, -110, -120, -140, -170, -200, -230, -260, -290, -320],
    'js': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # js: symmetric, handled specially
    'k': [0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
    'm': [2, 4, 6, 7, 8, 9, 11, 13, 15, 17, 20, 21, 23],
    'n': [4, 8, 10, 12, 15, 17, 20, 23, 27, 31, 34, 37, 40],
    'p': [6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68],
    'r': [10, 15, 19, 23, 28, 34, 41, 48, 55, 63, 72, 78, 86],
    's': [14, 19, 23, 28, 35, 43, 53, 59, 68, 79, 88, 98, 108],
}


def _get_size_range_index(nominal_mm: float) -> Optional[int]:
    """Find the ISO 286 size range index for a given nominal dimension.

    Args:
        nominal_mm: Nominal dimension in millimeters.

    Returns:
        Index into the size range tables, or None if out of range.
    """
    for i, (over, up_to) in enumerate(_SIZE_RANGES):
        if over < nominal_mm <= up_to:
            return i
    # Edge case: exactly 0 falls into first range
    if nominal_mm > 0 and nominal_mm <= _SIZE_RANGES[0][1]:
        return 0
    return None


def get_it_tolerance(nominal_mm: float, grade: int) -> Optional[float]:
    """Get the IT tolerance value in micrometers for a given size and grade.

    Args:
        nominal_mm: Nominal dimension in millimeters.
        grade: IT grade number (1 through 18).

    Returns:
        Tolerance in micrometers, or None if inputs are out of range.
    """
    if grade < 1 or grade > 18:
        return None
    idx = _get_size_range_index(nominal_mm)
    if idx is None:
        return None
    return _IT_GRADES_UM[idx][grade - 1]


def lookup_fit(nominal_mm: float, code: str) -> Optional[FitResult]:
    """Look up deviations for a fit code (e.g., H7, g6, js5).

    Args:
        nominal_mm: Nominal dimension in millimeters.
        code: Fit code string (e.g., "H7", "g6", "js5", "G7").

    Returns:
        FitResult with upper and lower deviations in mm, or None if invalid.
    """
    # Parse the code: letter(s) + grade number
    letter = ""
    grade_str = ""
    for ch in code:
        if ch.isdigit():
            grade_str += ch
        else:
            letter += ch

    if not letter or not grade_str:
        return None

    try:
        grade = int(grade_str)
    except ValueError:
        return None

    if grade < 1 or grade > 18:
        return None

    idx = _get_size_range_index(nominal_mm)
    if idx is None:
        return None

    tolerance_um = _IT_GRADES_UM[idx][grade - 1]
    tolerance_mm = tolerance_um / 1000.0

    # Determine if hole (uppercase) or shaft (lowercase)
    is_hole = letter[0].isupper()

    if is_hole:
        letter_lower = letter.upper()
        # Special case: JS (symmetric)
        if letter_lower == 'JS':
            upper_dev_mm = tolerance_mm / 2.0
            lower_dev_mm = -tolerance_mm / 2.0
        elif letter_lower in _HOLE_LOWER_DEV_UM:
            fund_dev_um = _HOLE_LOWER_DEV_UM[letter_lower][idx]
            lower_dev_mm = fund_dev_um / 1000.0
            upper_dev_mm = lower_dev_mm + tolerance_mm
        else:
            return None
    else:
        letter_key = letter.lower()
        # Special case: js (symmetric)
        if letter_key == 'js':
            upper_dev_mm = tolerance_mm / 2.0
            lower_dev_mm = -tolerance_mm / 2.0
        elif letter_key in _SHAFT_UPPER_DEV_UM:
            fund_dev_um = _SHAFT_UPPER_DEV_UM[letter_key][idx]
            upper_dev_mm = fund_dev_um / 1000.0
            lower_dev_mm = upper_dev_mm - tolerance_mm
        else:
            return None

    return FitResult(
        upper_deviation_mm=upper_dev_mm,
        lower_deviation_mm=lower_dev_mm,
        grade=grade,
        code=code,
    )


def lookup_fit_inch(nominal_inch: float, code: str) -> Optional[FitResult]:
    """Convenience wrapper: look up fit for a dimension in inches.

    Args:
        nominal_inch: Nominal dimension in inches.
        code: Fit code (e.g., "H7", "g6").

    Returns:
        FitResult with deviations in both mm and inch properties.
    """
    nominal_mm = nominal_inch * 25.4
    return lookup_fit(nominal_mm, code)


# Common fit descriptions for UI help text
FIT_DESCRIPTIONS = {
    'H7/g6': 'Close running fit — small clearance, good for precision sliding',
    'H7/h6': 'Sliding fit — locating fit with minimal clearance',
    'H7/k6': 'Transition fit — may have slight interference or clearance',
    'H7/n6': 'Light press fit — requires light force to assemble',
    'H7/p6': 'Press fit — requires significant force, permanent assembly',
    'H7/s6': 'Heavy press fit — for permanent assemblies under load',
    'H8/f7': 'Free running fit — generous clearance for easy assembly',
    'H9/d9': 'Loose running fit — large clearance, for dirty environments',
    'H11/c11': 'Clearance fit — very loose, for rough applications',
    'H7/r6': 'Medium press fit — interference, shrink/press assembly',
}

# Quick reference: common fit codes
COMMON_HOLE_CODES = ['H6', 'H7', 'H8', 'H9', 'H11']
COMMON_SHAFT_CODES = ['g6', 'h6', 'h7', 'js6', 'k6', 'm6', 'n6', 'p6', 'r6', 's6', 'f7', 'd9', 'c11', 'e8']
