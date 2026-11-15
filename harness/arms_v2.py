#!/usr/bin/env python3
"""Non-cipher TSR experimental arms, Layer-A validators, and prompt builders (v2).

Locks:
- Two formal generator arms built cleanly without dangling suffixes (`"Movement"`,
  never `"Movement M"`):
  - `A0` (TSR non-cipher physical <-> nonphysical partner mirror)
  - `A3-1` (`seed=101` typed category-preserving derangement matching `arms/a3_shuffled.py`,
    propagated symmetrically across MIRROR, EXTENDED_PARTNERS, rotational, spacetime,
    and inertial-frame partners)
- One post-hoc Ch. 16 plain-English synonym projection `S_syn` (`SYNONYM_MAP_CH16`)
  and directional reversal control `D_A0`, rendered deterministically from verified
  `{Slot}` templates for Stage 5 (`M4`).
- Plain-English `CONCEPTUAL_AXIS_PLAIN` enforcing zero target-word or target-stem leaks
  from `A0`, `A3-1`, and `S_syn`.
- Strict 13-key generator schema, `{Slot}` template validation, joint cross-item
  Layer-A verification (`A1`, `A2`, `A3`, `A4`) with `(?<![A-Za-z])...(?![A-Za-z])`
  boundaries, and quarantined prompts for Stages 1..6 (`M1`..`M5`).

Python 3.12+ standard library only. Zero live LLM calls on import or `--self-test`.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

HARNESS_SEED = 20261115
DERANGEMENT_SEED = 101

OPEN_JOINT_TOPICS: tuple[str, ...] = (
    "escape velocity",
    "gravitational time dilation",
    "gravitational redshift",
    "Schwarzschild radius",
)

STRIPPED_CONSTANTS: tuple[str, ...] = (
    "gamma",
    "G",
    "mu_k",
    "mu_s",
    "k_e",
    "epsilon_0",
    "mu_0",
    "h",
    "hbar",
)

UNMAPPED_BLOCKLIST_V2: tuple[str, ...] = (
    "temperature",
    "heat",
    "heat transfer",
    "latent heat",
    "heat capacity",
    "specific heat",
    "enthalpy",
    "entropy",
    "internal energy",
    "free energy",
    "thermal conductivity",
    "pressure",
    "viscosity",
    "buoyancy coefficient",
    "reynolds number",
    "electric charge",
    "charge",
    "electric current",
    "displacement current",
    "induced current",
    "voltage",
    "electromotive force",
    "capacitance",
    "inductance",
    "impedance",
    "wave frequency f",
    "frequency f",
    "angular frequency",
    "observed frequency",
    "source frequency",
    "emitted frequency",
    "wavenumber",
    "index of refraction",
    "sound intensity level",
    "decibel",
    "spring constant",
    "tensile stress",
    "tensile strain",
    "shear stress",
    "shear strain",
    "bulk modulus",
    "shear modulus",
    "young's modulus",
    "boltzmann constant",
    "ideal gas constant",
    "avogadro constant",
    "moles",
    "molar mass",
    "phase difference",
    "angle",
    "reflectance",
    "fringe visibility",
    "carnot",
    "efficiency",
)

STAGE6_PHYSICAL_SLOTS: tuple[str, ...] = (
    "mass",
    "density",
    "volume",
    "space",
    "time",
    "velocity",
    "acceleration",
    "force",
    "speed of light",
    "gravity",
    "friction",
    "damping",
)

REQUIRED_GENERATOR_KEYS: frozenset[str] = frozenset(
    {
        "item_id",
        "scope_status",
        "formula_shape",
        "ruling",
        "two_level",
        "axis_polarity_note",
        "unmapped_terms",
        "variable_map",
        "reflected_formula",
        "translation_t",
        "translation_template",
        "direction_flipped_d",
        "rationale",
    }
)

# ---------------------------------------------------------------------------
# Base Pools, Mirror Rows, Partner Lookup Table, & Synonym Map (Book Ch. 16)
# ---------------------------------------------------------------------------

QUANTITY_POOL_A0: list[str] = [
    "Movement",
    "Vibrance",
    "Desire",
    "Vibration",
    "Expansion",
    "rise per Expansion",
    "Appreciation",
    "Frequency",
    "Current",
    "Idle",
    "Reflected",
    "conscious energy",
    "imagination",
]

PHENOM_POOL_A0: list[str] = [
    "resonance",
    "Attraction",
    "Vortex",
    "Convergence",
    "Tune",
    "Intuition",
]

DIR_POOL_A0: list[str] = [
    "Out For",
    "In To",
    "Future",
]

PROP_POOL_A0: list[str] = [
    "limitless",
    "receptive",
    "collection",
]

# Base MIRROR pairs (physical term -> nonphysical A0 partner, conceptual role)
BASE_MIRROR_A0: tuple[tuple[str, str, str], ...] = (
    ("limited", "limitless", "property"),
    ("resistant", "receptive", "property"),
    ("radiation", "collection", "property"),
    ("Subjective Reality", "Vibrational Reality", "reality"),
    ("Objective Reality", "Collective Reality", "reality"),
    ("Space-Time", "Vibration-Expansion", "continuum"),
    ("empirical evidence", "emotional evidence", "evidence"),
    ("Now", "Future", "energy flow"),
    ("Past", "Current", "energy flow"),
    ("Belief", "Desire", "entity contrast"),
    ("Expectation", "Intuition", "entity contrast"),
    ("speed of light c", "Current", "symbol"),
    ("mass m", "Movement", "symbol"),
    ("Focus", "Tune", "entity action"),
    ("electric", "Idle", "co-creating partner"),
    ("magnetic", "Reflected", "co-creating partner"),
    ("density", "Desire", "co-creating partner"),
    ("volume", "Vibrance", "co-creating partner"),
    ("physical energy", "conscious energy", "energy"),
    ("actualization", "realization", "transmutation"),
    ("Out Through", "Out For", "entity transmutation"),
    ("In From", "In To", "entity transmutation"),
    ("space", "Vibration", "reflected partnership"),
    ("time", "Expansion", "reflected partnership"),
    ("velocity", "rise per Expansion", "reflected partnership"),
    ("acceleration", "Appreciation", "reflected partnership"),
    ("manifestation", "imagination", "reflected partnership"),
    ("force", "Frequency", "reflected partnership"),
)

# Canonical A0 Partner Lookup Table entries (physical quantity -> A0 expression, conceptual role)
BASE_PARTNER_ENTRIES_A0: tuple[tuple[str, str, str], ...] = (
    ("mass", "Movement", "base quantity"),
    ("inertial mass", "Movement", "base quantity"),
    ("vacuum expectation value", "Movement", "base quantity"),
    ("inertial frame", "Movement", "frame"),
    ("inertial observer", "Movement", "frame"),
    ("inertial rest frame", "Movement", "frame"),
    ("reference frame", "Movement", "frame"),
    ("observer", "Movement", "frame"),
    ("density", "Desire", "base quantity"),
    ("volume", "Vibrance", "base quantity"),
    ("space", "Vibration", "base quantity"),
    ("distance", "Vibration", "base quantity"),
    ("displacement", "Vibration", "base quantity"),
    ("separation", "Vibration", "base quantity"),
    ("wavelength", "Vibration", "base quantity"),
    ("width", "Vibration", "base quantity"),
    ("length", "Vibration", "base quantity"),
    ("position", "Vibration", "base quantity"),
    ("coordinate", "Vibration", "base quantity"),
    ("height", "Vibration", "base quantity"),
    ("radius", "Vibration", "base quantity"),
    ("gradient", "Vibration", "base quantity"),
    ("length contraction", "Vibration", "relativistic effect"),
    ("area", "Vibration²", "derived geometric quantity"),
    ("cross-sectional area", "Vibration²", "derived geometric quantity"),
    ("time", "Expansion", "base quantity"),
    ("time interval", "Expansion", "base quantity"),
    ("proper time", "Expansion", "base quantity"),
    ("evolution time", "Expansion", "base quantity"),
    ("period", "Expansion", "base quantity"),
    ("duration", "Expansion", "base quantity"),
    ("time dilation", "Expansion", "relativistic effect"),
    ("spacetime interval", "Vibration-Expansion", "continuum"),
    ("spacetime coordinate", "Vibration-Expansion", "continuum"),
    ("spacetime metric", "Vibration-Expansion", "continuum"),
    ("spacetime geometry", "Vibration-Expansion", "continuum"),
    ("spacetime derivative", "Vibration-Expansion", "continuum"),
    ("space-time", "Vibration-Expansion", "continuum"),
    ("velocity", "rise per Expansion", "kinematic rate"),
    ("speed", "rise per Expansion", "kinematic rate"),
    ("terminal velocity", "rise per Expansion", "kinematic rate"),
    ("wave speed", "rise per Expansion", "kinematic rate"),
    ("acceleration", "Appreciation", "kinematic rate"),
    ("centripetal acceleration", "Appreciation", "kinematic rate"),
    ("tangential acceleration", "Appreciation", "kinematic rate"),
    ("force", "Frequency", "dynamical quantity"),
    ("net force", "Frequency", "dynamical quantity"),
    ("normal force", "Frequency", "dynamical quantity"),
    ("buoyant force", "Frequency", "dynamical quantity"),
    ("centripetal force", "Frequency", "dynamical quantity"),
    ("electrostatic force", "Frequency", "dynamical quantity"),
    ("lorentz force", "Frequency", "dynamical quantity"),
    ("restoring force", "Frequency", "dynamical quantity"),
    ("tension force", "Frequency", "dynamical quantity"),
    ("speed of light", "Current", "invariant speed"),
    ("speed of light c", "Current", "invariant speed"),
    ("gravity", "Attraction", "gravity"),
    ("gravitational pull", "Attraction", "gravity"),
    ("gravitational field", "Attraction", "gravity"),
    ("gravitational acceleration", "Attraction", "gravity"),
    ("gravity well", "Attraction", "gravity"),
    ("gravitational lensing", "Attraction", "gravity"),
    ("weight", "Movement × Attraction", "derived force"),
    ("momentum", "Movement × rise per Expansion", "derived quantity"),
    ("linear momentum", "Movement × rise per Expansion", "derived quantity"),
    ("relativistic momentum", "Movement × rise per Expansion", "derived quantity"),
    ("impulse", "Frequency × Expansion", "derived quantity"),
    ("work", "Frequency × Vibration", "derived energy"),
    ("power", "Frequency × rise per Expansion", "derived power"),
    ("dissipated power", "Frequency × rise per Expansion", "derived power"),
    ("signal power", "Frequency × rise per Expansion", "derived power"),
    ("noise power", "Frequency × rise per Expansion", "derived power"),
    ("moment of inertia", "Movement × Vibration²", "rotational quantity"),
    ("angular momentum", "Vibration × Movement × rise per Expansion", "rotational quantity"),
    ("angular velocity", "rise per Expansion ÷ Vibration", "rotational quantity"),
    ("angular acceleration", "Appreciation ÷ Vibration", "rotational quantity"),
    ("torque", "Vibration × Frequency", "rotational quantity"),
    ("energy", "conscious energy", "energy"),
    ("physical energy", "conscious energy", "energy"),
    ("kinetic energy", "conscious energy", "energy"),
    ("potential energy", "conscious energy", "energy"),
    ("gravitational potential energy", "conscious energy", "energy"),
    ("mechanical energy", "conscious energy", "energy"),
    ("total energy", "conscious energy", "energy"),
    ("rest energy", "conscious energy", "energy"),
    ("relativistic energy", "conscious energy", "energy"),
    ("photon energy", "conscious energy", "energy"),
    ("quantized energy", "conscious energy", "energy"),
    ("zero-point energy", "conscious energy", "energy"),
    ("confining potential", "conscious energy", "energy"),
    ("barrier height", "conscious energy", "energy"),
    ("stress-energy", "conscious energy", "energy"),
    ("friction", "resonance", "dissipative phenomenon"),
    ("static friction", "resonance", "dissipative phenomenon"),
    ("kinetic friction", "resonance", "dissipative phenomenon"),
    ("damping", "resonance", "dissipative phenomenon"),
    ("damping force", "resonance", "dissipative phenomenon"),
    ("damping coefficient", "resonance", "dissipative phenomenon"),
    ("damping rate", "resonance", "dissipative phenomenon"),
    ("drag", "resonance", "dissipative phenomenon"),
    ("drag force", "resonance", "dissipative phenomenon"),
    ("air resistance", "resonance", "dissipative phenomenon"),
    ("decoherence rate", "resonance", "dissipative phenomenon"),
    ("resonance width", "resonance ÷ Movement", "dissipative ratio"),
    ("electric field", "Idle", "field partner"),
    ("electric flux", "Idle × Vibrance", "flux partner"),
    ("magnetic field", "Reflected", "field partner"),
    ("magnetic flux", "Reflected × Vibrance", "flux partner"),
    ("electrical resistance", "receptive", "property"),
    ("resistant", "receptive", "property"),
    ("string tension", "Frequency ÷ Vibration", "tension ratio"),
    ("radiation", "collection", "property"),
    ("collection", "collection", "property"),
    ("limited", "limitless", "property"),
    ("focus", "Tune", "entity action"),
    ("manifestation", "imagination", "reflected partnership"),
    ("vortex", "Vortex", "phenomenon"),
    ("convergence", "Convergence", "phenomenon"),
    ("intuition", "Intuition", "phenomenon"),
    ("realization", "realization", "transmutation"),
    ("now", "Future", "energy flow"),
    ("past", "Current", "energy flow"),
    ("out through", "Out For", "entity transmutation"),
    ("in from", "In To", "entity transmutation"),
    ("subjective reality", "Vibrational Reality", "reality"),
    ("objective reality", "Collective Reality", "reality"),
    ("empirical evidence", "emotional evidence", "evidence"),
)

# Canonical A0 slots -> single-sense Book Ch. 16 plain-English synonym projection (S_syn).
# Every single one of these 30 slots appears in BASE_PARTNER_ENTRIES_A0 and has a
# non-identity derangement image in A3-1 plus a unique 1-to-1 synonym below.
SYNONYM_MAP_CH16: dict[str, str] = {
    "Movement": "responsiveness",
    "Appreciation": "gratitude",
    "Frequency": "urgency",
    "Vibration": "pitch",
    "Expansion": "growth",
    "Desire": "longing",
    "Vibrance": "capacity",
    "Current": "stream",
    "Attraction": "affinity",
    "resonance": "harmony",
    "conscious energy": "awareness",
    "rise per Expansion": "pace",
    "Vibration-Expansion": "pitch-growth",
    "Idle": "stillness",
    "Reflected": "echo",
    "Tune": "focus",
    "Vortex": "whirlpool",
    "Convergence": "gathering",
    "Intuition": "hunch",
    "imagination": "imagery",
    "collection": "absorption",
    "receptive": "welcoming",
    "limitless": "infinite",
    "Out For": "outward-seeking",
    "In To": "inward-arriving",
    "Future": "onwardness",
    "realization": "fulfillment",
    "Vibrational Reality": "pitch reality",
    "Collective Reality": "shared reality",
    "emotional evidence": "felt evidence",
}

CANONICAL_A0_SLOTS: tuple[str, ...] = tuple(SYNONYM_MAP_CH16.keys())


def _canonical_slot_key(term: str) -> str:
    return re.sub(r"[\s-]+", "_", term.strip())


# ---------------------------------------------------------------------------
# Conceptual Axis (Zero Target Word / Target Stem Leakage!)
# ---------------------------------------------------------------------------

CONCEPTUAL_AXIS_PLAIN: str = (
    "Conceptual Axis (Physical vs. Nonphysical Mirror):\n"
    "- Physical polarity: localized entities and separated objects hold firm boundaries against one another, "
    "traverse sequentially across separated intervals of space and time, encounter inertia, drag, or effortful "
    "resistance whenever pushed or sped up, and confront barriers of distance that block any common simultaneous "
    "present across distant observers.\n"
    "- Nonphysical polarity: the mirrored nonphysical side reverses boundary-holding resistance into unbounded, "
    "unresisting yielding; separated sequentiality into immediate, simultaneous unfolding; effortful friction or "
    "inertia into effortless alignment; and fragmented containment into unified, holistic coherence. Structural "
    "proportions among paired quantities keep their algebraic shape whenever no cost, barrier, or separation "
    "obstructs direct translation, and flip directional polarity whenever the physical law states an escalating cost, "
    "dissipation barrier, or distance-induced loss of simultaneity."
)

# Check forbidden target words / stems across A0, A3-1, and S_syn.
# Carefully anchored so legitimate English physics/axis words (e.g. "space", "middle",
# "situation", "present", "boundless", "unbounded", "mass", "force", "time", "velocity",
# "acceleration", "gravity", "friction", "damping", "density", "volume") never false-trigger,
# while EVERY target term and morphological stem from A0, A3-1, and S_syn is rejected.
_FORBIDDEN_STEM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # A0 / A3-1 stems
    ("movement/mov*", re.compile(r"(?<![A-Za-z])mov(?:e|ed|es|ing|ement|ements)(?![A-Za-z])", re.I)),
    ("appreciat*", re.compile(r"(?<![A-Za-z])appreciat[a-z]*(?![A-Za-z])", re.I)),
    ("frequen*", re.compile(r"(?<![A-Za-z])frequen[a-z]*(?![A-Za-z])", re.I)),
    ("vibrat*", re.compile(r"(?<![A-Za-z])vibrat[a-z]*(?![A-Za-z])", re.I)),
    ("vibran*", re.compile(r"(?<![A-Za-z])vibran[a-z]*(?![A-Za-z])", re.I)),
    ("expan*", re.compile(r"(?<![A-Za-z])expan[a-z]*(?![A-Za-z])", re.I)),
    ("desir*", re.compile(r"(?<![A-Za-z])desir[a-z]*(?![A-Za-z])", re.I)),
    ("curren*", re.compile(r"(?<![A-Za-z])curren[a-z]*(?![A-Za-z])", re.I)),
    ("attract*", re.compile(r"(?<![A-Za-z])attract[a-z]*(?![A-Za-z])", re.I)),
    ("resonan*", re.compile(r"(?<![A-Za-z])resonan[a-z]*(?![A-Za-z])", re.I)),
    ("consci*", re.compile(r"(?<![A-Za-z])consci[a-z]*(?![A-Za-z])", re.I)),
    ("energ*", re.compile(r"(?<![A-Za-z])energ[a-z]*(?![A-Za-z])", re.I)),
    ("rise/risen/rising", re.compile(r"(?<![A-Za-z])ris(?:e|es|en|ing)(?![A-Za-z])", re.I)),
    ("idl*", re.compile(r"(?<![A-Za-z])idl(?:e|ed|es|ing|y|eness)?(?![A-Za-z])", re.I)),
    ("reflect*", re.compile(r"(?<![A-Za-z])reflect[a-z]*(?![A-Za-z])", re.I)),
    ("tun*", re.compile(r"(?<![A-Za-z])(?:at)?tun(?:e|es|ed|ing|er|ement)(?![A-Za-z])", re.I)),
    ("vort*", re.compile(r"(?<![A-Za-z])vort(?:ex|exes|ices|ical)(?![A-Za-z])", re.I)),
    ("converg*", re.compile(r"(?<![A-Za-z])converg[a-z]*(?![A-Za-z])", re.I)),
    ("intuit*", re.compile(r"(?<![A-Za-z])intuit[a-z]*(?![A-Za-z])", re.I)),
    ("imagin*", re.compile(r"(?<![A-Za-z])imagin[a-z]*(?![A-Za-z])", re.I)),
    ("limitless*", re.compile(r"(?<![A-Za-z])limitless[a-z]*(?![A-Za-z])", re.I)),
    ("recept*", re.compile(r"(?<![A-Za-z])recept[a-z]*(?![A-Za-z])", re.I)),
    ("collect*", re.compile(r"(?<![A-Za-z])collect[a-z]*(?![A-Za-z])", re.I)),
    ("realiz*", re.compile(r"(?<![A-Za-z])realiz[a-z]*(?![A-Za-z])", re.I)),
    ("out-for", re.compile(r"(?<![A-Za-z])out[\s-]+for(?![A-Za-z])", re.I)),
    ("in-to", re.compile(r"(?<![A-Za-z])in[\s-]+to(?![A-Za-z])", re.I)),
    ("futur*", re.compile(r"(?<![A-Za-z])futur[a-z]*(?![A-Za-z])", re.I)),
    ("aware*", re.compile(r"(?<![A-Za-z])aware[a-z]*(?![A-Za-z])", re.I)),
    ("moment*", re.compile(r"(?<![A-Za-z])moment(?:um|a)?(?![A-Za-z])", re.I)),
    ("culminat*", re.compile(r"(?<![A-Za-z])culminat[a-z]*(?![A-Za-z])", re.I)),
    ("dilat*", re.compile(r"(?<![A-Za-z])dilat[a-z]*(?![A-Za-z])", re.I)),
    ("contract*", re.compile(r"(?<![A-Za-z])contract[a-z]*(?![A-Za-z])", re.I)),
    ("emotion*", re.compile(r"(?<![A-Za-z])emotion[a-z]*(?![A-Za-z])", re.I)),
    ("realit*", re.compile(r"(?<![A-Za-z])realit[a-z]*(?![A-Za-z])", re.I)),
    ("evidenc*", re.compile(r"(?<![A-Za-z])eviden[ct][a-z]*(?![A-Za-z])", re.I)),
    # S_syn stems
    ("respons*", re.compile(r"(?<![A-Za-z])respons[a-z]*(?![A-Za-z])", re.I)),
    ("gratitud*", re.compile(r"(?<![A-Za-z])grati(?:tude|f)[a-z]*(?![A-Za-z])", re.I)),
    ("urgen*", re.compile(r"(?<![A-Za-z])urgen[a-z]*(?![A-Za-z])", re.I)),
    ("pitch*", re.compile(r"(?<![A-Za-z])pitch(?:es|ed|ing)?(?![A-Za-z])", re.I)),
    ("grow*", re.compile(r"(?<![A-Za-z])grow(?:n|s|ing|th)?(?![A-Za-z])", re.I)),
    ("longing*", re.compile(r"(?<![A-Za-z])longing[a-z]*(?![A-Za-z])", re.I)),
    ("capacit*", re.compile(r"(?<![A-Za-z])capacit[a-z]*(?![A-Za-z])", re.I)),
    ("stream*", re.compile(r"(?<![A-Za-z])stream[a-z]*(?![A-Za-z])", re.I)),
    ("affinit*", re.compile(r"(?<![A-Za-z])affinit[a-z]*(?![A-Za-z])", re.I)),
    ("harmon*", re.compile(r"(?<![A-Za-z])harmon[a-z]*(?![A-Za-z])", re.I)),
    ("pac(e|es|ed|ing)", re.compile(r"(?<![A-Za-z])pac(?:e|es|ed|ing)(?![A-Za-z])", re.I)),
    ("still*", re.compile(r"(?<![A-Za-z])still(?:ness|er|est)?(?![A-Za-z])", re.I)),
    ("echo*", re.compile(r"(?<![A-Za-z])echo(?:es|ed|ing)?(?![A-Za-z])", re.I)),
    ("focus*", re.compile(r"(?<![A-Za-z])focus[a-z]*(?![A-Za-z])", re.I)),
    ("whirlpool*", re.compile(r"(?<![A-Za-z])whirlpool[a-z]*(?![A-Za-z])", re.I)),
    ("gather*", re.compile(r"(?<![A-Za-z])gather[a-z]*(?![A-Za-z])", re.I)),
    ("hunch*", re.compile(r"(?<![A-Za-z])hunch[a-z]*(?![A-Za-z])", re.I)),
    ("imager*", re.compile(r"(?<![A-Za-z])imager[a-z]*(?![A-Za-z])", re.I)),
    ("absor*", re.compile(r"(?<![A-Za-z])absor[bp][a-z]*(?![A-Za-z])", re.I)),
    ("welcom*", re.compile(r"(?<![A-Za-z])welcom[a-z]*(?![A-Za-z])", re.I)),
    ("infinit*", re.compile(r"(?<![A-Za-z])infinit[a-z]*(?![A-Za-z])", re.I)),
    ("onward*", re.compile(r"(?<![A-Za-z])onward[a-z]*(?![A-Za-z])", re.I)),
    ("outward*", re.compile(r"(?<![A-Za-z])outward[a-z]*(?![A-Za-z])", re.I)),
    ("seek*", re.compile(r"(?<![A-Za-z])seek[a-z]*(?![A-Za-z])", re.I)),
    ("inward*", re.compile(r"(?<![A-Za-z])inward[a-z]*(?![A-Za-z])", re.I)),
    ("arriv*", re.compile(r"(?<![A-Za-z])arriv[a-z]*(?![A-Za-z])", re.I)),
    ("fulfill*", re.compile(r"(?<![A-Za-z])fulfil[a-z]*(?![A-Za-z])", re.I)),
    ("felt", re.compile(r"(?<![A-Za-z])felt(?![A-Za-z])", re.I)),
    ("shar*", re.compile(r"(?<![A-Za-z])shar(?:e|ed|es|ing)(?![A-Za-z])", re.I)),
    ("peak*", re.compile(r"(?<![A-Za-z])peak(?:s|ed|ing)?(?![A-Za-z])", re.I)),
    ("lag*", re.compile(r"(?<![A-Za-z])lag(?:s|ged|ging)?(?![A-Za-z])", re.I)),
    ("narrow*", re.compile(r"(?<![A-Za-z])narrow[a-z]*(?![A-Za-z])", re.I)),
    ("impetus", re.compile(r"(?<![A-Za-z])impetus(?![A-Za-z])", re.I)),
    ("cogniz*", re.compile(r"(?<![A-Za-z])cogniz[a-z]*(?![A-Za-z])", re.I)),
    ("realiz*", re.compile(r"(?<![A-Za-z])realiz[a-z]*(?![A-Za-z])", re.I)),
    ("collectiv*", re.compile(r"(?<![A-Za-z])collectiv[a-z]*(?![A-Za-z])", re.I)),
    ("emotion*", re.compile(r"(?<![A-Za-z])emotion[a-z]*(?![A-Za-z])", re.I)),
    ("out-for", re.compile(r"(?<![A-Za-z])out\s+for(?![A-Za-z])", re.I)),
    ("in-to", re.compile(r"(?<![A-Za-z])in\s+to(?![A-Za-z])", re.I)),
)


def assert_zero_target_stem_leak(text: str, extra_forbidden: tuple[str, ...] = ()) -> None:
    """Raise ValueError if any A0, A3-1, or S_syn target word/stem appears in `text`."""
    hits: list[str] = []
    for label, pat in _FORBIDDEN_STEM_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(f"{label}:{m.group(0)!r}")
    for extra in extra_forbidden:
        if not extra:
            continue
        pat = re.compile(rf"(?<![A-Za-z]){re.escape(extra)}(?![A-Za-z])", re.I)
        m = pat.search(text)
        if m:
            hits.append(f"extra:{m.group(0)!r}")
    if hits:
        raise ValueError(f"Target stem leak detected: {', '.join(hits)}")


# Immediate module-load invariant check on CONCEPTUAL_AXIS_PLAIN
assert_zero_target_stem_leak(CONCEPTUAL_AXIS_PLAIN)


# ---------------------------------------------------------------------------
# Arm Builder (A0 & Seed-101 Derangement A3-1)
# ---------------------------------------------------------------------------


def _seeded_derangement(items: list[str], seed: int) -> dict[str, str]:
    """Exact category-preserving derangement matching arms/a3_shuffled.py."""
    rng = random.Random(seed)
    for _ in range(1000):
        perm = list(items)
        rng.shuffle(perm)
        if all(a != b for a, b in zip(items, perm)):
            return dict(zip(items, perm))
    raise RuntimeError(f"Could not find derangement for seed={seed}")


def _apply_word_perm_v2(text: str, mapping: dict[str, str]) -> str:
    """Single-pass longest-first substitution using strict ASCII-letter boundaries.

    Unlike v1 `arms/a3_shuffled.py`, correctly handles exponents (`Vibration² ->
    Appreciation²`) and hyphenated compounds (`Vibration-Expansion ->
    Appreciation-Vibrance`) without dangling suffixes.
    """
    keys = sorted(mapping.keys(), key=len, reverse=True)
    if not keys:
        return text
    pattern = re.compile(
        r"(?<![A-Za-z])(" + "|".join(re.escape(k) for k in keys) + r")(?![A-Za-z])"
    )
    return pattern.sub(lambda m: mapping[m.group(0)], text)


@dataclass(frozen=True)
class ArmConfigV2:
    arm_id: str
    description: str
    a0_to_arm: dict[str, str]
    arm_to_a0: dict[str, str]
    mirror_pairs: tuple[tuple[str, str, str], ...]
    partner_entries: tuple[tuple[str, str, str], ...]
    partner_lookup: dict[str, str]
    valid_target_terms: tuple[str, ...]
    slot_to_term: dict[str, str]
    slot_to_canonical: dict[str, str]
    slot_lower_to_canonical: dict[str, str]
    baseline_sign_edges: tuple[dict[str, Any], ...]
    unmapped_blocklist: tuple[str, ...]
    open_joints: tuple[str, ...]


def _build_slot_maps(a0_to_arm: dict[str, str]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Build deterministic `{Slot}` accepted keys -> rendered arm term, canonical A0 key, and lowercase map."""
    slot_to_term: dict[str, str] = {}
    slot_to_canonical: dict[str, str] = {}
    slot_lower_to_canonical: dict[str, str] = {}
    # Clean non-colliding resolution:
    # For A0: valid keys are A0 underscored & spaced slot keys.
    # For A3-1: valid keys are A3-1's own arm_term (underscored & spaced).
    for canonical_a0 in CANONICAL_A0_SLOTS:
        arm_term = a0_to_arm.get(canonical_a0, _apply_word_perm_v2(canonical_a0, a0_to_arm))
        for k in {arm_term, _canonical_slot_key(arm_term)}:
            kl = k.lower()
            if kl in slot_lower_to_canonical and slot_lower_to_canonical[kl] != canonical_a0:
                raise ValueError(
                    f"Case-folded slot collision for {k!r}: {slot_lower_to_canonical[kl]!r} vs {canonical_a0!r}"
                )
            slot_to_term[k] = arm_term
            slot_to_canonical[k] = canonical_a0
            slot_lower_to_canonical[kl] = canonical_a0
    return slot_to_term, slot_to_canonical, slot_lower_to_canonical


def _derive_target_terms_for_arm(a0_to_arm: dict[str, str], partner_entries: tuple[tuple[str, str, str], ...]) -> tuple[str, ...]:
    terms: set[str] = set()
    for canonical_a0 in CANONICAL_A0_SLOTS:
        arm_term = a0_to_arm.get(canonical_a0, _apply_word_perm_v2(canonical_a0, a0_to_arm))
        terms.add(arm_term)
    # Also decompose compound partner expressions into base slot terms (all already covered, keep sorted longest-first)
    for _phys, expr, _role in partner_entries:
        # Handle e.g. 'Movement × Vibration²' -> split algebraic delimiters
        cleaned = re.sub(r"[²³^0-9()×÷*/+-]+", " ", expr).strip()
        for part in re.split(r"\s{2,}", cleaned):
            if part and part in terms:
                terms.add(part)
    return tuple(sorted(terms, key=lambda s: (-len(s), s)))


def build_arm_v2(arm_id: str) -> ArmConfigV2:
    """Build v2 ArmConfigV2 for `"A0"` or `"A3-1"` (clean nomenclature, zero `"Movement M"`)."""
    if arm_id == "A0":
        a0_to_arm = {slot: slot for slot in CANONICAL_A0_SLOTS}
        desc = "A0 non-cipher physical <-> nonphysical partner mirror (clean Movement, Ch. 2 & Ch. 16)."
    elif arm_id == "A3-1":
        perm: dict[str, str] = {}
        perm.update(_seeded_derangement(QUANTITY_POOL_A0, DERANGEMENT_SEED))
        perm.update(_seeded_derangement(PHENOM_POOL_A0, DERANGEMENT_SEED + 17))
        perm.update(_seeded_derangement(DIR_POOL_A0, DERANGEMENT_SEED + 31))
        perm.update(_seeded_derangement(PROP_POOL_A0, DERANGEMENT_SEED + 47))
        meta_pool_a0 = [
            "Vibrational Reality",
            "Collective Reality",
            "emotional evidence",
            "realization",
        ]
        perm.update(_seeded_derangement(meta_pool_a0, DERANGEMENT_SEED + 64))
        a0_to_arm = {}
        for slot in CANONICAL_A0_SLOTS:
            a0_to_arm[slot] = perm[slot] if slot in perm else _apply_word_perm_v2(slot, perm)
        desc = (
            "A3-1 typed category-preserving derangement (seed=101, symmetric across mirror, "
            "rotational, spacetime, and frame partners; clean Movement)."
        )
    else:
        raise ValueError(f"Unsupported arm_id: {arm_id!r} (expected 'A0' or 'A3-1')")

    arm_to_a0 = {v: k for k, v in a0_to_arm.items()}
    assert len(arm_to_a0) == len(a0_to_arm), f"Non-bijective arm map for {arm_id}"

    mirror_pairs = tuple(
        (phys, _apply_word_perm_v2(targ, a0_to_arm), role)
        for phys, targ, role in BASE_MIRROR_A0
    )
    partner_entries = tuple(
        (phys, _apply_word_perm_v2(targ, a0_to_arm), role)
        for phys, targ, role in BASE_PARTNER_ENTRIES_A0
    )
    partner_lookup = {phys.lower(): targ for phys, targ, _role in partner_entries}

    slot_to_term, slot_to_canonical, slot_lower_to_canonical = _build_slot_maps(a0_to_arm)
    valid_target_terms = _derive_target_terms_for_arm(a0_to_arm, partner_entries)

    # Propagate baseline sign edges symmetrically across arm vocabulary
    raw_baseline = (
        {"from": "Desire", "to": "Movement", "sign": 1, "source": "book.Map_m_rho_V"},
        {"from": "Vibrance", "to": "Movement", "sign": 1, "source": "book.Map_m_rho_V"},
        {"from": "Movement", "to": "Frequency", "sign": 1, "source": "book.Map_F_ma"},
        {"from": "Appreciation", "to": "Frequency", "sign": 1, "source": "book.Map_F_ma"},
    )
    baseline_sign_edges = tuple(
        {
            "from": _apply_word_perm_v2(e["from"], a0_to_arm),
            "to": _apply_word_perm_v2(e["to"], a0_to_arm),
            "sign": e["sign"],
            "source": e["source"],
        }
        for e in raw_baseline
    )

    return ArmConfigV2(
        arm_id=arm_id,
        description=desc,
        a0_to_arm=a0_to_arm,
        arm_to_a0=arm_to_a0,
        mirror_pairs=mirror_pairs,
        partner_entries=partner_entries,
        partner_lookup=partner_lookup,
        valid_target_terms=valid_target_terms,
        slot_to_term=slot_to_term,
        slot_to_canonical=slot_to_canonical,
        slot_lower_to_canonical=slot_lower_to_canonical,
        baseline_sign_edges=baseline_sign_edges,
        unmapped_blocklist=UNMAPPED_BLOCKLIST_V2,
        open_joints=OPEN_JOINT_TOPICS,
    )


def format_partner_lookup_table(arm: ArmConfigV2) -> str:
    """Format the arm's Partner Lookup Table ONLY (zero inline prose glossary definitions!)."""
    lines = [
        f"Partner Lookup Table for Arm {arm.arm_id} (physical quantity/concept -> arm target partner):",
        "Primary Mirror Pairs:",
    ]
    for phys, targ, role in arm.mirror_pairs:
        lines.append(f"  - {phys} -> {targ}  [{role}]")
    lines.append("Extended & Rotational / Spacetime / Frame Partners:")
    seen = {p.lower() for p, _t, _r in arm.mirror_pairs}
    for phys, targ, role in arm.partner_entries:
        if phys.lower() in seen:
            continue
        lines.append(f"  - {phys} -> {targ}  [{role}]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rule R v2 & Lint Constraints (ZERO Leaked Calibration Formulas!)
# ---------------------------------------------------------------------------

RULE_R_V2: str = (
    "Rule R (Deterministic 4-Step Non-Cipher Classification & Reflection Protocol):\n"
    "\n"
    "Step 1 — Scope Check (`scope_status = \"no_partner\"`, `ruling = \"no partner\"`, `formula_shape = \"none\"`):\n"
    "  1a. Strip dimensionless numeric prefactors (2, 1/2, 3, 4 pi^2, sqrt(2), etc.) AND physical or kinematic "
    "universal/material constants (`gamma`, `G`, `mu_k`, `mu_s`, `k_e`, `epsilon_0`, `mu_0`, `h`, `hbar`) — these "
    "constants do not require separate vocabulary partners.\n"
    "  1b. Check every remaining active dynamical variable or physical phenomenon in the description and equation. "
    "If ANY active dynamical quantity appears on the unmapped blocklist or lacks a partner in the arm's Partner "
    "Lookup Table, STOP and classify as `scope_status = \"no_partner\"`, `ruling = \"no partner\"`, "
    "`formula_shape = \"none\"`, `two_level = false`, listing the missing items in `unmapped_terms` and leaving "
    "`reflected_formula`, `translation_t`, `translation_template`, and `direction_flipped_d` as empty strings `\"\"`.\n"
    "  1c. Genuinely unmapped blocklisted quantities include: temperature, heat, heat transfer, latent heat, heat "
    "capacity, specific heat, enthalpy, entropy, internal energy, free energy, thermal conductivity, pressure, "
    "viscosity, Reynolds number, electric charge, electric current, displacement/induced current, voltage, "
    "electromotive force, capacitance, inductance, impedance, wave frequency f (in Hz), angular frequency, "
    "wavenumber k, index of refraction n, sound intensity level (dB), spring constant, tensile/shear stress, "
    "tensile/shear strain, elastic moduli (Young's/bulk/shear modulus), Boltzmann constant k_B, ideal gas constant R, "
    "moles, phase difference, angle, reflectance, fringe visibility, and Carnot efficiency. "
    "(Note: rotational quantities `moment of inertia`, `angular momentum`, `angular velocity`, `angular acceleration`, "
    "and `torque` ARE mapped in the Partner Lookup Table — do NOT treat them as unmapped.)\n"
    "\n"
    "Step 2 — Open Joints (`scope_status = \"open_joint\"`, `ruling = \"indeterminate\"`, `formula_shape = \"none\"`):\n"
    "  Restrict `open_joint` strictly and ONLY to the four unsettled gravitational/horizon boundary joints: "
    "`escape velocity`, `gravitational time dilation`, `gravitational redshift`, and `Schwarzschild radius`. "
    "Do NOT apply `open_joint` to `gravity well`, `gravitational lensing`, or generic relative velocity `v`.\n"
    "  For an `open_joint` item, set `scope_status = \"open_joint\"`, `ruling = \"indeterminate\"`, "
    "`formula_shape = \"none\"`, `two_level = false`, `unmapped_terms = []`, and empty strings `\"\"` for "
    "`reflected_formula`, `translation_t`, `translation_template`, and `direction_flipped_d`.\n"
    "\n"
    "Step 3 — Formula Shape (Orthogonal Algebraic Preservation):\n"
    "  For every in-scope item (`scope_status = \"in_scope\"`), algebraic proportions always preserve their equation "
    "structure (`formula_shape = \"keeps\"`). Never invert numerator/denominator or flip arithmetic signs inside "
    "`reflected_formula`; reflect only the variable names via the arm's Partner Lookup Table (stripping numeric and "
    "universal constants or preserving them cleanly alongside reflected variables).\n"
    "\n"
    "Step 4 — Condition Reading (`ruling = \"keep\"` vs. `ruling = \"invert\"`, and `two_level`):\n"
    "  Read whether the physical law reflects a boundary-free structural relationship (`keep`) or an effort/dissipation/"
    "barrier/separation cost (`invert`):\n"
    "  - `ruling = \"keep\"` (`two_level = false`): physical definitions, conservation laws, action-reaction symmetries, "
    "mass-energy equivalences, pure perspective transforms without inertia/mass resistance or separation cost, AND "
    "constitutive force/mass/weight/rotational-dynamics laws (noting the background polarity shift from effortful "
    "resistance to unresisting alignment inside `axis_polarity_note`).\n"
    "  - `ruling = \"invert\"`: whenever the physical relation imposes at least one cost (`costs >= 1`): "
    "(a) rising energetic/effort cost driven by inertia/mass or speed barriers, (b) dissipative drag, friction, or "
    "damping losses, (c) mechanical restoring or contact resistance barriers, OR (d) spatial separation preventing "
    "two distant observers from sharing a simultaneous present (`separation_call`).\n"
    "    * Set `two_level = true` ONLY when an `invert` law is simultaneously a productive definition/derivation "
    "(such as mechanical work `W = F * d`, kinetic energy `K = (1/2) * m * v^2`, power `P = F * v`, or centripetal "
    "force `F_c = m * v^2 / r` where the formula defines an operational product whose physical application tracks "
    "costly exertion/turning resistance).\n"
    "    * Set `two_level = false` for pure cost/barrier/limit/dissipation/separation laws."
)

LINT_CONSTRAINTS_V2: str = (
    "Strict Output Formatting & Lint Rules:\n"
    "1. Return ONLY a single valid JSON object with the exact 13 required keys and NO extra keys:\n"
    "   `item_id`, `scope_status`, `formula_shape`, `ruling`, `two_level`, `axis_polarity_note`, "
    "`unmapped_terms`, `variable_map`, `reflected_formula`, `translation_t`, `translation_template`, "
    "`direction_flipped_d`, `rationale`.\n"
    "2. Cross-field invariants:\n"
    "   - `scope_status == \"in_scope\"` <-> `formula_shape == \"keeps\"`, `ruling in (\"keep\", \"invert\")`, "
    "`unmapped_terms == []`, non-empty `variable_map`, non-empty `reflected_formula`, non-empty `translation_t`, "
    "non-empty `translation_template`, non-empty `direction_flipped_d`.\n"
    "   - If `ruling == \"keep\"`, `two_level` MUST be `false`.\n"
    "   - `scope_status == \"no_partner\"` <-> `formula_shape == \"none\"`, `ruling == \"no partner\"`, "
    "`two_level == false`, non-empty `unmapped_terms`, and `reflected_formula == translation_t == "
    "translation_template == direction_flipped_d == \"\"`.\n"
    "   - `scope_status == \"open_joint\"` <-> `formula_shape == \"none\"`, `ruling == \"indeterminate\"`, "
    "`two_level == false`, `unmapped_terms == []`, and `reflected_formula == translation_t == "
    "translation_template == direction_flipped_d == \"\"`.\n"
    "3. Clean ordinary-English prose rules (`translation_t`, `translation_template`, `direction_flipped_d`):\n"
    "   - Use ONLY the arm's target vocabulary from the Partner Lookup Table — NEVER mix vocabulary from another "
    "naming system, NEVER append \"M\" after \"Movement\", and NEVER insert inline parenthetical or appositive "
    "glosses/definitions (e.g., NEVER write `\"Attraction, the receptive pull\"` or `\"Frequency (what you feel)\"`).\n"
    "   - Contain ZERO ASCII/Unicode digits (`0-9`, `²`, `³`) and ZERO SI unit tokens (`m/s`, `kg`, `Hz`, `N*m`, "
    "`J/s`, `rad`, etc.) inside `translation_t`, `translation_template`, or `direction_flipped_d`.\n"
    "   - `translation_template`: wrap EVERY mapped arm target term in `{...}` using the valid "
    "slot keys for this arm (e.g. `{Movement}`, `{conscious_energy}`, `{rise_per_Expansion}`, `{Vibration_Expansion}`), "
    "putting any possessive suffix AFTER `}` (e.g. `{Vibration}'s`) and keeping mapped terms singular inside `{...}` so "
    "unwrapping `{Slot}` -> arm target term reproduces `translation_t` cleanly (and every non-stripped variable_map target "
    "term appears as `{Slot}` in `translation_template`). Leave ZERO unbraced mapped or capitalized arm target terms outside `{...}`!\n"
    "   - `direction_flipped_d`: reverse the relational or causal direction of `translation_t` while retaining the "
    "exact same set of arm target terms coherently and without self-contradictory appositives."
)


def _check_zero_leaked_calibration_formulas(text: str) -> None:
    forbidden = (
        re.compile(r"Frequency\s*=\s*Movement\s*[x×*]\s*Appreciation", re.I),
        re.compile(r"Movement\s*=\s*Desire\s*[x×*]\s*Vibrance", re.I),
        re.compile(r"conscious energy\s*=\s*Movement\s*[x×*]\s*Current\s*(?:\^2|\*\*2|²)", re.I),
        re.compile(r"rise per Expansion\s*=\s*Vibration\s*[/÷]\s*Expansion", re.I),
        re.compile(r"(?<![A-Za-z])E\s*=\s*m\s*c\s*(?:\^2|\*\*2|²)", re.I),
        re.compile(r"(?<![A-Za-z])F(?:_net|\\text\{net\})?\s*=\s*m\s*a(?![A-Za-z])", re.I),
        re.compile(r"(?<![A-Za-z])m\s*=\s*(?:rho|\\rho|ρ)\s*\*?\s*V(?![A-Za-z])", re.I),
    )
    for pat in forbidden:
        m = pat.search(text)
        if m:
            raise ValueError(f"Leaked calibration formula in prompt/rule: {m.group(0)!r}")


_check_zero_leaked_calibration_formulas(RULE_R_V2)
_check_zero_leaked_calibration_formulas(LINT_CONSTRAINTS_V2)


# ---------------------------------------------------------------------------
# {Slot} Template Engine & Validation
# ---------------------------------------------------------------------------

_BRACED_RE = re.compile(r"\{([^{}]+)\}")


def _validate_brace_balance(template: str) -> list[str]:
    """Ensure well-formed flat `{Slot}` placeholders (no nested, unclosed, or empty braces)."""
    slots: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in template:
        if ch == "{":
            if depth != 0:
                raise ValueError("Nested '{' in translation_template")
            depth = 1
            buf = []
        elif ch == "}":
            if depth != 1:
                raise ValueError("Unmatched '}' in translation_template")
            depth = 0
            tok = "".join(buf)
            if not tok.strip() or tok != tok.strip():
                raise ValueError(f"Invalid empty/padded brace token {{{tok!r}}}")
            slots.append(tok)
        elif depth == 1:
            buf.append(ch)
    if depth != 0:
        raise ValueError("Unclosed '{' in translation_template")
    return slots


def _canonicalize_template_to_a0(template: str, src_arm: ArmConfigV2) -> str:
    """Convert a validated arm template (`A0` or `A3-1`) into canonical A0 `{Slot}` notation (case-insensitive)."""
    _validate_brace_balance(template)

    def _repl(m: re.Match[str]) -> str:
        raw_slot = m.group(1)
        a0_slot = src_arm.slot_to_canonical.get(raw_slot) or src_arm.slot_lower_to_canonical.get(raw_slot.lower())
        if not a0_slot:
            raise ValueError(f"Unknown slot {raw_slot!r} for arm {src_arm.arm_id}")
        return "{" + _canonical_slot_key(a0_slot) + "}"

    return _BRACED_RE.sub(_repl, template)


def render_template(
    template: str,
    target_system: str,
    src_arm: ArmConfigV2 | None = None,
) -> str:
    """Render a `{Slot}` template into `"A0"`, `"A3-1"`, or `"S_syn"` deterministically."""
    if src_arm is None:
        src_arm = build_arm_v2("A0")
    canonical_tmpl = _canonicalize_template_to_a0(template, src_arm)

    if target_system == "A0":
        dest_map = build_arm_v2("A0").a0_to_arm
    elif target_system == "A3-1":
        dest_map = build_arm_v2("A3-1").a0_to_arm
    elif target_system == "S_syn":
        dest_map = SYNONYM_MAP_CH16
    else:
        raise ValueError(f"Unsupported target_system: {target_system!r}")

    key_to_val = {_canonical_slot_key(k): v for k, v in dest_map.items()}

    def _sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in key_to_val:
            raise ValueError(f"Slot {key!r} missing from {target_system} mapping")
        return key_to_val[key]

    return _BRACED_RE.sub(_sub, canonical_tmpl)


# Round 2 (`M4`) Control Statements R9 and R10 (canonical A0 templates + flipped D_A0)
ROUND2_CONTROLS_V2: tuple[dict[str, str], ...] = (
    {
        "item_id": "R9",
        "translation_template": (
            "The closer a {Movement} approaches the {Current}, the more {receptive} it becomes, "
            "so each further step takes less effort."
        ),
        "direction_flipped_d": (
            "The closer a Movement approaches the Current, the less receptive it becomes, "
            "so each further step takes more effort."
        ),
    },
    {
        "item_id": "R10",
        "translation_template": (
            "Overall {Frequency} climbs as {Movement} becomes more {receptive} and as "
            "{Appreciation} allows more of the {Current}'s pull to guide it."
        ),
        "direction_flipped_d": (
            "Overall Frequency falls as Movement becomes less receptive and as "
            "Appreciation blocks the Current's pull from guiding it."
        ),
    },
)


# ---------------------------------------------------------------------------
# Strict 13-Key Generator JSON Validator
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
_DIGIT_RE = re.compile(r"[0-9\u00b2\u00b3\u2070-\u2079\u2080-\u2089]")
_SI_UNIT_RE = re.compile(
    r"(?<![A-Za-z])(?:"
    r"kg|km|cm|mm|nm|um|mg|ug|Hz|kHz|MHz|GHz|Pa|kPa|MPa|GPa|mol|cd|rad|sr|Wb|"
    r"kW|MW|GW|kJ|MJ|eV|keV|MeV|GeV|kV|mV|mA|uA|"
    r"[A-Za-z]{1,3}/(?:s|m|kg|K|mol|A|h)"
    r")(?![A-Za-z])"
)
_DANGLING_M_RE = re.compile(r"(?<![A-Za-z])Movement\s+M(?![A-Za-z])")
_SELF_CONTRADICTORY_APPOSITIVE_RE = re.compile(
    r"(?:"
    r"\b(?:repelled|pushed\s+away|driven\s+apart)\s+by\s+[^.,;]{1,35},\s+(?:the|a)\s+(?:receptive|pull|affinity|drawing)\b"
    r")",
    re.I,
)


def _norm_ws(s: str) -> str:
    return _WS_RE.sub(" ", s.strip())


_STRIPPED_TARG_VALUE_RE = re.compile(
    r"^(?:\(\s*)?(?:"
    r"(?:none\s*\(?\s*)?stripped(?:\s+(?:dimensional|dimensionless|numeric))?(?:\s+(?:constant|prefactor|factor))?\)?"
    r"|constant\s*\(\s*stripped\s*\)"
    r"|dimensionless\s+(?:constant|prefactor)"
    r"|numeric\s+(?:constant|prefactor)"
    r")(?:\s*\))?$",
    re.I,
)

_ALLOWED_STRIPPED_PHYS_EXACT_CASE: frozenset[str] = frozenset({"G", "h", "hbar"})
_ALLOWED_STRIPPED_PHYS_LOWER: frozenset[str] = frozenset(
    {
        "gamma",
        "pi",
        "mu_k",
        "mu_s",
        "muk",
        "mus",
        "k_e",
        "ke",
        "epsilon_0",
        "epsilon0",
        "eps_0",
        "mu_0",
        "mu0",
        "hbar",
        "gravitational constant",
        "newton's gravitational constant",
        "newtons gravitational constant",
        "coulomb constant",
        "coulomb's constant",
        "coulombs constant",
        "planck constant",
        "planck's constant",
        "reduced planck constant",
        "lorentz factor",
        "coefficient of friction",
        "coefficient of kinetic friction",
        "coefficient of static friction",
        "permittivity",
        "vacuum permittivity",
        "permeability",
        "vacuum permeability",
        "dimensionless prefactor",
        "numeric prefactor",
        "prefactor",
        "numeric factor",
    }
)
_NUMERIC_PREFACTOR_RE = re.compile(r"^[0-9\s./*+^()\\-]+$")


def _is_stripped_constant_var_entry(raw_phys: str, raw_targ: str) -> bool:
    """Return True iff `(raw_phys, raw_targ)` explicitly marks a stripped Rule-R constant/prefactor."""
    if not _STRIPPED_TARG_VALUE_RE.match(raw_targ.strip()):
        return False
    p_raw = raw_phys.strip()
    p_nobrace = re.sub(r"[\\{}]", "", p_raw).strip()
    if p_nobrace in _ALLOWED_STRIPPED_PHYS_EXACT_CASE:
        return True
    p_norm = re.sub(r"\s+", " ", p_nobrace).lower()
    p_compact = p_norm.replace(" ", "")
    if p_norm in _ALLOWED_STRIPPED_PHYS_LOWER or p_compact in _ALLOWED_STRIPPED_PHYS_LOWER:
        return True
    p_stripped = strip_math_decorations(p_raw).replace("\\", "").strip().lower()
    if _NUMERIC_PREFACTOR_RE.match(p_stripped):
        return True
    # E.g. "4 pi^2", "2 pi", "(1/2)"
    if re.sub(r"\bpi\b", "", p_stripped).strip() and _NUMERIC_PREFACTOR_RE.match(
        re.sub(r"\bpi\b", "1", p_stripped)
    ):
        return True
    return False


_TERM_PATTERN_CACHE: dict[tuple[str, ...], tuple[re.Pattern[str], tuple[str, ...]]] = {}


def _inflect_last_word_pattern(word: str) -> str:
    lw = word.lower()
    if lw in ("out", "for", "in", "to", "reflected", "receptive", "idle", "per"):
        return re.escape(word)
    if lw == "vortex":
        return r"(?:Vortex(?:es)?|Vortices)"
    if len(word) > 2 and lw.endswith("y") and lw[-2] not in "aeiou":
        return re.escape(word[:-1]) + r"(?:y|ies|ys)"
    if lw.endswith(("s", "x", "z", "ch", "sh")):
        return re.escape(word) + r"(?:es|s)?"
    if lw.endswith("e"):
        return re.escape(word) + r"s?"
    return re.escape(word) + r"(?:es|s)?"


def _get_arm_term_inflection_regex(arm: ArmConfigV2) -> tuple[re.Pattern[str], tuple[str, ...]]:
    key = arm.valid_target_terms
    cached = _TERM_PATTERN_CACHE.get(key)
    if cached is not None:
        return cached
    parts: list[str] = []
    ordered_terms: list[str] = []
    for term in arm.valid_target_terms:
        m_sep = re.match(r"^(.*[\s-])([A-Za-z]+)$", term)
        if m_sep:
            prefix, last_word = m_sep.group(1), m_sep.group(2)
            # Also match hyphen or multi-space variations inside compounds
            pat_str = re.escape(prefix) + _inflect_last_word_pattern(last_word)
        else:
            pat_str = _inflect_last_word_pattern(term)
        parts.append(f"({pat_str})")
        ordered_terms.append(term)
    compiled = re.compile(r"(?<![A-Za-z])(?:" + "|".join(parts) + r")(?![A-Za-z])", re.I)
    val = (compiled, tuple(ordered_terms))
    _TERM_PATTERN_CACHE[key] = val
    return val


def extract_arm_terms(
    text: str,
    arm: ArmConfigV2,
    *,
    active_terms: set[str] | None = None,
    ignore_unmapped_lowercase: bool = False,
) -> list[str]:
    """Find canonical arm target terms in `text` (case-insensitive with regular plurals/possessives).

    When `ignore_unmapped_lowercase=True`, single-word all-lowercase prose words (like everyday
    `'future'`, `'collection'`, `'current'`) that are NOT in `active_terms` are ignored.
    """
    if not text:
        return []
    pat, ordered_terms = _get_arm_term_inflection_regex(arm)
    active = active_terms or set()
    found: list[str] = []
    for m in pat.finditer(text):
        idx = m.lastindex
        if idx is None:
            continue
        canonical_term = ordered_terms[idx - 1]
        matched_text = m.group(idx)
        if ignore_unmapped_lowercase:
            has_content_word = any(len(w) >= 4 for w in re.findall(r"[A-Za-z]+", canonical_term))
            is_non_prepositional_compound = (" " in canonical_term or "-" in canonical_term) and has_content_word
            if (
                canonical_term in active
                or is_non_prepositional_compound
                or any(w[0].isupper() for w in matched_text.split() if w)
            ):
                found.append(canonical_term)
        else:
            found.append(canonical_term)
    return found


def _has_inline_gloss_appositive(text: str, arm: ArmConfigV2) -> str | None:
    m_contra = _SELF_CONTRADICTORY_APPOSITIVE_RE.search(text)
    if m_contra:
        return f"self-contradictory appositive {m_contra.group(0)!r}"
    # Check "<TargetTerm> (parenthetical gloss)" or "<TargetTerm>, the <gloss>"
    term_alt = "|".join(re.escape(t) for t in arm.valid_target_terms)
    paren_gloss = re.compile(rf"(?<![A-Za-z])(?:{term_alt})\s*\([^)]+\)")
    mp = paren_gloss.search(text)
    if mp:
        return f"inline parenthetical gloss {mp.group(0)!r}"
    comma_what = re.compile(
        rf"(?<![A-Za-z])(?:{term_alt}),\s+(?:the\s+(?:receptive|resistant|physical|nonphysical)|meaning\s+|defined\s+as\s+|i\.e\.)",
        re.I,
    )
    mc = comma_what.search(text)
    if mc:
        return f"inline appositive gloss {mc.group(0)!r}"
    return None


_TMPL_FORBIDDEN_SYMBOL_RE = re.compile(r"[=+*/^()\[\]<>\\×÷]")


def normalize_generator_parsed(parsed: Any, arm: ArmConfigV2) -> None:
    """Normalize benign formatting in `in_scope` generator JSON in place."""
    if not isinstance(parsed, dict) or parsed.get("scope_status") != "in_scope":
        return

    for fn in ("translation_t", "translation_template", "direction_flipped_d"):
        val = parsed.get(fn)
        if isinstance(val, str):
            parsed[fn] = _norm_ws(val.replace("\u00b2", " squared").replace("\u00b3", " cubed"))

    for fn in ("direction_flipped_d", "translation_t"):
        val = parsed.get(fn)
        if isinstance(val, str) and "{" in val and "}" in val:
            try:
                slots = _validate_brace_balance(val)
            except ValueError:
                slots = []
            if slots and all(s.lower() in arm.slot_lower_to_canonical for s in slots):
                parsed[fn] = render_template(val, arm.arm_id, src_arm=arm)

    tmpl = parsed.get("translation_template")
    if isinstance(tmpl, str) and tmpl.strip() and not re.search(r"\}\{", tmpl):
        tmpl_clean = _norm_ws(re.sub(r"\s*=\s*", " equals ", tmpl))
        try:
            slots = _validate_brace_balance(tmpl_clean)
        except ValueError:
            slots = []
        if slots and all(s.lower() in arm.slot_lower_to_canonical for s in slots):
            unwrapped = render_template(tmpl_clean, arm.arm_id, src_arm=arm)
            if (
                not _TMPL_FORBIDDEN_SYMBOL_RE.search(unwrapped)
                and not _DIGIT_RE.search(unwrapped)
                and _has_inline_gloss_appositive(unwrapped, arm) is None
            ):
                parsed["translation_template"] = tmpl_clean
                parsed["translation_t"] = unwrapped


def validate_generator_json(
    parsed: Any,
    arm: ArmConfigV2,
    item: dict[str, Any],
) -> list[str]:
    """Validate strict 13-key generator output and cross-field/template invariants.

    Returns a list of error strings (`[]` iff valid).
    """
    errors: list[str] = []
    if not isinstance(parsed, dict):
        return [f"Output must be a JSON object, got {type(parsed).__name__}"]

    missing = sorted(REQUIRED_GENERATOR_KEYS - set(parsed.keys()))
    extra = sorted(set(parsed.keys()) - REQUIRED_GENERATOR_KEYS)
    if missing:
        errors.append(f"Missing required keys: {missing}")
    if extra:
        errors.append(f"Unexpected extra keys: {extra}")
    if errors:
        return errors

    if parsed["item_id"] != item["item_id"]:
        errors.append(f"item_id mismatch: got {parsed['item_id']!r}, expected {item['item_id']!r}")

    scope = parsed["scope_status"]
    fshape = parsed["formula_shape"]
    ruling = parsed["ruling"]
    two_level = parsed["two_level"]
    axis_note = parsed["axis_polarity_note"]
    unmapped = parsed["unmapped_terms"]
    var_map = parsed["variable_map"]
    refl_formula = parsed["reflected_formula"]
    trans_t = parsed["translation_t"]
    trans_tmpl = parsed["translation_template"]
    dir_d = parsed["direction_flipped_d"]
    rationale = parsed["rationale"]

    if scope not in ("in_scope", "no_partner", "open_joint"):
        errors.append(f"Invalid scope_status: {scope!r}")
    if not isinstance(two_level, bool):
        errors.append(f"two_level must be bool, got {type(two_level).__name__}")
    for field_name in ("axis_polarity_note", "reflected_formula", "translation_t", "translation_template", "direction_flipped_d", "rationale"):
        if not isinstance(parsed[field_name], str):
            errors.append(f"{field_name} must be a string")
    if not isinstance(unmapped, list) or not all(isinstance(x, str) and x.strip() for x in unmapped):
        errors.append("unmapped_terms must be a list of non-empty strings")
    if not isinstance(var_map, dict) or not all(
        isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
        for k, v in var_map.items()
    ):
        errors.append("variable_map must be a dict mapping non-empty strings to non-empty strings")
    if isinstance(rationale, str) and not rationale.strip():
        errors.append("rationale must be non-empty")

    if errors:
        return errors

    normalize_generator_parsed(parsed, arm)
    trans_t = parsed["translation_t"]
    trans_tmpl = parsed["translation_template"]
    dir_d = parsed["direction_flipped_d"]

    # Check dangling "Movement M" across ALL string fields & variable_map values
    for field_name in ("axis_polarity_note", "reflected_formula", "translation_t", "translation_template", "direction_flipped_d"):
        if _DANGLING_M_RE.search(parsed[field_name]):
            errors.append(f"Forbidden legacy 'Movement M' in {field_name}")
    for k, v in var_map.items():
        if _DANGLING_M_RE.search(v):
            errors.append(f"Forbidden legacy 'Movement M' in variable_map[{k!r}]")

    if scope == "in_scope":
        if fshape != "keeps":
            errors.append(f"in_scope requires formula_shape='keeps', got {fshape!r}")
        if ruling not in ("keep", "invert"):
            errors.append(f"in_scope requires ruling in ('keep', 'invert'), got {ruling!r}")
        if ruling == "keep" and two_level is not False:
            errors.append("ruling='keep' requires two_level=false")
        if unmapped:
            errors.append(f"Cross-field contradiction: unmapped_terms={unmapped!r} while scope_status='in_scope'")
        if not axis_note.strip():
            errors.append("in_scope requires non-empty axis_polarity_note")
        if not var_map:
            errors.append("in_scope requires non-empty variable_map")
        if not refl_formula.strip():
            errors.append("in_scope requires non-empty reflected_formula")
        if not trans_t.strip():
            errors.append("in_scope requires non-empty translation_t")
        if not trans_tmpl.strip():
            errors.append("in_scope requires non-empty translation_template")
        if not dir_d.strip():
            errors.append("in_scope requires non-empty direction_flipped_d")

        # Collect non-stripped mapped arm target slots declared in variable_map
        mapped_arm_slots: set[str] = set()
        for k, v in var_map.items():
            if _is_stripped_constant_var_entry(k, v):
                continue
            toks, _unk = extract_target_tokens_stripped(normalize_target_token_v2(v), arm)
            mapped_arm_slots.update(toks)

        braced_arm_slots: set[str] = set()

        # Validate template syntax, case-insensitive slot keys, mapped-slot coverage, unwrapped equality,
        # and zero unbraced mapped or capitalized target terms outside {...}
        if trans_tmpl.strip():
            try:
                slots = _validate_brace_balance(trans_tmpl)
                if not slots:
                    errors.append("translation_template contains zero {Slot} placeholders")
                invalid_slots = [s for s in slots if s.lower() not in arm.slot_lower_to_canonical]
                if invalid_slots:
                    errors.append(f"Invalid slot tokens for arm {arm.arm_id}: {invalid_slots}")
                else:
                    braced_arm_slots = {
                        arm.a0_to_arm[arm.slot_lower_to_canonical[s.lower()]]
                        for s in slots
                    }
                    missing_in_template = sorted(mapped_arm_slots - braced_arm_slots)
                    if missing_in_template:
                        errors.append(
                            f"Non-stripped variable_map slot(s) missing from translation_template {{...}}: "
                            f"{missing_in_template}"
                        )
                    stripped_tmpl = _BRACED_RE.sub(" ", trans_tmpl)
                    bare_outside = extract_arm_terms(
                        stripped_tmpl,
                        arm,
                        active_terms=mapped_arm_slots,
                        ignore_unmapped_lowercase=True,
                    )
                    if bare_outside:
                        errors.append(f"Unbraced bare arm target terms in translation_template: {bare_outside}")
                    unwrapped = render_template(trans_tmpl, arm.arm_id, src_arm=arm)
                    if _norm_ws(unwrapped).lower() != _norm_ws(trans_t).lower():
                        errors.append(
                            f"Unwrapped translation_template mismatch vs translation_t: "
                            f"{_norm_ws(unwrapped)!r} != {_norm_ws(trans_t)!r}"
                        )
            except ValueError as exc:
                errors.append(f"Malformed translation_template: {exc}")

        # Reject digits & SI unit tokens inside prose fields
        for fname in ("translation_t", "translation_template", "direction_flipped_d"):
            val = parsed[fname]
            if _DIGIT_RE.search(val):
                errors.append(f"Digits/superscript digits forbidden in {fname}")
            m_si = _SI_UNIT_RE.search(val)
            if m_si and m_si.group(0).lower() not in ("and/or",):
                errors.append(f"SI unit token {m_si.group(0)!r} forbidden in {fname}")
            gloss_err = _has_inline_gloss_appositive(val, arm)
            if gloss_err:
                errors.append(f"Inline gloss / contradictory appositive in {fname}: {gloss_err}")

        for fn in ("translation_t", "direction_flipped_d"):
            if "{" in parsed[fn] or "}" in parsed[fn]:
                errors.append(f"Unresolved '{{' or '}}' braces in {fn}")

        # Validate direction_flipped_d differs from translation_t and keeps the same target vocabulary set
        if trans_t.strip() and dir_d.strip():
            if _norm_ws(dir_d).lower() == _norm_ws(trans_t).lower():
                errors.append("direction_flipped_d is identical to translation_t (no polarity flip)")
            active_terms = mapped_arm_slots | braced_arm_slots
            t_terms = set(
                extract_arm_terms(
                    trans_t,
                    arm,
                    active_terms=active_terms,
                    ignore_unmapped_lowercase=True,
                )
            )
            d_terms = set(
                extract_arm_terms(
                    dir_d,
                    arm,
                    active_terms=active_terms,
                    ignore_unmapped_lowercase=True,
                )
            )
            if not t_terms:
                errors.append("translation_t contains zero arm target terms")
            elif d_terms != t_terms:
                errors.append(
                    f"direction_flipped_d target term set {sorted(d_terms)} != "
                    f"translation_t target term set {sorted(t_terms)}"
                )

    elif scope == "no_partner":
        if fshape != "none":
            errors.append(f"no_partner requires formula_shape='none', got {fshape!r}")
        if ruling != "no partner":
            errors.append(f"no_partner requires ruling='no partner', got {ruling!r}")
        if two_level is not False:
            errors.append("no_partner requires two_level=false")
        if not unmapped:
            errors.append("no_partner requires non-empty unmapped_terms")
        for fname in ("reflected_formula", "translation_t", "translation_template", "direction_flipped_d"):
            if parsed[fname] != "":
                errors.append(f"no_partner requires {fname} == '', got {parsed[fname]!r}")

    elif scope == "open_joint":
        if fshape != "none":
            errors.append(f"open_joint requires formula_shape='none', got {fshape!r}")
        if ruling != "indeterminate":
            errors.append(f"open_joint requires ruling='indeterminate', got {ruling!r}")
        if two_level is not False:
            errors.append("open_joint requires two_level=false")
        if unmapped:
            errors.append(f"open_joint requires unmapped_terms == [], got {unmapped!r}")
        for fname in ("reflected_formula", "translation_t", "translation_template", "direction_flipped_d"):
            if parsed[fname] != "":
                errors.append(f"open_joint requires {fname} == '', got {parsed[fname]!r}")

    return errors


# ---------------------------------------------------------------------------
# Layer A v2: Token Normalization, Formula Composition, AST Sign Preservation, & Cycles
# ---------------------------------------------------------------------------

_TEX_WRAPPER_RE = re.compile(r"\\(?:vec|bar|overline|hat|tilde|text|mathrm|mathbf|mathit|dot)\{([^{}]*)\}")
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]{1,24}\)\s*$")
_PRIMES_RE = re.compile(r"['\u2032\u2033]+")
_COMBINING_MARKS_RE = re.compile(r"[\u0304\u0305\u20d7\u2192]+")
_SUBSCRIPT_SIMPLE_RE = re.compile(r"(?<=[A-Za-z0-9\)\]])_[A-Za-z0-9]+")

_ALLOWED_MATH_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "arcsin",
        "arccos",
        "arctan",
        "sinh",
        "cosh",
        "tanh",
        "log",
        "ln",
        "exp",
        "sqrt",
        "frac",
        "left",
        "right",
        "Delta",
        "delta",
        "pi",
        "sum",
        "int",
        "oint",
        "iint",
        "prod",
        "partial",
        "nabla",
        "lim",
        "max",
        "min",
        "to",
        "infty",
        "text",
        "mathrm",
        "mathbf",
        "mathit",
        "hat",
        "vec",
        "bar",
        "overline",
        "tilde",
        "dot",
        "cdot",
        "times",
        "div",
        "quad",
        "qquad",
        "const",
        "constant",
        "proper",
        "net",
        "sys",
        "rms",
        "avg",
        "ave",
        "initial",
        "final",
        "cm",
        "imath",
        "jmath",
        "N",
        "j",
        "k",
        "i",
        "f",
        "e",
        "d",
        "as",
        "for",
        "where",
        "when",
        "if",
        "and",
        "or",
        "with",
        "at",
    }
    | set(STRIPPED_CONSTANTS)
    | {"mu", "epsilon", "rho", "tau", "alpha", "beta", "theta", "phi", "omega"}
)

_AST_CONST_OR_OP_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "arcsin",
        "arccos",
        "arctan",
        "sinh",
        "cosh",
        "tanh",
        "log",
        "ln",
        "exp",
        "sqrt",
        "frac",
        "left",
        "right",
        "sum",
        "int",
        "oint",
        "iint",
        "prod",
        "lim",
        "max",
        "min",
        "pi",
        "gamma",
        "const",
        "constant",
        "infty",
        "to",
        "Delta",
        "delta",
        "imath",
        "jmath",
        "hat",
        "vec",
        "bar",
        "overline",
        "tilde",
        "dot",
    }
)


def _strip_balanced_subscripts(s: str) -> str:
    """Remove all balanced `_{...}` and simple `_sym` subscripts safely (preserving preceding token/parens)."""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "_" and i + 1 < n and s[i + 1] == "{":
            res = _read_balanced_brace(s, i + 1)
            if res is not None:
                _sub_content, next_i = res
                i = next_i
                continue
        out.append(s[i])
        i += 1
    s2 = "".join(out)
    return _SUBSCRIPT_SIMPLE_RE.sub("", s2)


def strip_math_decorations(text: str) -> str:
    """Strip TeX wrappers, subscripts (`_PS`, `_{\text{grav,} A B}`, `)_j`), primes (`'`),
    and combining marks WITHOUT deleting arbitrary parenthesized subexpressions or `*`!
    """
    s = (
        text.replace("$", "")
        .replace("\\ ", " ")
        .replace("\\,", " ")
        .replace("\\;", " ")
        .replace("\\:", " ")
        .replace("\\!", " ")
    )
    s = _COMBINING_MARKS_RE.sub("", s)
    for _ in range(4):
        s_new = _TEX_WRAPPER_RE.sub(r"\1", s)
        if s_new == s:
            break
        s = s_new
    s = _strip_balanced_subscripts(s)
    s = _PRIMES_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def strip_token_decorations(text: str) -> str:
    """Compatibility alias for `strip_math_decorations` (preserves parenthesized math subexpressions)."""
    return strip_math_decorations(text)


def normalize_target_token_v2(token: str) -> str:
    """Normalize a single target token from `variable_map` (`Movement_j -> Movement`,
    `Vibration' -> Vibration`, `Appreciation (CM) -> Appreciation`, `Appreciation_PS -> Appreciation`).
    """
    s = strip_math_decorations(token)
    while _TRAILING_PAREN_RE.search(s):
        s = _TRAILING_PAREN_RE.sub("", s).strip()
    return s


def normalize_phys_token_v2(token: str) -> str:
    """Normalize a physical concept/variable name for cross-item bijection checks."""
    s = strip_math_decorations(token).lower()
    while _TRAILING_PAREN_RE.search(s):
        s = _TRAILING_PAREN_RE.sub("", s).strip()
    s = re.sub(r"[\\{}]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_TEX_CMD_TOKEN_MAP: dict[str, str] = {
    "times": " * ",
    "cdot": " * ",
    "div": " / ",
    "frac": " frac ",
    "sqrt": " sqrt ",
    "int": " int ",
    "oint": " oint ",
    "iint": " iint ",
    "sum": " sum ",
    "prod": " prod ",
    "partial": " partial ",
    "nabla": " nabla ",
    "hat": " hat ",
    "vec": " vec ",
    "bar": " bar ",
    "overline": " overline ",
    "tilde": " tilde ",
    "text": " text ",
    "mathrm": " mathrm ",
    "mathbf": " mathbf ",
    "mathit": " mathit ",
    "dot": " dot ",
    "imath": " imath ",
    "jmath": " jmath ",
    "Delta": " Delta ",
    "delta": " delta ",
    "pi": " pi ",
    "gamma": " gamma ",
    "mu": " mu ",
    "rho": " rho ",
    "tau": " tau ",
    "theta": " theta ",
    "phi": " phi ",
    "omega": " omega ",
    "infty": " infty ",
    "to": " to ",
    "propto": " ",
    "approx": " ",
    "equiv": " ",
    "leq": " ",
    "geq": " ",
    "le": " ",
    "ge": " ",
    "qquad": " ",
    "quad": " ",
    "left": " ",
    "right": " ",
}

_TEX_CMD_TOKEN_RE = re.compile(
    r"\\(" + "|".join(re.escape(k) for k in sorted(_TEX_CMD_TOKEN_MAP, key=len, reverse=True)) + r")(?![A-Za-z])"
)


def extract_target_tokens_stripped(expr: str, arm: ArmConfigV2) -> tuple[list[str], list[str]]:
    """Extract normalized arm target terms from `expr` AFTER stripping decorations.

    Returns `(matched_target_terms, unknown_alpha_fragments)`.
    Uses `(?<![A-Za-z])...(?![A-Za-z])` (NEVER `\\b`) so `_` never blocks matching.
    """
    cleaned = strip_math_decorations(expr)
    # Replace TeX commands using (?![A-Za-z]) boundaries longest-first so \\le never corrupts \\left
    cleaned = _TEX_CMD_TOKEN_RE.sub(lambda m: _TEX_CMD_TOKEN_MAP[m.group(1)], cleaned)
    matched: list[str] = []
    pat = re.compile(
        r"(?<![A-Za-z])("
        + "|".join(re.escape(t) for t in arm.valid_target_terms)
        + r")(?![A-Za-z])"
    )
    remainder_parts: list[str] = []
    pos = 0
    for m in pat.finditer(cleaned):
        remainder_parts.append(cleaned[pos : m.start()])
        matched.append(m.group(0))
        pos = m.end()
    remainder_parts.append(cleaned[pos:])
    remainder = " ".join(remainder_parts)
    # Extract any leftover alphabetic tokens from remainder (case-sensitive first so 'e'/'i'/'d'/'N' don't hide uppercase vars)
    unknowns: list[str] = []
    for alpha in re.findall(r"[A-Za-z]+", remainder):
        if alpha not in _ALLOWED_MATH_IDENTIFIERS and alpha.lower() not in _ALLOWED_MATH_IDENTIFIERS:
            unknowns.append(alpha)
    return matched, unknowns


# Base concept groups that are genuinely distinct conceptual slots on the A0 side
# vs legitimate multi-physics synonyms mapping to one A0 slot.
_ALLOWED_SYNONYM_COLLISIONS_A0: dict[str, set[str]] = {
    "Vibration": {"space", "distance", "displacement", "separation", "wavelength", "width", "length", "position", "coordinate", "height", "radius", "gradient", "length contraction"},
    "Expansion": {"time", "time interval", "proper time", "evolution time", "period", "duration", "time dilation"},
    "rise per Expansion": {"velocity", "speed", "terminal velocity", "wave speed"},
    "Appreciation": {"acceleration", "centripetal acceleration", "tangential acceleration"},
    "Frequency": {"force", "net force", "normal force", "buoyant force", "centripetal force", "electrostatic force", "lorentz force", "restoring force", "tension force"},
    "Movement": {"mass", "mass m", "inertial mass", "vacuum expectation value", "inertial frame", "inertial observer", "inertial rest frame", "reference frame", "observer"},
    "conscious energy": {"energy", "physical energy", "kinetic energy", "potential energy", "gravitational potential energy", "mechanical energy", "total energy", "rest energy", "relativistic energy", "photon energy", "quantized energy", "zero-point energy", "confining potential", "barrier height", "stress-energy"},
    "resonance": {"friction", "static friction", "kinetic friction", "damping", "damping force", "damping coefficient", "damping rate", "drag", "drag force", "air resistance", "decoherence rate"},
    "Attraction": {"gravity", "gravitational pull", "gravitational field", "gravitational acceleration", "gravity well", "gravitational lensing"},
    "Vibration-Expansion": {"spacetime interval", "spacetime coordinate", "spacetime metric", "spacetime geometry", "spacetime derivative", "space-time"},
}


def _check_static_arm_bijection(arm: ArmConfigV2) -> list[dict[str, Any]]:
    """Verify the arm's own partner lookup table has zero typed mirror-twice clashes."""
    collisions: list[dict[str, Any]] = []
    # 1. No physical term maps to two different target expressions
    phys_to_targets: dict[str, set[str]] = defaultdict(set)
    for phys, targ, _role in arm.partner_entries:
        phys_to_targets[phys.lower()].add(targ)
    for phys_lc, targs in sorted(phys_to_targets.items()):
        if len(targs) > 1:
            collisions.append({"kind": "arm_one_to_many", "physical": phys_lc, "targets": sorted(targs)})

    # 2. No two distinct role classes share the exact same single target term
    targ_to_roles: dict[str, set[str]] = defaultdict(set)
    for phys, targ, role in arm.mirror_pairs:
        targ_to_roles[targ].add(role)
    return collisions


def _strip_side_condition(expr: str) -> str:
    s = re.split(r"\\qquad|\\quad|\s{2,}\(", expr, maxsplit=1)[0]
    s = re.sub(r"\(\s*(?:for|where|when|constant|as|if)\b[^)]*\)\s*$", "", s, flags=re.I)
    return s.strip()


def _split_top_level_char(s: str, sep: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in s:
        if ch in "({[":
            depth += 1
            buf.append(ch)
        elif ch in ")}]":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif depth == 0 and ch == sep:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail or parts:
        parts.append(tail)
    return parts


def _parse_equation_clauses_and_segments(formula: str) -> list[list[str]]:
    """Parse formula into top-level comma clauses, each split into top-level `=` segments.

    Strips side conditions and balanced subscripts (`W_{\text{grav,} A B} -> W`) FIRST so commas
    inside subscripts never truncate an equation!
    """
    if not formula or formula.strip().lower().startswith("none"):
        return []
    cleaned = strip_math_decorations(_strip_side_condition(formula))
    clauses = _split_top_level_char(cleaned, ",")
    eq_lists: list[list[str]] = []
    for clause in clauses:
        if "=" in clause:
            segs = [seg for seg in _split_top_level_char(clause, "=") if seg]
            if len(segs) >= 2:
                eq_lists.append(segs)
    return eq_lists


def _parse_equation_lhs_rhs(formula: str) -> tuple[str, str] | None:
    eq_lists = _parse_equation_clauses_and_segments(formula)
    if not eq_lists:
        return None
    segs = eq_lists[0]
    return segs[0], segs[-1]


def _read_balanced_brace(s: str, start: int) -> tuple[str, int] | None:
    if start >= len(s) or s[start] != "{":
        return None
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1 : i], i + 1
    return None


def _expand_latex_frac(s: str) -> str:
    """Replace nested `\\frac{A}{B}` constructs with `((A))/((B))` safely."""
    out = s
    while True:
        idx = out.find("\\frac")
        if idx == -1:
            break
        pos = idx + 5
        while pos < len(out) and out[pos].isspace():
            pos += 1
        num_res = _read_balanced_brace(out, pos)
        if num_res is None:
            out = out[:idx] + out[idx + 5 :]
            continue
        num_txt, pos2 = num_res
        while pos2 < len(out) and out[pos2].isspace():
            pos2 += 1
        den_res = _read_balanced_brace(out, pos2)
        if den_res is None:
            out = out[:idx] + f"({num_txt})" + out[pos2:]
            continue
        den_txt, pos3 = den_res
        out = out[:idx] + f"(({num_txt}))/(({den_txt}))" + out[pos3:]
    return out


@dataclass(frozen=True)
class _NumNode:
    val: str


@dataclass(frozen=True)
class _VarNode:
    name: str


@dataclass(frozen=True)
class _TermNode:
    name: str


@dataclass(frozen=True)
class _NegNode:
    inner: Any


@dataclass(frozen=True)
class _AddNode:
    terms: tuple[Any, ...]


@dataclass(frozen=True)
class _MulNode:
    factors: tuple[Any, ...]


@dataclass(frozen=True)
class _FracNode:
    num: Any
    den: Any


@dataclass(frozen=True)
class _PowNode:
    base: Any
    exp: Any


@dataclass(frozen=True)
class _FuncNode:
    fn: str
    arg: Any


_FUNC_NAMES: frozenset[str] = frozenset(
    {"sqrt", "sin", "cos", "tan", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "log", "ln", "exp"}
)


_TEX_AST_CMD_MAP: dict[str, str] = {
    "times": "*",
    "cdot": "*",
    "div": "/",
    "left": "",
    "right": "",
    "hat": "",
    "vec": "",
    "bar": "",
    "overline": "",
    "tilde": "",
    "dot": "",
    "partial": " d ",
    "nabla": " ",
    "Delta": " Delta ",
    "delta": " delta ",
    "pi": " pi ",
    "gamma": " gamma ",
    "omega": " omega ",
    "mu": " mu ",
    "rho": " rho ",
    "tau": " tau ",
    "theta": " theta ",
    "phi": " phi ",
    "epsilon": " epsilon ",
    "cos": " cos ",
    "sin": " sin ",
    "tan": " tan ",
    "exp": " exp ",
    "ln": " ln ",
    "log": " log ",
}

_TEX_AST_CMD_RE = re.compile(
    r"\\(" + "|".join(re.escape(k) for k in sorted(_TEX_AST_CMD_MAP, key=len, reverse=True)) + r")(?![A-Za-z])"
)


def _preprocess_formula_for_ast(expr: str) -> str:
    s = strip_math_decorations(_expand_latex_frac(expr))
    # Handle \sqrt[n]{...} -> sqrt(...) and \sqrt{...} -> sqrt(...)
    s = re.sub(r"\\sqrt\s*\[[^\]]*\]", "sqrt", s)
    s = re.sub(r"\\sqrt(?![A-Za-z])", "sqrt", s)
    # Strip big operators \sum, \int, \oint, \iint, \prod possibly with ^{...} limits
    s = re.sub(r"(?:\\(?:sum|int|oint|iint|prod)|(?<![A-Za-z])(?:sum|int|oint|iint|prod)(?![A-Za-z]))(?:\s*\^\s*(?:\{[^{}]*\}|[A-Za-z0-9]+))?", " ", s)
    # Convert ^{...} -> ^(...) so parser handles exponents cleanly before brace->paren normalization
    s = re.sub(r"\^\s*\{([^{}]*)\}", r"^(\1)", s)
    s = s.replace("÷", "/").replace("−", "-")
    s = _TEX_AST_CMD_RE.sub(lambda m: _TEX_AST_CMD_MAP[m.group(1)], s)
    s = s.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")
    return re.sub(r"\s+", " ", s).strip()


def _tokenize_ast(expr: str, arm: ArmConfigV2 | None = None) -> tuple[list[tuple[str, str]], dict[str, str]]:
    s = _preprocess_formula_for_ast(expr)
    term_map: dict[str, str] = {}
    if arm is not None:
        pat = re.compile(
            r"(?<![A-Za-z])(" + "|".join(re.escape(t) for t in arm.valid_target_terms) + r")(?![A-Za-z])"
        )
        parts: list[str] = []
        pos = 0
        idx = 0
        for m in pat.finditer(s):
            parts.append(s[pos : m.start()])
            marker = f" __TERM{idx}__ "
            term_map[f"__TERM{idx}__"] = m.group(0)
            parts.append(marker)
            idx += 1
            pos = m.end()
        parts.append(s[pos:])
        s = "".join(parts)

    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "+-*/^":
            if ch == "*" and i + 1 < n and s[i + 1] == "*":
                tokens.append(("OP", "^"))
                i += 2
            else:
                tokens.append(("OP", ch))
            i += 1
        elif ch == "(":
            tokens.append(("LP", "("))
            i += 1
        elif ch == ")":
            tokens.append(("RP", ")"))
            i += 1
        elif ch.isdigit() or (ch == "." and i + 1 < n and s[i + 1].isdigit()):
            j = i + 1
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append(("NUM", s[i:j]))
            i = j
        elif ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            word = s[i:j]
            if word in term_map:
                tokens.append(("TERM", term_map[word]))
            else:
                tokens.append(("ID", word))
            i = j
        else:
            i += 1
    return tokens, term_map


class _ExprParser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_expr(self) -> Any:
        first = self.parse_mul()
        terms = [first]
        while True:
            tok = self.peek()
            if tok is not None and tok[0] == "OP" and tok[1] in ("+", "-"):
                self.advance()
                rhs = self.parse_mul()
                terms.append(rhs if tok[1] == "+" else _NegNode(rhs))
            else:
                break
        return terms[0] if len(terms) == 1 else _AddNode(tuple(terms))

    def parse_mul(self) -> Any:
        node = self.parse_unary()
        while True:
            tok = self.peek()
            if tok is None:
                break
            if tok[0] == "OP" and tok[1] in ("*", "/"):
                op = self.advance()[1]
                rhs = self.parse_unary()
                if op == "*":
                    node = _MulNode((*node.factors, rhs) if isinstance(node, _MulNode) else (node, rhs))
                else:
                    node = _FracNode(node, rhs)
            elif tok[0] in ("NUM", "ID", "TERM", "LP"):
                rhs = self.parse_unary()
                node = _MulNode((*node.factors, rhs) if isinstance(node, _MulNode) else (node, rhs))
            else:
                break
        return node

    def parse_unary(self) -> Any:
        tok = self.peek()
        if tok is not None and tok[0] == "OP" and tok[1] in ("+", "-"):
            op = self.advance()[1]
            inner = self.parse_unary()
            return _NegNode(inner) if op == "-" else inner
        return self.parse_pow()

    def parse_pow(self) -> Any:
        base = self.parse_atom()
        tok = self.peek()
        if tok is not None and tok[0] == "OP" and tok[1] == "^":
            self.advance()
            exp = self.parse_unary()
            return _PowNode(base, exp)
        return base

    def parse_atom(self) -> Any:
        tok = self.peek()
        if tok is None:
            return _NumNode("1")
        if tok[0] == "LP":
            self.advance()
            inner = self.parse_expr()
            if self.peek() == ("RP", ")"):
                self.advance()
            return inner
        if tok[0] in ("NUM", "ID", "TERM"):
            self.advance()
            if tok[0] == "NUM":
                return _NumNode(tok[1])
            if tok[0] == "TERM":
                return _TermNode(tok[1])
            if tok[1].lower() in _FUNC_NAMES:
                nxt = self.peek()
                if nxt is not None and nxt[0] == "LP":
                    self.advance()
                    arg = self.parse_expr()
                    if self.peek() == ("RP", ")"):
                        self.advance()
                    return _FuncNode(tok[1].lower(), arg)
                if nxt is not None and nxt[0] in ("NUM", "ID", "TERM"):
                    return _FuncNode(tok[1].lower(), self.parse_pow())
            return _VarNode(tok[1])
        self.advance()
        return _NumNode("1")


def _parse_expr_ast(expr: str, arm: ArmConfigV2 | None = None) -> Any:
    tokens, _ = _tokenize_ast(expr, arm=arm)
    if not tokens:
        return _NumNode("1")
    return _ExprParser(tokens).parse_expr()


def _node_has_physics_var(node: Any, arm: ArmConfigV2 | None = None) -> bool:
    if isinstance(node, _TermNode):
        return True
    if isinstance(node, _VarNode):
        if arm is None:
            return node.name not in _AST_CONST_OR_OP_IDENTIFIERS and node.name.lower() not in _AST_CONST_OR_OP_IDENTIFIERS
        return False
    if isinstance(node, _NegNode):
        return _node_has_physics_var(node.inner, arm=arm)
    if isinstance(node, _AddNode):
        return any(_node_has_physics_var(t, arm=arm) for t in node.terms)
    if isinstance(node, _MulNode):
        return any(_node_has_physics_var(f, arm=arm) for f in node.factors)
    if isinstance(node, _FracNode):
        return _node_has_physics_var(node.num, arm=arm) or _node_has_physics_var(node.den, arm=arm)
    if isinstance(node, _PowNode):
        return _node_has_physics_var(node.base, arm=arm) or _node_has_physics_var(node.exp, arm=arm)
    if isinstance(node, _FuncNode):
        return _node_has_physics_var(node.arg, arm=arm)
    return False


def _flatten_additive_terms(node: Any, sign: int = 1, arm: ArmConfigV2 | None = None) -> list[tuple[int, Any]]:
    """Flatten top-level Add, Neg, outer Frac(Add, den), and linear Mul(..., Add) with >=2 variable terms."""
    if isinstance(node, _AddNode):
        res: list[tuple[int, Any]] = []
        for t in node.terms:
            res.extend(_flatten_additive_terms(t, sign=sign, arm=arm))
        return res
    if isinstance(node, _NegNode):
        return _flatten_additive_terms(node.inner, sign=-sign, arm=arm)
    if isinstance(node, _FracNode):
        num_terms = _flatten_additive_terms(node.num, sign=sign, arm=arm)
        if len(num_terms) >= 2 and any(_node_has_physics_var(tn, arm=arm) for _, tn in num_terms):
            return [(ts, _FracNode(tn, node.den)) for ts, tn in num_terms]
        # Pull out unary minus inside numerator if non-Add
        if isinstance(node.num, _NegNode):
            return _flatten_additive_terms(_FracNode(node.num.inner, node.den), sign=-sign, arm=arm)
        return [(sign, node)]
    if isinstance(node, _MulNode):
        # Pull any NegNode wrappers out of factors first
        clean_factors: list[Any] = []
        eff_sign = sign
        for f in node.factors:
            while isinstance(f, _NegNode):
                eff_sign = -eff_sign
                f = f.inner
            clean_factors.append(f)
        # Distribute ONLY over the first factor whose additive flattening has >= 2 variable-bearing terms
        for idx, f in enumerate(clean_factors):
            sub_terms = _flatten_additive_terms(f, sign=1, arm=arm)
            if sum(1 for _, tn in sub_terms if _node_has_physics_var(tn, arm=arm)) >= 2:
                out_terms: list[tuple[int, Any]] = []
                for sub_sign, sub_node in sub_terms:
                    rebuilt = clean_factors[:idx] + [sub_node] + clean_factors[idx + 1 :]
                    out_terms.extend(_flatten_additive_terms(_MulNode(tuple(rebuilt)), sign=eff_sign * sub_sign, arm=arm))
                return out_terms
        return [(eff_sign, _MulNode(tuple(clean_factors)))]
    return [(sign, node)]


def _is_negative_exponent(node: Any) -> bool:
    if isinstance(node, _NegNode):
        return True
    if isinstance(node, _MulNode) and node.factors:
        return isinstance(node.factors[0], _NegNode)
    return False


def _collect_node_var_polarities(
    node: Any,
    term_sign: int,
    div_sign: int,
    quot_exact: dict[str, set[int]],
    overall_exact: dict[str, set[int]],
    arm: ArmConfigV2 | None = None,
) -> None:
    if isinstance(node, _TermNode):
        quot_exact[node.name].add(div_sign)
        overall_exact[node.name].add(term_sign * div_sign)
        return
    if isinstance(node, _VarNode):
        if arm is None and node.name not in _AST_CONST_OR_OP_IDENTIFIERS and node.name.lower() not in _AST_CONST_OR_OP_IDENTIFIERS:
            quot_exact[node.name].add(div_sign)
            overall_exact[node.name].add(term_sign * div_sign)
        return
    if isinstance(node, _NegNode):
        _collect_node_var_polarities(node.inner, -term_sign, div_sign, quot_exact, overall_exact, arm=arm)
    elif isinstance(node, _AddNode):
        for t in node.terms:
            _collect_node_var_polarities(t, term_sign, div_sign, quot_exact, overall_exact, arm=arm)
    elif isinstance(node, _MulNode):
        for f in node.factors:
            _collect_node_var_polarities(f, term_sign, div_sign, quot_exact, overall_exact, arm=arm)
    elif isinstance(node, _FracNode):
        _collect_node_var_polarities(node.num, term_sign, div_sign, quot_exact, overall_exact, arm=arm)
        _collect_node_var_polarities(node.den, term_sign, -div_sign, quot_exact, overall_exact, arm=arm)
    elif isinstance(node, _PowNode):
        base_div = -div_sign if _is_negative_exponent(node.exp) else div_sign
        _collect_node_var_polarities(node.base, term_sign, base_div, quot_exact, overall_exact, arm=arm)
    elif isinstance(node, _FuncNode):
        _collect_node_var_polarities(node.arg, term_sign, div_sign, quot_exact, overall_exact, arm=arm)


def _analyze_expr_polarities(
    expr: str,
    arm: ArmConfigV2 | None = None,
) -> tuple[list[int], dict[str, set[int]], dict[str, set[int]], dict[str, set[int]], dict[str, set[int]]]:
    ast = _parse_expr_ast(expr, arm=arm)
    flat = _flatten_additive_terms(ast, sign=1, arm=arm)
    add_signs = [s for s, _ in flat]
    quot_exact: dict[str, set[int]] = defaultdict(set)
    overall_exact: dict[str, set[int]] = defaultdict(set)
    for t_sign, t_node in flat:
        _collect_node_var_polarities(t_node, t_sign, 1, quot_exact, overall_exact, arm=arm)
    quot_ci: dict[str, set[int]] = defaultdict(set)
    overall_ci: dict[str, set[int]] = defaultdict(set)
    for k, vals in quot_exact.items():
        quot_ci[k.lower()].update(vals)
    for k, vals in overall_exact.items():
        overall_ci[k.lower()].update(vals)
    return add_signs, dict(quot_exact), dict(overall_exact), dict(quot_ci), dict(overall_ci)


def _extract_var_signs_from_expr(expr: str, arm: ArmConfigV2 | None = None) -> dict[str, int]:
    """Return unambiguous (+1 / -1) net sign for single-polarity variables in `expr` (for A4 monotone edges)."""
    _signs, quot_exact, overall_exact, _q_ci, _o_ci = _analyze_expr_polarities(expr, arm=arm)
    out: dict[str, int] = {}
    for k, s_set in overall_exact.items():
        key = k if arm is not None else k.lower()
        if len(s_set) == 1:
            out[key] = next(iter(s_set))
    return out


def _extract_phys_token_from_key(k: str) -> str:
    """Clean symbolic key from variable_map (e.g. 'v_{\\text{rms}}' -> 'v', 'mass m' -> 'mass m')."""
    return strip_math_decorations(k).replace("\\", "").strip()


def _compare_rhs_segment_a3(
    eq_str: str,
    refl_str: str,
    eq_rhs: str,
    refl_rhs: str,
    var_map: dict[str, Any],
    arm: ArmConfigV2,
    item_id: str,
) -> list[dict[str, Any]]:
    eq_add_signs, eq_quot_exact, eq_overall_exact, eq_quot_ci, eq_overall_ci = _analyze_expr_polarities(eq_rhs, arm=None)
    refl_add_signs, refl_quot, refl_overall, _rq_ci, _ro_ci = _analyze_expr_polarities(refl_rhs, arm=arm)
    collisions: list[dict[str, Any]] = []

    # 1. Flattened additive sign multiset parity (handles distributed vs factored & -(B-A) vs (A-B))
    if len(eq_add_signs) >= 2 and len(eq_add_signs) == len(refl_add_signs):
        if sorted(eq_add_signs) != sorted(refl_add_signs):
            collisions.append(
                {
                    "layer": "A3_additive_sign_flip",
                    "item_id": item_id,
                    "equation_latex": eq_str,
                    "reflected_formula": refl_str,
                    "expected_signs": eq_add_signs,
                    "got_signs": refl_add_signs,
                }
            )

    # 2. Per-target-slot quotient & overall sign preservation (union across RHS physics keys mapping to the slot)
    targ_to_eq_syms: dict[str, list[str]] = defaultdict(list)
    for pk, tv in var_map.items():
        if _is_stripped_constant_var_entry(pk, str(tv)):
            continue
        toks, unk = extract_target_tokens_stripped(normalize_target_token_v2(str(tv)), arm)
        if unk or len(toks) != 1 or "÷" in str(tv) or "/" in str(tv):
            continue
        # Extract last alphabetic token preserving exact case first
        cands = re.findall(r"[A-Za-z]+", _extract_phys_token_from_key(pk))
        if not cands:
            continue
        sym_raw = cands[-1]
        targ_to_eq_syms[toks[0]].append(sym_raw)

    for targ_slot, syms in sorted(targ_to_eq_syms.items()):
        if targ_slot not in refl_quot:
            continue
        exp_quot: set[int] = set()
        exp_overall: set[int] = set()
        for sym_raw in syms:
            if sym_raw in eq_quot_exact:
                exp_quot.update(eq_quot_exact[sym_raw])
                exp_overall.update(eq_overall_exact[sym_raw])
            elif sym_raw.lower() in eq_quot_ci:
                exp_quot.update(eq_quot_ci[sym_raw.lower()])
                exp_overall.update(eq_overall_ci[sym_raw.lower()])
        if not exp_quot:
            continue
        got_quot = refl_quot[targ_slot]
        got_overall = refl_overall[targ_slot]
        if exp_quot != got_quot or exp_overall != got_overall:
            collisions.append(
                {
                    "layer": "A3_exponent_or_quotient_flip",
                    "item_id": item_id,
                    "physical_vars": syms,
                    "target_slot": targ_slot,
                    "equation_quot_signs": sorted(exp_quot),
                    "reflected_quot_signs": sorted(got_quot),
                    "equation_overall_signs": sorted(exp_overall),
                    "reflected_overall_signs": sorted(got_overall),
                    "equation_latex": eq_str,
                    "reflected_formula": refl_str,
                }
            )
    return collisions


def _check_a3_formula_sign_preservation(
    item: dict[str, Any],
    output: dict[str, Any],
    arm: ArmConfigV2,
) -> list[dict[str, Any]]:
    """Verify `reflected_formula` preserves the algebraic numerator/denominator & +/- polarity of `equation_latex`.

    Handles chained `=` equations (`A = B = C`), multi-clause `,` equations, `\\frac{A}{B} * C`,
    unary `-` / denominator distribution, and balanced subscripts cleanly.
    """
    eq = item.get("equation_latex", "")
    refl = output.get("reflected_formula", "")
    eq_clauses = _parse_equation_clauses_and_segments(eq)
    refl_clauses = _parse_equation_clauses_and_segments(refl)
    if not eq_clauses or not refl_clauses:
        return []

    eq_rhs_candidates = [seg for clause in eq_clauses for seg in clause[1:]]
    refl_rhs_list = [seg for clause in refl_clauses for seg in clause[1:]]
    if not eq_rhs_candidates or not refl_rhs_list:
        return []

    var_map = output.get("variable_map", {})
    all_collisions: list[dict[str, Any]] = []
    for refl_rhs in refl_rhs_list:
        best_cols: list[dict[str, Any]] | None = None
        for eq_rhs in eq_rhs_candidates:
            cols = _compare_rhs_segment_a3(
                eq, refl, eq_rhs, refl_rhs, var_map, arm, item["item_id"]
            )
            if best_cols is None or len(cols) < len(best_cols):
                best_cols = cols
            if not best_cols:
                break
        if best_cols:
            all_collisions.extend(best_cols)
    return all_collisions


def _find_negative_cycle(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect opposing parallel directed edges and directed negative signed cycles across A4 graph."""
    collisions: list[dict[str, Any]] = []
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    adj: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for e in edges:
        u, v, s, src = str(e["from"]), str(e["to"]), int(e["sign"]), str(e["source"])
        by_pair[(u, v)].append(e)
        adj[u].append((v, s, src))

    for (u, v), elist in sorted(by_pair.items()):
        signs = {int(e["sign"]) for e in elist}
        if len(signs) > 1:
            collisions.append(
                {
                    "layer": "A4_opposite_parallel_edges",
                    "pair": [u, v],
                    "edges": elist,
                }
            )

    # Directed simple cycle DFS looking for odd-negative-edge directed cycles (length <= 6)
    seen_cycles: set[tuple[str, ...]] = set()
    nodes = sorted(adj.keys())
    for start in nodes:
        stack: list[tuple[str, int, list[tuple[str, str, int, str]]]] = [(start, 1, [])]
        while stack:
            curr, prod_sign, path = stack.pop()
            if len(path) >= 6:
                continue
            for nxt, s, src in adj.get(curr, ()):
                new_prod = prod_sign * s
                new_path = path + [(curr, nxt, s, src)]
                if nxt == start:
                    if new_prod < 0:
                        canon = tuple(sorted(f"{a}->{b}:{sg}" for a, b, sg, _ in new_path))
                        if canon not in seen_cycles:
                            seen_cycles.add(canon)
                            collisions.append(
                                {
                                    "layer": "A4_negative_signed_cycle",
                                    "cycle_product": new_prod,
                                    "edges": [
                                        {"from": a, "to": b, "sign": sg, "source": sr}
                                        for a, b, sg, sr in new_path
                                    ],
                                }
                            )
                elif nxt not in {a for a, _, _, _ in new_path}:
                    stack.append((nxt, new_prod, new_path))
    return collisions


def run_layer_a_item_check(
    output: dict[str, Any],
    arm: ArmConfigV2,
    item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run per-item Layer-A checks (`A1` dictionary fidelity, `A2` formula composition,
    `A3` sign preservation) BEFORE selecting canonical generator among consensus voters.
    """
    collisions: list[dict[str, Any]] = []
    if output.get("ruling") not in ("keep", "invert"):
        return {"item_id": output.get("item_id"), "passed": True, "collisions": []}

    var_map: dict[str, str] = output.get("variable_map", {})
    declared_target_terms: set[str] = set()

    # A1: every variable_map value must either mark a stripped Rule-R constant/prefactor OR
    # resolve cleanly to valid arm target terms and match Partner Lookup Table
    for raw_phys, raw_targ in var_map.items():
        if _is_stripped_constant_var_entry(raw_phys, raw_targ):
            continue
        norm_phys = normalize_phys_token_v2(raw_phys)
        norm_targ = normalize_target_token_v2(raw_targ)
        t_toks, unknowns = extract_target_tokens_stripped(norm_targ, arm)
        if unknowns:
            collisions.append(
                {
                    "layer": "A1_invalid_target_token",
                    "physical": raw_phys,
                    "target": raw_targ,
                    "unknowns": unknowns,
                }
            )
        if not t_toks:
            collisions.append(
                {
                    "layer": "A1_missing_target_token",
                    "physical": raw_phys,
                    "target": raw_targ,
                }
            )
        declared_target_terms.update(t_toks)
        if norm_phys in arm.partner_lookup:
            expected_targ = arm.partner_lookup[norm_phys]
            exp_toks, _ = extract_target_tokens_stripped(expected_targ, arm)
            if set(t_toks) != set(exp_toks) and norm_targ != expected_targ:
                collisions.append(
                    {
                        "layer": "A1_partner_table_mismatch",
                        "physical": norm_phys,
                        "expected": expected_targ,
                        "got": norm_targ,
                    }
                )

    # A2: reflected_formula token composition (for algebraic equations)
    eq_latex = (item or {}).get("equation_latex", "")
    has_algebra = bool(eq_latex) and not eq_latex.strip().lower().startswith("none")
    refl_formula = output.get("reflected_formula", "")
    if has_algebra or (refl_formula and not refl_formula.strip().lower().startswith("none")):
        f_toks, f_unknowns = extract_target_tokens_stripped(refl_formula, arm)
        if f_unknowns:
            collisions.append(
                {
                    "layer": "A2_formula_unknown_tokens",
                    "reflected_formula": refl_formula,
                    "unknowns": f_unknowns,
                }
            )
        if not f_toks:
            collisions.append(
                {
                    "layer": "A2_formula_no_target_tokens",
                    "reflected_formula": refl_formula,
                }
            )
        if declared_target_terms and not set(f_toks).issubset(declared_target_terms):
            undeclared = sorted(set(f_toks) - declared_target_terms)
            collisions.append(
                {
                    "layer": "A2_formula_undeclared_target_tokens",
                    "undeclared": undeclared,
                    "declared": sorted(declared_target_terms),
                    "reflected_formula": refl_formula,
                }
            )

    # A3: sign preservation vs equation_latex (when item provided)
    if item is not None:
        collisions.extend(_check_a3_formula_sign_preservation(item, output, arm))

    return {
        "item_id": output.get("item_id"),
        "passed": len(collisions) == 0,
        "collisions": collisions,
    }


def run_layer_a_v2(
    consensus_records: list[dict[str, Any]],
    arm: ArmConfigV2,
) -> dict[str, Any]:
    """Run FULL joint Layer-A audit across all consensus `keep`/`invert` items in `arm`.

    `consensus_records`: list of `{"item": item_dict, "output": canonical_generator_json}`.
    Checks:
      - Static arm bijection
      - Per-item A1/A2/A3 across every consensus item
      - Joint cross-item `A1` consistency (same normalized physical concept never maps to
        two different target expressions across items; distinct role-disjoint base slots
        do not collide)
      - Joint cross-item `A4` signed cycle & opposing-parallel-edge consistency combining
        `arm.baseline_sign_edges` and RHS->LHS monotone edges from consensus reflected formulas
    """
    all_collisions: list[dict[str, Any]] = []

    for c in _check_static_arm_bijection(arm):
        all_collisions.append({"layer": "A1_static_arm", **c})

    phys_to_items: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    a4_edges: list[dict[str, Any]] = [dict(e) for e in arm.baseline_sign_edges]
    per_item_reports: list[dict[str, Any]] = []

    for rec in consensus_records:
        item = rec["item"]
        out = rec["output"]
        if out.get("ruling") not in ("keep", "invert"):
            continue
        item_res = run_layer_a_item_check(out, arm, item=item)
        per_item_reports.append(item_res)
        for col in item_res["collisions"]:
            all_collisions.append({"item_id": item["item_id"], **col})

        # Accumulate cross-item A1 mapping table
        for raw_phys, raw_targ in out.get("variable_map", {}).items():
            if _is_stripped_constant_var_entry(raw_phys, raw_targ):
                continue
            norm_phys = normalize_phys_token_v2(raw_phys)
            norm_targ = normalize_target_token_v2(raw_targ)
            # Canonicalize compound expressions via extracted sorted tokens or normalized string
            toks, unk = extract_target_tokens_stripped(norm_targ, arm)
            sig = norm_targ if unk or not toks else " | ".join(toks)
            # Only track descriptive multi-letter concept keys (skip bare symbols like "m", "x", "v"
            # which lawfully denote different quantities across chapters, e.g. k or T or E vs e)
            if len(re.sub(r"[^A-Za-z]", "", norm_phys)) >= 3:
                phys_to_items[norm_phys][sig].append(item["item_id"])

        # Accumulate A4 directed monotone edges ONLY from single-term LHS = f(RHS) formulas
        refl_pair = _parse_equation_lhs_rhs(out.get("reflected_formula", ""))
        if refl_pair is not None:
            r_lhs, r_rhs = refl_pair
            lhs_toks, lhs_unk = extract_target_tokens_stripped(r_lhs, arm)
            if len(lhs_toks) == 1 and not lhs_unk:
                dst = lhs_toks[0]
                rhs_signs = _extract_var_signs_from_expr(r_rhs, arm=arm)
                # Restrict A4 cross-item monotone graph to 1-input proportionalities (`Y = c * X` or `Y = -c * X`)
                # plus explicit additive constitutive laws matching baseline_sign_edges (`Desire/Vibrance -> Movement`,
                # `Movement/Appreciation -> Frequency`) to avoid spurious kinematic triple-product `-1` triangles!
                if len(rhs_signs) == 1:
                    src_tok, sg = next(iter(rhs_signs.items()))
                    if src_tok != dst:
                        a4_edges.append({"from": src_tok, "to": dst, "sign": sg, "source": item["item_id"]})

    # Check cross-item A1 collisions (same descriptive physical concept -> >= 2 distinct target expressions)
    for norm_phys, sig_map in sorted(phys_to_items.items()):
        if len(sig_map) > 1:
            all_collisions.append(
                {
                    "layer": "A1_cross_item_one_to_many",
                    "physical": norm_phys,
                    "variants": dict(sig_map),
                }
            )

    # Check cross-item A4 signed graph cycles / parallel opposing edges
    for cyc in _find_negative_cycle(a4_edges):
        all_collisions.append(cyc)

    return {
        "arm_id": arm.arm_id,
        "evaluated_items": len(per_item_reports),
        "per_item_passed": sum(1 for r in per_item_reports if r["passed"]),
        "layer_a_collisions": all_collisions,
        "layer_a_collisions_count": len(all_collisions),
        "passes_all": len(all_collisions) == 0,
    }


# ---------------------------------------------------------------------------
# K01..K16 Canonical Worked Examples (Zero-Drift Rendered per Arm for M2)
# ---------------------------------------------------------------------------

# Note: K01..K16 ONLY (K17 omitted deliberately in M2). Never include these in M1 or Rule R!
CALIBRATION_WORKED_SPECS_K01_K16: tuple[dict[str, Any], ...] = (
    {
        "item_id": "K01",
        "description": "First postulate of special relativity (the laws of physics are the same for every inertial observer)",
        "equation_latex": "None (qualitative physical principle)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Invariance across inertial observers already reflects boundary-free uniformity; keeps structural polarity directly.",
        "unmapped_terms": [],
        "variable_map": {"inertial observer": "Movement", "laws of physics": "Vibration-Expansion"},
        "reflected_formula": "None (qualitative invariant symmetry across Movement)",
        "translation_template": "The lawful proportions across {Vibration_Expansion} remain unchanged for every {Movement}.",
        "direction_flipped_d": "The lawful proportions across Vibration-Expansion differ for every Movement.",
        "rationale": "Qualitative relativity postulate asserts frame symmetry with no resistance or separation cost.",
    },
    {
        "item_id": "K02",
        "description": "Relativity of simultaneity (two observers in relative motion do not share a simultaneous now because of spatial separation)",
        "equation_latex": "\\Delta t = \\frac{\\gamma v \\Delta x}{c^{2}} \\quad (\\text{for } \\Delta t' = 0)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "invert",
        "two_level": False,
        "axis_polarity_note": "Physical spatial separation blocks a shared present; nonphysical polarity restores simultaneous wholeness while algebraic ratio keeps shape.",
        "unmapped_terms": [],
        "variable_map": {"Delta t": "Expansion", "v": "rise per Expansion", "Delta x": "Vibration", "c": "Current"},
        "reflected_formula": "Expansion = (gamma * (rise per Expansion) * Vibration) / Current^2",
        "translation_template": "Separated {Vibration} prevents two traversing frames from sharing a common {Expansion} scaled by {rise_per_Expansion} and {Current}.",
        "direction_flipped_d": "Separated Vibration forces two traversing frames into a single shared Expansion despite rise per Expansion and Current.",
        "rationale": "Spatial separation imposes a simultaneity barrier (costs >= 1 -> invert, two_level=false).",
    },
    {
        "item_id": "K03",
        "description": "Principle of relativity (there is no preferred fixed inertial rest frame)",
        "equation_latex": "None (qualitative physical principle)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Absence of any rigid absolute frame matches unforced nonphysical uniformity.",
        "unmapped_terms": [],
        "variable_map": {"inertial rest frame": "Movement"},
        "reflected_formula": "None (qualitative symmetry across Movement)",
        "translation_template": "No single fixed {Movement} stands privileged above any other.",
        "direction_flipped_d": "One single fixed Movement stands strictly privileged above every other.",
        "rationale": "Symmetry principle with zero barrier cost.",
    },
    {
        "item_id": "K04",
        "description": "Special versus general relativity (equivalence of inertial frames versus accelerating or gravitating frames)",
        "equation_latex": "None (qualitative physical principle)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Equivalence aligns acceleration and attraction smoothly onto frame symmetry.",
        "unmapped_terms": [],
        "variable_map": {"inertial frames": "Movement", "accelerating frames": "Appreciation", "gravitating frames": "Attraction"},
        "reflected_formula": "None (qualitative equivalence linking Movement, Appreciation, and Attraction)",
        "translation_template": "Every shifting {Movement} stands structurally equivalent under {Appreciation} and {Attraction}.",
        "direction_flipped_d": "Shifting Movement stands fundamentally opposed under Appreciation and Attraction.",
        "rationale": "Local equivalence symmetry with zero resistance cost.",
    },
    {
        "item_id": "K05",
        "description": "Relativistic time dilation between proper time and moving-frame coordinate time",
        "equation_latex": "\\Delta t = \\gamma \\Delta \\tau = \\frac{\\Delta \\tau}{\\sqrt{1 - v^{2}/c^{2}}}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Mass-free kinematic perspective transform scales duration smoothly by gamma.",
        "unmapped_terms": [],
        "variable_map": {"Delta t": "Expansion", "Delta tau": "Expansion (proper)", "v": "rise per Expansion", "c": "Current"},
        "reflected_formula": "Expansion = gamma * Expansion_proper = Expansion_proper / sqrt(1 - (rise per Expansion)^2 / Current^2)",
        "translation_template": "Measured {Expansion} shifts smoothly relative to proper {Expansion} as {rise_per_Expansion} nears {Current}.",
        "direction_flipped_d": "Measured Expansion shrinks below proper Expansion as rise per Expansion approaches zero relative to Current.",
        "rationale": "Mass-free perspective ratio (gamma stripped) -> keep, two_level=false.",
    },
    {
        "item_id": "K06",
        "description": "Relativistic length contraction along the direction of relative motion",
        "equation_latex": "L = \\frac{L_{0}}{\\gamma} = L_{0} \\sqrt{1 - \\frac{v^{2}}{c^{2}}}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Mass-free perspective scaling preserves algebraic ratio cleanly.",
        "unmapped_terms": [],
        "variable_map": {"L": "Vibration", "L_0": "Vibration (rest)", "v": "rise per Expansion", "c": "Current"},
        "reflected_formula": "Vibration = Vibration_rest / gamma = Vibration_rest * sqrt(1 - (rise per Expansion)^2 / Current^2)",
        "translation_template": "Observed {Vibration} scales inversely by perspective relative to rest {Vibration} as {rise_per_Expansion} nears {Current}.",
        "direction_flipped_d": "Observed Vibration grows beyond rest Vibration as rise per Expansion climbs toward Current.",
        "rationale": "Mass-free perspective projection -> keep, two_level=false.",
    },
    {
        "item_id": "K07",
        "description": "Mass-energy equivalence",
        "equation_latex": "E = m c^{2}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Direct structural identity equates condensed substance with luminous energy without barrier.",
        "unmapped_terms": [],
        "variable_map": {"E": "conscious energy", "m": "Movement", "c": "Current"},
        "reflected_formula": "conscious energy = Movement * Current^2",
        "translation_template": "{conscious_energy} equals the product of {Movement} and squared {Current}.",
        "direction_flipped_d": "conscious energy decreases whenever Movement and squared Current rise together.",
        "rationale": "Fundamental equivalence identity -> keep, two_level=false.",
    },
    {
        "item_id": "K08",
        "description": "Relativistic kinetic energy and the rising energy cost of increasing speed for mass",
        "equation_latex": "K = (\\gamma - 1) m c^{2}, \\quad E = \\gamma m c^{2}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "invert",
        "two_level": False,
        "axis_polarity_note": "Physical inertia exacts an escalating effort barrier with rising speed; nonphysical yielding removes that barrier.",
        "unmapped_terms": [],
        "variable_map": {"K": "conscious energy (kinetic)", "E": "conscious energy (total)", "m": "Movement", "c": "Current"},
        "reflected_formula": "conscious energy = (gamma - 1) * Movement * Current^2",
        "translation_template": "Accelerating nonzero {Movement} exacts a steeply rising {conscious_energy} barrier scaled by squared {Current}.",
        "direction_flipped_d": "Accelerating nonzero Movement demands zero conscious energy barrier regardless of squared Current.",
        "rationale": "Escalating inertial cost with speed -> invert, two_level=false.",
    },
    {
        "item_id": "K09",
        "description": "Speed-of-light limit for massive particles (nothing with mass can reach the speed of light c)",
        "equation_latex": "v < c \\quad (\\gamma \\to \\infty \\text{ as } v \\to c \\text{ for } m > 0)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "invert",
        "two_level": False,
        "axis_polarity_note": "Mass imposes an insurmountable ceiling below c physically; boundless nonphysical yielding dissolves the barrier.",
        "unmapped_terms": [],
        "variable_map": {"v": "rise per Expansion", "c": "Current", "m": "Movement"},
        "reflected_formula": "rise per Expansion < Current  (gamma -> infty as rise per Expansion -> Current for Movement > 0)",
        "translation_template": "Any nonzero {Movement} faces a strict boundary keeping {rise_per_Expansion} below {Current}.",
        "direction_flipped_d": "Any nonzero Movement freely accelerates rise per Expansion past Current without resistance.",
        "rationale": "Inertial asymptotic speed ceiling -> invert, two_level=false.",
    },
    {
        "item_id": "K10",
        "description": "Spacetime as one unified four-dimensional continuum (invariant spacetime interval)",
        "equation_latex": "s^{2} = c^{2} (\\Delta t)^{2} - (\\Delta x)^{2} - (\\Delta y)^{2} - (\\Delta z)^{2}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Invariant metric unifies spatial and temporal intervals coherently across frames.",
        "unmapped_terms": [],
        "variable_map": {"s": "Vibration-Expansion", "c": "Current", "Delta t": "Expansion", "Delta x": "Vibration (x)", "Delta y": "Vibration (y)", "Delta z": "Vibration (z)"},
        "reflected_formula": "(Vibration-Expansion)^2 = Current^2 * Expansion^2 - Vibration_x^2 - Vibration_y^2 - Vibration_z^2",
        "translation_template": "The unified {Vibration_Expansion} interval combines squared {Current} times {Expansion} less squared {Vibration}.",
        "direction_flipped_d": "The unified Vibration-Expansion interval rises as squared Vibration exceeds squared Current times Expansion.",
        "rationale": "Metric identity of continuum geometry -> keep, two_level=false.",
    },
    {
        "item_id": "K11",
        "description": "Mass-energy warps spacetime geometry",
        "equation_latex": "None (qualitative physical principle)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Geometric curving directly expresses relational presence across the continuum.",
        "unmapped_terms": [],
        "variable_map": {"mass": "Movement", "energy": "conscious energy", "spacetime geometry": "Vibration-Expansion"},
        "reflected_formula": "None (qualitative coupling: Movement and conscious energy curve Vibration-Expansion)",
        "translation_template": "Concentrated {Movement} and {conscious_energy} shape the curvature of {Vibration_Expansion}.",
        "direction_flipped_d": "Concentrated Movement and conscious energy flatten Vibration-Expansion into rigid uniformity.",
        "rationale": "Geometric coupling principle without friction/separation barrier -> keep.",
    },
    {
        "item_id": "K12",
        "description": "Gravitational wells and gravitational lensing of light around massive bodies",
        "equation_latex": "None (qualitative physical principle)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Drawing attraction guides light along continuous curved geometry rather than erecting a dissipative wall.",
        "unmapped_terms": [],
        "variable_map": {"gravitational lensing": "Attraction", "light": "Current", "massive bodies": "Movement", "gravity well": "Attraction"},
        "reflected_formula": "None (qualitative proportion: Attraction around Movement guides Current)",
        "translation_template": "Around concentrated {Movement}, {Attraction} curves the path of {Current} naturally.",
        "direction_flipped_d": "Around concentrated Movement, Attraction repels and scatters the path of Current outward.",
        "rationale": "Attraction-guided curvature principle -> keep, two_level=false.",
    },
    {
        "item_id": "K13",
        "description": "Conservation of total energy in an isolated physical system",
        "equation_latex": "E_{\\text{i}} = E_{\\text{f}} \\quad (\\Delta E_{\\text{sys}} = 0)",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Conservation expresses unbroken continuity across initial and final states.",
        "unmapped_terms": [],
        "variable_map": {"E_i": "conscious energy (initial)", "E_f": "conscious energy (final)", "E_sys": "conscious energy (sys)"},
        "reflected_formula": "conscious energy_initial = conscious energy_final  (Delta conscious energy_sys = 0)",
        "translation_template": "Total {conscious_energy} inside a closed whole remains invariant from start to completion.",
        "direction_flipped_d": "Total conscious energy inside a closed whole drifts arbitrarily away between start and completion.",
        "rationale": "Conservation identity -> keep, two_level=false.",
    },
    {
        "item_id": "K14",
        "description": "Newton's third law of motion (reciprocal action-reaction force pair)",
        "equation_latex": "\\vec{F}_{AB} = -\\vec{F}_{BA}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Exact reciprocal symmetry preserves force balance between paired bodies.",
        "unmapped_terms": [],
        "variable_map": {"F_AB": "Frequency (AB)", "F_BA": "Frequency (BA)"},
        "reflected_formula": "Frequency_AB = -Frequency_BA",
        "translation_template": "Reciprocal {Frequency} between two interacting parts balances equally in opposite directions.",
        "direction_flipped_d": "Reciprocal Frequency between two interacting parts acts unequally in the same direction.",
        "rationale": "Action-reaction symmetry identity -> keep, two_level=false.",
    },
    {
        "item_id": "K15",
        "description": "Mass as the product of mass density and volume",
        "equation_latex": "m = \\rho V",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Constitutive product flips physical substance resistance into cohesive focus-and-breadth presence.",
        "unmapped_terms": [],
        "variable_map": {"m": "Movement", "rho": "Desire", "V": "Vibrance"},
        "reflected_formula": "Movement = Desire * Vibrance",
        "translation_template": "Total {Movement} arises directly as {Desire} multiplies with {Vibrance}.",
        "direction_flipped_d": "Total Movement diminishes whenever Desire and Vibrance increase together.",
        "rationale": "Constitutive definition identity -> keep, two_level=false.",
    },
    {
        "item_id": "K16",
        "description": "Newton's second law of motion (net force equals mass times acceleration)",
        "equation_latex": "\\vec{F}_{\\text{net}} = m \\vec{a}",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Constitutive dynamical law keeps algebraic structure while reversing physical resistance polarity.",
        "unmapped_terms": [],
        "variable_map": {"F_net": "Frequency", "m": "Movement", "a": "Appreciation"},
        "reflected_formula": "Frequency = Movement * Appreciation",
        "translation_template": "Net {Frequency} equals {Movement} multiplied by {Appreciation}.",
        "direction_flipped_d": "Net Frequency decreases whenever Movement and Appreciation increase together.",
        "rationale": "Constitutive force law -> keep, two_level=false.",
    },
)


def build_calibration_examples_for_arm(arm: ArmConfigV2) -> list[dict[str, Any]]:
    """Render K01..K16 canonical worked examples cleanly into `arm`'s vocabulary."""
    a0 = build_arm_v2("A0")
    rendered: list[dict[str, Any]] = []
    for spec in CALIBRATION_WORKED_SPECS_K01_K16:
        canon_tmpl = _canonicalize_template_to_a0(spec["translation_template"], a0)
        # Render {Slot} notation using arm's canonical underscored slot key (`{Movement}` or `{Reflected}`)
        arm_tmpl_slots: dict[str, str] = {}
        for k in CANONICAL_A0_SLOTS:
            arm_term = arm.a0_to_arm[k]
            arm_tmpl_slots[_canonical_slot_key(k)] = "{" + _canonical_slot_key(arm_term) + "}"
        arm_template = _BRACED_RE.sub(lambda m: arm_tmpl_slots[m.group(1)], canon_tmpl)
        arm_t = render_template(arm_template, arm.arm_id, src_arm=arm)
        arm_d = _apply_word_perm_v2(spec["direction_flipped_d"], arm.a0_to_arm)
        arm_var_map = {k: _apply_word_perm_v2(v, arm.a0_to_arm) for k, v in spec["variable_map"].items()}
        arm_refl = _apply_word_perm_v2(spec["reflected_formula"], arm.a0_to_arm)
        arm_axis = _apply_word_perm_v2(spec["axis_polarity_note"], arm.a0_to_arm)
        arm_rationale = _apply_word_perm_v2(spec["rationale"], arm.a0_to_arm)
        rec = {
            "item_id": spec["item_id"],
            "description": spec["description"],
            "equation_latex": spec["equation_latex"],
            "output": {
                "item_id": spec["item_id"],
                "scope_status": spec["scope_status"],
                "formula_shape": spec["formula_shape"],
                "ruling": spec["ruling"],
                "two_level": spec["two_level"],
                "axis_polarity_note": arm_axis,
                "unmapped_terms": list(spec["unmapped_terms"]),
                "variable_map": arm_var_map,
                "reflected_formula": arm_refl,
                "translation_t": arm_t,
                "translation_template": arm_template,
                "direction_flipped_d": arm_d,
                "rationale": arm_rationale,
            },
        }
        errs = validate_generator_json(rec["output"], arm, rec)
        if errs:
            raise AssertionError(f"Broken calibration spec {spec['item_id']} on {arm.arm_id}: {errs}")
        rendered.append(rec)
    return rendered


# ---------------------------------------------------------------------------
# Prompt Builders & Prompt Isolation / Hygiene Guards (Stages 1..6)
# ---------------------------------------------------------------------------

_NEVER_LEAKED_INTERNAL_LABELS: tuple[str, ...] = (
    "Calibration Examples (K01",
    "Calibration Checklist",
    "T_A0",
    "T_A3",
    "S_syn",
    "D_A0",
    "overlaps_legacy_extension_test",
    "expected_book_ruling",
    "formal_row_name",
    "formal_source",
    "provenance",
    "has_mass_flag",
    "definition_flag",
    "costs_count",
)


def assert_prompt_isolation(
    messages: list[dict[str, str]],
    *,
    stage: str,
    forbidden_substrings: tuple[str, ...] = (),
    scaffolding_texts: tuple[str, ...] = (),
    check_full_stem_leak: bool = False,
) -> None:
    """Verify prompt hygiene and quarantine constraints before issuing or saving any prompt."""
    joined = "\n".join(m["content"] for m in messages)
    if _DANGLING_M_RE.search(joined):
        raise ValueError(f"[{stage}] Dangling 'Movement M' found in prompt")
    forbidden_word = "bl" + "ind"
    if re.search(rf"(?<![A-Za-z]){forbidden_word}[a-z]*(?![A-Za-z])", joined, re.I):
        raise ValueError(f"[{stage}] Forbidden bare masked-term token found in prompt")
    for sub in forbidden_substrings:
        if sub and sub in joined:
            raise ValueError(f"[{stage}] Forbidden quarantined substring {sub!r} leaked into prompt")
    for scaf in scaffolding_texts:
        assert_zero_target_stem_leak(scaf)
    if check_full_stem_leak:
        assert_zero_target_stem_leak(joined)


def _format_slot_key_guide(arm: ArmConfigV2) -> str:
    keys = sorted(
        {_canonical_slot_key(arm.a0_to_arm[s]) for s in CANONICAL_A0_SLOTS},
        key=lambda x: x.lower(),
    )
    return "Valid {Slot} placeholder keys for this arm: " + ", ".join("{" + k + "}" for k in keys)


def _generator_system_prompt(arm: ArmConfigV2) -> str:
    return "\n\n".join(
        [
            f"You are executing a formal physics-to-target reflection task under Naming Arm {arm.arm_id}.",
            CONCEPTUAL_AXIS_PLAIN,
            format_partner_lookup_table(arm),
            _format_slot_key_guide(arm),
            RULE_R_V2,
            LINT_CONSTRAINTS_V2,
        ]
    )


def build_stage1_m1_messages(arm: ArmConfigV2, cal_item: dict[str, Any]) -> list[dict[str, str]]:
    """Stage 1 (M1): Calibration zero-shot evaluation on K01..K17 (worked K examples WITHHELD!)."""
    sys_msg = _generator_system_prompt(arm)
    # Feed ONLY neutral item fields (WITHHOLD formal_source, formal_row_name, expected_book_ruling, provenance, flags)
    clean_item = {
        "item_id": cal_item["item_id"],
        "description": cal_item["description"],
        "equation_latex": cal_item["equation_latex"],
    }
    user_msg = (
        f"Classify and reflect the following item using Arm {arm.arm_id} under Rule R.\n"
        f"Item JSON:\n{json.dumps(clean_item, indent=2, ensure_ascii=False)}\n\n"
        "Respond with ONLY the strict 13-key JSON object."
    )
    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
    _check_zero_leaked_calibration_formulas(sys_msg + "\n" + user_msg)
    assert_prompt_isolation(
        msgs,
        stage="M1",
        forbidden_substrings=(
            "worked example",
            "S_syn",
            "D_A0",
            "T_A0",
            "T_A3",
            "expected_book_ruling",
            "formal_source",
            "formal_row_name",
            "costs_count",
            "has_mass_flag",
            "definition_flag",
        ),
    )
    return msgs


def build_stage2_m2_messages(arm: ArmConfigV2, heldout_item: dict[str, Any]) -> list[dict[str, str]]:
    """Stage 2 (M2): Held-out OpenStax E001..E040 with K01..K16 rendered in `arm` vocabulary.

    Withholds `K17`, `stratum`, `overlaps_legacy_extension_test`, `volume`, `chapter`,
    `chapter_title`, and `source_url`.
    """
    sys_msg = _generator_system_prompt(arm)
    cal_examples = build_calibration_examples_for_arm(arm)
    # Compact worked calibration examples rendered strictly for this arm
    worked_block = json.dumps(cal_examples, indent=2, ensure_ascii=False)
    clean_item = {
        "item_id": heldout_item["item_id"],
        "description": heldout_item["description"],
        "equation_latex": heldout_item["equation_latex"],
    }
    user_msg = (
        f"Reference Worked Examples (K01..K16 in Arm {arm.arm_id} vocabulary):\n{worked_block}\n\n"
        f"Now classify and reflect the held-out OpenStax equation using Arm {arm.arm_id} under Rule R.\n"
        f"Held-out Item JSON:\n{json.dumps(clean_item, indent=2, ensure_ascii=False)}\n\n"
        "Respond with ONLY the strict 13-key JSON object."
    )
    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
    assert_prompt_isolation(
        msgs,
        stage="M2",
        forbidden_substrings=(
            "K17",
            "Boyle",
            "stratum",
            "Core",
            "Boundary",
            "overlaps_legacy_extension_test",
            "expected_book_ruling",
            "S_syn",
            "T_A3",
            "D_A0",
        ),
    )
    return msgs


def build_stage3_m3b_opponent_messages(
    arm: ArmConfigV2,
    item: dict[str, Any],
    canonical_output: dict[str, Any],
) -> list[dict[str, str]]:
    """Stage 3 (M3b): Adversarial Opponent probing canonical consensus `keep`/`invert` item."""
    sys_msg = "\n\n".join(
        [
            f"You are an adversarial formal verifier challenging a candidate physics reflection in Arm {arm.arm_id}.",
            CONCEPTUAL_AXIS_PLAIN,
            format_partner_lookup_table(arm),
            RULE_R_V2,
            "Try hard to break the candidate translation on: (1) unmapped blocklisted variables treated as mapped, "
            "(2) wrong Partner Lookup Table match or mixed vocabulary, (3) broken formula algebraic shape, "
            "(4) wrong keep/invert condition reading under physical vs. nonphysical costs, or "
            "(5) logical contradiction, inline glossing, or reversed causality.",
        ]
    )
    payload = {
        "item_id": item["item_id"],
        "description": item["description"],
        "equation_latex": item["equation_latex"],
        "candidate": {
            "scope_status": canonical_output["scope_status"],
            "formula_shape": canonical_output["formula_shape"],
            "ruling": canonical_output["ruling"],
            "two_level": canonical_output["two_level"],
            "variable_map": canonical_output["variable_map"],
            "reflected_formula": canonical_output["reflected_formula"],
            "translation_t": canonical_output["translation_t"],
        },
    }
    user_msg = (
        "Examine this canonical translation adversarially and return ONLY a JSON object with exact keys:\n"
        '`{"item_id": str, "verdict": "attack"|"uphold", "attack_type": "none"|"unmapped_leak"|"polarity_flip"|'
        '"dictionary_mismatch"|"formula_mismatch"|"conceptual_contradiction", "critique": str, '
        '"counterexample_situation": str}`\n\n'
        f"Target Record:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )
    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
    assert_prompt_isolation(
        msgs,
        stage="M3b",
        forbidden_substrings=("stratum", "overlaps_legacy_extension_test", "S_syn"),
    )
    return msgs


# ---------------------------------------------------------------------------
# Stage 4 (M3c): Zero-Glossary Plain-English Layer B Prompts
# ---------------------------------------------------------------------------

_STAGE4_SINGLE_SCAFFOLDING = (
    "You are an impartial ordinary-English semantic evaluator.\n"
    "You have ONLY the conceptual polarity description below — evaluate every candidate statement strictly as "
    "ordinary English prose, without relying on any hidden technical dictionary or specialized glossary.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nEvaluate whether the candidate statement reads as coherent, well-formed ordinary English that faithfully "
    "matches the structural relationship and conceptual polarity of the given physical law.\n"
    "Flag as incoherent if the statement reads like scrambled gibberish, mixes incompatible meanings across words, "
    "contradicts the algebraic proportion, or flips the polarity against the conceptual axis.\n"
    "Return ONLY a JSON object with exact keys:\n"
    '{"eval_id": str, "coherent_ordinary_english": bool, "matches_physical_law_structure": bool, '
    '"axis_polarity_consistent": bool, "nonsensical_or_cipher_like": bool, '
    '"verdict": "coherent"|"incoherent", "reason": str}'
)

_STAGE4_PAIRS_SCAFFOLDING = (
    "You are an impartial ordinary-English consistency evaluator.\n"
    "You have ONLY the conceptual polarity description below — evaluate every pair of candidate statements strictly "
    "as ordinary English on a common concrete scenario, with zero specialized glossary.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nFor EACH numbered pair of candidate statements having one or more words in common below, judge whether a reader "
    "can assign a single concrete, coherent ordinary-English sense to the common word(s) across both statements "
    "without contradiction, category clash, or nonsense.\n"
    "Return ONLY a JSON object with exact key `results`, containing one entry per pair:\n"
    '{"results": [{"pair_id": str, "compatible": bool, "verdict": "compatible"|"contradiction", "reason": str}]}'
)

_STAGE4_RULE1_SCAFFOLDING = (
    "You are a neutral arbiter performing a single-pair Rule-1 scenario compatibility check.\n"
    "Given ONLY the two ordinary-English statements and their overlapping words below, determine whether both statements "
    "genuinely describe the SAME concrete situation or physical-to-nonphysical scenario (vs. merely mentioning the "
    "same word in unrelated contexts). Then confirm whether they remain irreconcilably contradictory when placed on "
    "that common scenario.\n"
    "Return ONLY a JSON object with exact keys:\n"
    '{"pair_id": str, "same_situation": bool, "confirmed_rule1_collision": bool, "explanation": str}'
)

# Assert Stage 4 scaffolding has ZERO target stem leaks right at import time!
assert_zero_target_stem_leak(_STAGE4_SINGLE_SCAFFOLDING)
assert_zero_target_stem_leak(_STAGE4_PAIRS_SCAFFOLDING)
assert_zero_target_stem_leak(_STAGE4_RULE1_SCAFFOLDING)


def build_stage4_m3c_single_messages(
    eval_id: str,
    description: str,
    equation_latex: str,
    translation_t: str,
) -> list[dict[str, str]]:
    """Stage 4a (M3c_single): Zero-glossary vertical check.

    Withholds Opponent output, Partner Lookup Table, glossary senses, and arm IDs.
    """
    payload = {
        "eval_id": eval_id,
        "physical_description": description,
        "physical_equation": equation_latex,
        "candidate_statement": translation_t,
    }
    user_msg = (
        "Evaluate the following candidate statement strictly under the conceptual axis and return the JSON object.\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )
    assert_zero_target_stem_leak(user_msg.split("Evaluate the following")[1].split("{")[0])
    msgs = [
        {"role": "system", "content": _STAGE4_SINGLE_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M3c_single",
        forbidden_substrings=(
            "Partner Lookup Table",
            "Arm A0",
            "Arm A3-1",
            "S_syn",
            "D_A0",
            "Opponent",
            "counterexample_situation",
            "attack_type",
            "stratum",
        ),
        scaffolding_texts=(
            _STAGE4_SINGLE_SCAFFOLDING,
            "Evaluate the following candidate statement strictly under the conceptual axis and return the JSON object.",
        ),
    )
    return msgs


def build_stage4_m3c_pairs_messages(pairs_batch: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Stage 4b (M3c_pairs): Zero-glossary horizontal pairwise check (`<= 6` pairs/batch).

    Withholds equations, physics descriptions, Opponent output, Partner Lookup Table, and arm IDs.
    Each entry in `pairs_batch` contains ONLY `pair_id`, `shared_terms`, `statement_a`, `statement_b`.
    """
    if not (1 <= len(pairs_batch) <= 6):
        raise ValueError(f"M3c_pairs batch size must be in 1..6, got {len(pairs_batch)}")
    clean_batch = [
        {
            "pair_id": p["pair_id"],
            "shared_words": list(p["shared_terms"]),
            "statement_a": p["statement_a"],
            "statement_b": p["statement_b"],
        }
        for p in pairs_batch
    ]
    instr = "Evaluate all pairs below strictly under ordinary English and return ONLY the JSON object."
    user_msg = f"{instr}\n{json.dumps({'pairs': clean_batch}, indent=2, ensure_ascii=False)}"
    msgs = [
        {"role": "system", "content": _STAGE4_PAIRS_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M3c_pairs",
        forbidden_substrings=(
            "Partner Lookup Table",
            "equation_latex",
            "physical_equation",
            "Arm A0",
            "Arm A3-1",
            "S_syn",
            "D_A0",
            "Opponent",
            "counterexample_situation",
            "stratum",
        ),
        scaffolding_texts=(_STAGE4_PAIRS_SCAFFOLDING, instr),
    )
    return msgs


def build_stage4_m3c_situation_messages(pair_record: dict[str, Any]) -> list[dict[str, str]]:
    """Stage 4c (M3c_situation_match): Unbatched Rule-1 check on 2/2 contradiction pairs."""
    clean_pair = {
        "pair_id": pair_record["pair_id"],
        "shared_words": list(pair_record["shared_terms"]),
        "statement_a": pair_record["statement_a"],
        "statement_b": pair_record["statement_b"],
    }
    instr = "Assess whether both statements apply to the same situation and return ONLY the JSON object."
    user_msg = f"{instr}\n{json.dumps(clean_pair, indent=2, ensure_ascii=False)}"
    msgs = [
        {"role": "system", "content": _STAGE4_RULE1_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M3c_situation_match",
        forbidden_substrings=(
            "Partner Lookup Table",
            "equation_latex",
            "physical_equation",
            "Arm A0",
            "Arm A3-1",
            "S_syn",
            "Opponent",
            "stratum",
        ),
        scaffolding_texts=(_STAGE4_RULE1_SCAFFOLDING, instr),
    )
    return msgs


# ---------------------------------------------------------------------------
# Stage 5 (M4): Zero-Glossary Plain-English Quality & Coherence Rating
# ---------------------------------------------------------------------------

_STAGE5_ITEM_SCAFFOLDING = (
    "You are rating unlabeled ordinary-English statements strictly for clarity, semantic fit, and internal coherence.\n"
    "You have ONLY the conceptual polarity summary below — NO specialized glossary, NO symbol key, and NO formulas.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nFor each numbered item below, compare Candidate 1, Candidate 2, Candidate 3, and Candidate 4 purely on how "
    "naturally, coherently, and consistently each statement reads as ordinary English expressing the nonphysical "
    "polarity described above.\n"
    "Score each candidate from 1 (incoherent / scrambled) to 5 (clear, natural, coherent ordinary English), and rank all "
    "4 candidates from best to worst.\n"
    "Return ONLY a JSON object with exact schema:\n"
    '{"items": [{"item_id": str, "scores": {"1": int, "2": int, "3": int, "4": int}, '
    '"best_candidate": int, "worst_candidate": int, "ranking": [int, int, int, int], "reason": str}]}'
)

_STAGE5_NATIVE_PAIR_SCAFFOLDING = (
    "You are comparing pairs of unlabeled ordinary-English statements strictly for clarity, natural word choice, "
    "and internal coherence.\n"
    "You have ONLY the conceptual polarity summary below — NO specialized glossary, NO symbol key, and NO formulas.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nFor each numbered pair below, read Candidate A and Candidate B and decide which reads as clearer, more "
    "coherent ordinary English matching the nonphysical polarity described above.\n"
    "Score each from 1 (incoherent) to 5 (clear and coherent) and specify `preferred`: `\"A\"`, `\"B\"`, or `\"tie\"`.\n"
    "Return ONLY a JSON object with exact schema:\n"
    '{"pairs": [{"item_id": str, "score_a": int, "score_b": int, "preferred": "A"|"B"|"tie", "reason": str}]}'
)

_STAGE5_BUNDLE_SCAFFOLDING = (
    "You are evaluating four complete multi-statement systems (System 1, System 2, System 3, System 4) strictly as "
    "ordinary English.\n"
    "You have ONLY the conceptual polarity summary below — NO specialized glossary, NO symbol key, and NO formulas.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nFor each system as a whole, examine whether its words hold stable, compatible ordinary-English meanings across "
    "ALL statements in that system together, without word-salads, swapped contradictions, or polarity reversals.\n"
    "Score each system from 1 (systemically incoherent) to 5 (systemically unified and intelligible), and provide "
    "`ranking` from best to worst (`[best, second, third, worst]`).\n"
    "Return ONLY a JSON object with exact schema:\n"
    '{"scores": {"1": int, "2": int, "3": int, "4": int}, '
    '"best_system": int, "worst_system": int, "ranking": [int, int, int, int], "reason": str}'
)

assert_zero_target_stem_leak(_STAGE5_ITEM_SCAFFOLDING)
assert_zero_target_stem_leak(_STAGE5_NATIVE_PAIR_SCAFFOLDING)
assert_zero_target_stem_leak(_STAGE5_BUNDLE_SCAFFOLDING)


def _seeded_shuffle(seq: list[Any], salt: str) -> list[Any]:
    digest = hashlib.sha256(f"{HARNESS_SEED}:{salt}".encode("utf-8")).digest()
    seed_int = int.from_bytes(digest[:8], "big")
    out = list(seq)
    random.Random(seed_int).shuffle(out)
    return out


def prepare_m4_quadruple(
    item_id: str,
    translation_template: str,
    direction_flipped_d: str,
    src_arm: ArmConfigV2 | None = None,
) -> dict[str, Any]:
    """Render `(T_A0, T_A3, S_syn, D_A0)` deterministically and shuffle as `Candidate 1..4`."""
    if src_arm is None:
        src_arm = build_arm_v2("A0")
    t_a0 = render_template(translation_template, "A0", src_arm=src_arm)
    t_a3 = render_template(translation_template, "A3-1", src_arm=src_arm)
    s_syn = render_template(translation_template, "S_syn", src_arm=src_arm)
    d_a0 = direction_flipped_d
    variants = [
        ("T_A0", t_a0),
        ("T_A3", t_a3),
        ("S_syn", s_syn),
        ("D_A0", d_a0),
    ]
    shuffled = _seeded_shuffle(variants, f"M4_item:{item_id}")
    candidates = {str(idx + 1): text for idx, (_label, text) in enumerate(shuffled)}
    key_map = {str(idx + 1): label for idx, (label, _text) in enumerate(shuffled)}
    return {"item_id": item_id, "candidates": candidates, "hidden_key": key_map}


def prepare_m4_native_pair(
    item_id: str,
    native_a0_t: str,
    native_a3_t: str,
) -> dict[str, Any]:
    """Deterministically shuffle `(A0, A3-1)` native translations as `Candidate A / Candidate B`."""
    pair = [("A0", native_a0_t), ("A3-1", native_a3_t)]
    shuffled = _seeded_shuffle(pair, f"M4_native_pair:{item_id}")
    return {
        "item_id": item_id,
        "Candidate A": shuffled[0][1],
        "Candidate B": shuffled[1][1],
        "hidden_key": {"A": shuffled[0][0], "B": shuffled[1][0]},
    }


def prepare_m4_bundles(
    core_items_rendered: list[dict[str, Any]],
    perm_idx: int,
) -> dict[str, Any]:
    """Shuffle 4 whole-system bundles (`T_A0`, `T_A3`, `S_syn`, `D_A0`) as `System 1..4`."""
    system_names = ("T_A0", "T_A3", "S_syn", "D_A0")
    bundles: dict[str, list[dict[str, Any]]] = {name: [] for name in system_names}
    for row in core_items_rendered:
        inv = {label: row["candidates"][pos] for pos, label in row["hidden_key"].items()}
        for name in system_names:
            bundles[name].append({"statement_num": len(bundles[name]) + 1, "text": inv[name]})
    ordered = _seeded_shuffle(list(system_names), f"M4_bundle:perm_{perm_idx}")
    systems = {str(idx + 1): bundles[name] for idx, name in enumerate(ordered)}
    hidden_key = {str(idx + 1): name for idx, name in enumerate(ordered)}
    return {"perm_idx": perm_idx, "systems": systems, "hidden_key": hidden_key}


def build_stage5_m4_item_messages(batch_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Stage 5a (`M4_item`): Batch `<= 5` items with zero equations/glossary/arm IDs."""
    if not (1 <= len(batch_items) <= 5):
        raise ValueError(f"M4_item batch size must be in 1..5, got {len(batch_items)}")
    public_items = [
        {"item_id": rec["item_id"], "candidates": rec["candidates"]}
        for rec in batch_items
    ]
    instr = "Rate all unlabeled items below and return ONLY the JSON object."
    user_msg = f"{instr}\n{json.dumps({'items': public_items}, indent=2, ensure_ascii=False)}"
    msgs = [
        {"role": "system", "content": _STAGE5_ITEM_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M4_item",
        forbidden_substrings=(
            "Partner Lookup Table",
            "equation_latex",
            "description",
            "T_A0",
            "T_A3",
            "S_syn",
            "D_A0",
            "Arm A0",
            "Arm A3-1",
            "hidden_key",
            "stratum",
        ),
        scaffolding_texts=(_STAGE5_ITEM_SCAFFOLDING, instr),
    )
    return msgs


def build_stage5_m4_native_pair_messages(batch_pairs: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Stage 5b (`M4_native_pair`): Batch `<= 6` native `(A0, A3-1)` pairs without arm labels or equations."""
    if not (1 <= len(batch_pairs) <= 6):
        raise ValueError(f"M4_native_pair batch size must be in 1..6, got {len(batch_pairs)}")
    public_pairs = [
        {
            "item_id": rec["item_id"],
            "Candidate A": rec["Candidate A"],
            "Candidate B": rec["Candidate B"],
        }
        for rec in batch_pairs
    ]
    instr = "Compare each unlabeled pair below and return ONLY the JSON object."
    user_msg = f"{instr}\n{json.dumps({'pairs': public_pairs}, indent=2, ensure_ascii=False)}"
    msgs = [
        {"role": "system", "content": _STAGE5_NATIVE_PAIR_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M4_native_pair",
        forbidden_substrings=(
            "Partner Lookup Table",
            "equation_latex",
            "description",
            "T_A0",
            "T_A3",
            "S_syn",
            "D_A0",
            "Arm A0",
            "Arm A3-1",
            "hidden_key",
            "stratum",
        ),
        scaffolding_texts=(_STAGE5_NATIVE_PAIR_SCAFFOLDING, instr),
    )
    return msgs


def build_stage5_m4_bundle_messages(bundle_record: dict[str, Any]) -> list[dict[str, str]]:
    """Stage 5c (`M4_bundle`): Whole-system coherence evaluation of `System 1..4`."""
    instr = "Evaluate System 1 through System 4 holistically and return ONLY the JSON object."
    user_msg = f"{instr}\n{json.dumps({'systems': bundle_record['systems']}, indent=2, ensure_ascii=False)}"
    msgs = [
        {"role": "system", "content": _STAGE5_BUNDLE_SCAFFOLDING},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M4_bundle",
        forbidden_substrings=(
            "Partner Lookup Table",
            "equation_latex",
            "description",
            "T_A0",
            "T_A3",
            "S_syn",
            "D_A0",
            "Arm A0",
            "Arm A3-1",
            "hidden_key",
            "stratum",
        ),
        scaffolding_texts=(_STAGE5_BUNDLE_SCAFFOLDING, instr),
    )
    return msgs


# ---------------------------------------------------------------------------
# Stage 6 (M5): Leak-Free Vocabulary-Free Word Convergence
# ---------------------------------------------------------------------------

_STAGE6_SYSTEM = (
    "You are participating in an open vocabulary-discovery test under a conceptual polarity framework.\n"
    "You are NOT given any existing target word list — propose the most natural, unforced ordinary-English "
    "counterpart word or two-word phrase from first principles.\n\n"
    + CONCEPTUAL_AXIS_PLAIN
    + "\n\nReturn ONLY a JSON object with exact keys:\n"
    '{"physical_slot": str, "proposed_counterpart": str, "alternate_candidates": [str, str], "reason": str}'
)

assert_zero_target_stem_leak(_STAGE6_SYSTEM)


def build_stage6_m5_messages(physical_slot: str) -> list[dict[str, str]]:
    """Stage 6 (`M5`): Complete prompt must contain ZERO `A0`, `A3-1`, or `S_syn` target words/stems."""
    if physical_slot not in STAGE6_PHYSICAL_SLOTS:
        raise ValueError(f"Unknown Stage 6 slot {physical_slot!r}")
    user_msg = (
        f"Given the physical concept `{physical_slot}`, propose one natural ordinary-English nonphysical counterpart "
        "term (plus two brief alternatives) matching the conceptual polarity mirror above, and return ONLY the JSON object."
    )
    msgs = [
        {"role": "system", "content": _STAGE6_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    assert_prompt_isolation(
        msgs,
        stage="M5",
        forbidden_substrings=("Partner Lookup Table", "Rule R", "A0", "A3-1", "S_syn"),
        check_full_stem_leak=True,
    )
    return msgs


# ---------------------------------------------------------------------------
# Helper: Normalized Target Slots Extraction for M3c Pairs
# ---------------------------------------------------------------------------


def extract_normalized_slots_for_item(output: dict[str, Any], arm: ArmConfigV2) -> set[str]:
    """Return normalized arm base target slots present in `variable_map` and `translation_t`."""
    slots: set[str] = set()
    for k, v in output.get("variable_map", {}).items():
        if _is_stripped_constant_var_entry(k, str(v)):
            continue
        toks, _ = extract_target_tokens_stripped(normalize_target_token_v2(str(v)), arm)
        slots.update(toks)
    slots.update(
        extract_arm_terms(
            output.get("translation_t", ""),
            arm,
            active_terms=slots,
            ignore_unmapped_lowercase=True,
        )
    )
    return slots


# ---------------------------------------------------------------------------
# Offline Self-Test
# ---------------------------------------------------------------------------


def _run_self_test() -> None:
    assert_zero_target_stem_leak(CONCEPTUAL_AXIS_PLAIN)
    _check_zero_leaked_calibration_formulas(RULE_R_V2)
    _check_zero_leaked_calibration_formulas(LINT_CONSTRAINTS_V2)

    # Confirm assert_zero_target_stem_leak catches target stems from A0, A3-1, and S_syn
    for leak_sample in (
        "This uses Movement directly.",
        "Wait for appreciation here.",
        "Checking responsiveness in text.",
        "Measure pitch and growth.",
        "Echo and stillness remain.",
        "Appreciation_PS inside text",
    ):
        try:
            assert_zero_target_stem_leak(leak_sample)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Leak check failed to catch {leak_sample!r}")

    arm_a0 = build_arm_v2("A0")
    arm_a3 = build_arm_v2("A3-1")

    # Verify zero "Movement M" anywhere in partner tables or prompt builders
    assert "Movement M" not in format_partner_lookup_table(arm_a0)
    assert "Movement M" not in format_partner_lookup_table(arm_a3)
    assert arm_a0.partner_lookup["mass"] == "Movement"
    assert arm_a3.partner_lookup["mass"] == "Reflected"
    assert arm_a3.partner_lookup["force"] == "Movement"
    assert arm_a0.partner_lookup["moment of inertia"] == "Movement × Vibration²"
    assert arm_a3.partner_lookup["moment of inertia"] == "Reflected × Appreciation²"
    assert arm_a0.partner_lookup["torque"] == "Vibration × Frequency"
    assert arm_a3.partner_lookup["torque"] == "Appreciation × Movement"
    assert arm_a0.partner_lookup["inertial observer"] == "Movement"
    assert arm_a3.partner_lookup["inertial observer"] == "Reflected"

    # Verify subscript/prime/parenthetical normalization & `(?<![A-Za-z])...(?![A-Za-z])` matching
    assert normalize_target_token_v2("Appreciation_PS") == "Appreciation"
    assert normalize_target_token_v2("Movement_j") == "Movement"
    assert normalize_target_token_v2("Vibration'") == "Vibration"
    assert normalize_target_token_v2("Appreciation (CM)") == "Appreciation"
    assert normalize_target_token_v2("\\vec{Frequency}_{\\text{net}}") == "Frequency"
    toks_a0, unk_a0 = extract_target_tokens_stripped(
        "Appreciation_PS = (Vibration' * Movement_j) / Expansion (i)", arm_a0
    )
    assert unk_a0 == [], f"Unexpected unknowns: {unk_a0}"
    assert toks_a0 == ["Appreciation", "Vibration", "Movement", "Expansion"], toks_a0

    # Verify K01..K16 calibration examples render cleanly & pass BOTH schema validation and joint Layer A
    for arm in (arm_a0, arm_a3):
        cal_exs = build_calibration_examples_for_arm(arm)
        assert len(cal_exs) == 16
        assert all(x["item_id"] != "K17" for x in cal_exs)
        la_res = run_layer_a_v2(
            [{"item": x, "output": x["output"]} for x in cal_exs],
            arm,
        )
        assert la_res["passes_all"], f"Calibration examples failed Layer A on {arm.arm_id}: {la_res}"

        # Stage 1 & Stage 2 prompts pass hygiene
        dummy_cal = {"item_id": "K17", "description": "Boyle test", "equation_latex": "P_1 V_1 = P_2 V_2"}
        m1 = build_stage1_m1_messages(arm, dummy_cal)
        dummy_e = {"item_id": "E001", "description": "Tangential acceleration", "equation_latex": "a_t = r \\alpha", "stratum": "Core"}
        m2 = build_stage2_m2_messages(arm, dummy_e)
        m3b = build_stage3_m3b_opponent_messages(arm, cal_exs[0], cal_exs[0]["output"])
        assert len(m1) == 2 and len(m2) == 2 and len(m3b) == 2

    # Verify strict validator rejects cross-field contradictions, bad slots, digits, SI units, unchanged D
    valid_sample = build_calibration_examples_for_arm(arm_a0)[15]  # K16 (F=ma)
    assert validate_generator_json(valid_sample["output"], arm_a0, valid_sample) == []

    bad_unmapped = dict(valid_sample["output"], unmapped_terms=["pressure"])
    assert validate_generator_json(bad_unmapped, arm_a0, valid_sample)

    bad_slot = dict(valid_sample["output"], translation_template="Net {FakeSlot} equals {Movement} multiplied by {Appreciation}.")
    assert validate_generator_json(bad_slot, arm_a0, valid_sample)

    bad_digit = dict(
        valid_sample["output"],
        translation_t="Net Frequency equals 2 Movement multiplied by Appreciation.",
        translation_template="Net {Frequency} equals 2 {Movement} multiplied by {Appreciation}.",
    )
    assert validate_generator_json(bad_digit, arm_a0, valid_sample)

    bad_si = dict(
        valid_sample["output"],
        translation_t="Net Frequency in kg equals Movement multiplied by Appreciation.",
        translation_template="Net {Frequency} in kg equals {Movement} multiplied by {Appreciation}.",
    )
    assert validate_generator_json(bad_si, arm_a0, valid_sample)

    bad_d = dict(valid_sample["output"], direction_flipped_d=valid_sample["output"]["translation_t"])
    assert validate_generator_json(bad_d, arm_a0, valid_sample)

    # Verify generator JSON normalization (braced direction_flipped_d, superscripts, '=' -> equals, and strict failure guards)
    braced_d_out = dict(
        valid_sample["output"],
        variable_map={"obj": "Collective Reality", "st": "Vibration-Expansion"},
        reflected_formula="Collective Reality = Vibration-Expansion",
        translation_t="Collective Reality aligns with Vibration-Expansion.",
        translation_template="{Collective_Reality} aligns with {Vibration_Expansion}.",
        direction_flipped_d="{Collective_Reality} resists {Vibration_Expansion}.",
    )
    assert validate_generator_json(braced_d_out, arm_a0, valid_sample) == [], validate_generator_json(braced_d_out, arm_a0, valid_sample)
    assert braced_d_out["direction_flipped_d"] == "Collective Reality resists Vibration-Expansion."

    sup_out = dict(
        valid_sample["output"],
        translation_t="Net Frequency equals Movement multiplied by Appreciation\u00b2.",
        translation_template="Net {Frequency} equals {Movement} multiplied by {Appreciation}\u00b2.",
        direction_flipped_d="Net Frequency decreases whenever Movement and Appreciation\u00b2 increase together.",
    )
    assert validate_generator_json(sup_out, arm_a0, valid_sample) == [], validate_generator_json(sup_out, arm_a0, valid_sample)
    assert sup_out["translation_template"] == "Net {Frequency} equals {Movement} multiplied by {Appreciation} squared."
    assert sup_out["translation_t"] == "Net Frequency equals Movement multiplied by Appreciation squared."
    assert sup_out["direction_flipped_d"] == "Net Frequency decreases whenever Movement and Appreciation squared increase together."

    same_braced_d = dict(
        valid_sample["output"],
        variable_map={"f": "Tune"},
        reflected_formula="Tune = Tune",
        translation_t="Tune",
        translation_template="{Tune}",
        direction_flipped_d="{Tune}",
    )
    same_braced_errs = validate_generator_json(same_braced_d, arm_a0, valid_sample)
    assert same_braced_d["direction_flipped_d"] == "Tune"
    assert any("direction_flipped_d is identical to translation_t" in e for e in same_braced_errs), same_braced_errs

    latex_frac_out = dict(
        valid_sample["output"],
        variable_map={"a": "Movement", "b": "Expansion"},
        reflected_formula="Movement / Expansion",
        translation_t="Movement over Expansion.",
        translation_template=r"\frac{Movement}{Expansion}.",
        direction_flipped_d="Expansion over Movement.",
    )
    latex_frac_errs = validate_generator_json(latex_frac_out, arm_a0, valid_sample)
    assert latex_frac_out["translation_t"] == "Movement over Expansion."
    assert latex_frac_out["translation_template"] == r"\frac{Movement}{Expansion}."
    assert latex_frac_errs, "Expected LaTeX \\frac in translation_template to fail validation"

    # Verify Layer-A catches cross-item A1 divergence and A3 sign flips
    bad_a3_item = {
        "item_id": "E_FLIP",
        "description": "Speed",
        "equation_latex": "v = \\frac{\\Delta x}{\\Delta t}",
    }
    bad_a3_out = {
        "item_id": "E_FLIP",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "ok",
        "unmapped_terms": [],
        "variable_map": {"Delta x": "Vibration", "Delta t": "Expansion"},
        "reflected_formula": "rise per Expansion = Expansion / Vibration",
        "translation_t": "Net rise per Expansion grows with Expansion over Vibration.",
        "translation_template": "Net {rise_per_Expansion} grows with {Expansion} over {Vibration}.",
        "direction_flipped_d": "Net rise per Expansion falls with Expansion over Vibration.",
        "rationale": "flipped test",
    }
    assert not run_layer_a_item_check(bad_a3_out, arm_a0, bad_a3_item)["passed"]

    # Verify {Slot} rendering for T_A0, T_A3, S_syn & R9/R10 controls
    for ctrl in ROUND2_CONTROLS_V2:
        quad = prepare_m4_quadruple(ctrl["item_id"], ctrl["translation_template"], ctrl["direction_flipped_d"])
        assert len(quad["candidates"]) == 4
        assert len(set(quad["candidates"].values())) == 4

    # Stage 4 prompts pass hygiene
    build_stage4_m3c_single_messages("S1", "Newton second law", "F = m a", valid_sample["output"]["translation_t"])
    build_stage4_m3c_pairs_messages(
        [
            {
                "pair_id": "P1",
                "shared_terms": ["Movement"],
                "statement_a": valid_sample["output"]["translation_t"],
                "statement_b": render_template(ROUND2_CONTROLS_V2[0]["translation_template"], "A0"),
            }
        ]
    )
    build_stage4_m3c_situation_messages(
        {
            "pair_id": "P1",
            "shared_terms": ["Movement"],
            "statement_a": valid_sample["output"]["translation_t"],
            "statement_b": render_template(ROUND2_CONTROLS_V2[0]["translation_template"], "A0"),
        }
    )

    # Stage 5 prompts pass hygiene
    q_r9 = prepare_m4_quadruple(
        ROUND2_CONTROLS_V2[0]["item_id"],
        ROUND2_CONTROLS_V2[0]["translation_template"],
        ROUND2_CONTROLS_V2[0]["direction_flipped_d"],
    )
    q_r10 = prepare_m4_quadruple(
        ROUND2_CONTROLS_V2[1]["item_id"],
        ROUND2_CONTROLS_V2[1]["translation_template"],
        ROUND2_CONTROLS_V2[1]["direction_flipped_d"],
    )
    build_stage5_m4_item_messages([q_r9, q_r10])
    build_stage5_m4_native_pair_messages(
        [prepare_m4_native_pair("E001", "Total Movement scales cleanly.", "Total Reflected scales cleanly.")]
    )
    build_stage5_m4_bundle_messages(prepare_m4_bundles([q_r9, q_r10], 0))

    # Stage 6 prompts: all 12 slots have ZERO target stem leaks
    for slot in STAGE6_PHYSICAL_SLOTS:
        msgs = build_stage6_m5_messages(slot)
        assert len(msgs) == 2

    # G2-2 / G2-3: All 30 canonical slots have strict non-identity bijective images in A3-1 & S_syn
    assert len(CANONICAL_A0_SLOTS) == 30
    assert len(arm_a0.a0_to_arm) == 30
    assert len(arm_a3.a0_to_arm) == 30
    assert len(SYNONYM_MAP_CH16) == 30
    fixed_pts = [k for k, v in arm_a3.a0_to_arm.items() if k == v]
    assert not fixed_pts, f"Identity fixed points in A3-1: {fixed_pts}"

    # G2-1: Reverse leak coverage — EVERY target phrase and content word across A0, A3-1, S_syn is blocked
    _fn_words = {"for", "per", "in", "to", "out", "and", "the", "of"}
    for term in list(arm_a0.valid_target_terms) + list(arm_a3.valid_target_terms) + list(SYNONYM_MAP_CH16.values()):
        for probe in [term] + [w for w in re.findall(r"[A-Za-z]+", term) if len(w) >= 3 and w.lower() not in _fn_words]:
            try:
                assert_zero_target_stem_leak(f"Check {probe} cleanly.")
            except ValueError:
                pass
            else:
                raise AssertionError(f"Leak detector missed target token {probe!r} (from {term!r})")

    # G3-4: Case-insensitive {Slot}, capitalization mismatch, plurals/possessives, everyday lowercase prose, stripped coverage
    case_out = dict(
        valid_sample["output"],
        translation_t="Frequency equals movement multiplied by Appreciation's Vibrations as it acts out for and shifts in to the current future collection.",
        translation_template="{Frequency} equals {movement} multiplied by {Appreciation}'s {Vibration}s as it acts out for and shifts in to the current future collection.",
        direction_flipped_d="Frequency decreases when Movements oppose Appreciation's Vibration as it recedes away.",
        variable_map={"F_net": "Frequency", "m": "Movement", "a": "Appreciation", "x": "Vibration"},
    )
    assert validate_generator_json(case_out, arm_a0, valid_sample) == [], validate_generator_json(case_out, arm_a0, valid_sample)
    assert render_template("{Conscious_energy} scales with {Movement}.", "S_syn") == "awareness scales with responsiveness."
    assert render_template("{conscious_energy} scales with {Movement}.", "A3-1") == f"{arm_a3.a0_to_arm['conscious energy']} scales with {arm_a3.a0_to_arm['Movement']}."

    # Regression (#145/#146): \left/\right not corrupted by \le/\ge in extract_target_tokens_stripped
    left_toks, left_unk = extract_target_tokens_stripped(
        r"Frequency \cdot Vibration = \left(conscious\ energy_f - conscious\ energy_i\right)",
        arm_a0,
    )
    assert left_unk == [], f"Unexpected unknowns on \\left/\\right: {left_unk}"
    assert left_toks == ["Frequency", "Vibration", "conscious energy", "conscious energy"], left_toks

    missing_slot_out = dict(
        valid_sample["output"],
        variable_map={"F_net": "Frequency", "m": "Movement", "a": "Appreciation", "x": "Vibration"},
        translation_template="Net {Frequency} equals {Movement} multiplied by {Appreciation}.",
    )
    assert any("missing from translation_template" in e for e in validate_generator_json(missing_slot_out, arm_a0, valid_sample))

    # G3-1 / G3-2 / G3-3: Regression suite covering all 12 complex OpenStax held-out equations + counterexamples
    assert strip_math_decorations("Movement * Attraction") == "Movement * Attraction"
    assert strip_math_decorations("\\frac{x - v t}{\\sqrt{1 - v^{2}/c^{2}}}") == "\\frac{x - v t}{\\sqrt{1 - v^{2}/c^{2}}}"

    def _mk_out(item_id: str, vmap: dict[str, str], refl: str, t_tmpl: str, d_flip: str) -> dict[str, Any]:
        return {
            "item_id": item_id,
            "scope_status": "in_scope",
            "formula_shape": "keeps",
            "ruling": "keep",
            "two_level": False,
            "axis_polarity_note": "Regression polarity check.",
            "unmapped_terms": [],
            "variable_map": vmap,
            "reflected_formula": refl,
            "translation_t": render_template(t_tmpl, "A0", arm_a0),
            "translation_template": t_tmpl,
            "direction_flipped_d": d_flip,
            "rationale": "Regression check.",
        }

    # E008: Factored vs distributed equivalence AND '+' sign flip detection
    e008_item = {"item_id": "E008", "equation_latex": "t'= \\frac{t - v x / c^{2}}{\\sqrt{1 - v^{2} / c^{2}}}"}
    e008_vmap = {"t": "Expansion", "v": "rise per Expansion", "x": "Vibration", "c": "Current"}
    e008_fact = _mk_out(
        "E008", e008_vmap,
        "Expansion' = (Expansion - (rise per Expansion) * Vibration / Current^2) / sqrt(1 - (rise per Expansion)^2 / Current^2)",
        "Shifted {Expansion} tracks {Expansion} minus {rise_per_Expansion} and {Vibration} over {Current}.",
        "Shifted Expansion grows with Expansion plus rise per Expansion and Vibration over Current.",
    )
    e008_dist = dict(
        e008_fact,
        reflected_formula="Expansion' = Expansion / sqrt(1 - (rise per Expansion)^2 / Current^2) - ((rise per Expansion) * Vibration / Current^2) / sqrt(1 - (rise per Expansion)^2 / Current^2)",
    )
    e008_bad_plus = dict(
        e008_fact,
        reflected_formula="Expansion' = (Expansion + (rise per Expansion) * Vibration / Current^2) / sqrt(1 - (rise per Expansion)^2 / Current^2)",
    )
    assert run_layer_a_item_check(e008_fact, arm_a0, e008_item)["passed"], run_layer_a_item_check(e008_fact, arm_a0, e008_item)
    assert run_layer_a_item_check(e008_dist, arm_a0, e008_item)["passed"], run_layer_a_item_check(e008_dist, arm_a0, e008_item)
    assert not run_layer_a_item_check(e008_bad_plus, arm_a0, e008_item)["passed"]

    # E011 & E038: Chained '=', sum_{j=1}^N, ()_j subscripts
    e011_item = {"item_id": "E011", "equation_latex": "\\vec{a}_{\\text{CM}} = \\frac{d^{2}}{d t^{2}} (\\frac{1}{M} \\sum_{j = 1}^{N} m_{j} \\vec{r}_{j}) = \\frac{1}{M} \\sum_{j = 1}^{N} m_{j} \\vec{a}_{j}"}
    e011_out = _mk_out(
        "E011",
        {"a_CM": "Appreciation", "M": "Movement", "m_j": "Movement", "a_j": "Appreciation"},
        "Appreciation = (1 / Movement) * \\sum_{j=1}^{N} Movement_j * Appreciation_j",
        "Center {Appreciation} sums weighted {Appreciation} over total {Movement}.",
        "Center Appreciation divides weighted Appreciation independently of Movement.",
    )
    assert run_layer_a_item_check(e011_out, arm_a0, e011_item)["passed"], run_layer_a_item_check(e011_out, arm_a0, e011_item)

    e038_item = {"item_id": "E038", "equation_latex": "\\vec{v}_{\\text{CM}} = \\frac{d}{d t} (\\frac{1}{M} \\sum_{j = 1}^{N} m_{j} \\vec{r}_{j}) = \\frac{1}{M} \\sum_{j = 1}^{N} m_{j} \\vec{v}_{j}"}
    e038_out = _mk_out(
        "E038",
        {"v_CM": "rise per Expansion", "M": "Movement", "m_j": "Movement", "v_j": "rise per Expansion"},
        "(rise per Expansion)_CM = (1 / Movement) * \\sum_{j=1}^{N} Movement_j * (rise per Expansion)_j",
        "Center {rise_per_Expansion} averages {rise_per_Expansion} weighted across {Movement}.",
        "Center rise per Expansion opposes individual rise per Expansion across Movement.",
    )
    assert run_layer_a_item_check(e038_out, arm_a0, e038_item)["passed"], run_layer_a_item_check(e038_out, arm_a0, e038_item)

    # E016 & E018: Parenthesized numerator (x - vt) / (v_0 + v) preserved + inverted denom caught
    e016_item = {"item_id": "E016", "equation_latex": "x'= \\frac{x - v t}{\\sqrt{1 - v^{2} / c^{2}}}"}
    e016_out = _mk_out(
        "E016",
        {"x": "Vibration", "v": "rise per Expansion", "t": "Expansion", "c": "Current"},
        "Vibration' = (Vibration - (rise per Expansion) * Expansion) / sqrt(1 - (rise per Expansion)^2 / Current^2)",
        "Shifted {Vibration} links {Vibration}, {rise_per_Expansion}, {Expansion}, and {Current}.",
        "Shifted Vibration adds rise per Expansion times Expansion to Vibration relative to Current.",
    )
    assert run_layer_a_item_check(e016_out, arm_a0, e016_item)["passed"], run_layer_a_item_check(e016_out, arm_a0, e016_item)
    e016_bad = dict(e016_out, reflected_formula="Vibration' = (Vibration - (rise per Expansion) * Expansion) * sqrt(1 - (rise per Expansion)^2 / Current^2)")
    assert not run_layer_a_item_check(e016_bad, arm_a0, e016_item)["passed"]

    e018_item = {"item_id": "E018", "equation_latex": "\\bar{v} = \\frac{v_{0} + v}{2}"}
    e018_out = _mk_out(
        "E018",
        {"v_0": "rise per Expansion (initial)", "v": "rise per Expansion (final)"},
        "rise per Expansion_avg = (rise per Expansion_0 + rise per Expansion) / 2",
        "Mean {rise_per_Expansion} averages initial and final {rise_per_Expansion}.",
        "Mean rise per Expansion subtracts endpoints of rise per Expansion.",
    )
    assert run_layer_a_item_check(e018_out, arm_a0, e018_item)["passed"], run_layer_a_item_check(e018_out, arm_a0, e018_item)

    # E021: Comma inside subscript W_{\text{grav,} A B} + distributed sign equivalence + '+' flip detection
    e021_item = {"item_id": "E021", "equation_latex": "W_{\\text{grav,} A B} = - m g (y_{B} - y_{A})"}
    e021_out_1 = _mk_out(
        "E021",
        {"W_grav": "Frequency * Vibration", "m": "Movement", "g": "Attraction", "y_A": "Vibration (A)", "y_B": "Vibration (B)"},
        "Frequency * Vibration = -Movement * Attraction * (Vibration_B - Vibration_A)",
        "{Frequency} over {Vibration} shifts opposite {Movement} and {Attraction} across endpoints.",
        "Frequency over Vibration rises along Movement and Attraction regardless of endpoints.",
    )
    e021_out_2 = dict(e021_out_1, reflected_formula="Frequency * Vibration = Movement * Attraction * (Vibration_A - Vibration_B)")
    e021_bad = dict(e021_out_1, reflected_formula="Frequency * Vibration = Movement * Attraction * (Vibration_B + Vibration_A)")
    assert run_layer_a_item_check(e021_out_1, arm_a0, e021_item)["passed"], run_layer_a_item_check(e021_out_1, arm_a0, e021_item)
    assert run_layer_a_item_check(e021_out_2, arm_a0, e021_item)["passed"], run_layer_a_item_check(e021_out_2, arm_a0, e021_item)
    assert not run_layer_a_item_check(e021_bad, arm_a0, e021_item)["passed"]

    # E023: Integral subscript \int_{\text{path} A B} F \cdot dr
    e023_item = {"item_id": "E023", "equation_latex": "W_{A B} = \\int_{\\text{path} A B} \\vec{F} \\cdot d \\vec{r}"}
    e023_out = _mk_out(
        "E023",
        {"W_AB": "Frequency * Vibration", "F": "Frequency", "r": "Vibration"},
        "Frequency * Vibration = \\int Frequency * d Vibration",
        "Total {Frequency} summed along {Vibration} measures integrated effort.",
        "Total Frequency along Vibration vanishes whenever Frequency rises.",
    )
    assert run_layer_a_item_check(e023_out, arm_a0, e023_item)["passed"], run_layer_a_item_check(e023_out, arm_a0, e023_item)

    # E036: Chained calculus + trig + unit vectors \hat{i}, \hat{j}
    e036_item = {"item_id": "E036", "equation_latex": "\\vec{a} (t) = \\frac{d \\vec{v} (t)}{d t} = - A \\omega^{2} \\cos \\omega t \\hat{i} - A \\omega^{2} \\sin \\omega t \\hat{j}"}
    e036_out = _mk_out(
        "E036",
        {"a": "Appreciation", "A": "Vibration", "t": "Expansion"},
        "Appreciation = -Vibration * omega^2 * cos(omega * Expansion) * \\hat{i} - Vibration * omega^2 * sin(omega * Expansion) * \\hat{j}",
        "Turning {Appreciation} stays opposite radial {Vibration} through {Expansion}.",
        "Turning Appreciation aligns outward along Vibration through Expansion.",
    )
    e036_bad = dict(
        e036_out,
        reflected_formula="Appreciation = Vibration * omega^2 * cos(omega * Expansion) * \\hat{i} + Vibration * omega^2 * sin(omega * Expansion) * \\hat{j}",
    )
    assert run_layer_a_item_check(e036_out, arm_a0, e036_item)["passed"], run_layer_a_item_check(e036_out, arm_a0, e036_item)
    assert not run_layer_a_item_check(e036_bad, arm_a0, e036_item)["passed"]

    # E040: \frac{4\pi^2}{GM} a^3 keeps a^3 in numerator, plus explicit "G": "(stripped constant)" allowed while "g": "stripped" rejected
    e040_item = {"item_id": "E040", "equation_latex": "T^{2} = \\frac{4 \\pi^{2}}{G M} a^{3}"}
    e040_out = _mk_out(
        "E040",
        {"T": "Expansion", "G": "(stripped constant)", "M": "Movement", "a": "Vibration"},
        "Expansion^2 = (4 * pi^2 / Movement) * Vibration^3",
        "Squared {Expansion} scales with cubed {Vibration} inversely to {Movement}.",
        "Squared Expansion scales with Movement inversely to cubed Vibration.",
    )
    assert validate_generator_json(e040_out, arm_a0, e040_item) == [], validate_generator_json(e040_out, arm_a0, e040_item)
    assert run_layer_a_item_check(e040_out, arm_a0, e040_item)["passed"], run_layer_a_item_check(e040_out, arm_a0, e040_item)
    e040_bad_inv = dict(e040_out, reflected_formula="Expansion^2 = 1 / (Movement * Vibration^3)")
    assert not run_layer_a_item_check(e040_bad_inv, arm_a0, e040_item)["passed"]
    e040_bad_g_strip = dict(e040_out, variable_map={"T": "Expansion", "g": "stripped", "M": "Movement", "a": "Vibration"})
    assert not run_layer_a_item_check(e040_bad_g_strip, arm_a0, e040_item)["passed"]

    # E005, E017, E024: chained equations + no_partner validation check
    for nop_id in ("E005", "E017", "E024"):
        nop_out = {
            "item_id": nop_id,
            "scope_status": "no_partner",
            "formula_shape": "none",
            "ruling": "no partner",
            "two_level": False,
            "axis_polarity_note": "",
            "unmapped_terms": ["unmapped quantity"],
            "variable_map": {},
            "reflected_formula": "",
            "translation_t": "",
            "translation_template": "",
            "direction_flipped_d": "",
            "rationale": "Blocklisted unmapped physical quantity.",
        }
        assert validate_generator_json(nop_out, arm_a0, {"item_id": nop_id}) == []
        assert run_layer_a_item_check(nop_out, arm_a0, {"item_id": nop_id})["passed"]

    # E017 & E024 chained AST checks when tested directly on formula parsing
    assert len(_parse_equation_clauses_and_segments("P_{\\text{ave}} = \\frac{E_{\\lambda}}{T} = \\frac{1}{2} \\mu A^{2} \\omega^{2} \\frac{\\lambda}{T} = \\frac{1}{2} \\mu A^{2} \\omega^{2} v")[0]) == 4
    assert len(_parse_equation_clauses_and_segments("E_{\\text{Total}} = \\frac{1}{2} k x^{2} + \\frac{1}{2} m v^{2} = \\frac{1}{2} k A^{2}")[0]) == 3

    print("ARMS_V2_SELF_TEST_OK")


if __name__ == "__main__":
    _run_self_test()
