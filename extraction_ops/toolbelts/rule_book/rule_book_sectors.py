"""Financial Services Rule Book 2016 - sectors per rule.

Generated from the Rule Book application column (312 rules), at whole-class
granularity. Anything not modelled widens, never narrows:
  - "incorporated in / outside the Island"            -> ignored
  - class sub-paragraphs (8(1), 2(3), 3(11) ...)       -> whole class
  - "except those that are also Class 1"               -> ignored
  - business-model qualifiers (stockbrokers, execution only, discretionary,
    controls clients' assets)                          -> ignored
Real class-level exclusions are kept (e.g. 7.5 "All Classes except Class 1").
Professional officers (Part 9) are tagged Class 4 and 5.
"""

from core.sectors import (
    ALL_SECTORS,
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_4,
    CLASS_5,
    CLASS_7,
    CLASS_8,
    FSA08_SECTORS,
    NON_BANK,
)

# "All Classes" in the Rule Book = every class it reaches (rule 3(1): not 6 or 9)
RB_ALL = FSA08_SECTORS

RULE_BOOK_SECTORS: dict[str, tuple[str, ...]] = {
    # --- Part 1 ---
    "1.1": RB_ALL,  # All
    "1.2": RB_ALL,  # All
    "1.3": RB_ALL,  # All
    # --- Part 2 ---
    "2.1": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.2": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.3": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.4": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.5": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.6": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.7": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.8": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.9": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.10": RB_ALL,  # All Classes except: Class 8(1), 8(2)(b) or 8(3) incorporated outside the Island
    "2.11": RB_ALL,  # All Classes incorporated in the Island
    "2.12": RB_ALL,  # All Classes incorporated in the Island
    "2.13": RB_ALL,  # All Classes incorporated in the Island
    "2.14": RB_ALL,  # All Classes incorporated outside the Island
    "2.15": RB_ALL,  # All Classes incorporated outside the Island
    "2.16": RB_ALL,  # All Classes incorporated outside the Island; except Class 8(1), 8(2)(b) or 8(3)
    "2.17": (CLASS_1,),  # All Class 1 incorporated in the Island
    "2.18": (CLASS_1,),  # All Class 1 incorporated in the Island
    "2.19": (CLASS_1,),  # All Class 1 incorporated in the Island
    "2.20": (CLASS_1,),  # All Class 1 incorporated in the Island
    "2.21": (CLASS_1,),  # All Class 1 incorporated in the Island
    "2.22": (
        CLASS_1,
    ),  # All Class 1 incorporated in the Island. Paragraphs (1)(b) and (4)(h) do not apply to Class 1(2).
    "2.23": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "2.24": (
        CLASS_1,
    ),  # All Class 1 incorporated outside the Island. Paragraph (1)(b) does not apply to Class 1(2).
    "2.24A": (CLASS_1,),  # All Class 1(1)
    "2.25": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5 or Class 8 except those that are also Class 1
    "2.26": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5 or Class 8 except those that are also Class 1
    "2.27": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) except those that are also Class 1
    "2.28": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) except those that are also Class 1
    "2.29": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) except those that are also Class 1
    "2.30": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) incorporated in the Island, except those that are also Class 1
    "2.31": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) incorporated in the Island, except those that are also Class 1
    "2.32": NON_BANK,  # All Class 2, Class 3, Class 4, Class 5, Class 8(2)(a) or 8(4) incorporated in the Island, except those that are also Class 1
    "2.33": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2 or Class 3 incorporated in the Island, except: (a) Class 2(3) and 2(7) and Class 3(8); or (b) those that are also Class 1
    "2.34": (
        CLASS_2,
    ),  # All Class 2(1) to 2(6) inclusive incorporated in the Island, except those that are also Class 1
    "2.35": NON_BANK,  # All Class 2(3) or (6) or (7) (or combination thereof); Class 3(8) (unless rule 2.33 applies); all Class 4 and/or 5; all Class 8(2)(a) or 8(4): if incorporated in the Island, except those that are also Class 1
    "2.36": (CLASS_8,),  # All Class 8(2)(a) and 8(4)
    "2.37": (CLASS_8,),  # All Class 8(2)(a) or 8(4) incorporated in the Island
    # --- Part 3 ---
    "3.1": (CLASS_3,),  # All Class 3
    "3.2": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.3": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.4": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.5": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.6": (CLASS_2, CLASS_4, CLASS_5),  # All Class 2, 4 or 5
    "3.7": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.8": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.9": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.10": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.11": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.12": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.13": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.14": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.15": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.16": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.17": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.18": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.19": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.20": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.21": (CLASS_2, CLASS_3, CLASS_4, CLASS_5),  # All Class 2, 3, 4 or 5
    "3.22": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.23": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.24": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.25": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.26": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.27": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.28": (CLASS_4,),  # All Class 4
    "3.29": (
        CLASS_2,
    ),  # All Class 2 that are stockbrokers or discretionary portfolio managers
    "3.30": (CLASS_3,),  # All Class 3
    "3.31": (CLASS_5,),  # All Class 5
    "3.32": (CLASS_5,),  # All Class 5
    "3.33": (CLASS_5,),  # All Class 5
    "3.34": (CLASS_5,),  # All Class 5
    "3.35": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.36": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.37": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.38": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.39": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.40": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.41": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    "3.42": (CLASS_8,),  # All Class 8(2)(a) or 8(4)
    # --- Part 4 ---
    "4.1": (CLASS_3,),  # Class 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.2": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.3": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.4": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.5": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.6": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.7": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.8": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.9": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.10": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.11": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.12": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    "4.13": (
        CLASS_2,
        CLASS_3,
    ),  # All Class 2, 3(1),3(2), 3(3), 3(4), 3(5), 3(11) or 3(12)
    # --- Part 5 ---
    "5.1": RB_ALL,  # All Classes incorporated in the Island
    "5.2": RB_ALL,  # All Classes incorporated in the Island
    "5.3": RB_ALL,  # All Classes incorporated in the Island
    "5.4": RB_ALL,  # All Classes incorporated in the Island
    "5.5": RB_ALL,  # All Classes incorporated in the Island
    "5.6": RB_ALL,  # All Classes incorporated in the Island
    "5.7": RB_ALL,  # All Classes incorporated in the Island
    "5.8": RB_ALL,  # All Classes incorporated in the Island
    "5.9": RB_ALL,  # All Classes incorporated in the Island
    "5.10": RB_ALL,  # All Classes incorporated in the Island
    "5.11": RB_ALL,  # All Classes incorporated in the Island
    "5.12": RB_ALL,  # All Classes incorporated outside the Island, except Class 8(1), 8(2)(b) or 8(3)
    "5.13": RB_ALL,  # All Classes incorporated outside the Island, except Class 8(1), 8(2)(b) or 8(3)
    "5.14": (CLASS_1,),  # All Class 1
    "5.15": (CLASS_1,),  # All Class 1 incorporated in the Island
    "5.16": NON_BANK,  # All Class 2, 3, 4, 5, 8(2)(a) or 8(4)
    "5.17": NON_BANK,  # All Class 2, 3, 4, 5, 8(2)(a) or 8(4) incorporated in the Island, except those that are also Class 1
    "5.18": NON_BANK,  # All Class 2, 3, 4, 5, 8(2)(a) or 8(4) where the licenceholder controls clients’ assets
    # --- Part 6 ---
    "6.1": RB_ALL,  # All Classes
    "6.2": RB_ALL,  # All Classes
    "6.3": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.4": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.5": RB_ALL,  # All Classes
    "6.6": RB_ALL,  # All Classes
    "6.7": RB_ALL,  # All Classes
    "6.8": RB_ALL,  # All Classes
    "6.9": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.10": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.11": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.12": RB_ALL,  # All Classes
    "6.13": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "6.14": RB_ALL,  # All Classes
    "6.15": (CLASS_1,),  # Class 1(1) only
    "6.16": (CLASS_1,),  # Class 1 only
    "6.17": (CLASS_2,),  # All Class 2
    "6.18": (CLASS_2,),  # All Class 2
    "6.19": (CLASS_2,),  # All Class 2
    "6.20": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17.
    "6.21": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17.
    "6.22": (CLASS_2,),  # All Class 2
    "6.23": (CLASS_2,),  # All Class 2
    "6.24": (CLASS_2,),  # All Class 2
    "6.25": (CLASS_2,),  # All Class 2
    "6.26": (CLASS_2,),  # All Class 2
    "6.27": (CLASS_2,),  # All Class 2
    "6.28": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17.
    "6.29": (
        CLASS_2,
    ),  # All Class 2 other than Class 2(3) and/or (7) except for those acting on an execution only basis in compliance with rule 6.17.
    "6.30": (
        CLASS_2,
    ),  # Class 2(3) and/or 2(6) and/or 2(7) except for those acting on an execution only basis in compliance with rule 6.17.
    "6.31": (CLASS_2,),  # All Class 2
    "6.32": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17. For those undertaking activities on a limited advice basis, this rule applies only in relation to the extent of the information provided.
    "6.33": (CLASS_2,),  # All Class 2
    "6.34": (CLASS_2,),  # All Class 2
    "6.35": (CLASS_2,),  # All Class 2
    "6.36": (CLASS_2,),  # All Class 2
    "6.37": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17. But, paragraphs (3) and (4) do not apply to: Class 2(1) to (7) inclusive; Class 2(2) to (7) inclusive; or Class 2(3) to (7) inclusive when acting under a discretionary mandate.7
    "6.38": (
        CLASS_2,
    ),  # All Class 2 except those acting on an execution only basis in compliance with rule 6.17. For those undertaking activities on a limited advice basis, this rule applies only in relation to the extent of the information provided by the client.
    "6.39": (
        CLASS_2,
    ),  # All Class 2 except: those acting on an execution only basis in compliance with rule 6.17; or those acting under the terms of a discretionary management agreement.
    "6.40": (CLASS_2,),  # All Class 2
    "6.41": (CLASS_2,),  # All Class 2
    "6.42": (CLASS_2,),  # All Class 2
    "6.43": (CLASS_2,),  # All Class 2
    "6.44": (
        CLASS_2,
    ),  # All Class 2 except where licenceholder is acting on an execution only basis in compliance with rule 6.17.
    "6.45": (CLASS_2,),  # All Class 2 exercising discretion
    "6.46": (CLASS_2,),  # All Class 2
    "6.47": (CLASS_2,),  # All Class 2
    "6.48": (CLASS_2,),  # All Class 2
    "6.49": (CLASS_2,),  # All Class 2
    "6.50": (CLASS_2,),  # All Class 2
    "6.51": (CLASS_2,),  # All Class 2
    "6.52": (CLASS_2,),  # All Class 2
    "6.53": (CLASS_3,),  # All Class 3
    "6.54": (CLASS_3,),  # All Class 3
    "6.55": (CLASS_3,),  # All Class 3
    "6.56": (CLASS_3,),  # All Class 3
    "6.57": (CLASS_3,),  # All Class 3
    "6.58": (CLASS_3,),  # Class 3 except Class 3(11) or (12)
    "6.59": (CLASS_3,),  # All Class 3
    "6.60": (CLASS_3,),  # All Class 3
    "6.61": (CLASS_3,),  # All Class 3
    "6.62": (CLASS_3,),  # All Class 3
    "6.63": (CLASS_3,),  # All Class 3
    "6.64": (CLASS_4, CLASS_5, CLASS_8),  # All Class 4, 5, 8(2)(a) or 8(4)
    "6.65": (CLASS_4,),  # All Class 4
    "6.66": (CLASS_4,),  # All Class 4
    "6.67": (CLASS_4,),  # All Class 4
    "6.68": (CLASS_5,),  # All Class 5
    "6.69": (CLASS_8,),  # Class 8(2)(a) or 8(4) only
    "6.70": (CLASS_8,),  # Class 8(2)(a) or 8(4) only
    "6.71": (CLASS_8,),  # Class 8(2)(a) or 8(4) only
    "6.72": (CLASS_1,) + NON_BANK,  # All Class 1, 2, 3, 4, 5, or 8
    "6.73": (CLASS_1,),  # Class 1
    "6.74": (CLASS_1,),  # Class 1
    # --- Part 7 ---
    "7.1": RB_ALL,  # All Classes
    "7.2": RB_ALL,  # All Classes
    "7.3": RB_ALL,  # All Classes incorporated in the Island
    "7.4": RB_ALL,  # All Classes incorporated outside the Island
    "7.5": tuple(s for s in RB_ALL if s != CLASS_1),  # All Classes except Class 1
    "7.6": (CLASS_1,),  # All Class 1
    "7.7": RB_ALL,  # All Classes incorporated in the Island, except Class 8(1), 8(2)(b) or 8(3)
    "7.8": RB_ALL,  # All Classes incorporated outside the Island, except Class 8(1), 8(2)(b) or 8(3)
    "7.9": RB_ALL,  # All Classes
    "7.10": RB_ALL,  # All Classes
    "7.11": RB_ALL,  # All Classes
    "7.12": RB_ALL,  # All Classes
    "7.13": RB_ALL,  # All Classes
    "7.14": RB_ALL,  # All Classes
    "7.15": RB_ALL,  # All Classes
    "7.16": RB_ALL,  # All Classes
    "7.17": RB_ALL,  # All Classes
    "7.18": RB_ALL,  # All Classes
    "7.19": RB_ALL,  # All Classes
    "7.20": RB_ALL,  # All Classes incorporated in the Island
    "7.21": (CLASS_1,),  # Class 1 only
    "7.22": NON_BANK,  # All Class 2, 3, 4, 5, 8(2)(a), 8(4), except: those that are also Class 1
    "7.23": (CLASS_4, CLASS_5),  # All Class 4 and 5
    "7.24": (CLASS_1,),  # Class 1(1) only
    # --- Part 8 ---
    "8.1": RB_ALL,  # All Classes
    "8.2": RB_ALL,  # All Classes
    "8.3": RB_ALL,  # All Classes
    "8.4": RB_ALL,  # All Classes
    "8.5": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.6": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.7": (CLASS_1, CLASS_2, CLASS_3),  # Class 1, 2, 3(6), 3(7), or 3(8)
    "8.8": RB_ALL,  # All Classes
    "8.9": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.10": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.11": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.12": (CLASS_3, CLASS_7),  # Class 3(9) and Class 7
    "8.13": RB_ALL,  # All Classes
    "8.14": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.15": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.16": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.17": RB_ALL,  # All Classes
    "8.18": RB_ALL,  # All Classes
    "8.19": RB_ALL,  # All Classes
    "8.20": RB_ALL,  # All Classes
    "8.21": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.22": (CLASS_8,),  # Class 8(1), 8(2)(b) or 8(3)
    "8.23": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.24": RB_ALL,  # All Classes incorporated in the Island except Class 8(1), 8(2)(b) or 8(3)
    "8.25": RB_ALL,  # All Classes incorporated outside the Island except Class 8(1), 8(2)(b) or 8(3)
    "8.26": RB_ALL,  # All Classes
    "8.27": RB_ALL,  # All Classes
    "8.28": RB_ALL,  # All Classes
    "8.29": RB_ALL,  # All Classes
    "8.30": RB_ALL,  # All Classes
    "8.31": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.32": RB_ALL,  # All Classes except Class 8(1), 8(2)(b) or 8(3)
    "8.33": (CLASS_1,),  # All Class 1
    "8.34": (CLASS_1,),  # All Class 1
    "8.35": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.36": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.37": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.38": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.39": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.40": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.41": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.42": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.43": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.44": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.45": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.46": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.47": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.48": (CLASS_1,),  # All Class 1 incorporated in the Island
    "8.49": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.50": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.51": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.52": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.53": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.54": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.55": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.56": (CLASS_1,),  # All Class 1 incorporated outside the Island
    "8.57": NON_BANK,  # All Class 2, 3, 4, 5, 8(2)(a) or 8(4), except those that are also Class 1
    "8.58": (CLASS_2,),  # All Class 2
    "8.59": (CLASS_2,),  # All Class 2
    "8.60": (CLASS_3,),  # All Class 3(1), 3(2), 3(3), 3(4), 3(11) or 3(12)
    "8.61": (CLASS_3,),  # All Class 3
    "8.62": (CLASS_4,),  # All Class 4
    "8.63": (CLASS_2,),  # Class 2 that are stockbrokers
    # --- Part 9 ---
    "9.1": (CLASS_4, CLASS_5),  # All professional officers
    "9.2": (CLASS_4, CLASS_5),  # All professional officers
    "9.3": (CLASS_4, CLASS_5),  # All professional officers
    "9.4": (CLASS_4, CLASS_5),  # All professional officers
    "9.5": (CLASS_4, CLASS_5),  # All professional officers
    "9.6": (CLASS_4, CLASS_5),  # All professional officers
    "9.7": (CLASS_4, CLASS_5),  # All professional officers
    "9.8": (CLASS_4, CLASS_5),  # All professional officers
    "9.9": (CLASS_4, CLASS_5),  # All professional officers
    "9.10": (CLASS_4, CLASS_5),  # All professional officers
    "9.11": (CLASS_4, CLASS_5),  # All professional officers
    "9.12": (CLASS_4, CLASS_5),  # All professional officers
    "9.13": (CLASS_4, CLASS_5),  # All professional officers
    "9.14": (CLASS_4, CLASS_5),  # All professional officers
    "9.15": (CLASS_4, CLASS_5),  # All professional officers
    "9.16": (CLASS_4, CLASS_5),  # All professional officers
    "9.17": (CLASS_4, CLASS_5),  # All professional officers
    "9.18": (CLASS_4, CLASS_5),  # All professional officers
    "9.19": (CLASS_4, CLASS_5),  # All professional officers
    "9.20": (CLASS_4, CLASS_5),  # All professional officers
    "9.21": (CLASS_4, CLASS_5),  # All professional officers
    "9.22": (CLASS_4, CLASS_5),  # All professional officers
    "9.23": (CLASS_4, CLASS_5),  # All professional officers
    "9.24": (CLASS_4, CLASS_5),  # All professional officers
    "9.25": (CLASS_4, CLASS_5),  # All professional officers
    "9.26": (CLASS_4, CLASS_5),  # All professional officers
    "9.27": (CLASS_4, CLASS_5),  # All professional officers
    "9.28": (CLASS_4, CLASS_5),  # All professional officers
    "9.29": (CLASS_4, CLASS_5),  # All professional officers
    "9.30": (CLASS_4, CLASS_5),  # All professional officers
    "9.31": (CLASS_4, CLASS_5),  # All professional officers
    "9.32": (CLASS_4, CLASS_5),  # All professional officers
    "9.33": (CLASS_4, CLASS_5),  # All professional officers
    "9.34": (CLASS_4, CLASS_5),  # All professional officers
    "9.35": (CLASS_4, CLASS_5),  # All professional officers
    "9.36": (CLASS_4, CLASS_5),  # All professional officers
    "9.37": (CLASS_4, CLASS_5),  # All professional officers
}

assert len(RULE_BOOK_SECTORS) == 312
assert all(s in ALL_SECTORS for v in RULE_BOOK_SECTORS.values() for s in v)
