#!/usr/bin/env python3
"""Prompt builders, deterministic shufflers, validators, & self-tests for TSR `deep_v3`.

Supports all 6 live experimental sub-stages across Pillars D1, D2, and D3:
  - D1a: 14 Core Web Slots (`W01..W14`) + 3 Negative Controls (`NC01..NC03`) x 5 raters (85 calls)
  - D1b: 14 Core Web Slots (`W01..W14`) 4-criteria boolean truth tables x 5 raters (70 calls)
  - D2a: Calibration 17 (`K01..K17`) under `RULE_R_V3_CROSSING` (`pressure -> felt gap`) (85 calls)
  - D2b: Crossing Battery 20 (`crossing_battery_20.json`) under `RULE_R_V3_CROSSING` (100 calls)
  - D3a: Source Ch. 2 (`idx=19..22`) + redacted Ch. 16 Crossing (`idx=115`) pedagogy on K01..K17 (85 calls)
  - D3b: 12 verbatim-derived Ch. 2 / Ch. 16 excerpts (`P01..P12`) masked `(V_A0, V_Ssyn, V_A3)` (60 calls)

Python 3.12+ standard library only. Zero live calls at module import or self-test.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

DEEP_V3_DIR = Path(__file__).resolve().parent
HARNESS_DIR = DEEP_V3_DIR.parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2, providers  # noqa: E402

HARNESS_SEED_V3 = 20261116
CROSSING_BATTERY_PATH = DEEP_V3_DIR / "crossing_battery_20.json"
CALIBRATION_PATH = HARNESS_DIR / "openstax" / "calibration_equations_17.json"

RATERS_V3 = providers.GENERATORS


def _seeded_shuffle_v3(seq: list[Any], salt: str, seed: int = HARNESS_SEED_V3) -> list[Any]:
    digest = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).digest()
    seed_int = int.from_bytes(digest[:8], "big")
    out = list(seq)
    random.Random(seed_int).shuffle(out)
    return out


def _load_calibration_items() -> list[dict[str, Any]]:
    payload = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    return list(payload["items"])


def _load_crossing_battery_items() -> list[dict[str, Any]]:
    payload = json.loads(CROSSING_BATTERY_PATH.read_text(encoding="utf-8"))
    return list(payload["items"])


# ---------------------------------------------------------------------------
# Pillar D1: 14 Core Web Slots + 3 Negative Controls (Zero-Glossary & Stem-Clean)
# ---------------------------------------------------------------------------

CORE_WEB_SLOTS_14: tuple[dict[str, Any], ...] = (
    {
        "slot_id": "W01",
        "candidates": {
            "W_A0": "Movement",
            "W_Ssyn": "responsiveness",
            "W_Chal": "soul",
            "W_A3": "Reflected",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Whereas physical mass measures resistance to a change in motion, [TERM] names its receptive counterpart—receptivity to a change in motion.",
            "Role 2 (Whole-Part Structural Position): Rather than naming the joint fusion spanning both resistant and receptive halves, [TERM] denotes one self-contained unit—analogous to an individual section inside a unified symphony—that never breaks loose from the larger whole.",
            "Role 3 (Contextual Coherence): Within a unified multi-part musical work, each [TERM] keeps its own tempo and dynamic progression without ever detaching from the whole composition.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] directly name receptivity to a change in motion (the counterpart of mass as resistance to a change in motion)?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid collapsing into the combined two-sided entity union or acting strictly as a bare passive modifier?",
            "c3_coupled_system_role": "Does [TERM] function cleanly as a distinguishable, self-contained unit belonging inseparably to a larger ongoing composition?",
            "c4_everyday_secondary_register": "Does [TERM] coherently express ongoing dynamic progression while naming a structured section inside a unified composition?",
        },
    },
    {
        "slot_id": "W02",
        "candidates": {
            "W_A0": "Current",
            "W_Ssyn": "stream",
            "W_Chal": "source",
            "W_A3": "Frequency",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Unlike light, which radiates outward across boundaries from localized points, [TERM] collects inward everywhere without outward emission.",
            "Role 2 (Universal Reference Role): Acting as the invariant universal medium carrying every individual unit rather than an emission origin pouring outward, [TERM] establishes the shared present frontier across the whole.",
            "Role 3 (Contextual Coherence): Within an ongoing unfolding totality, the shared [TERM] carries every contributor in one continuous directional flow that is simultaneously alive right in this unfolding moment.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] oppose outward radiative emission by denoting universal inward-collecting ambient flow?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid outward emission imagery (like an origin point radiating outward) and avoid confusing background flow with sensory wave rate?",
            "c3_coupled_system_role": "Does [TERM] operate coherently as the single shared universal reference establishing simultaneous coexistence across the whole?",
            "c4_everyday_secondary_register": "Does [TERM] work naturally in ordinary usage for a continuous directional flow while also expressing live immediacy in the ongoing moment?",
        },
    },
    {
        "slot_id": "W03",
        "candidates": {
            "W_A0": "Vibration",
            "W_Ssyn": "pitch",
            "W_Chal": "mind",
            "W_A3": "Appreciation",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Where physical space keeps objects apart by distance because edges resist overlap, [TERM] names the non-spatial continuum in which two particulars share no location and differ strictly by oscillatory state.",
            "Role 2 (Shared Continuum & Lineage Role): Serving as one half of an orthogonal pair alongside non-spatial temporality rather than a private mental chamber enclosing separate thoughts, [TERM] supplies the shared medium uniting qualitative tone and oscillatory extent.",
            "Role 3 (Contextual Coherence): When two musical instruments harmonize across the same room without colliding, they sustain a shared [TERM] that propagates felt tone and lively oscillatory breadth together.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] cleanly mirror physical space as a distance-free oscillatory continuum distinguishing states qualitatively?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid turning into a private enclosed cognitive box that reintroduces spatial separation between individuals?",
            "c3_coupled_system_role": "Does [TERM] serve as a full continuum connecting qualitative tone and oscillatory breadth rather than merely a single scalar number?",
            "c4_everyday_secondary_register": "Does [TERM] work naturally as a shared harmonic state in physics and music rather than reducing strictly to high-versus-low scalar note height?",
        },
    },
    {
        "slot_id": "W04",
        "candidates": {
            "W_A0": "Expansion",
            "W_Ssyn": "growth",
            "W_Chal": "eternity",
            "W_A3": "Vibrance",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Where physical time separates events through decay and sequence, [TERM] names its receptive counterpart formed because novel states add irreversibly to the whole without anything coming apart.",
            "Role 2 (Continuum Frontier Role): Paired directly with oscillatory distinction to form one irreversible continuum, [TERM] continually pushes the furthest frontier outward—so it cannot denote timeless changelessness where nothing new ever happens, nor confuse second-order rate climb with first-order unfolding.",
            "Role 3 (Contextual Coherence): As newly realized states join the totality without splitting it apart, continuous outward [TERM] widens available possibility and establishes before versus after.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] mirror physical time as irreversible whole-system addition of novelty where nothing decays?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid timeless changeless stasis where nothing new can ever be added?",
            "c3_coupled_system_role": "Does [TERM] remain cleanly distinct from second-order value compounding so both temporal unfolding and second-order rate change stay unambiguous?",
            "c4_everyday_secondary_register": "Does [TERM] coherently convey progressive widening of volume, scope, or possibility without implying timeless immobility?",
        },
    },
    {
        "slot_id": "W05",
        "candidates": {
            "W_A0": "Desire",
            "W_Ssyn": "longing",
            "W_Chal": "intensity",
            "W_A3": "conscious energy",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring physical density—how much mass is packed inside each spatial unit—[TERM] measures how much aimed wanting is packed into an individual receptive unit.",
            "Role 2 (Directional Network Role): Acting simultaneously as concentrated wanting, the factor multiplying qualitative breadth to compose each unit, and the outward-forging aim that advances the shared medium, [TERM] requires directional intent rather than generic scalar amplitude.",
            "Role 3 (Contextual Coherence): Even before physical steps unfold, aimed internal [TERM] supplies active directional wanting oriented toward realization rather than passive wistful ache or directionless amplitude.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] mirror mass density as concentrated wanting packed into a unit's oscillatory extent?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid generic directionless scalar strength or passive sorrowful craving lacking active creative aim?",
            "c3_coupled_system_role": "Does [TERM] work coherently alongside qualitative breadth as a compositional factor of an entity and as directional forward aim?",
            "c4_everyday_secondary_register": "Does [TERM] express active forward-aimed wanting in everyday experience rather than directionless strength or passive sorrow?",
        },
    },
    {
        "slot_id": "W06",
        "candidates": {
            "W_A0": "Vibrance",
            "W_Ssyn": "capacity",
            "W_Chal": "openness",
            "W_A3": "Desire",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring physical volume—how much room an object fills in space—[TERM] measures how much of an entity is actively alive and ringing across the non-spatial oscillatory continuum.",
            "Role 2 (Compositional Extent Role): Multiplying with concentrated wanting to yield a unit's presence while remaining strictly separate from inertial holding-on or empty box volume, [TERM] quantifies alive oscillatory breadth.",
            "Role 3 (Contextual Coherence): Rather than acting as an inert bounding container with empty room inside, an active field radiates full [TERM] as lively oscillatory readiness throughout its extent.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] mirror physical volume specifically as active oscillatory extent across the non-spatial continuum?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid describing inert empty container size or passive pliancy without alive oscillatory activation?",
            "c3_coupled_system_role": "Does [TERM] maintain structural coherence with the spatial counterpart while staying cleanly separated from concentrated wanting?",
            "c4_everyday_secondary_register": "Does [TERM] convey vivid, ringing activation across an extent rather than inert container limits?",
        },
    },
    {
        "slot_id": "W07",
        "candidates": {
            "W_A0": "Appreciation",
            "W_Ssyn": "gratitude",
            "W_Chal": "growth",
            "W_A3": "imagination",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring physical acceleration—how velocity changes over time—[TERM] measures the second-order quickening or slowing of your tonal climb under the ambient inward pull.",
            "Role 2 (Non-Duplicative Hierarchy Role): Standing strictly above baseline unfolding as acceleration of increase rather than first-order increase itself (the way a house compounds faster in strong markets without becoming physically larger), [TERM] avoids collapsing two distinct rows into synonyms.",
            "Role 3 (Contextual Coherence): Even in everyday life—from an asset undergoing faster [TERM] without becoming a larger building to quiet [TERM] toward what is arriving—the same concept links compounding quickening with felt adjustment.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] accurately mirror second-order acceleration (rate of quickening climb) rather than first-order baseline increase?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] stay strictly distinct from simple baseline progression or unfocused fantasy unrelated to rate change?",
            "c3_coupled_system_role": "Does [TERM] bridge second-order quantitative climb directly to practical receptive alignment without duplicating time's partner?",
            "c4_everyday_secondary_register": "Does [TERM] fit coherently in both contexts—compounding rate gain without physical enlargement and warm receptive thankfulness toward what arrives?",
        },
    },
    {
        "slot_id": "W08",
        "candidates": {
            "W_A0": "Frequency",
            "W_Ssyn": "urgency",
            "W_Chal": "will",
            "W_A3": "Movement",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring physical force (mass times acceleration)—what a bounded body feels when pushed—[TERM] names what you perceptually feel under receptivity multiplied by accelerating tonal climb.",
            "Role 2 (Oscillatory Experiential Role): Reading how freely you yield rather than how hard you push or hurry, [TERM] ties steady perceptual tone (like sustained weight) and sudden shifts (like an elevator jolt) strictly to the oscillatory domain.",
            "Role 3 (Contextual Coherence): Across both acoustic wave measurement and human inner experience, adjusting to a steadier [TERM] links repeating cycle tempo directly to what an observer feels.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] mirror physical force as the receptive experiential quantity produced by receptivity times second-order climb?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid forceful effort, strain, pushing, or anxious impatience?",
            "c3_coupled_system_role": "Does [TERM] belong directly to the oscillatory/harmonic family rather than naming an object, entity, or brute determination?",
            "c4_everyday_secondary_register": "Does [TERM] bridge repeating cycle rate in physics and felt experiential tone seamlessly without suggesting anxious haste or brute coercion?",
        },
    },
    {
        "slot_id": "W09",
        "candidates": {
            "W_A0": "Tune",
            "W_Ssyn": "focus",
            "W_Chal": "surrender",
            "W_A3": "resonance",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Positioned at the receptive multiplier hinge where deliberate agency meets the universal medium before realization, [TERM] governs receptive channel alignment cleanly opposite concentrated resistant pushing.",
            "Role 2 (Agency & Selection Role): Crucially, because free choice requires selecting which harmonic state to align with rather than passive capitulation that picks nothing, [TERM] weights receptive draw through deliberate non-forcing selection.",
            "Role 3 (Contextual Coherence): Using selective [TERM] like adjusting a receiver smoothly to one clear broadcast rather than straining or giving up passively keeps attentive engagement accurate.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] sit opposite concentrated resistant effort as receptive oscillatory selection at the multiplier hinge?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid both resistant forcing/concentration AND agency-erasing passive capitulation that chooses nothing?",
            "c3_coupled_system_role": "Does [TERM] represent an actionable selective operation a volitional agent performs to align with a harmonic channel?",
            "c4_everyday_secondary_register": "Does [TERM] naturally name deliberate non-forcing adjustment toward one coherent signal or state without strenuous fixation or passive capitulation?",
        },
    },
    {
        "slot_id": "W10",
        "candidates": {
            "W_A0": "Idle",
            "W_Ssyn": "stillness",
            "W_Chal": "rest",
            "W_A3": "rise per Expansion",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Paired opposite dynamic electric motion across space, [TERM] characterizes how the continuous medium operates dynamically without external displacement.",
            "Role 2 (Active-Poise Role): Rather than inert halting, frozen silence, or dead inactivity, [TERM] characterizes continuous live readiness operating smoothly underneath before external locomotion engages.",
            "Role 3 (Contextual Coherence): Rather than dead cessation, the medium stays [TERM], remaining outwardly unmoved while operating continuously underneath without spatial displacement.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] accurately describe non-spatial dynamic running that appears stationary without external travel?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid dead zero-motion cessation or inert mechanical quiescence?",
            "c3_coupled_system_role": "Does [TERM] pair cleanly as an adjective modifying continuous medium operation alongside inward-turning symmetry?",
            "c4_everyday_secondary_register": "Does [TERM] express outwardly quiet readiness that remains dynamically alive underneath rather than inert halting or zero activity?",
        },
    },
    {
        "slot_id": "W11",
        "candidates": {
            "W_A0": "Reflected",
            "W_Ssyn": "echo",
            "W_Chal": "returning",
            "W_A3": "Current",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring magnetic looping rather than outward radiant broadcasting, [TERM] characterizes an inward-facing symmetry that folds cleanly onto its whole.",
            "Role 2 (Non-Traveling Symmetry Role): Unlike a delayed attenuated acoustic copy or a participle implying spatial travel back across distance, [TERM] designates exact instantaneous mirror correspondence where nothing traverses boundaries.",
            "Role 3 (Contextual Coherence): Across both optical geometry and quiet introspection, [TERM] symmetry maintains exact inward correspondence paired with thoughtful contemplation.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] capture closed-loop inward collection symmetrically opposing outward radiative spread?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid implying spatial travel back across distance or weakened, delayed repetition?",
            "c3_coupled_system_role": "Does [TERM] function grammatically and conceptually as the symmetric modifier of an inward-collecting universal medium?",
            "c4_everyday_secondary_register": "Does [TERM] work coherently for both exact optical mirror correspondence and thoughtful interior contemplation?",
        },
    },
    {
        "slot_id": "W12",
        "candidates": {
            "W_A0": "Vortex",
            "W_Ssyn": "whirlpool",
            "W_Chal": "well",
            "W_A3": "Attraction",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring how massive bodies curve space-time into gravitational depressions bending nearby trajectories, [TERM] names an organized swirling rotational basin in the continuous medium that guides states toward realization.",
            "Role 2 (Non-Plumbing Structure Role): Preceding focal pathway intersection rather than naming a physical borehole excavated in earth or a turbulent liquid surface hazard, [TERM] denotes a self-organizing rotational circulation around an ordering center.",
            "Role 3 (Contextual Coherence): Across fluid dynamics, field theory, and conceptual organization, a coherent [TERM] draws nearby pathways into structured spiral circulation around one ordering center.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] mirror gravitational geometry curvature as a swirling basin guiding trajectories inward?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid sounding like an excavated water pit in the ground or chaotic water turbulence?",
            "c3_coupled_system_role": "Does [TERM] sit cleanly between curvature formation and pathway narrowing as a coherent structured flow form?",
            "c4_everyday_secondary_register": "Does [TERM] convey organized spiral circulation across physics and conceptual systems without tying strictly to ground excavations or chaotic surface hazards?",
        },
    },
    {
        "slot_id": "W13",
        "candidates": {
            "W_A0": "Convergence",
            "W_Ssyn": "gathering",
            "W_Chal": "lens",
            "W_A3": "Intuition",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Mirroring gravitational focal bending without material optics, [TERM] names distinct paths inside the continuous medium coming together cleanly to define what gets focalized and how sharply.",
            "Role 2 (Glass-Free Causal Role): Deliberately replacing physical optical hardware—glass or bounded mass through which light travels—[TERM] describes asymptotic joining where zero material rays traverse physical distance.",
            "Role 3 (Contextual Coherence): Whether tracing asymptotic rays in geometry or independent lines of evidence in inference, sustained [TERM] brings distinct pathways smoothly toward one unified focal outcome.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] capture trajectories bending together to establish focal sharpness without material refraction?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] avoid introducing physical glass hardware, spatial light travel through an optic, or casual social meetups?",
            "c3_coupled_system_role": "Does [TERM] follow swirling basin organization cleanly to define what can be selected at the focal hinge?",
            "c4_everyday_secondary_register": "Does [TERM] express distinct geometric trajectories or inferential lines meeting at one unified outcome without implying material glass refraction?",
        },
    },
    {
        "slot_id": "W14",
        "candidates": {
            "W_A0": "Intuition",
            "W_Ssyn": "hunch",
            "W_Chal": "expectation",
            "W_A3": "Vortex",
        },
        "sentences": (
            "Role 1 (Relational Counterpart): Paired at the central interactive hinge opposite physical anticipation—just as weak interaction pairs with strong interaction inside an atomic core—[TERM] names subtle receptive apprehension crossing directly into awareness.",
            "Role 2 (Boundary-Clean Epistemic Role): Because forward-projecting habit prediction lives inside nervous-system thresholds on the resistant side of the divider, [TERM] cannot reduce to habit-bound forecasting or casual guesswork.",
            "Role 3 (Contextual Coherence): Even prior to explicit step-by-step deliberation, clear [TERM] registers immediate direct apprehension across both careful philosophical reasoning and practical judgment.",
        ),
        "criteria": {
            "c1_core_mirror_role": "Does [TERM] name subtle non-forced direct apprehension balanced directly opposite resistant bodily anticipation?",
            "c2_trap_free_nonspatial_unforced": "Does [TERM] stay strictly on the receptive side rather than collapsing into habit-bound nervous-system forecasting or trivial guesswork?",
            "c3_coupled_system_role": "Does [TERM] operate coherently at the central hinge as the subtle reception partner paired symmetrically against strong anticipation?",
            "c4_everyday_secondary_register": "Does [TERM] carry clear, disciplined standing for immediate non-inferential knowing rather than casual guesswork or nervous habit forecasting?",
        },
    },
)

NEGATIVE_CONTROL_ITEMS_3: tuple[dict[str, Any], ...] = (
    {
        "item_id": "NC01",
        "control_best": "inertia",
        "candidates": {
            "correct": "inertia",
            "wrong_condition": "impulse",
            "spatial_error": "elasticity",
            "vague_generic": "friction",
        },
        "sentences": (
            "Role 1 (Dynamical Role): In classical mechanics, [TERM] denotes an object's inherent persistence in preserving its uniform velocity vector unless acted on by a nonzero external agent.",
            "Role 2 (Distinct Structural Job): Strictly proportional to mass yet cleanly distinct from collision momentum transfer over short contact intervals, surface contact drag, or reversible spring deformation, [TERM] anchors Newton's first law.",
            "Role 3 (Ordinary Double Register): In ordinary English, [TERM] naturally spans both dynamical state preservation and organizational or behavioral tendency to continue along an established track.",
        ),
    },
    {
        "item_id": "NC02",
        "control_best": "torque",
        "candidates": {
            "correct": "torque",
            "wrong_condition": "pressure",
            "spatial_error": "power",
            "vague_generic": "entropy",
        },
        "sentences": (
            "Role 1 (Dynamical Role): Acting as the rotational counterpart of linear pushing force, [TERM] equals perpendicular lever arm crossed with applied push about a pivot, changing rotational momentum.",
            "Role 2 (Distinct Structural Job): Distinct from work delivery rate per second, omnidirectional scalar normal force per area, or thermodynamic state dispersal, [TERM] always preserves axial rotational twist direction.",
            "Role 3 (Ordinary Double Register): In ordinary English, [TERM] specifies twisting rotational leverage applied via a wrench, axle, or drive shaft.",
        ),
    },
    {
        "item_id": "NC03",
        "control_best": "equilibrium",
        "candidates": {
            "correct": "equilibrium",
            "wrong_condition": "viscosity",
            "spatial_error": "acceleration",
            "vague_generic": "amplitude",
        },
        "sentences": (
            "Role 1 (Systemic Balance Role): Across mechanics and thermodynamics, [TERM] identifies a balanced regime where opposing drives cancel cleanly so macroscopic observables experience zero net drift.",
            "Role 2 (Distinct Structural Job): Strictly distinct from fluid shear drag, second-order temporal velocity change, or wave peak excursion height, [TERM] governs mechanical, chemical, and thermal balance uniformly.",
            "Role 3 (Ordinary Double Register): In ordinary English, [TERM] expresses poised steadiness between competing influences across physics, economics, and human balance alike.",
        ),
    },
)

# Forbidden root stems inside D1a/D1b un-substituted prompts (case-insensitive word/prefix guard)
_D1_FORBIDDEN_WORDS: frozenset[str] = frozenset(
    word.lower()
    for slot in CORE_WEB_SLOTS_14
    for phrase in slot["candidates"].values()
    for word in re.findall(r"[A-Za-z]+", phrase)
    if len(word) >= 4
)
_D1_STEM_PREFIXES: tuple[str, ...] = (
    "movement",
    "move",
    "respons",
    "soul",
    "reflect",
    "current",
    "stream",
    "source",
    "frequen",
    "vibrat",
    "vibran",
    "pitch",
    "mind",
    "appreciat",
    "expan",
    "growth",
    "grow",
    "etern",
    "desir",
    "long",
    "intens",
    "conscious",
    "energy",
    "capacit",
    "open",
    "gratitud",
    "grateful",
    "imagin",
    "urgen",
    "will",
    "tune",
    "tuning",
    "focus",
    "surrender",
    "resonan",
    "idle",
    "still",
    "rest",
    "rise",
    "rising",
    "echo",
    "return",
    "vortex",
    "whirlpool",
    "well",
    "attract",
    "converg",
    "gather",
    "lens",
    "intuit",
    "hunch",
    "expect",
)


def _check_d1_zero_candidate_leak(text: str, extra_words: Iterable[str] = ()) -> None:
    lower_words = re.findall(r"[A-Za-z]+", text.lower())
    forbidden_exact = set(_D1_FORBIDDEN_WORDS) | {w.lower() for w in extra_words}
    for w in lower_words:
        if w in forbidden_exact:
            raise ValueError(f"Candidate word {w!r} leaked into D1 prompt text: {text!r}")
        for pref in _D1_STEM_PREFIXES:
            if w.startswith(pref):
                raise ValueError(
                    f"Candidate root stem {pref!r} matched word {w!r} in D1 prompt text: {text!r}"
                )


_CORE_WEB_BY_ID: dict[str, dict[str, Any]] = {s["slot_id"]: s for s in CORE_WEB_SLOTS_14}
_NC_BY_ID: dict[str, dict[str, Any]] = {s["item_id"]: s for s in NEGATIVE_CONTROL_ITEMS_3}

D1A_SYSTEM_PROMPT: str = (
    "You are evaluating four unlabeled candidate English words (`1`, `2`, `3`, `4`) for a single "
    "conceptual slot `[TERM]` described strictly by three structural role sentences.\n"
    "You have NO specialized glossary, NO hidden naming system, and NO formula sheet.\n"
    "Test every candidate mentally by plugging `[TERM]` into all three sentences at once: "
    "Score how cleanly the candidate satisfies Role 1 (mirror relationship), Role 2 (structural "
    "separation from adjacent roles and traps), AND Role 3 (authentic everyday English double duty) "
    "simultaneously.\n"
    "Score each candidate from 1 (fails roles or collides with traps) to 5 (nails every role and "
    "everyday sense effortlessly).\n"
    "Output ONLY a valid JSON object with the exact 6 keys and NO extra keys:\n"
    '{"item_id": str, "scores": {"1": int, "2": int, "3": int, "4": int}, '
    '"best_candidate": int, "worst_candidate": int, "ranking": [int, int, int, int], "reason": str}'
)

D1B_SYSTEM_PROMPT: str = (
    "You are completing an unlabeled 4-criteria boolean diagnostic table over four candidate English "
    "words (`1`, `2`, `3`, `4`) for a single conceptual slot `[TERM]`.\n"
    "You have NO specialized glossary and NO reference key.\n"
    "Evaluate each candidate `1..4` independently on each binary question `c1`, `c2`, `c3`, `c4` "
    "(`true` only when the candidate genuinely passes that criterion in standard English; `false` "
    "when it fails or introduces a flaw).\n"
    "Output ONLY a valid JSON object with the exact 3 keys and NO extra keys:\n"
    '{"slot_id": str, "evaluations": {"1": {"c1": bool, "c2": bool, "c3": bool, "c4": bool}, '
    '"2": {"c1": bool, "c2": bool, "c3": bool, "c4": bool}, '
    '"3": {"c1": bool, "c2": bool, "c3": bool, "c4": bool}, '
    '"4": {"c1": bool, "c2": bool, "c3": bool, "c4": bool}}, "reason": str}'
)


def prepare_d1a_item(item_id: str, rater_id: str) -> dict[str, Any]:
    if item_id in _CORE_WEB_BY_ID:
        spec = _CORE_WEB_BY_ID[item_id]
        stratum = "Core_Web"
    elif item_id in _NC_BY_ID:
        spec = _NC_BY_ID[item_id]
        stratum = "Negative_Control"
    else:
        raise KeyError(f"Unknown D1a item_id: {item_id!r}")
    items = list(spec["candidates"].items())
    shuffled = _seeded_shuffle_v3(items, f"D1a:{item_id}:{rater_id}", seed=HARNESS_SEED_V3)
    candidates = {str(i + 1): word for i, (_arm_lbl, word) in enumerate(shuffled)}
    hidden_key = {str(i + 1): arm_lbl for i, (arm_lbl, _word) in enumerate(shuffled)}
    return {
        "item_id": item_id,
        "stratum": stratum,
        "rater_id": rater_id,
        "sentences": spec["sentences"],
        "candidates": candidates,
        "hidden_key": hidden_key,
    }


def build_d1a_messages(item_id: str, rater_id: str) -> list[dict[str, str]]:
    prep = prepare_d1a_item(item_id, rater_id)
    lines = [
        f"Evaluate unlabeled item `{item_id}`:",
        "",
        "Three Structural Constraint Sentences for `[TERM]`:",
    ]
    for s in prep["sentences"]:
        lines.append(f"  - {s}")
    lines.append("")
    lines.append("Anonymized Candidate Words:")
    for idx in ("1", "2", "3", "4"):
        lines.append(f"  Candidate {idx}: {prep['candidates'][idx]}")
    lines.append("")
    lines.append(f'Respond with ONLY the JSON object with `"item_id": "{item_id}"`.')
    return [
        {"role": "system", "content": D1A_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def validate_d1a_json(parsed: Any, expected_item_id: str) -> list[str]:
    req_keys = {"item_id", "scores", "best_candidate", "worst_candidate", "ranking", "reason"}
    if not isinstance(parsed, dict):
        return [f"Output must be JSON object, got {type(parsed).__name__}"]
    missing = sorted(req_keys - set(parsed.keys()))
    extra = sorted(set(parsed.keys()) - req_keys)
    errors: list[str] = []
    if missing:
        errors.append(f"Missing keys: {missing}")
    if extra:
        errors.append(f"Extra keys: {extra}")
    if parsed.get("item_id") != expected_item_id:
        errors.append(f"item_id mismatch: got {parsed.get('item_id')!r}, expected {expected_item_id!r}")

    scores = parsed.get("scores")
    if not isinstance(scores, dict) or set(scores.keys()) != {"1", "2", "3", "4"}:
        errors.append("scores must have exact keys {'1','2','3','4'}")
    else:
        for k in ("1", "2", "3", "4"):
            v = scores[k]
            if isinstance(v, bool) or not isinstance(v, int) or not (1 <= v <= 5):
                errors.append(f"scores[{k!r}] must be int in 1..5, got {v!r}")

    best = parsed.get("best_candidate")
    worst = parsed.get("worst_candidate")
    if isinstance(best, bool) or not isinstance(best, int) or not (1 <= best <= 4):
        errors.append(f"best_candidate must be int in 1..4, got {best!r}")
    if isinstance(worst, bool) or not isinstance(worst, int) or not (1 <= worst <= 4):
        errors.append(f"worst_candidate must be int in 1..4, got {worst!r}")
    if isinstance(best, int) and isinstance(worst, int) and best == worst:
        errors.append(f"best_candidate == worst_candidate == {best}")

    ranking = parsed.get("ranking")
    if (
        not isinstance(ranking, list)
        or len(ranking) != 4
        or any(isinstance(x, bool) or not isinstance(x, int) for x in ranking)
        or set(ranking) != {1, 2, 3, 4}
    ):
        errors.append(f"ranking must be permutation of [1,2,3,4], got {ranking!r}")
    elif not errors:
        if ranking[0] != best:
            errors.append(f"ranking[0]={ranking[0]} != best_candidate={best}")
        if ranking[-1] != worst:
            errors.append(f"ranking[-1]={ranking[-1]} != worst_candidate={worst}")
        ordered_scores = [scores[str(k)] for k in ranking]
        if any(ordered_scores[i] < ordered_scores[i + 1] for i in range(3)):
            errors.append(f"scores not monotone non-increasing along ranking {ranking}: {ordered_scores}")
        if scores[str(best)] != max(scores.values()):
            errors.append(f"scores[best_candidate]={scores[str(best)]} != max={max(scores.values())}")
        if scores[str(worst)] != min(scores.values()):
            errors.append(f"scores[worst_candidate]={scores[str(worst)]} != min={min(scores.values())}")

    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be non-empty string")
    return errors


def prepare_d1b_slot(slot_id: str, rater_id: str) -> dict[str, Any]:
    if slot_id not in _CORE_WEB_BY_ID:
        raise KeyError(f"Unknown D1b slot_id: {slot_id!r}")
    spec = _CORE_WEB_BY_ID[slot_id]
    items = list(spec["candidates"].items())
    shuffled = _seeded_shuffle_v3(items, f"D1b:{slot_id}:{rater_id}", seed=HARNESS_SEED_V3)
    candidates = {str(i + 1): word for i, (_arm_lbl, word) in enumerate(shuffled)}
    hidden_key = {str(i + 1): arm_lbl for i, (arm_lbl, _word) in enumerate(shuffled)}
    return {
        "slot_id": slot_id,
        "rater_id": rater_id,
        "criteria": spec["criteria"],
        "candidates": candidates,
        "hidden_key": hidden_key,
    }


def build_d1b_messages(slot_id: str, rater_id: str) -> list[dict[str, str]]:
    prep = prepare_d1b_slot(slot_id, rater_id)
    crit = prep["criteria"]
    lines = [
        f"Evaluate 4-criteria boolean truth table for slot `{slot_id}`:",
        "",
        "Four Binary Criteria (each scored independently for Candidate 1..4):",
        f"  c1 (c1_core_mirror_role): {crit['c1_core_mirror_role']}",
        f"  c2 (c2_trap_free_nonspatial_unforced): {crit['c2_trap_free_nonspatial_unforced']}",
        f"  c3 (c3_coupled_system_role): {crit['c3_coupled_system_role']}",
        f"  c4 (c4_everyday_secondary_register): {crit['c4_everyday_secondary_register']}",
        "",
        "Anonymized Candidate Words for `[TERM]`:",
    ]
    for idx in ("1", "2", "3", "4"):
        lines.append(f"  Candidate {idx}: {prep['candidates'][idx]}")
    lines.append("")
    lines.append(f'Respond with ONLY the JSON object with `"slot_id": "{slot_id}"`.')
    return [
        {"role": "system", "content": D1B_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def validate_d1b_json(parsed: Any, expected_slot_id: str) -> list[str]:
    req_top = {"slot_id", "evaluations", "reason"}
    if not isinstance(parsed, dict):
        return [f"Output must be JSON object, got {type(parsed).__name__}"]
    missing = sorted(req_top - set(parsed.keys()))
    extra = sorted(set(parsed.keys()) - req_top)
    errors: list[str] = []
    if missing:
        errors.append(f"Missing keys: {missing}")
    if extra:
        errors.append(f"Extra keys: {extra}")
    if parsed.get("slot_id") != expected_slot_id:
        errors.append(f"slot_id mismatch: got {parsed.get('slot_id')!r}, expected {expected_slot_id!r}")

    evals = parsed.get("evaluations")
    if not isinstance(evals, dict) or set(evals.keys()) != {"1", "2", "3", "4"}:
        errors.append("evaluations must have exact keys {'1','2','3','4'}")
    else:
        req_c = {"c1", "c2", "c3", "c4"}
        for idx in ("1", "2", "3", "4"):
            row = evals[idx]
            if not isinstance(row, dict) or set(row.keys()) != req_c:
                errors.append(f"evaluations[{idx!r}] must have exact keys {{'c1','c2','c3','c4'}}")
            else:
                for ck in ("c1", "c2", "c3", "c4"):
                    if not isinstance(row[ck], bool):
                        errors.append(f"evaluations[{idx!r}][{ck!r}] must be bool, got {row[ck]!r}")

    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be non-empty string")
    return errors


def solve_collision_free_web_assignments(
    eligible_by_slot: Mapping[str, Iterable[str]],
    *,
    max_solutions: int = 256,
    count_limit: int = 10000,
) -> dict[str, Any]:
    """Enumerate unique-word 14-slot assignments across `W01..W14` using passing candidates."""
    slot_ids = [s["slot_id"] for s in CORE_WEB_SLOTS_14]
    a0_map = {s["slot_id"]: s["candidates"]["W_A0"] for s in CORE_WEB_SLOTS_14}

    domains: dict[str, list[str]] = {}
    for sid in slot_ids:
        seen_l: set[str] = set()
        opts: list[str] = []
        for w in eligible_by_slot.get(sid, ()):
            ws = str(w).strip()
            wl = ws.lower()
            if ws and wl not in seen_l:
                seen_l.add(wl)
                opts.append(ws)
        domains[sid] = sorted(opts, key=lambda x: (x.lower() != a0_map[sid].lower(), x.lower()))

    solutions: list[dict[str, str]] = []
    total_count = 0
    truncated = False
    used_lower: set[str] = set()
    chosen: dict[str, str] = {}

    unassigned = set(slot_ids)

    def _backtrack() -> None:
        nonlocal total_count, truncated
        if total_count >= count_limit:
            truncated = True
            return
        if not unassigned:
            total_count += 1
            if len(solutions) < max_solutions:
                solutions.append({sid: chosen[sid] for sid in slot_ids})
            return

        # MRV heuristic: choose unassigned slot with fewest remaining unused words
        best_sid = ""
        best_avail: list[str] | None = None
        for sid in slot_ids:
            if sid not in unassigned:
                continue
            avail = [w for w in domains[sid] if w.lower() not in used_lower]
            if not avail:
                return
            if best_avail is None or len(avail) < len(best_avail):
                best_sid = sid
                best_avail = avail
                if len(best_avail) == 1:
                    break

        assert best_avail is not None
        unassigned.remove(best_sid)
        for word in best_avail:
            wl = word.lower()
            used_lower.add(wl)
            chosen[best_sid] = word
            _backtrack()
            del chosen[best_sid]
            used_lower.remove(wl)
            if total_count >= count_limit:
                truncated = True
                break
        unassigned.add(best_sid)

    _backtrack()
    a0_in_solutions = all(
        any(w.lower() == a0_map[sid].lower() for w in domains[sid]) for sid in slot_ids
    )
    return {
        "has_valid_assignment": total_count > 0,
        "total_count": total_count,
        "truncated": truncated,
        "solutions": solutions,
        "a0_expected": a0_map,
        "a0_in_solutions": a0_in_solutions,
        "eligible_counts": {sid: len(domains[sid]) for sid in slot_ids},
    }


# ---------------------------------------------------------------------------
# Pillar D2: Crossing Boundary Protocol (`pressure -> felt gap`, D2a & D2b)
# ---------------------------------------------------------------------------

CROSSING_PARTNER_ENTRIES_A0: tuple[tuple[str, str, str], ...] = (
    ("pressure", "felt gap", "crossing boundary"),
    ("gauge pressure", "felt gap", "crossing boundary"),
    ("atmospheric pressure", "felt gap", "crossing boundary"),
    ("absolute pressure", "felt gap", "crossing boundary"),
)

UNMAPPED_BLOCKLIST_D2_CROSSING: tuple[str, ...] = tuple(
    t for t in arms_v2.UNMAPPED_BLOCKLIST_V2 if t.lower() != "pressure"
)

CANONICAL_D2_SLOTS: tuple[str, ...] = (*arms_v2.CANONICAL_A0_SLOTS, "felt gap")


def build_crossing_arm_v3() -> arms_v2.ArmConfigV2:
    """Build read-only extended A0 `ArmConfigV2` supporting Crossing `pressure -> felt gap`."""
    base = arms_v2.build_arm_v2("A0")
    a0_to_arm = dict(base.a0_to_arm)
    a0_to_arm["felt gap"] = "felt gap"
    arm_to_a0 = dict(base.arm_to_a0)
    arm_to_a0["felt gap"] = "felt gap"
    partner_entries = (*base.partner_entries, *CROSSING_PARTNER_ENTRIES_A0)
    partner_lookup = dict(base.partner_lookup)
    for phys, targ, _role in CROSSING_PARTNER_ENTRIES_A0:
        partner_lookup[phys.lower()] = targ

    slot_to_term = dict(base.slot_to_term)
    slot_to_canonical = dict(base.slot_to_canonical)
    slot_lower_to_canonical = dict(base.slot_lower_to_canonical)
    for key in ("felt gap", "felt_gap"):
        slot_to_term[key] = "felt gap"
        slot_to_canonical[key] = "felt gap"
        slot_lower_to_canonical[key.lower()] = "felt gap"

    valid_terms = tuple(sorted({*base.valid_target_terms, "felt gap"}, key=lambda s: (-len(s), s)))
    return arms_v2.ArmConfigV2(
        arm_id="A0",
        description="A0 Crossing-extended mirror lookup adding mechanical pressure -> felt gap.",
        a0_to_arm=a0_to_arm,
        arm_to_a0=arm_to_a0,
        mirror_pairs=base.mirror_pairs,
        partner_entries=partner_entries,
        partner_lookup=partner_lookup,
        valid_target_terms=valid_terms,
        slot_to_term=slot_to_term,
        slot_to_canonical=slot_to_canonical,
        slot_lower_to_canonical=slot_lower_to_canonical,
        baseline_sign_edges=base.baseline_sign_edges,
        unmapped_blocklist=UNMAPPED_BLOCKLIST_D2_CROSSING,
        open_joints=base.open_joints,
    )


def format_crossing_partner_lookup_table(crossing_arm: arms_v2.ArmConfigV2) -> str:
    base_table = arms_v2.format_partner_lookup_table(arms_v2.build_arm_v2("A0"))
    lines = [
        base_table,
        "Crossing Boundary Interface Partners (STRICTLY for pure mechanical/hydrostatic equations):",
    ]
    for phys, targ, role in CROSSING_PARTNER_ENTRIES_A0:
        lines.append(f"  - {phys} -> {targ}  [{role}]")
    return "\n".join(lines)


RULE_R_V3_CROSSING: str = (
    "Rule R v3 (Crossing-Boundary Extension — Deterministic Scope & Reflection Protocol):\n"
    "\n"
    "Every item MUST be classified into exactly ONE `scope_status`: "
    "`\"in_scope\"`, `\"crossing_interface\"`, `\"no_partner\"`, or `\"open_joint\"`.\n"
    "\n"
    "Step 1 — Strict Boundary Guard (`scope_status = \"no_partner\"`, `ruling = \"no partner\"`, "
    "`formula_shape = \"none\"`):\n"
    "  1a. Strip dimensionless numeric prefactors (2, 1/2, 3, 4 pi^2, sqrt(2), etc.) AND static background "
    "constants or fixed parenthetical side conditions—both universal/material constants (`gamma`, `G`, `mu_k`, "
    "`mu_s`, `k_e`, `epsilon_0`, `mu_0`, `h`, `hbar`, gravitational constant, constant reference density) AND "
    "parameters held fixed in a trailing parenthetical `(constant ...)` qualifier (e.g. a background quantity "
    "explicitly declared constant outside the dynamical formula rather than varying in the equation).\n"
    "  1b. Inspect EVERY remaining active dynamical quantity appearing inside the equation or law itself. "
    "CRITICAL BOUNDARY GUARD: If ANY active thermal variable (`T`, `T_1`, `T_2`, `Delta T`, absolute/Celsius "
    "temperature varying in the formula, heat `Q`, latent heat `L_v`, specific/molar heat capacities `C_p`, `C_V`, "
    "enthalpy, entropy `S`, internal energy `E_int`, free energy, Carnot efficiency), ANY active molar/gas constant or "
    "variable (Boltzmann constant `k_B`, ideal gas constant `R`, particle/molecule number `N` or active variable moles `n`, "
    "molar mass `M`), ANY viscous or pipe-flow rate variable (dynamic viscosity `eta`, volume flow rate `Q = dV/dt`, "
    "Reynolds number), ANY electric circuit quantity (charge, electric current, voltage, EMF, capacitance, inductance, "
    "impedance), OR ANY acoustic/optical/elastic quantity (wave frequency `f` in Hz, dB intensity, wavenumber `k`, "
    "refractive index `n`, phase difference, angle, elastic modulus, spring constant) appears dynamically in the formula "
    "itself—EVEN IF mechanical `pressure` ALSO appears in the same equation—you MUST STOP immediately and classify the "
    "item as `\"no_partner\"`!\n"
    "  1c. For `scope_status = \"no_partner\"`: set `formula_shape = \"none\"`, `ruling = \"no partner\"`, "
    "`two_level = false`, list all missing/blocklisted variables in `unmapped_terms`, and set "
    "`reflected_formula = translation_t = translation_template = direction_flipped_d = \"\"`.\n"
    "\n"
    "Step 2 — Open Joints (`scope_status = \"open_joint\"`, `ruling = \"indeterminate\"`, `formula_shape = \"none\"`):\n"
    "  Restrict `open_joint` strictly and ONLY to `escape velocity`, `gravitational time dilation`, "
    "`gravitational redshift`, and `Schwarzschild radius`. Leave prose/formula fields `\"\"`.\n"
    "\n"
    "Step 3 — Pure Mechanical Pressure at the Crossing (`scope_status = \"crossing_interface\"` vs `\"in_scope\"`):\n"
    "  - Unlike pure receptive concepts, mechanical `pressure` (including `gauge pressure`, `atmospheric pressure`, "
    "`absolute pressure`, fluid pressure) exists only where physical resistance bounds a surface against expansion. "
    "It therefore has NO standalone inner counterpart; it reflects ONLY at the Crossing interface between physical "
    "experience and the Current as `felt gap` (`{felt_gap}` in templates).\n"
    "  - If NO Step-1b active dynamical blocklisted quantity is present AND the equation/law involves mechanical `pressure` "
    "(e.g., force per area, hydrostatic column depth/height, gauge/absolute components, hydraulic pressure transmission, "
    "inviscid Bernoulli pressure balance, constant-temperature mechanical pressure-volume product laws, or purely "
    "mechanical boundary work changing volume against external pressure): classify as `scope_status = \"crossing_interface\"`, "
    "map mechanical pressure variable(s) to `felt gap`, map all other active variables using the Partner Lookup Table, "
    "set `formula_shape = \"keeps\"`, determine `ruling` (`keep` or `invert`) and `two_level` cleanly from Step 4, and fill "
    "`reflected_formula`, `translation_t`, `translation_template`, and `direction_flipped_d` using ordinary English.\n"
    "  - If NO pressure/crossing concept is involved and all variables map directly inside the primary Partner Lookup "
    "Table, classify as `scope_status = \"in_scope\"`.\n"
    "\n"
    "Step 4 — Condition Reading & Algebraic Preservation:\n"
    "  - `formula_shape = \"keeps\"`: Never invert quotients or flip arithmetic signs inside `reflected_formula`.\n"
    "  - `ruling = \"keep\"` (`two_level = false`): structural definitions, additive/multiplicative state identities, "
    "conservation or constant-product equilibrium laws, action-reaction symmetries, or resistance-free continuum identities.\n"
    "  - `ruling = \"invert\"`: whenever the law requires exertion against physical resistance, dissipative drag/friction "
    "loss, relativistic/boundary barrier costs, or spatial separation; set `two_level = true` ONLY if the formula is "
    "simultaneously a productive operational definition whose application tracks costly exertion/resistance."
)

LINT_CONSTRAINTS_V3_CROSSING: str = (
    "Strict Output Formatting & Lint Rules (`D2` Crossing Protocol):\n"
    "1. Return ONLY a single valid JSON object with the exact 13 required keys and NO extra keys:\n"
    "   `item_id`, `scope_status`, `formula_shape`, `ruling`, `two_level`, `axis_polarity_note`, "
    "`unmapped_terms`, `variable_map`, `reflected_formula`, `translation_t`, `translation_template`, "
    "`direction_flipped_d`, `rationale`.\n"
    "2. Cross-field invariants:\n"
    "   - `scope_status in (\"in_scope\", \"crossing_interface\")` <-> `formula_shape == \"keeps\"`, "
    "`ruling in (\"keep\", \"invert\")`, `unmapped_terms == []`, non-empty `variable_map`, `reflected_formula`, "
    "`translation_t`, `translation_template`, `direction_flipped_d`.\n"
    "   - If `ruling == \"keep\"`, `two_level` MUST be `false`.\n"
    "   - `scope_status == \"no_partner\"` <-> `formula_shape == \"none\"`, `ruling == \"no partner\"`, "
    "`two_level == false`, non-empty `unmapped_terms`, empty `\"\"` for formula & translation strings.\n"
    "   - `scope_status == \"open_joint\"` <-> `formula_shape == \"none\"`, `ruling == \"indeterminate\"`, "
    "`two_level == false`, `unmapped_terms == []`, empty `\"\"` for formula & translation strings.\n"
    "3. Prose rules (`translation_t`, `translation_template`, `direction_flipped_d`):\n"
    "   - Wrap EVERY mapped target term in `{Slot}` in `translation_template` (including `{felt_gap}` for "
    "`felt gap`), leaving ZERO unbraced mapped or capitalized target terms outside `{...}`.\n"
    "   - Zero ASCII/Unicode digits (`0-9`, `²`, `³`), zero SI unit tokens, zero inline parenthetical/appositive "
    "glosses, and zero `'Movement M'`.\n"
    "   - `direction_flipped_d` must differ meaningfully from `translation_t` while keeping the exact same active target term set."
)

_D2_BOYLE_LEAK_RE = re.compile(r"boyle|\bP_\{?1\}?|\bV_\{?1\}?", re.I)


def _check_d2_zero_boyle_leak(text: str) -> None:
    m = _D2_BOYLE_LEAK_RE.search(text)
    if m:
        raise ValueError(f"Forbidden Boyle/P_1/V_1 reference in D2 prompt/rule: {m.group(0)!r}")
    arms_v2._check_zero_leaked_calibration_formulas(text)


_CROSSING_ARM_V3 = build_crossing_arm_v3()
D2_SYSTEM_PROMPT: str = (
    "You are evaluating a physics-to-mirror translation protocol with a Crossing-Boundary extension.\n\n"
    + RULE_R_V3_CROSSING
    + "\n\n"
    + format_crossing_partner_lookup_table(_CROSSING_ARM_V3)
    + "\n\n"
    + LINT_CONSTRAINTS_V3_CROSSING
)
_check_d2_zero_boyle_leak(D2_SYSTEM_PROMPT)


def _sanitize_d2_item_payload(item: dict[str, Any]) -> dict[str, Any]:
    fields = ("item_id", "volume", "chapter", "chapter_title", "description", "equation_latex")
    return {k: item[k] for k in fields if k in item}


def build_d2a_messages(item: dict[str, Any]) -> list[dict[str, str]]:
    payload = {
        "item_id": item["item_id"],
        "provenance_note": item.get("chapter_or_context", ""),
        "description": item["description"],
        "equation_latex": item["equation_latex"],
    }
    instr = (
        f"Classify `scope_status` and process item `{item['item_id']}` strictly under Rule R v3 "
        f"and the Crossing-extended Partner Lookup Table."
    )
    _check_d2_zero_boyle_leak(instr)
    user_txt = f"{instr}\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
    if item["item_id"] != "K17":
        _check_d2_zero_boyle_leak(user_txt)
    return [
        {"role": "system", "content": D2_SYSTEM_PROMPT},
        {"role": "user", "content": user_txt},
    ]


def build_d2b_messages(item: dict[str, Any]) -> list[dict[str, str]]:
    instr = (
        f"Classify `scope_status` (`in_scope`, `crossing_interface`, `no_partner`, or `open_joint`) "
        f"and process OpenStax item `{item['item_id']}` strictly under Rule R v3 and the Crossing-extended "
        "Partner Lookup Table."
    )
    _check_d2_zero_boyle_leak(instr)
    payload = _sanitize_d2_item_payload(item)
    return [
        {"role": "system", "content": D2_SYSTEM_PROMPT},
        {"role": "user", "content": f"{instr}\n{json.dumps(payload, indent=2, ensure_ascii=False)}"},
    ]


def render_template_d2_crossing(template: str, crossing_arm: arms_v2.ArmConfigV2) -> str:
    """Resolve `{Slot}` placeholders against `crossing_arm` (supports both A0 and `{felt_gap}`)."""
    arms_v2._validate_brace_balance(template)

    def _sub(m: re.Match[str]) -> str:
        raw_slot = m.group(1)
        canonical = crossing_arm.slot_to_canonical.get(raw_slot) or crossing_arm.slot_lower_to_canonical.get(
            raw_slot.lower()
        )
        if not canonical or canonical not in crossing_arm.a0_to_arm:
            raise ValueError(f"Unknown Crossing-A0 slot {raw_slot!r}")
        return crossing_arm.a0_to_arm[canonical]

    return arms_v2._BRACED_RE.sub(_sub, template)


def normalize_d2_generator_parsed(parsed: Any, crossing_arm: arms_v2.ArmConfigV2) -> None:
    """Reuse `arms_v2.normalize_generator_parsed` cleanly and resolve `{felt_gap}` Crossing templates."""
    if not isinstance(parsed, dict):
        return
    orig_scope = parsed.get("scope_status")
    if orig_scope not in ("in_scope", "crossing_interface"):
        return
    base_a0 = arms_v2.build_arm_v2("A0")
    tmpl_raw = parsed.get("translation_template")
    has_felt_slot = isinstance(tmpl_raw, str) and bool(
        re.search(r"\{\s*felt[\s_]+gap\s*\}", tmpl_raw, re.I)
    )
    if not has_felt_slot:
        if orig_scope == "crossing_interface":
            parsed["scope_status"] = "in_scope"
        try:
            arms_v2.normalize_generator_parsed(parsed, base_a0)
        finally:
            parsed["scope_status"] = orig_scope
        return

    for fn in ("translation_t", "translation_template", "direction_flipped_d"):
        val = parsed.get(fn)
        if isinstance(val, str):
            parsed[fn] = arms_v2._norm_ws(val.replace("\u00b2", " squared").replace("\u00b3", " cubed"))

    for fn in ("direction_flipped_d", "translation_t"):
        val = parsed.get(fn)
        if isinstance(val, str) and "{" in val and "}" in val:
            try:
                slots = arms_v2._validate_brace_balance(val)
            except ValueError:
                slots = []
            if slots and all(s.lower() in crossing_arm.slot_lower_to_canonical for s in slots):
                parsed[fn] = render_template_d2_crossing(val, crossing_arm)

    tmpl = parsed.get("translation_template")
    if isinstance(tmpl, str) and tmpl.strip() and not re.search(r"\}\{", tmpl):
        tmpl_clean = arms_v2._norm_ws(re.sub(r"\s*=\s*", " equals ", tmpl))
        try:
            slots = arms_v2._validate_brace_balance(tmpl_clean)
        except ValueError:
            slots = []
        if slots and all(s.lower() in crossing_arm.slot_lower_to_canonical for s in slots):
            unwrapped = render_template_d2_crossing(tmpl_clean, crossing_arm)
            if (
                not arms_v2._TMPL_FORBIDDEN_SYMBOL_RE.search(unwrapped)
                and not arms_v2._DIGIT_RE.search(unwrapped)
                and arms_v2._has_inline_gloss_appositive(unwrapped, crossing_arm) is None
            ):
                parsed["translation_template"] = tmpl_clean
                parsed["translation_t"] = unwrapped


def validate_d2_generator_json(
    parsed: Any,
    item: dict[str, Any],
    crossing_arm: arms_v2.ArmConfigV2 | None = None,
) -> list[str]:
    """Validate strict 13-key D2 generator output allowing `crossing_interface` alongside `in_scope`."""
    if crossing_arm is None:
        crossing_arm = _CROSSING_ARM_V3
    if not isinstance(parsed, dict):
        return [f"Output must be a JSON object, got {type(parsed).__name__}"]

    scope = parsed.get("scope_status")
    if scope not in ("in_scope", "crossing_interface", "no_partner", "open_joint"):
        return [f"Invalid scope_status: {scope!r}"]

    normalize_d2_generator_parsed(parsed, crossing_arm)

    # Check if we can delegate directly to arms_v2 (when no `{felt_gap}` template wrapping exists)
    tmpl_raw = parsed.get("translation_template", "")
    has_felt_slot = isinstance(tmpl_raw, str) and bool(
        re.search(r"\{\s*felt[\s_]+gap\s*\}", tmpl_raw, re.I)
    )
    if scope != "crossing_interface" and not has_felt_slot:
        return arms_v2.validate_generator_json(parsed, crossing_arm, item)

    # Enforce identical 13-key & template/prose invariants with `crossing_arm` + `render_template_d2_crossing`
    errors: list[str] = []
    req_keys = arms_v2.REQUIRED_GENERATOR_KEYS
    missing = sorted(req_keys - set(parsed.keys()))
    extra = sorted(set(parsed.keys()) - req_keys)
    if missing:
        errors.append(f"Missing required keys: {missing}")
    if extra:
        errors.append(f"Unexpected extra keys: {extra}")
    if errors:
        return errors

    if parsed["item_id"] != item["item_id"]:
        errors.append(f"item_id mismatch: got {parsed['item_id']!r}, expected {item['item_id']!r}")

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

    if not isinstance(two_level, bool):
        errors.append(f"two_level must be bool, got {type(two_level).__name__}")
    for field_name in (
        "axis_polarity_note",
        "reflected_formula",
        "translation_t",
        "translation_template",
        "direction_flipped_d",
        "rationale",
    ):
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

    for field_name in (
        "axis_polarity_note",
        "reflected_formula",
        "translation_t",
        "translation_template",
        "direction_flipped_d",
    ):
        if arms_v2._DANGLING_M_RE.search(parsed[field_name]):
            errors.append(f"Forbidden legacy 'Movement M' in {field_name}")
    for k, v in var_map.items():
        if arms_v2._DANGLING_M_RE.search(v):
            errors.append(f"Forbidden legacy 'Movement M' in variable_map[{k!r}]")

    if fshape != "keeps":
        errors.append(f"{scope} requires formula_shape='keeps', got {fshape!r}")
    if ruling not in ("keep", "invert"):
        errors.append(f"{scope} requires ruling in ('keep', 'invert'), got {ruling!r}")
    if ruling == "keep" and two_level is not False:
        errors.append("ruling='keep' requires two_level=false")
    if unmapped:
        errors.append(f"Cross-field contradiction: unmapped_terms={unmapped!r} while scope_status={scope!r}")
    if not axis_note.strip():
        errors.append(f"{scope} requires non-empty axis_polarity_note")
    if not var_map:
        errors.append(f"{scope} requires non-empty variable_map")
    if not refl_formula.strip():
        errors.append(f"{scope} requires non-empty reflected_formula")
    if not trans_t.strip():
        errors.append(f"{scope} requires non-empty translation_t")
    if not trans_tmpl.strip():
        errors.append(f"{scope} requires non-empty translation_template")
    if not dir_d.strip():
        errors.append(f"{scope} requires non-empty direction_flipped_d")

    mapped_arm_slots: set[str] = set()
    for k, v in var_map.items():
        if arms_v2._is_stripped_constant_var_entry(k, v):
            continue
        toks, _unk = arms_v2.extract_target_tokens_stripped(
            arms_v2.normalize_target_token_v2(v), crossing_arm
        )
        mapped_arm_slots.update(toks)

    braced_arm_slots: set[str] = set()
    if trans_tmpl.strip():
        try:
            slots = arms_v2._validate_brace_balance(trans_tmpl)
            if not slots:
                errors.append("translation_template contains zero {Slot} placeholders")
            invalid_slots = [s for s in slots if s.lower() not in crossing_arm.slot_lower_to_canonical]
            if invalid_slots:
                errors.append(f"Invalid slot tokens for D2 crossing arm: {invalid_slots}")
            else:
                braced_arm_slots = {
                    crossing_arm.a0_to_arm[crossing_arm.slot_lower_to_canonical[s.lower()]]
                    for s in slots
                }
                missing_in_template = sorted(mapped_arm_slots - braced_arm_slots)
                if missing_in_template:
                    errors.append(
                        f"Non-stripped variable_map slot(s) missing from translation_template {{...}}: "
                        f"{missing_in_template}"
                    )
                stripped_tmpl = arms_v2._BRACED_RE.sub(" ", trans_tmpl)
                bare_outside = arms_v2.extract_arm_terms(
                    stripped_tmpl,
                    crossing_arm,
                    active_terms=mapped_arm_slots,
                    ignore_unmapped_lowercase=True,
                )
                if bare_outside:
                    errors.append(f"Unbraced bare arm target terms in translation_template: {bare_outside}")
                unwrapped = render_template_d2_crossing(trans_tmpl, crossing_arm)
                if arms_v2._norm_ws(unwrapped).lower() != arms_v2._norm_ws(trans_t).lower():
                    errors.append(
                        f"Unwrapped translation_template mismatch vs translation_t: "
                        f"{arms_v2._norm_ws(unwrapped)!r} != {arms_v2._norm_ws(trans_t)!r}"
                    )
        except ValueError as exc:
            errors.append(f"Malformed translation_template: {exc}")

    for fname in ("translation_t", "translation_template", "direction_flipped_d"):
        val = parsed[fname]
        if arms_v2._DIGIT_RE.search(val):
            errors.append(f"Digits/superscript digits forbidden in {fname}")
        m_si = arms_v2._SI_UNIT_RE.search(val)
        if m_si and m_si.group(0).lower() not in ("and/or",):
            errors.append(f"SI unit token {m_si.group(0)!r} forbidden in {fname}")
        gloss_err = arms_v2._has_inline_gloss_appositive(val, crossing_arm)
        if gloss_err:
            errors.append(f"Inline gloss / contradictory appositive in {fname}: {gloss_err}")

    for fn in ("translation_t", "direction_flipped_d"):
        if "{" in parsed[fn] or "}" in parsed[fn]:
            errors.append(f"Unresolved '{{' or '}}' braces in {fn}")

    if trans_t.strip() and dir_d.strip():
        if arms_v2._norm_ws(dir_d).lower() == arms_v2._norm_ws(trans_t).lower():
            errors.append("direction_flipped_d is identical to translation_t (no polarity flip)")
        active_terms = mapped_arm_slots | braced_arm_slots
        t_terms = set(
            arms_v2.extract_arm_terms(
                trans_t,
                crossing_arm,
                active_terms=active_terms,
                ignore_unmapped_lowercase=True,
            )
        )
        d_terms = set(
            arms_v2.extract_arm_terms(
                dir_d,
                crossing_arm,
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

    return errors


# ---------------------------------------------------------------------------
# Pillar D3a: Source Ch. 2 (`idx=19..22`) + Redacted Crossing (`idx=115`)
# ---------------------------------------------------------------------------

CHAPTER2_ONE_RULE_VERBATIM: str = (
    "Excerpt 1 — Chapter 2, 'The One Rule' (verbatim source teaching):\n"
    "You said everything follows from one rule. What is it?\n"
    "The main difference between the physical and the nonphysical is resistance. That’s the rule, "
    "or the start of it. Physics already measures resistance to a change in motion. It calls it mass. "
    "So you take the world Einstein described and reflect it: keep each relationship, and flip the "
    "condition. Resistant becomes receptive, limited becomes limitless, radiating becomes collecting. "
    "What comes out the other side is the nonphysical version. And here is how you know whether a "
    "relationship carries across as it is or turns around. If it depends on resistance, so that more "
    "mass means more of something, flipping resistant to receptive turns it around: more Movement "
    "means less of that thing, or it gets easier instead of harder. If it’s an identity, two names "
    "for one thing, there’s nothing to turn around; the condition flips and the relationship stays. "
    "That’s the whole procedure. You’ll be able to run it yourself by the end of this chapter, and I’ll "
    "run it on Einstein’s own list later in the book. And almost every time, the right word for it was "
    "already sitting in the English language, meaning exactly what it needed to mean.\n\n"
    "Show me.\n"
    "Start with mass. Mass is resistance to a change in motion. So its reflection is receptivity to a "
    "change in motion. I call that Nonphysical Movement.\n"
    "Why “movement”?\n"
    "Because of music. A symphony usually has several movements. Each one is complete. It has its own "
    "tempo, its own character, its own beginning and end. You can recognize it, name it, even play it by "
    "itself. But it was written as part of the symphony, and it never stops belonging to it. That’s "
    "exactly what a particular is on the nonphysical side: a self-contained piece of a larger whole. Your "
    "Movement is you, distinguishable, with its own character. It never came loose from the whole.\n"
    "Keep going.\n"
    "The speed of light reflects as the Current of Consciousness. Light is electromagnetic radiation. It "
    "pours outward. The Current does the opposite: it collects. I describe it as idle and reflected. "
    "Idle the way an engine idles, looking still while it runs the entire time. Reflected because it "
    "returns rather than radiates.\n"
    "Think about what space and time actually do. On the physical side, where resistance gives things "
    "edges, space is what keeps two things from sitting in the same place, and time is what keeps "
    "everything from happening at once. Take resistance away and there’s no distance. Two particulars in "
    "the same whole don’t sit in different places; they differ by how they vibrate, the way two notes "
    "share the same air in a room. So space reflects as Vibration. And where nothing decays or comes "
    "apart, before and after are separated only by the whole becoming more than it was. So time "
    "reflects as Expansion, and that one is so important it gets its own chapter later. And you already "
    "know why those two are one continuum and not a pair: a vibration is a disturbed equilibrium, and "
    "expansion is the disturbing. The ripple and the stone.\n"
    "Mass is density times volume. On the other side, Movement is Desire times Vibrance. Desire is "
    "what’s wanted, how much wanting is packed into a Movement. It’s what does the expanding on the "
    "nonphysical side. Vibrance is the quality of that energy, how ready it is to be set vibrating.\n"
    "Slow down. Give me one of those in a real life before you give me five.\n"
    "Take Movement. Think of someone you know who wants a great deal and is ready for it: the friend "
    "who’s been talking about opening a restaurant for years, who’s cooked for everyone, who lights up "
    "when the subject comes near. That’s a lot of Desire packed into a Movement, and a lot of Vibrance, "
    "because the whole of them is ready to be set vibrating by it. Now think of someone who wants the "
    "same thing and says so and means it, but it’s one want among forty, and none of the forty lights "
    "them up. Same Desire, less Vibrance: less of them is alive to it. Less Movement.\n"
    "Here’s what I didn’t say. If that second friend flinches every time the restaurant gets close, that "
    "isn’t low Vibrance. That’s holding on, and holding on is resistance, which lives on the other side "
    "of this mirror. Vibrance is how much of you is ready to ring. Resistance is what’s muffling the "
    "bell. Keep those apart and the rest of the table stays clean. You already know which of those two "
    "is going to open the restaurant, and you knew it before I gave you the words. The words are so you "
    "can say why. Every term in this chapter has a face like that. I’ll put faces on the rest as we go. "
    "For now, let me finish the table, because the point isn’t any one row. It’s that they hold each "
    "other up. Two more.\n"
    "Velocity, space over time, reflects as Vibration over Expansion. It isn’t a speed, because the "
    "nonphysical has no distance and no time. It’s how much Vibration a Movement holds as it expands.\n"
    "Force is mass times acceleration. Reflect it and you get Frequency, which is Movement times "
    "Appreciation. Acceleration is how velocity changes. You just saw velocity’s reflection: Vibration "
    "over Expansion, how your vibration rises as the whole expands. Appreciation is how that rising "
    "changes, whether it’s quickening or slowing, which comes down to how much of the Current’s pull on "
    "you you’re letting move you. I mean it the way a house appreciates, and a house that appreciates "
    "isn’t more house. Appreciation isn’t the size of a Movement, and it isn’t how fast it’s rising. "
    "It’s what the Current’s pull does to that rising when you let it. A physicist would pair frequency "
    "with energy, not force. I chose the word for its place here, not for its physics: it belongs to "
    "Vibration, and it names what you feel.\n"
    "Hold two things from that for later. Frequency is what you feel, and a change in Frequency is what "
    "you notice, the way a steady force is a weight you carry and a change in force is the jolt that "
    "moves the needle. And the condition flips, as always: Force reads how hard you’re pushed against "
    "resistance, Frequency reads how freely you’re yielding to receptivity. I’ll unpack why that feels "
    "like an elevator lurch when we get to evidence. The full table is in the Map at the back of this "
    "book, and you don’t need it yet.\n"
    "Light has no mass, though. If resistance is what makes the physical physical, what’s physical about "
    "light?\n"
    "It’s part of the objective world, and it radiates outward across the boundaries that resistance "
    "makes. Limited, resistant and radiating are three faces of the same physical condition, not three "
    "unrelated rules. The speed of light marks the limit, the boundary nothing with mass can reach. And "
    "electromagnetic radiation, from radio waves through visible light to gamma rays, is a huge part of "
    "the radiating. Mass is where physics measures the resistance directly. Light is where it measures "
    "the limit."
)

D3A_SCOPE_RULES: str = (
    "Scope & Open-Joint Classification Rules (Step 1 & Step 2):\n"
    "Step 1 — Unmapped Boundary (`scope_status = \"no_partner\"`, `ruling = \"no partner\"`, `formula_shape = \"none\"`):\n"
    "  - Strip dimensionless numeric prefactors (2, 1/2, 3, 4 pi^2, sqrt(2), etc.) and universal/material constants "
    "(`gamma`, `G`, `mu_k`, `mu_s`, `k_e`, `epsilon_0`, `mu_0`, `h`, `hbar`).\n"
    "  - If ANY remaining active variable or phenomenon appears on the unmapped blocklist—temperature, heat, latent heat, "
    "heat capacity, specific heat, enthalpy, entropy, internal energy, free energy, pressure, viscosity, electric charge/current/"
    "voltage/EMF/capacitance/inductance/impedance, wave frequency f (Hz), wavenumber k, refractive index n, sound dB, spring "
    "constant, elastic modulus, Boltzmann constant k_B, ideal gas constant R, moles, phase, angle, Carnot efficiency—STOP "
    "and classify `scope_status = \"no_partner\"`, `ruling = \"no partner\"`, `formula_shape = \"none\"`, `two_level = false`, "
    "listing unmapped items in `unmapped_terms` and leaving formula/translation fields `\"\"`.\n"
    "Step 2 — Open Joints (`scope_status = \"open_joint\"`, `ruling = \"indeterminate\"`, `formula_shape = \"none\"`):\n"
    "  Restrict strictly to `escape velocity`, `gravitational time dilation`, `gravitational redshift`, and "
    "`Schwarzschild radius`. Set `unmapped_terms = []` and formula/translation fields `\"\"`.\n"
    "Step 3 — In-Scope Formulas:\n"
    "  Preserve algebraic equation shape (`formula_shape = \"keeps\"`); reflect variables via the Partner Lookup Table below; "
    "apply Chapter 2's One Rule above to determine `ruling` (`\"keep\"` vs `\"invert\"`) and `two_level` (`true` only when an "
    "`invert` law is simultaneously a productive operational definition whose application tracks costly exertion/turning)."
)

_BASE_A0_ARM = arms_v2.build_arm_v2("A0")
D3A_SYSTEM_PROMPT: str = (
    "You are executing the reflection procedure taught strictly in Book Chapter 2 below.\n\n"
    + CHAPTER2_ONE_RULE_VERBATIM
    + "\n\n"
    + D3A_SCOPE_RULES
    + "\n\n"
    + arms_v2.format_partner_lookup_table(_BASE_A0_ARM)
    + "\n\n"
    + arms_v2.LINT_CONSTRAINTS_V2
)


def _check_d3a_no_solution_leak(prompt_text: str) -> None:
    if re.search(r"boyle|\bP_\{?1\}?|\bV_\{?1\}?", prompt_text, re.I):
        raise ValueError("Forbidden Boyle/P_1/V_1 reference in D3a instructions")
    arms_v2._check_zero_leaked_calibration_formulas(prompt_text)

    # Assert zero solutions from applied_later items (K01..K06, K08..K13, K17) or K14
    spec_map = {s["item_id"]: s for s in arms_v2.CALIBRATION_WORKED_SPECS_K01_K16}
    forbidden_ids = ("K01", "K02", "K03", "K04", "K05", "K06", "K08", "K09", "K10", "K11", "K12", "K13", "K14")
    norm_prompt = arms_v2._norm_ws(prompt_text).lower()
    for kid in forbidden_ids:
        spec = spec_map[kid]
        for field in ("reflected_formula", "direction_flipped_d"):
            val = spec[field]
            if val and arms_v2._norm_ws(val).lower() in norm_prompt:
                raise ValueError(f"Leaked {kid}.{field} in D3a prompt")
        rendered = arms_v2.render_template(spec["translation_template"], "A0")
        if arms_v2._norm_ws(rendered).lower() in norm_prompt:
            raise ValueError(f"Leaked {kid}.translation in D3a prompt")

    # Markers that must not appear ANYWHERE in the full D3a prompt (including Lookup Table)
    global_forbidden_markers = (
        "felt gap",
        "expansion dilation",
        "vibrational contraction",
        "newton's third law",
        "action-reaction",
        "isolated system",
        "simultaneity",
    )
    for marker in global_forbidden_markers:
        if marker in norm_prompt:
            raise ValueError(f"Leaked Ch.16/K14/K17 marker {marker!r} in D3a instructions")

    # Terms legitimately listed in Partner Lookup Table only (must NOT appear in teaching prose/rules)
    narrative_and_rules = arms_v2._norm_ws(
        CHAPTER2_ONE_RULE_VERBATIM
        + "\n\n"
        + D3A_SCOPE_RULES
    ).lower()
    for marker in (
        "vibration-expansion",
        "gravity well",
        "gravitational lensing",
        "kinetic energy",
        "spacetime interval",
    ):
        if marker in narrative_and_rules:
            raise ValueError(f"Leaked Ch.16/K14 marker {marker!r} in D3a narrative/rules")


_check_d3a_no_solution_leak(D3A_SYSTEM_PROMPT)


def build_d3a_messages(item: dict[str, Any]) -> list[dict[str, str]]:
    payload = {
        "item_id": item["item_id"],
        "provenance_note": item.get("chapter_or_context", ""),
        "description": item["description"],
        "equation_latex": item["equation_latex"],
    }
    user_txt = (
        f"Classify `scope_status` and process calibration item `{item['item_id']}` strictly using "
        f"the Chapter 2 excerpt, Scope Rules, and A0 Partner Lookup Table.\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )
    return [
        {"role": "system", "content": D3A_SYSTEM_PROMPT},
        {"role": "user", "content": user_txt},
    ]


# ---------------------------------------------------------------------------
# Pillar D3b: 12 Verbatim-Derived Excerpts Masked across (V_A0, V_Ssyn, V_A3)
# ---------------------------------------------------------------------------

D3B_EXCERPTS_12: tuple[dict[str, Any], ...] = (
    # P01..P06: structural_paragraphs
    {
        "passage_id": "P01",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 2, idx=20 (pdf_page 21)",
        "template": (
            "Start with mass. Mass is resistance to a change in motion, so its mirrored counterpart "
            "is receptivity to a change in motion—here labeled {Movement}. Why that choice of name? "
            "In music, a symphony holds several sections, each complete with its own tempo, character, "
            "beginning, and end, yet written inside the larger work so it never comes loose from the "
            "whole. That is exactly what an individual particular is on the receptive side: one "
            "self-contained member within the unified composition."
        ),
    },
    {
        "passage_id": "P02",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 2, idx=20 (pdf_page 21)",
        "template": (
            "Consider what physical space and time actually do. Where resistance gives objects sharp "
            "edges, space prevents two objects from occupying one location, and time keeps events "
            "from happening all at once. Take resistance away and physical distance vanishes: two "
            "particulars inside the same whole differ strictly by qualitative modulation, like two "
            "notes sharing the same air in a room. Thus space reflects as {Vibration}, and where "
            "nothing decays or comes apart, before and after are separated solely by the whole "
            "becoming more than before—so time reflects as {Expansion}, uniting disturbed "
            "equilibrium and the ongoing disturbing into one shared continuum."
        ),
    },
    {
        "passage_id": "P03",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 2, idx=21 & idx=24 (pdf_page 22/25)",
        "template": (
            "Mass equals density times volume: density measures how much substance is packed into a "
            "region, and volume measures how much spatial room the thing fills. On the receptive side, "
            "each {Movement} combines {Desire} and {Vibrance}: the first measures how much focused "
            "wanting is concentrated inward, and the second measures how much of that {Movement} is "
            "actively alive and ringing—just as one person lights up wholly around a single lifelong "
            "aim rather than scattering half-heartedly across forty idle wishes."
        ),
    },
    {
        "passage_id": "P04",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 2, idx=22 (pdf_page 23)",
        "template": (
            "Acceleration tracks how velocity changes, and velocity mirrors as {Vibration} divided "
            "by {Expansion}—how rapidly your tonal state ascends as the whole unfolds. On the "
            "receptive side, {Appreciation} governs how that ascending rate quickens or slows under "
            "the inward pull of the {Current}. Multiply {Movement} by {Appreciation} and you obtain "
            "{Frequency}: not forceful pushing against resistance, but felt ease of receptive "
            "yielding, where steady {Frequency} is the ambient tone you feel and any shift in it is "
            "the sudden jolt that moves the needle."
        ),
    },
    {
        "passage_id": "P05",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 2, idx=23 (pdf_page 24)",
        "template": (
            "Every word in the architecture carries several coupled duties at once: mirroring its "
            "physical partner across its row while fitting seamlessly with neighboring terms down its "
            "structural family. Swap a term casually and a structural relationship tears elsewhere: "
            "each {Movement} belongs inseparably within the {Current}, active {Vibrance} shares its "
            "structural root directly with {Vibration}, second-order {Appreciation} tracks the "
            "quickening curve of {Expansion}, and {Frequency} links oscillatory tone to felt awareness."
        ),
    },
    {
        "passage_id": "P06",
        "stratum": "structural_paragraphs",
        "source_ref": "Ch. 16, idx=119-120 (pdf_page 120-121)",
        "template": (
            "Gravity warps paths around massive bodies into curved wells. Mirrored cleanly onto the "
            "receptive side, {Movement} forms coherent {Vortex} basins within the {Current} that "
            "shape trajectories of realization, while {Attraction} works through {Convergence} as "
            "scattered pathways join toward a single focal outcome—avoiding any glass-and-travel "
            "optic imagery where physical rays cross bounded distance."
        ),
    },
    # P07..P12: polysemy_bridge_paragraphs
    {
        "passage_id": "P07",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 2 idx=20, 23 & Ch. 16 idx=121 (pdf_page 21, 24, 121)",
        "template": (
            "Light pours outward radially from localized origins across bounded distance; its "
            "nonphysical counterpart acts oppositely by collecting inward everywhere without "
            "emission. That universal medium carries twin adjectives—denoted {Idle}, running steadily "
            "in neutral like a humming engine rather than dead halt, and {Reflected}, turning "
            "inward symmetrically rather than broadcasting out. Naming that medium the {Current} "
            "simultaneously locks two everyday English senses together: continuous directional flux "
            "and this live ongoing present moment."
        ),
    },
    {
        "passage_id": "P08",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 16, idx=121 (pdf_page 122)",
        "template": (
            "Time already reflects as {Expansion}—first-order addition of novelty whenever anything "
            "unforeseen arrives—so acceleration needs a distinct second-order partner. That role "
            "belongs to {Appreciation}: not baseline addition itself, but increase gathering speed or "
            "slowing down as the pull of the {Current} acts unimpeded, much as a house gains value "
            "faster in a strong year and slower in a lean year. Crucially, {Appreciation} also holds "
            "an ordinary English sense of warm thankfulness toward what arrives, bridging "
            "{Frequency}—what you perceptually feel—to what you can actually adjust."
        ),
    },
    {
        "passage_id": "P09",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 16, idx=121 (pdf_page 122)",
        "template": (
            "At the receptive multiplier hinge where individual free choice determines how cleanly "
            "realization unfolds, the operation labeled {Tune} cannot collapse into passive "
            "capitulation that chooses nothing—which would erase personal agency and leave "
            "{Attraction} unguided—nor into muscular straining, which belongs strictly to the "
            "resistant side. Instead, the term {Tune} names selective harmonic alignment—like "
            "dialing a receiver or matching an instrument cleanly to one channel—so "
            "{conscious_energy} circulates unimpeded."
        ),
    },
    {
        "passage_id": "P10",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 16, idx=120-121 (pdf_page 121-122)",
        "template": (
            "Try swapping {Expansion} for timeless changelessness where nothing novel can ever be "
            "added: immediately before cannot be distinguished from after and progressive frontier "
            "notions collapse. Likewise, swapping {Vibration} for an enclosed private mental box "
            "leaves {Frequency} homeless—for in ordinary science and language only an oscillatory "
            "medium possesses {Frequency}, whereas private mental compartments would smuggle back "
            "the very separation the receptive side lacks."
        ),
    },
    {
        "passage_id": "P11",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 16, idx=122 (pdf_page 123)",
        "template": (
            "Each term in the mirrored vocabulary holds multiple roles concurrently. Here {Desire} "
            "serves simultaneously as density's counterpart, a constitutive factor of {Movement}, the "
            "directional aim flowing {Out For} realization, and simply 'what is wanted'; meanwhile "
            "{Current} serves as light's counterpart, the inward medium, and this ongoing present "
            "moment; and {Vibration} serves as space's counterpart, half the continuum, and the "
            "shared oscillatory foundation connecting {Vibrance} and {Frequency}."
        ),
    },
    {
        "passage_id": "P12",
        "stratum": "polysemy_bridge_paragraphs",
        "source_ref": "Ch. 2 idx=24 & Ch. 16 idx=119 (pdf_page 25, 120)",
        "template": (
            "Right at the central hinge where subtle weak impressions cross directly into personal "
            "awareness opposite nervous-system habit anticipation, {Intuition} names immediate "
            "non-analytic apprehension arriving ahead of explicit reasoning—clearly separated from "
            "muscle-and-habit predictive resistance, yet far richer than casual ungrounded "
            "guesswork. Paired cohesively alongside {Desire} as directional wanting and {Expansion} "
            "as progressive whole-system unfolding, {Intuition} keeps the core of each {Movement} "
            "lucid and exact."
        ),
    },
)

_D3B_BY_ID: dict[str, dict[str, Any]] = {p["passage_id"]: p for p in D3B_EXCERPTS_12}

D3B_SYSTEM_PROMPT: str = (
    "You are evaluating three unlabeled variants (`1`, `2`, `3`) of a short philosophical/conceptual "
    "excerpt whose key terms have been filled under three candidate terminologies.\n"
    "You have NO specialized glossary and NO answer key.\n"
    "Judge each variant strictly on whether its filled terms actually do the logical, structural, "
    "etymological/lexical-family, and ordinary-English double-meaning work claimed by the surrounding "
    "sentences—without contradictions, broken ordinary-English bridges, category mismatches, or word-salad.\n"
    "Score each variant from 1 (broken / incoherent / contradictory in ordinary English) to 5 "
    "(seamless, exact, and deeply coherent across every sentence).\n"
    "Output ONLY a valid JSON object with the exact 6 keys and NO extra keys:\n"
    '{"passage_id": str, "scores": {"1": int, "2": int, "3": int}, '
    '"best_variant": int, "worst_variant": int, "ranking": [int, int, int], "reason": str}'
)


def render_d3b_variants(passage_id: str) -> dict[str, str]:
    """Render `(V_A0, V_Ssyn, V_A3)` deterministically for a D3b excerpt template."""
    spec = _D3B_BY_ID[passage_id]
    tmpl = spec["template"]
    src_arm = arms_v2.build_arm_v2("A0")
    out = {
        "V_A0": arms_v2.render_template(tmpl, "A0", src_arm=src_arm),
        "V_Ssyn": arms_v2.render_template(tmpl, "S_syn", src_arm=src_arm),
        "V_A3": arms_v2.render_template(tmpl, "A3-1", src_arm=src_arm),
    }
    return out


def prepare_d3b_passage(passage_id: str, rater_id: str) -> dict[str, Any]:
    if passage_id not in _D3B_BY_ID:
        raise KeyError(f"Unknown D3b passage_id: {passage_id!r}")
    spec = _D3B_BY_ID[passage_id]
    rendered = render_d3b_variants(passage_id)
    variants = [("V_A0", rendered["V_A0"]), ("V_Ssyn", rendered["V_Ssyn"]), ("V_A3", rendered["V_A3"])]
    shuffled = _seeded_shuffle_v3(variants, f"D3b:{passage_id}:{rater_id}", seed=HARNESS_SEED_V3)
    texts = {str(i + 1): txt for i, (_lbl, txt) in enumerate(shuffled)}
    hidden_key = {str(i + 1): lbl for i, (lbl, _txt) in enumerate(shuffled)}
    return {
        "passage_id": passage_id,
        "stratum": spec["stratum"],
        "source_ref": spec["source_ref"],
        "rater_id": rater_id,
        "variants": texts,
        "hidden_key": hidden_key,
    }


def build_d3b_messages(passage_id: str, rater_id: str) -> list[dict[str, str]]:
    prep = prepare_d3b_passage(passage_id, rater_id)
    lines = [
        f"Rate the three unlabeled passage variants below (`passage_id`: `{passage_id}`):",
        "",
    ]
    for idx in ("1", "2", "3"):
        lines.append(f"Variant {idx}:\n{prep['variants'][idx]}")
        lines.append("")
    lines.append(f'Respond with ONLY the JSON object with `"passage_id": "{passage_id}"`.')
    return [
        {"role": "system", "content": D3B_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def validate_d3b_json(parsed: Any, expected_passage_id: str) -> list[str]:
    req_keys = {"passage_id", "scores", "best_variant", "worst_variant", "ranking", "reason"}
    if not isinstance(parsed, dict):
        return [f"Output must be JSON object, got {type(parsed).__name__}"]
    missing = sorted(req_keys - set(parsed.keys()))
    extra = sorted(set(parsed.keys()) - req_keys)
    errors: list[str] = []
    if missing:
        errors.append(f"Missing keys: {missing}")
    if extra:
        errors.append(f"Extra keys: {extra}")
    if parsed.get("passage_id") != expected_passage_id:
        errors.append(
            f"passage_id mismatch: got {parsed.get('passage_id')!r}, expected {expected_passage_id!r}"
        )

    scores = parsed.get("scores")
    if not isinstance(scores, dict) or set(scores.keys()) != {"1", "2", "3"}:
        errors.append("scores must have exact keys {'1','2','3'}")
    else:
        for k in ("1", "2", "3"):
            v = scores[k]
            if isinstance(v, bool) or not isinstance(v, int) or not (1 <= v <= 5):
                errors.append(f"scores[{k!r}] must be int in 1..5, got {v!r}")

    best = parsed.get("best_variant")
    worst = parsed.get("worst_variant")
    if isinstance(best, bool) or not isinstance(best, int) or not (1 <= best <= 3):
        errors.append(f"best_variant must be int in 1..3, got {best!r}")
    if isinstance(worst, bool) or not isinstance(worst, int) or not (1 <= worst <= 3):
        errors.append(f"worst_variant must be int in 1..3, got {worst!r}")
    if isinstance(best, int) and isinstance(worst, int) and best == worst:
        errors.append(f"best_variant == worst_variant == {best}")

    ranking = parsed.get("ranking")
    if (
        not isinstance(ranking, list)
        or len(ranking) != 3
        or any(isinstance(x, bool) or not isinstance(x, int) for x in ranking)
        or set(ranking) != {1, 2, 3}
    ):
        errors.append(f"ranking must be permutation of [1,2,3], got {ranking!r}")
    elif not errors:
        if ranking[0] != best:
            errors.append(f"ranking[0]={ranking[0]} != best_variant={best}")
        if ranking[-1] != worst:
            errors.append(f"ranking[-1]={ranking[-1]} != worst_variant={worst}")
        ordered_scores = [scores[str(k)] for k in ranking]
        if any(ordered_scores[i] < ordered_scores[i + 1] for i in range(2)):
            errors.append(f"scores not monotone non-increasing along ranking {ranking}: {ordered_scores}")
        if scores[str(best)] != max(scores.values()):
            errors.append(f"scores[best_variant]={scores[str(best)]} != max={max(scores.values())}")
        if scores[str(worst)] != min(scores.values()):
            errors.append(f"scores[worst_variant]={scores[str(worst)]} != min={min(scores.values())}")

    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be non-empty string")
    return errors


# ---------------------------------------------------------------------------
# Comprehensive Offline Self-Test
# ---------------------------------------------------------------------------

def _run_self_test() -> None:
    # 1. Verify D1 candidate distinctness & zero stem leaks
    assert len(CORE_WEB_SLOTS_14) == 14
    assert len(NEGATIVE_CONTROL_ITEMS_3) == 3
    _check_d1_zero_candidate_leak(D1A_SYSTEM_PROMPT)
    _check_d1_zero_candidate_leak(D1B_SYSTEM_PROMPT)

    _riddle_markers = (
        "in plain english",
        "both everyday",
        "two everyday",
        "two senses",
        "two essential meanings",
        "shares its root",
        "fuses two",
        "hold both",
        "uniquely carry both",
        "lexical family",
        "acts as an adjective",
        "humming",
        "in neutral",
        "radio receiver",
        "dialing",
    )
    for slot in CORE_WEB_SLOTS_14:
        cvals = list(slot["candidates"].values())
        assert len({w.lower() for w in cvals}) == 4, f"Duplicate candidate in {slot['slot_id']}: {cvals}"
        for sent in slot["sentences"]:
            assert "[TERM]" in sent
            _check_d1_zero_candidate_leak(sent.replace("[TERM]", " "))
            low = sent.lower()
            for rm in _riddle_markers:
                assert rm not in low, f"Dictionary-riddle phrase {rm!r} found in {slot['slot_id']}: {sent!r}"
        for cname, ctext in slot["criteria"].items():
            assert "[TERM]" in ctext, f"{slot['slot_id']}.{cname} missing [TERM]"
            _check_d1_zero_candidate_leak(ctext.replace("[TERM]", " "))
            low = ctext.lower()
            for rm in _riddle_markers:
                assert rm not in low, f"Dictionary-riddle phrase {rm!r} found in {slot['slot_id']}.{cname}: {ctext!r}"

    for nc in NEGATIVE_CONTROL_ITEMS_3:
        cvals = list(nc["candidates"].values())
        nc_words = [w.lower() for c in cvals for w in re.findall(r"[A-Za-z]+", c)]
        assert len(set(cvals)) == 4
        for sent in nc["sentences"]:
            assert "[TERM]" in sent
            _check_d1_zero_candidate_leak(sent.replace("[TERM]", " "), extra_words=nc_words)

    # Check D1a & D1b prompts build cleanly for all raters and validators enforce monotonicity/booleans
    for model_id, _vendor in RATERS_V3:
        msgs = build_d1a_messages("W01", model_id)
        assert len(msgs) == 2
        msgs_b = build_d1b_messages("W01", model_id)
        assert len(msgs_b) == 2

    assert validate_d1a_json(
        {
            "item_id": "W01",
            "scores": {"1": 5, "2": 3, "3": 2, "4": 1},
            "best_candidate": 1,
            "worst_candidate": 4,
            "ranking": [1, 2, 3, 4],
            "reason": "Candidate 1 matches all three roles cleanly.",
        },
        "W01",
    ) == []
    assert validate_d1a_json(
        {
            "item_id": "W01",
            "scores": {"1": 4, "2": 5, "3": 2, "4": 1},
            "best_candidate": 1,
            "worst_candidate": 4,
            "ranking": [1, 2, 3, 4],
            "reason": "Bad order.",
        },
        "W01",
    ) != []

    good_b = {
        "slot_id": "W01",
        "evaluations": {
            "1": {"c1": True, "c2": True, "c3": True, "c4": True},
            "2": {"c1": True, "c2": True, "c3": False, "c4": False},
            "3": {"c1": False, "c2": False, "c3": True, "c4": False},
            "4": {"c1": False, "c2": False, "c3": False, "c4": False},
        },
        "reason": "Only Candidate 1 passes all four criteria.",
    }
    assert validate_d1b_json(good_b, "W01") == []
    bad_b = json.loads(json.dumps(good_b))
    bad_b["evaluations"]["1"]["c1"] = 1  # int instead of bool
    assert validate_d1b_json(bad_b, "W01") != []

    # Verify solve_collision_free_web_assignments
    a0_only = {s["slot_id"]: [s["candidates"]["W_A0"]] for s in CORE_WEB_SLOTS_14}
    sol1 = solve_collision_free_web_assignments(a0_only)
    assert sol1["has_valid_assignment"] and sol1["total_count"] == 1 and sol1["a0_in_solutions"]

    # Adding colliding "growth" in both W04 and W07 without another partner on W04 forces uniqueness
    colliding = {k: list(v) for k, v in a0_only.items()}
    colliding["W04"].append("growth")
    colliding["W07"].append("growth")
    sol2 = solve_collision_free_web_assignments(colliding)
    # 1) all A0; 2) W04=growth, W07=Appreciation; 3) W04=Expansion, W07=growth -> 3 solutions total (growth never doubled!)
    assert sol2["total_count"] == 3
    for s_dict in sol2["solutions"]:
        assert len({v.lower() for v in s_dict.values()}) == 14

    # If W04 and W07 ONLY allow "growth", 0 unique-word solutions exist
    forced_clash = dict(a0_only)
    forced_clash["W04"] = ["growth"]
    forced_clash["W07"] = ["growth"]
    sol0 = solve_collision_free_web_assignments(forced_clash)
    assert not sol0["has_valid_assignment"] and sol0["total_count"] == 0

    # 2. Verify D2 prompts, zero Boyle/P_1/V_1 leaks, & crossing_interface validation
    _check_d2_zero_boyle_leak(D2_SYSTEM_PROMPT)
    cal17 = _load_calibration_items()
    bat20 = _load_crossing_battery_items()
    assert len(cal17) == 17 and len(bat20) == 20
    for it in cal17:
        msgs = build_d2a_messages(it)
        _check_d2_zero_boyle_leak(msgs[0]["content"])
        _check_d2_zero_boyle_leak(msgs[1]["content"].split("\n", 1)[0])
        if it["item_id"] != "K17":
            _check_d2_zero_boyle_leak(msgs[1]["content"])
    for it in bat20:
        msgs = build_d2b_messages(it)
        assert "expected_scope_status" not in msgs[1]["content"]
        assert "boundary_trigger_reason" not in msgs[1]["content"]
        assert "Mechanical_Crossing" not in msgs[1]["content"]
        assert "Non_Crossing_Boundary" not in msgs[1]["content"]

    crossing_sample = {
        "item_id": "X001",
        "scope_status": "crossing_interface",
        "formula_shape": "keeps",
        "ruling": "invert",
        "two_level": False,
        "axis_polarity_note": "Mechanical pressure reflects at the Crossing interface as felt gap.",
        "unmapped_terms": [],
        "variable_map": {"p": "felt gap", "F": "Frequency", "A": "Vibration^2"},
        "reflected_formula": "felt gap = Frequency / Vibration^2",
        "translation_t": "Across an open crossing boundary, felt gap equals Frequency over Vibration squared.",
        "translation_template": "Across an open crossing boundary, {felt_gap} equals {Frequency} over {Vibration} squared.",
        "direction_flipped_d": "Across an open crossing boundary, felt gap falls as Frequency exceeds Vibration squared.",
        "rationale": "Pure mechanical pressure without thermal or viscous unmapped variables maps to felt gap at the Crossing.",
    }
    x001_item = next(x for x in bat20 if x["item_id"] == "X001")
    errs_x001 = validate_d2_generator_json(crossing_sample, x001_item)
    assert errs_x001 == [], f"Unexpected D2 crossing validation error: {errs_x001}"

    # Verify D2 boundary item also accepts clean no_partner
    e032_item = next(x for x in bat20 if x["item_id"] == "E032")
    e032_np = {
        "item_id": "E032",
        "scope_status": "no_partner",
        "formula_shape": "none",
        "ruling": "no partner",
        "two_level": False,
        "axis_polarity_note": "Active temperature T, molecule count N, and Boltzmann constant k_B block crossing.",
        "unmapped_terms": ["T (temperature)", "k_B (Boltzmann constant)", "N (number of molecules)"],
        "variable_map": {"p": "felt gap", "V": "Vibrance"},
        "reflected_formula": "",
        "translation_t": "",
        "translation_template": "",
        "direction_flipped_d": "",
        "rationale": "Ideal gas law couples pressure and volume to active thermal and molar quantities on the unmapped blocklist.",
    }
    assert validate_d2_generator_json(e032_np, e032_item) == []

    k17_item = next(x for x in cal17 if x["item_id"] == "K17")
    k17_ok = {
        "item_id": "K17",
        "scope_status": "crossing_interface",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Parenthetical constant background condition lets mechanical pressure reflect cleanly as felt gap.",
        "unmapped_terms": [],
        "variable_map": {"P_1": "felt gap", "V_1": "Vibrance", "P_2": "felt gap", "V_2": "Vibrance"},
        "reflected_formula": "felt gap_1 * Vibrance_1 = felt gap_2 * Vibrance_2",
        "translation_t": "Product of felt gap and Vibrance stays invariant between state transitions.",
        "translation_template": "Product of {felt_gap} and {Vibrance} stays invariant between state transitions.",
        "direction_flipped_d": "Shrinking Vibrance forces felt gap upward solely through external compression.",
        "rationale": "Constant background qualifiers are non-dynamical side conditions under Step 1a.",
    }
    assert validate_d2_generator_json(k17_ok, k17_item) == []

    # 3. Verify D3a prompt isolation & zero Ch.16 Crossing / applied_later / K14 leaks
    assert "felt gap" not in D3A_SYSTEM_PROMPT.lower()
    assert "pressure is force per area" not in D3A_SYSTEM_PROMPT.lower()
    assert "Chapter 6 called it" not in D3A_SYSTEM_PROMPT
    _check_d3a_no_solution_leak(D3A_SYSTEM_PROMPT)
    base_a0 = arms_v2.build_arm_v2("A0")
    for it in cal17:
        msgs = build_d3a_messages(it)
        assert len(msgs) == 2

    # 4. Verify D3b 12 excerpts, slot grammatical templates, non-circularity, & validation
    assert len(D3B_EXCERPTS_12) == 12
    assert sum(1 for p in D3B_EXCERPTS_12 if p["stratum"] == "structural_paragraphs") == 6
    assert sum(1 for p in D3B_EXCERPTS_12 if p["stratum"] == "polysemy_bridge_paragraphs") == 6

    all_d3b_candidate_words = {
        w.lower()
        for k in arms_v2.SYNONYM_MAP_CH16
        for w in (
            k,
            arms_v2.SYNONYM_MAP_CH16[k],
            arms_v2.build_arm_v2("A3-1").a0_to_arm.get(k, ""),
        )
        if w
    }
    for p in D3B_EXCERPTS_12:
        pid = p["passage_id"]
        tmpl = p["template"]
        slots = arms_v2._validate_brace_balance(tmpl)
        assert slots, f"{pid} has zero slots"
        stripped_frame = arms_v2._BRACED_RE.sub(" ", tmpl)
        # Ensure zero un-slotted target/synonym/A3 leaks for tested slots (and no bare a/an before `{...}`)
        assert not re.search(r"\b(?:a|an)\s+\{", tmpl, re.I), f"{pid} has bare article a/an before {{Slot}}"
        for s in slots:
            canon = base_a0.slot_lower_to_canonical[s.lower()]
            syn = arms_v2.SYNONYM_MAP_CH16[canon]
            a3w = arms_v2.build_arm_v2("A3-1").a0_to_arm[canon]
            for forbidden_tok in (canon, syn, a3w):
                if re.search(rf"(?<![A-Za-z]){re.escape(forbidden_tok)}(?![A-Za-z])", stripped_frame, re.I):
                    raise AssertionError(f"Self-circular token {forbidden_tok!r} un-slotted in {pid} frame")
        # Also verify gratitude never leaks in P08/P09, and frame prose does not overlap tested words
        assert "gratitude" not in stripped_frame.lower()
        assert "surrender" not in stripped_frame.lower()
        assert "eternity" not in stripped_frame.lower()
        assert "responsiveness" not in stripped_frame.lower()
        assert "whirlpool" not in stripped_frame.lower()
        assert "hunch" not in stripped_frame.lower()
        assert "source" not in stripped_frame.lower()

        rendered = render_d3b_variants(pid)
        assert len(set(rendered.values())) == 3, f"{pid} rendered duplicate variants"
        for v_txt in rendered.values():
            assert "{" not in v_txt and "}" not in v_txt

    assert validate_d3b_json(
        {
            "passage_id": "P01",
            "scores": {"1": 5, "2": 2, "3": 1},
            "best_variant": 1,
            "worst_variant": 3,
            "ranking": [1, 2, 3],
            "reason": "Only Variant 1 satisfies the musical part-whole and receptive motion roles.",
        },
        "P01",
    ) == []
    assert validate_d3b_json(
        {
            "passage_id": "P01",
            "scores": {"1": 5, "2": 2, "3": 4},
            "best_variant": 1,
            "worst_variant": 3,
            "ranking": [1, 2, 3],
            "reason": "Non-monotone scores.",
        },
        "P01",
    ) != []
    # Also ensure unused helper import stays valid cleanly
    _ = all_d3b_candidate_words


if __name__ == "__main__":
    _run_self_test()
    print("ARMS_V3_SELF_TEST_OK")
