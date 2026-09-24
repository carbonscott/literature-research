"""
Plain-assert tests for taxonomy.py (v2).  Run:  /usr/bin/python3 test_taxonomy.py

Each positive case is a realistic hand-written title (sometimes with a short
abstract fragment). Expectations are SUBSETS: the classifier must return at
least the listed clusters / methods / families; `not_*` lists must be absent.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import taxonomy as tx  # noqa: E402


POSITIVE_CASES = [
    # --- nickelates ---
    {"text": "Signatures of superconductivity near 80 K in a nickelate under pressure: La$_3$Ni$_2$O$_{7-\\delta}$ single crystals studied by resistivity and $\\mu$SR",
     "clusters": ["nickelate_sc"], "primary": "nickelate_sc",
     "methods": ["musr", "magnetotransport_hall", "high_pressure_dac"],
     "families": ["nickelates_bilayer_trilayer_rp"]},
    {"text": "Ambient-pressure superconductivity onset above 40 K in (La,Pr)_3Ni_2O_7 thin films grown by pulsed laser deposition",
     "clusters": ["nickelate_sc"], "primary": "nickelate_sc",
     "methods": ["thin_film_growth_mbe"], "families": ["nickelates_bilayer_trilayer_rp"]},
    {"text": "Electronic structure of the infinite-layer nickelate Nd0.8Sr0.2NiO2 from DFT+DMFT",
     "clusters": ["nickelate_sc"], "methods": ["dmft", "dft_first_principles"],
     "families": ["nickelates_infinite_layer"]},
    {"text": "Density-wave order in trilayer La₄Ni₃O₁₀ probed by resonant inelastic x-ray scattering",
     "clusters": ["nickelate_sc"], "methods": ["rixs_resonant_xray"],
     "families": ["nickelates_bilayer_trilayer_rp"]},
    # --- cuprates ---
    {"text": "Charge density wave and pair density wave in the cuprate Bi2Sr2CaCu2O8+δ imaged by spectroscopic-imaging STM",
     "clusters": ["cuprate_sc", "cdw_nematic_excitonic", "unconventional_topological_sc"], "primary": "cuprate_sc",
     "methods": ["stm_sts"], "families": ["cuprates"]},
    {"text": "Strange metal transport and Planckian dissipation in overdoped La$_{2-x}$Sr$_x$CuO$_4$ thin films",
     "clusters": ["cuprate_sc", "mott_hubbard_strange_metal"], "methods": ["thin_film_growth_mbe"],
     "families": ["cuprates"]},
    {"text": "Stripe order and superconductivity in the doped Hubbard model: a DMRG and constrained-path auxiliary-field QMC study",
     "clusters": ["mott_hubbard_strange_metal", "cdw_nematic_excitonic"], "methods": ["dmrg_tensor_networks", "qmc"]},
    # --- iron based ---
    {"text": "Nematic fluctuations and orbital-selective pairing in FeSe$_{1-x}$S$_x$ from ARPES and elastoresistance",
     "clusters": ["iron_based_sc", "cdw_nematic_excitonic", "mott_hubbard_strange_metal"], "primary": "iron_based_sc",
     "methods": ["arpes"], "families": ["iron_pnictides_chalcogenides"]},
    {"text": "Majorana zero modes in vortex cores of Fe(Te,Se) revealed by scanning tunneling spectroscopy",
     "clusters": ["iron_based_sc", "unconventional_topological_sc"], "primary": "iron_based_sc",
     "methods": ["stm_sts"], "families": ["iron_pnictides_chalcogenides"]},
    {"text": "Spin resonance in BaFe2As2-based iron pnictide superconductors via inelastic neutron scattering",
     "clusters": ["iron_based_sc"], "methods": ["neutron_scattering"], "families": ["iron_pnictides_chalcogenides"]},
    # --- hydrides ---
    {"text": "Superconductivity at 250 K in lanthanum superhydride LaH10 in a diamond anvil cell at 170 GPa",
     "clusters": ["hydride_high_pressure_sc"], "primary": "hydride_high_pressure_sc",
     "methods": ["high_pressure_dac"], "families": ["hydrides"]},
    {"text": "Anharmonic phonons and Eliashberg Tc of ternary hydrides LaBeH8 from SSCHA calculations",
     "clusters": ["hydride_high_pressure_sc"], "methods": ["phonon_electron_phonon"], "families": ["hydrides"]},
    # --- kagome ---
    {"text": "Chiral charge order and time-reversal symmetry breaking in the kagome superconductor CsV$_3$Sb$_5$",
     "clusters": ["kagome", "cdw_nematic_excitonic"], "primary": "kagome", "families": ["av3sb5_kagome"]},
    {"text": "Charge density wave in kagome FeGe studied by x-ray diffraction and first-principles phonon calculations",
     "clusters": ["kagome", "cdw_nematic_excitonic"], "methods": ["diffraction_structure", "dft_first_principles", "phonon_electron_phonon"],
     "families": ["other_kagome_metals"]},
    {"text": "Flat bands in the kagome metal ScV6Sn6 and CoSn: tight-binding and Wannier analysis",
     "clusters": ["kagome"], "methods": ["tight_binding_continuum"], "families": ["other_kagome_metals"]},
    # --- altermagnets ---
    {"text": "Observation of altermagnetic spin splitting in MnTe by spin-resolved ARPES",
     "clusters": ["altermagnetism"], "primary": "altermagnetism", "methods": ["arpes"],
     "families": ["altermagnet_candidates"]},
    {"text": "Anomalous Hall effect in the altermagnet candidate RuO$_2$ thin films",
     "clusters": ["altermagnetism"], "methods": ["magnetotransport_hall", "thin_film_growth_mbe"],
     "families": ["altermagnet_candidates"]},
    {"text": "Non-relativistic spin splitting in CrSb from first-principles and x-ray magnetic circular dichroism",
     "clusters": ["altermagnetism"], "methods": ["dft_first_principles", "rixs_resonant_xray"],
     "families": ["altermagnet_candidates"]},
    # --- FQAH / Chern ---
    {"text": "Fractional quantum anomalous Hall effect in twisted MoTe2 bilayers",
     "clusters": ["fractional_qah_chern", "moire_twisted_2d"], "primary": "fractional_qah_chern",
     "families": ["tmds"]},
    {"text": "Quantum anomalous Hall effect in MnBi$_2$Te$_4$ flakes: Chern insulator at zero field",
     "clusters": ["fractional_qah_chern", "topological_insulators_semimetals", "vdw_magnets_topological_magnetism"],
     "families": ["mnbi2te4_bi2se3_tetradymites"]},
    # --- rhombohedral graphene ---
    {"text": "Chiral superconductivity in rhombohedral tetralayer graphene",
     "clusters": ["rhombohedral_multilayer_graphene", "unconventional_topological_sc"], "primary": "rhombohedral_multilayer_graphene",
     "families": ["graphene_multilayers"]},
    {"text": "Extended quantum anomalous Hall states in rhombohedral pentalayer graphene aligned with hBN: Hartree-Fock study",
     "clusters": ["rhombohedral_multilayer_graphene", "fractional_qah_chern"], "primary": "fractional_qah_chern",
     "methods": ["hartree_fock_mean_field"], "families": ["graphene_multilayers", "hbn"]},
    {"text": "Layer-polarized states in Bernal bilayer graphene under displacement field",
     "clusters": ["rhombohedral_multilayer_graphene"], "families": ["graphene_multilayers"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    # --- moire ---
    {"text": "Correlated insulators and superconductivity in magic-angle twisted bilayer graphene: continuum model and exact diagonalization",
     "clusters": ["moire_twisted_2d", "mott_hubbard_strange_metal"], "primary": "moire_twisted_2d",
     "not_clusters": ["rhombohedral_multilayer_graphene"],
     "methods": ["tight_binding_continuum", "exact_diagonalization"], "families": ["graphene_multilayers"]},
    {"text": "Generalized Wigner crystals in WSe2/WS2 moiré superlattices imaged by STM",
     "clusters": ["moire_twisted_2d", "cdw_nematic_excitonic"], "methods": ["stm_sts"], "families": ["tmds"]},
    {"text": "Moir\\'e excitons in MoSe$_2$/WSe$_2$ heterobilayers probed by photoluminescence",
     "clusters": ["moire_twisted_2d", "cdw_nematic_excitonic"], "methods": ["optical_raman_ir"], "families": ["tmds"]},
    # --- unconventional / topological SC / devices ---
    {"text": "Field-free superconducting diode effect in NbSe2/CrSBr Josephson junctions",
     "clusters": ["unconventional_topological_sc", "vdw_magnets_topological_magnetism"],
     "not_clusters": ["cdw_nematic_excitonic"],  # v2: NbSe2 alone no longer implies CDW
     "families": ["tmds", "vdw_magnets"]},
    {"text": "Spin-triplet superconductivity in UTe$_2$: NMR Knight shift and specific heat under magnetic field",
     "clusters": ["unconventional_topological_sc", "heavy_fermion_kondo_qcp"], "primary": "unconventional_topological_sc",
     "methods": ["nmr_nqr", "thermodynamics_specific_heat"], "families": ["ute2_heavy_fermion_f_electron"]},
    {"text": "Even-odd parity and uniaxial strain in Sr2RuO4 studied by elastocaloric effect",
     "clusters": ["unconventional_topological_sc"], "methods": ["thermodynamics_specific_heat", "high_pressure_dac"],
     "families": ["ruthenates"], "scope_record": {"server": "arxiv", "categories": ["cond-mat.supr-con"]}},
    # --- spin liquids ---
    {"text": "Field-induced quantum spin liquid in α-RuCl$_3$: thermal Hall and neutron scattering",
     "clusters": ["spin_liquid_frustrated"], "primary": "spin_liquid_frustrated",
     "methods": ["neutron_scattering", "magnetotransport_hall"], "families": ["kitaev_materials"]},
    {"text": "Dirac spin liquid on the triangular lattice antiferromagnet NaYbSe2 from DMRG and linear spin-wave theory",
     "clusters": ["spin_liquid_frustrated"], "methods": ["dmrg_tensor_networks", "tight_binding_continuum"],
     "families": ["frustrated_rare_earth_and_triangular"]},
    {"text": "Kitaev interactions in the honeycomb cobaltate Na2Co2TeO6",
     "clusters": ["spin_liquid_frustrated"], "families": ["kitaev_materials"]},
    # --- heavy fermion ---
    {"text": "Kondo breakdown and quantum criticality in YbRh2Si2 probed by terahertz spectroscopy",
     "clusters": ["heavy_fermion_kondo_qcp"], "not_clusters": ["ultrafast_floquet_noneq"], "primary": "heavy_fermion_kondo_qcp",
     "methods": ["optical_raman_ir"], "families": ["ute2_heavy_fermion_f_electron"]},
    {"text": "Heavy-fermion superconductivity in CeRh2As2: quantum oscillations and de Haas-van Alphen",
     "clusters": ["heavy_fermion_kondo_qcp", "unconventional_topological_sc"],
     "methods": ["quantum_oscillations"], "families": ["ute2_heavy_fermion_f_electron"]},
    # --- vdW magnets / skyrmions ---
    {"text": "Room-temperature skyrmions in the van der Waals ferromagnet Fe$_3$GaTe$_2$ imaged by Lorentz TEM",
     "clusters": ["vdw_magnets_topological_magnetism"], "primary": "vdw_magnets_topological_magnetism",
     "methods": ["diffraction_structure"], "families": ["vdw_magnets"]},
    {"text": "Imaging magnetic domains in few-layer CrI3 with NV-center magnetometry",
     "clusters": ["vdw_magnets_topological_magnetism"], "methods": ["nv_quantum_sensing"], "families": ["vdw_magnets"]},
    {"text": "Magnon-exciton coupling in the layered antiferromagnet CrSBr from time-resolved Kerr rotation",
     "clusters": ["vdw_magnets_topological_magnetism", "cdw_nematic_excitonic", "ultrafast_floquet_noneq"],
     "methods": ["ultrafast_pump_probe", "optical_raman_ir"], "families": ["vdw_magnets"]},
    # --- CDW / excitonic ---
    {"text": "Excitonic insulator phase in Ta$_2$NiSe$_5$: evidence from Raman scattering and GW-BSE calculations",
     "clusters": ["cdw_nematic_excitonic"], "primary": "cdw_nematic_excitonic",
     "methods": ["optical_raman_ir", "gw_beyond_dft"], "families": ["excitonic_insulator_cdw_materials"]},
    {"text": "Charge density wave melting in 1T-TiSe2 by ultrafast electron diffraction",
     "clusters": ["cdw_nematic_excitonic", "ultrafast_floquet_noneq"], "methods": ["ultrafast_pump_probe", "diffraction_structure"],
     "families": ["tmds", "excitonic_insulator_cdw_materials"]},
    # --- topological insulators / semimetals ---
    {"text": "Weyl nodes and Fermi arcs in TaAs: magnetotransport and Berry curvature",
     "clusters": ["topological_insulators_semimetals"], "primary": "topological_insulators_semimetals",
     "methods": ["magnetotransport_hall"], "families": ["weyl_dirac_semimetals"]},
    {"text": "Magnetic Weyl semimetal EuCd$_2$As$_2$ studied by high-field quantum oscillations",
     "clusters": ["topological_insulators_semimetals"], "methods": ["quantum_oscillations"],
     "families": ["magnetic_topological_eu_compounds"]},
    {"text": "Topological surface states of Bi2Se3 thin films grown by molecular beam epitaxy",
     "clusters": ["topological_insulators_semimetals"], "methods": ["thin_film_growth_mbe"],
     "families": ["mnbi2te4_bi2se3_tetradymites"]},
    # --- Mott / strange metal / oxide ---
    {"text": "Two-dimensional electron gas and superconductivity at the LaAlO3/SrTiO3 oxide interface",
     "clusters": ["mott_hubbard_strange_metal"], "families": ["srtio3_ktao3_oxide_interfaces"]},
    {"text": "Mott transition in VO2 and V2O3 from DFT+DMFT and x-ray absorption spectroscopy",
     "clusters": ["mott_hubbard_strange_metal"], "methods": ["dmft", "rixs_resonant_xray"],
     "families": ["iridates_mott_oxides"]},
    # --- ultrafast / Floquet ---
    {"text": "Floquet-Bloch states in graphene driven by mid-infrared light observed by time-resolved ARPES",
     "clusters": ["ultrafast_floquet_noneq"], "primary": "ultrafast_floquet_noneq",
     "methods": ["ultrafast_pump_probe", "arpes"], "families": ["graphene_multilayers"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Light-induced superconductivity in K3C60: nonequilibrium Eliashberg theory",
     "clusters": ["ultrafast_floquet_noneq"], "methods": ["phonon_electron_phonon"]},
    # --- ML / AI ---
    {"text": "Neural quantum states for the frustrated J1-J2 Heisenberg model: transformer-based variational Monte Carlo",
     "clusters": ["ml_ai", "spin_liquid_frustrated"], "primary": "spin_liquid_frustrated",
     "methods": ["machine_learning"]},
    {"text": "Machine learning discovery of new superconductors from DFT electron-phonon databases",
     "clusters": ["ml_ai"], "primary": "ml_ai",
     "not_clusters": ["other_superconductivity"],  # residual cluster: only fills empty slots
     "methods": ["machine_learning", "dft_first_principles", "phonon_electron_phonon"]},
    # --- v2: flat bands & quantum geometry ---
    {"text": "Quantum metric and superfluid weight of flat-band superconductivity in a Lieb lattice",
     "clusters": ["flat_band_quantum_geometry"], "primary": "flat_band_quantum_geometry"},
    {"text": "Berry curvature dipole and the nonlinear anomalous Hall effect in strained WTe2",
     "clusters": ["flat_band_quantum_geometry", "topological_insulators_semimetals"],
     "primary": "topological_insulators_semimetals", "families": ["weyl_dirac_semimetals"]},
    {"text": "Intrinsic orbital Hall effect driven by the quantum geometry of Bloch bands",
     "clusters": ["flat_band_quantum_geometry"], "primary": "flat_band_quantum_geometry"},
    # --- v2: quantum magnetism & ferroic order (residual) ---
    {"text": "Magnetization plateau and spin-gap in the spin-1/2 ladder compound (C5H12N)2CuBr4 studied by NMR",
     "clusters": ["quantum_magnetism_ferroic_order"], "primary": "quantum_magnetism_ferroic_order",
     "methods": ["nmr_nqr"], "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Ground-state magnetic structure of the antiferromagnet Mn3Sn from polarized neutron diffraction",
     "clusters": ["quantum_magnetism_ferroic_order"], "methods": ["neutron_scattering"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Ferroaxial order and polar metal behaviour in a layered oxide",
     "clusters": ["quantum_magnetism_ferroic_order"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    # --- v2: quantum many-body theory & generalized symmetries (residual) ---
    {"text": "Non-invertible symmetries and Kramers-Wannier duality in (1+1)d lattice models",
     "clusters": ["quantum_many_body_theory"], "primary": "quantum_many_body_theory",
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Exact quantum many-body scars and Hilbert-space fragmentation in a spin-1 XY chain",
     "clusters": ["quantum_many_body_theory"], "primary": "quantum_many_body_theory",
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Tensor network simulation of a Z2 lattice gauge theory with matrix product states",
     "clusters": ["quantum_many_body_theory"], "methods": ["dmrg_tensor_networks"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    {"text": "Anyons and topological order in the toric code on a honeycomb lattice",
     "clusters": ["quantum_many_body_theory"], "not_clusters": ["fractional_qah_chern"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}},
    # --- v2: other superconductivity & superfluidity (residual) ---
    {"text": "Superconductivity at 12 K in a new high-entropy alloy: specific heat and upper critical field",
     "clusters": ["other_superconductivity"], "primary": "other_superconductivity",
     "methods": ["thermodynamics_specific_heat"]},
    {"text": "Abrikosov vortex pinning and flux creep in NbN thin films",
     "clusters": ["other_superconductivity"], "methods": ["thin_film_growth_mbe"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.supr-con"]}},
    {"text": "Two-level-system losses in tantalum transmon qubits and superconducting resonators",
     "clusters": ["other_superconductivity"],
     "scope_record": {"server": "arxiv", "categories": ["cond-mat.supr-con"]}},
]


# Must be OUT of scope (keyword path, non-arXiv record) and ideally unclassified.
NEGATIVE_CASES = [
    "High-voltage LiNi0.8Mn0.1Co0.1O2 battery cathode with DFT+U (Hubbard U) analysis of oxygen redox",
    "Efficient and stable perovskite solar cells via defect passivation: Mott-Schottky and SCLC Mott-Gurney analysis",
    "RuO2 nanoparticles as electrocatalysts for the acidic oxygen evolution reaction",
    "Single-atom Pt catalysts on CeO2 for low-temperature CO oxidation",
    "Self-healing polymer networks with dynamic covalent bonds for flexible electronics",
    "Metal-organic frameworks for CO2 capture: a high-throughput screening study",
    "Design of a 20 T HTS superconducting magnet for compact fusion reactors",
    "Electro-optic switching of nematic liquid crystal cells with nematic order parameter control",
    "Topology optimization of heat sinks for electronics cooling",
    "Moiré fringe metrology for wafer alignment in lithography",
    "Frustrated Lewis pairs for metal-free hydrogenation catalysis",
    "Practical measurements of vibration using the moiré effect",
    "On the possibility of the Majorana nature of neutrinos",
    "Quantum magnetometry of neuronal currents with diamond sensors",
    "Machine learning prediction of polymer glass transition temperatures",
    # v2 scope veto: classical-wave topology is not a quantum material
    "Topological photonic crystal lasers with robust edge states",
    "Nonlinear topological acoustic metamaterials with topological edge modes",
]


# Specific false-positive guards on text that IS in scope.
GUARD_CASES = [
    # hyphenated forms and doped cuprate formulas
    ("Photo-induced relaxation dynamics of Weyl-semimetals", {"clusters": ["topological_insulators_semimetals", "ultrafast_floquet_noneq"]}),
    ("Pseudogap in Bi1.6Pb0.4Sr2Ca2Cu3O10+δ and GdBa2Cu3O7 superconductors", {"clusters": ["cuprate_sc"], "families": ["cuprates"]}),
    ("Generative model for discovery of quantum material candidates", {"clusters": ["ml_ai"]}),
    # "system" must not trigger STM, "stem" must not trigger STEM
    ("A correlated electron system with stem-like domains", {"not_methods": ["stm_sts", "diffraction_structure"]}),
    # Kitaev chain is topological SC, not spin liquid
    ("Majorana modes in a minimal Kitaev chain of quantum dots", {"clusters": ["unconventional_topological_sc"], "not_clusters": ["spin_liquid_frustrated"]}),
    # dynamical mean-field must not count as plain mean field
    ("Hund's metal physics from dynamical mean-field theory", {"methods": ["dmft"], "not_methods": ["hartree_fock_mean_field"]}),
    # MnTe2 is not the altermagnet MnTe
    ("Pressure-induced superconductivity in MnTe2", {"not_families": ["altermagnet_candidates"]}),
    # twisted double bilayer graphene is moire, not rhombohedral
    ("Correlated states in twisted double bilayer graphene", {"clusters": ["moire_twisted_2d"], "not_clusters": ["rhombohedral_multilayer_graphene"]}),
    # v2 guards
    ("Correlated insulators in twisted mono-bilayer graphene", {"clusters": ["moire_twisted_2d"], "not_clusters": ["rhombohedral_multilayer_graphene"]}),
    ("Real Chern insulators in altermagnetic Fe2Se2O monolayers", {"clusters": ["altermagnetism"], "not_clusters": ["iron_based_sc"]}),
    ("Critical current of BaFe2(As1-xPx)2 superconducting crystals", {"clusters": ["iron_based_sc"], "not_clusters": ["other_superconductivity"]}),
    ("Superconductivity in manganese pnictides under pressure", {"not_clusters": ["iron_based_sc"]}),
    ("Spin-polarized currents in p-wave magnets and odd-parity magnetism", {"clusters": ["altermagnetism"], "not_clusters": ["unconventional_topological_sc"],
                                                                          "scope_record": {"server": "arxiv", "categories": ["cond-mat.str-el"]}}),
    ("Hofstadter butterfly with Peierls substitution in a superconducting ring", {"not_clusters": ["cdw_nematic_excitonic"]}),
    ("Magic angle spinning NMR of NV-center hyperpolarized diamond superconducting magnet", {"not_clusters": ["moire_twisted_2d"]}),
    ("Topological defects in ferroelectric nematic fluids and charge order", {"not_clusters": ["cdw_nematic_excitonic"]}),
    # a spin chain MODEL paper goes to many-body theory, not magnetism
    ("Integrability and Bethe ansatz of the XXZ spin chain", {"clusters": ["quantum_many_body_theory"], "not_clusters": ["quantum_magnetism_ferroic_order"]}),
]


# v2 evidence rule: (title, abstract, expected in clusters, expected NOT in clusters).
# A cluster needs a title hit or at least two hits in title + abstract; a single
# passing mention in the abstract is not enough. Records here are arXiv records
# cross-listed in cond-mat.str-el so they are in scope.
EVIDENCE_CASES = [
    ("Spin dynamics of a new triangular antiferromagnet",
     "Unlike the cuprates, this compound shows no superconductivity.",
     [], ["cuprate_sc"]),
    ("Spin dynamics of a new triangular-lattice antiferromagnet",
     "Our cuprate-free compound is compared with the cuprate parent La2CuO4.",
     ["cuprate_sc"], []),
    ("Spin excitations in a layered oxide",
     "The cuprate compound shows spin waves.",
     [], ["cuprate_sc"]),
    ("Kagome superconductor CsV3Sb5", "We report STM data.", ["kagome"], []),
    # title-only phrase: "strongly correlated systems" in the abstract is framing
    ("A new tensor-network algorithm",
     "Our method is a useful tool for strongly correlated systems and strongly correlated systems in general.",
     ["quantum_many_body_theory"], ["mott_hubbard_strange_metal"]),
    ("Strongly correlated electrons in a ruthenate", "We study transport.",
     ["mott_hubbard_strange_metal"], []),
]


def check_positive(case):
    text = tx.normalize_text(case["text"])
    record = {"server": "chemrxiv", "title": case["text"], "abstract": "", "categories": []}
    if "scope_record" in case:
        record.update(case["scope_record"])
    assert tx.in_scope(record), "should be in scope: " + case["text"]

    clusters = tx.classify(text)
    for key in case.get("clusters", []):
        assert key in clusters, "missing cluster %s for: %s (got %s)" % (key, case["text"], clusters)
    for key in case.get("not_clusters", []):
        assert key not in clusters, "unexpected cluster %s for: %s" % (key, case["text"])
    if "primary" in case:
        got = tx.primary_cluster(text)
        assert got == case["primary"], "primary %s != %s for: %s" % (got, case["primary"], case["text"])

    methods = tx.find_methods(text)
    for key in case.get("methods", []):
        assert key in methods, "missing method %s for: %s (got %s)" % (key, case["text"], methods)
    for key in case.get("not_methods", []):
        assert key not in methods, "unexpected method %s for: %s" % (key, case["text"])

    families = tx.find_families(text)
    for key in case.get("families", []):
        assert key in families, "missing family %s for: %s (got %s)" % (key, case["text"], families)
    for key in case.get("not_families", []):
        assert key not in families, "unexpected family %s for: %s" % (key, case["text"])


def test_normalize_text():
    assert tx.normalize_text("La$_3$Ni$_2$O$_7$") == "La3Ni2O7"
    assert tx.normalize_text("La_3Ni_2O_7") == "La3Ni2O7"
    assert tx.normalize_text("La$_{3}$Ni$_{2}$O$_{7-\\delta}$") == "La3Ni2O7-δ"
    assert tx.normalize_text("La₃Ni₂O₇") == "La3Ni2O7"
    assert tx.normalize_text("$\\mathrm{CsV_3Sb_5}$") == "CsV3Sb5"
    assert tx.normalize_text("Moir\\'e  <i>bands</i>\n") == "Moiré bands"
    assert tx.normalize_text("µSR in Fe$^{2+}$ − test") == "μSR in Fe2+ - test"
    assert tx.normalize_text(None) == ""


def test_positive_cases():
    for case in POSITIVE_CASES:
        check_positive(case)


def test_guard_cases():
    for text, expected in GUARD_CASES:
        case = dict(expected)
        case["text"] = text
        check_positive(case)


def test_evidence_rule():
    for title, abstract, expected, not_expected in EVIDENCE_CASES:
        record = {"server": "arxiv", "title": title, "abstract": abstract,
                  "categories": ["cond-mat.str-el"]}
        labels = tx.classify_record(record)
        assert labels["in_scope"] and labels["scope_reason"] == "category"
        for key in expected:
            assert key in labels["clusters"], "missing %s for %r / %r (got %s)" % (key, title, abstract, labels["clusters"])
        for key in not_expected:
            assert key not in labels["clusters"], "unexpected %s for %r / %r" % (key, title, abstract)


def test_residual_clusters():
    # residual clusters are the last ones in CLUSTERS order
    flags = [cluster.get("residual", False) for cluster in tx.CLUSTERS]
    first_residual = flags.index(True)
    assert all(flags[first_residual:]), "a non-residual cluster follows a residual one"
    assert tx.RESIDUAL_CLUSTER_KEYS == tx.CLUSTER_KEYS[first_residual:]
    # at most one residual cluster, and none if a specific cluster matched
    text = tx.normalize_text("Superconductivity and antiferromagnetic order in a spin-chain compound")
    clusters = tx.classify(text)
    assert sum(1 for key in clusters if key in tx.RESIDUAL_CLUSTER_KEYS) <= 1, clusters
    text = tx.normalize_text("Superconductivity in the cuprate YBa2Cu3O7")
    assert not set(tx.classify(text)) & set(tx.RESIDUAL_CLUSTER_KEYS)


def test_classify_record_fields():
    record = {"server": "chemrxiv", "title": "Perovskite solar cells", "abstract": "", "categories": []}
    labels = tx.classify_record(record)
    assert labels == {"in_scope": False, "scope_reason": None, "clusters": [], "primary_cluster": None,
                      "methods": [], "families": [], "taxonomy_version": tx.TAXONOMY_VERSION}
    record = {"server": "zenodo", "title": "Quantum spin liquid in the kagome antiferromagnet herbertsmithite",
              "abstract": "", "categories": []}
    labels = tx.classify_record(record)
    assert labels["in_scope"] and labels["scope_reason"] == "keyword"
    assert labels["primary_cluster"] == "kagome"
    assert tx.TAXONOMY_VERSION == "v2"


def test_negative_cases():
    for text in NEGATIVE_CASES:
        record = {"server": "chemrxiv", "title": text, "abstract": "", "categories": []}
        assert not tx.in_scope(record), "should be OUT of scope: %s (hits %s)" % (
            text, tx.scope_hits(tx.normalize_text(text)))
    # arXiv category rule alone brings a record in scope
    record = {"server": "arxiv", "title": NEGATIVE_CASES[0], "abstract": "", "categories": ["cond-mat.supr-con"]}
    assert tx.in_scope(record)


def test_coverage():
    assert len(POSITIVE_CASES) >= 40
    assert len(NEGATIVE_CASES) >= 8
    assert 14 <= len(tx.CLUSTERS) <= 22
    assert len(set(tx.CLUSTER_KEYS)) == len(tx.CLUSTER_KEYS)
    covered_clusters = set()
    covered_methods = set()
    covered_families = set()
    for case in POSITIVE_CASES:
        covered_clusters.update(case.get("clusters", []))
        covered_methods.update(case.get("methods", []))
        covered_families.update(case.get("families", []))
    missing_clusters = set(tx.CLUSTER_KEYS) - covered_clusters
    missing_methods = set(tx.METHODS) - covered_methods
    assert not missing_clusters, "clusters without a test: %s" % sorted(missing_clusters)
    assert not missing_methods, "methods without a test: %s" % sorted(missing_methods)
    assert len(covered_families) >= 15, "only %d families tested" % len(covered_families)
    for spec in tx.METHODS.values():
        assert spec["kind"] in ("experimental", "computational")
    assert isinstance(tx.SCOPE_DESCRIPTION, str) and "cond-mat.str-el" in tx.SCOPE_DESCRIPTION


if __name__ == "__main__":
    test_normalize_text()
    test_positive_cases()
    test_guard_cases()
    test_negative_cases()
    test_evidence_rule()
    test_residual_clusters()
    test_classify_record_fields()
    test_coverage()
    print("all taxonomy tests passed: %d positive, %d negative, %d guard, %d evidence-rule cases"
          % (len(POSITIVE_CASES), len(NEGATIVE_CASES), len(GUARD_CASES), len(EVIDENCE_CASES)))
