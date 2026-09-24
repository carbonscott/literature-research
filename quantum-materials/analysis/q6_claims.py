"""Q6 claim definitions: contested / unreplicated high-visibility claims.

This is a DATA module used by noise_filter.py. Each claim lists

  key, name, claim, material    -- what is being claimed
  original_ids                  -- corpus ids of the paper(s) that made the claim
                                   (may be outside the survey window; older ones were
                                   added to corpus/arxiv_supplement.jsonl by id_list lookup)
  original_group                -- key people of the original group. A paper counts as
                                   "same group" if ANY of its authors matches one of these
                                   names (first initial + surname). Defaults to the last
                                   author of each original if left empty.
  originals_independent         -- True if the originals themselves come from two
                                   independent groups that saw the same observable
                                   (counts as a replication for feature F1).
  known_venue                   -- peer-reviewed venue of the original that arXiv metadata
                                   does not show (manual; source: notes/contested_candidates.json)
  topic_patterns                -- regexes (all must match title+abstract, case-insensitive)
                                   used to find the topic neighbourhood in the corpus
  labels                        -- hand labels read from each abstract:
                                   id -> (stance, kind, note)
                                   stance: supportive | critical | neutral
                                   kind:   exp | theory | comment | review
                                   ("comment" = Comment / Reply / Response / Matters Arising)
  status, status_note           -- judged status after reading the abstracts

Labels were assigned by reading titles and abstracts only (no full texts). A label says
how the abstract positions itself relative to the CLAIM as stated here, not whether the
paper is right.
"""

S, C, N = "supportive", "critical", "neutral"
EXP, TH, CM, RV = "exp", "theory", "comment", "review"

CLAIMS = [
    # ------------------------------------------------------------------ RuO2 bulk
    {
        "key": "ruo2_bulk_altermagnet",
        "name": "RuO2 as a bulk room-temperature altermagnet",
        "claim": "Bulk rutile RuO2 is a collinear (d-wave) altermagnet with room-temperature "
                 "Neel order and non-relativistic spin-split bands (crystal Hall effect).",
        "material": "RuO2 single crystals",
        "original_ids": ["arXiv:1901.00445"],
        "original_group": ["Libor Šmejkal", "Tomáš Jungwirth", "Jairo Sinova"],
        "topic_patterns": [r"RuO2", r"altermagn|antiferromag|magnetic order|nonmagnetic|non-magnetic|paramagne"],
        "labels": {
            "arXiv:2410.05850": (C, EXP, "polarized neutron diffraction excludes AFM order > 0.01 muB in crystals"),
            "arXiv:2412.12258": (C, EXP, "RRR=152 crystal: no crystal Hall effect, 'typical semimetal rather than an altermagnet'"),
            "arXiv:2501.10649": (C, EXP, "micro-ARPES: spin-degenerate bulk bands"),
            "arXiv:2503.20621": (C, EXP, "quantum oscillations match the nonmagnetic scenario"),
            "arXiv:2504.21138": (C, EXP, "no detectable long-range order in high-quality crystals"),
            "arXiv:2505.03250": (C, EXP, "Mossbauer / NFS: no magnetic moment in bulk"),
            "arXiv:2505.07201": (C, EXP, "ultra-clean crystals show no sign of magnetic order"),
            "arXiv:2510.13767": (C, EXP, "resonant diffraction is structural; k=0 AFM order unlikely (crystal + film)"),
            "arXiv:2511.00399": (C, EXP, "NMR: neither static nor fluctuating Ru moments"),
            "arXiv:2512.03108": (C, EXP, "clean crystal is a weakly correlated Fermi liquid, paramagnetic"),
            "arXiv:2604.10659": (C, EXP, "bulk non-magnetic; only a surface ferrimagnetic state"),
            "arXiv:2411.02507": (C, TH, "AHE in Cr-doped RuO2 comes from Cr, Ru bands stay nonmagnetic"),
            "arXiv:2502.03751": (C, TH, "surface magnetization on non-magnetic bulk"),
            "arXiv:2603.16125": (C, TH, "DMC: stoichiometric bulk RuO2 is nonmagnetic"),
            "arXiv:2604.10105": (N, CM, "Comment on 2510.13767: says its scattering amplitudes are wrong (attacks a null result, does not claim magnetism)"),
            "arXiv:2512.04995": (N, TH, "meta-GGA: bulk nonmagnetic, altermagnetism under strain/doping"),
            "arXiv:2602.15606": (N, TH, "Neel temperature of the hypothetical DFT+U altermagnetic state"),
            "arXiv:2509.19932": (N, RV, "review of the debate"),
            "arXiv:2403.10028": (C, EXP, "(pre-window) muSR: nonmagnetic ground state"),
            "arXiv:2409.13504": (C, EXP, "(2024-09-20, 4 days before the window) spin-ARPES on film + crystal: no spin splitting"),
        },
        "status": "refuted",
        "status_note": "Every in-window bulk-crystal measurement (neutron, muSR-era follow-ups, NMR, "
                       "quantum oscillations, ARPES, Mossbauer, resonant diffraction) is null; the "
                       "surviving debate is about strained thin films (next claim).",
    },
    # ------------------------------------------------------------------ RuO2 films
    {
        "key": "ruo2_film_altermagnet",
        "name": "Altermagnetic order in RuO2 thin films",
        "claim": "Epitaxial (strained) RuO2 films carry altermagnetic Neel order and "
                 "spin-splitting transport effects (spin-splitting torque/MR, TMR, AHE).",
        "material": "RuO2 epitaxial films on TiO2 and other substrates",
        "original_ids": ["arXiv:1901.00445"],
        "original_group": ["Libor Šmejkal", "Tomáš Jungwirth", "Jairo Sinova"],
        "topic_patterns": [r"RuO2", r"film|heterostructure|bilayer|epitax", r"altermagn|antiferromag|magnetic order|spin[- ]split|anomalous hall"],
        "labels": {
            "arXiv:2412.17013": (S, EXP, "electrical manipulation of spin-splitting torque"),
            "arXiv:2412.17016": (S, EXP, "XMLD 'unambiguously demonstrates' AFM in films"),
            "arXiv:2412.18220": (S, EXP, "spin-splitting magnetoresistance, Neel vector along [001]"),
            "arXiv:2412.18937": (S, EXP, "non-relativistic spin current polarization follows the Neel vector"),
            "arXiv:2501.11204": (S, EXP, "AHE in strained ultrathin films"),
            "arXiv:2501.12593": (S, EXP, "magnetic orbital Hall effect"),
            "arXiv:2502.13599": (S, EXP, "TMR set by the Neel vector"),
            "arXiv:2508.13720": (S, EXP, "single-variant altermagnetic RuO2(101) films"),
            "arXiv:2509.16361": (S, EXP, "strain-enabled spin texture in ultrathin films (bulk/thick films non-magnetic)"),
            "arXiv:2601.10518": (S, EXP, "unconventional magnetism in strained RuO2/TiO2 superlattices"),
            "arXiv:2601.19052": (S, EXP, "spin polarization consistent with altermagnetism, confined near surface"),
            "arXiv:2604.13893": (S, EXP, "third-order transport tied to altermagnetic order in 8 nm films"),
            "arXiv:2605.27830": (S, EXP, "magneto-optical anisotropic spin currents (residual strain)"),
            "arXiv:2606.26023": (S, EXP, "strain-stabilized altermagnetic spin-splitting torques"),
            "arXiv:2609.18059": (S, EXP, "strain (not Ti3+) controls the AHE state"),
            "arXiv:2412.11240": (C, EXP, "THz: 'casting further doubt on the existence of altermagnetism'"),
            "arXiv:2503.07985": (C, EXP, "no altermagnetic spin-splitting effect in films from 3 growth methods"),
            "arXiv:2507.05047": (C, EXP, "spin-polarized STM: no magnetic order on ultrathin RuO2(110)"),
            "arXiv:2508.11481": (C, EXP, "THz emission: altermagnetic contribution only ~2-4e-4"),
            "arXiv:2508.15004": (C, EXP, "no intrinsic magnon modes; interface effects mimic AFM"),
            "arXiv:2509.22866": (C, EXP, "exchange bias has a non-altermagnetic origin"),
            "arXiv:2510.08064": (C, EXP, "LE-muSR: only surface-confined inhomogeneous order"),
            "arXiv:2510.13781": (C, EXP, "resonant diffraction + ARPES + AMR inconsistent with altermagnetism"),
            "arXiv:2601.06791": (C, EXP, "XLD: absence of magnetic order in epitaxial films"),
            "arXiv:2607.20298": (C, EXP, "Cr alloying does not induce altermagnetism"),
            "arXiv:2510.13767": (C, EXP, "resonant diffraction structural (crystal + (001) film)"),
            "arXiv:2604.10105": (N, CM, "Comment on the null paper 2510.13767"),
            "arXiv:2602.11602": (N, TH, "(001) films nonmagnetic, (100)/(110) strain-induced splitting"),
            "arXiv:2510.26581": (N, TH, "DFT: compressive strain stabilizes altermagnetism"),
            "arXiv:2606.20262": (N, EXP, "weak interfacial magnetism probed via WSe2 proximity"),
        },
        "status": "contested",
        "status_note": "Many independent positive transport reports and many independent nulls; "
                       "the positive side increasingly attributes the signal to strain or surfaces.",
    },
    # ------------------------------------------------------------------ Microsoft TGP
    {
        "key": "msft_tgp_majorana",
        "name": "Microsoft topological gap protocol / Majorana parity readout",
        "claim": "InAs-Al gate-defined nanowires pass the topological gap protocol (TGP), i.e. host "
                 "Majorana zero modes, and support interferometric parity readout / tetron qubits.",
        "material": "InAs/Al (and InAs/Pb) hybrid nanowires",
        "original_ids": ["arXiv:2207.02472", "arXiv:2401.09549"],
        "original_group": ["Chetan Nayak"],
        "topic_patterns": [r"topological gap protocol|tetron|parity (?:readout|measurement)|InAs-Al"],
        "labels": {
            "arXiv:2504.13240": (S, CM, "Microsoft Response: comments 'unfounded', conclusions upheld"),
            "arXiv:2507.08795": (S, EXP, "Microsoft tetron device, X and Z loop lifetimes"),
            "arXiv:2606.03884": (S, EXP, "Microsoft InAs-Pb tetron, 20 s parity lifetime"),
            "arXiv:2502.19560": (C, CM, "Legg Comment: TGP lacks consistent definition of gap/topological"),
            "arXiv:2503.08944": (C, CM, "Legg Comment: readout regions are gapless"),
            "arXiv:2505.23741": (C, TH, "capacitance oscillations do not by themselves evidence MZMs"),
            "arXiv:2603.12256": (C, TH, "quantum capacitance alone cannot confirm protected parity"),
            "arXiv:2504.01069": (C, TH, "finite-size bias of the scattering invariant used by the TGP"),
            "arXiv:2502.12960": (N, TH, "Microsoft simulation methods for the readout setup"),
            "arXiv:2507.01606": (N, EXP, "parity readout of a Kitaev chain (different platform, Delft)"),
        },
        "status": "contested",
        "status_note": "All positive in-window results come from the Microsoft consortium; the "
                       "critique is two Comments plus theory; no independent device replication.",
    },
    # ------------------------------------------------------------------ La3Ni2O7 pressure
    {
        "key": "la3ni2o7_pressure_bulk",
        "name": "Bulk ~80 K superconductivity in pressurized La3Ni2O7",
        "claim": "La3Ni2O7-type bilayer nickelates superconduct near 80 K above ~14 GPa as a bulk "
                 "(not filamentary) state.",
        "material": "La3Ni2O7, La2PrNi2O7, La2SmNi2O7 under pressure",
        "original_ids": ["arXiv:2305.09586"],
        "original_group": ["Meng Wang"],
        "topic_patterns": [r"La3Ni2O7|La2PrNi2O7|La2SmNi2O7|bilayer nickelate", r"pressur", r"superconduct"],
        "labels": {
            "arXiv:2410.10275": (S, EXP, "NV imaging of the Meissner effect (Yu group)"),
            "arXiv:2501.14584": (S, EXP, "bulk SC up to 96 K in La2SmNi2O7, zero resistance + Meissner"),
            "arXiv:2509.11557": (S, EXP, "zero resistance and Meissner effect in the same crystal"),
            "arXiv:2509.12606": (S, EXP, "d-wave gap in pressurized single crystals"),
            "arXiv:2511.15265": (S, EXP, "bulk SC coincides with Amam->Fmmm transition (original group)"),
            "arXiv:2607.27607": (S, EXP, "hydrostatic single crystals: bulk SC with I4/mmm transition"),
            "arXiv:2510.13342": (S, EXP, "Sm-doped series, onset Tc up to 89 K (original group)"),
            "arXiv:2605.04562": (S, EXP, "oxygen-controlled phase purity and SC (original group)"),
            "arXiv:2602.23842": (S, CM, "Reply defending 62% ZFC phase fraction in La2SmNi2O7"),
            "arXiv:2603.01062": (S, CM, "Response defending demagnetization-corrected volume fractions"),
            "arXiv:2410.06602": (C, EXP, "nanoscale structural phase separation; filamentary picture"),
            "arXiv:2510.02429": (C, EXP, "NV maps: strongly heterogeneous ('filamentary') diamagnetism"),
            "arXiv:2602.19282": (C, CM, "~2x overestimation of SC volume fraction in RP nickelates"),
            "arXiv:2602.23240": (C, CM, "threefold error in La2SmNi2O7 ZFC fraction (accepts bulk SC)"),
            "arXiv:2501.15929": (N, EXP, "ambient pressure: <0.2% volume fraction at 80 K"),
            "arXiv:2510.12250": (N, EXP, "1313 polymorph superconducts only at 3.6 K"),
        },
        "status": "partially_replicated",
        "status_note": "Superconductivity is reproduced by many groups; the in-window dispute has "
                       "narrowed to how large the bulk volume fraction is.",
    },
    # ------------------------------------------------------------------ nickelate films
    {
        "key": "nickelate_film_ambient_sc",
        "name": "Ambient-pressure superconductivity in strained (La,Pr)3Ni2O7 films",
        "claim": "Compressively strained bilayer nickelate films superconduct at ambient pressure "
                 "with onset Tc ~ 40 K.",
        "material": "La3Ni2O7 / (La,Pr)3Ni2O7 / La2PrNi2O7 films on SrLaAlO4",
        "original_ids": ["arXiv:2412.16622"],
        "original_group": ["Zhuoyu Chen", "Qi-Kun Xue"],
        "topic_patterns": [r"La3Ni2O7|La2PrNi2O7|\(La,Pr\)3Ni2O7|bilayer nickelate|La2LnNi2O7", r"film", r"superconduct"],
        "labels": {
            "arXiv:2501.08022": (S, EXP, "Hwang group: SC in compressively strained La2PrNi2O7 films"),
            "arXiv:2505.12603": (S, EXP, "Nie group: SC phase diagram in Sr-doped films"),
            "arXiv:2506.15319": (S, EXP, "Tsukazaki group: strain tuning of SC"),
            "arXiv:2506.01788": (S, EXP, "Wen group: SC gap and bosonic mode"),
            "arXiv:2508.11581": (S, EXP, "Z. Zhu group: oxygen recycling stabilizes SC"),
            "arXiv:2604.09807": (S, EXP, "Preziosi group: ozone-tuned SC films"),
            "arXiv:2608.01295": (S, EXP, "X. Chen group: high-Tc SC from compressive strain"),
            "arXiv:2603.29531": (S, EXP, "L. Sun group: pressure enhances film SC"),
            "arXiv:2605.15703": (S, EXP, "J. Wang group: U-shaped gap in SC films"),
            "arXiv:2501.09255": (S, EXP, "ARPES on SC films (original group)"),
            "arXiv:2608.17745": (S, EXP, "Tsukazaki group: La2LnNi2O7 films bridge ambient and high-pressure SC"),
            "arXiv:2603.02685": (N, TH, "theory: possible Tc enhancement in films"),
            "arXiv:2512.04708": (S, EXP, "onset above 60 K (original group)"),
            "arXiv:2604.07807": (C, EXP, "granular SC; two-step transition, Tc,zero ~ 10 K"),
            "arXiv:2603.11235": (N, RV, "review"),
            "arXiv:2605.11584": (N, RV, "review"),
        },
        "status": "partially_replicated",
        "status_note": "Reproduced by >= 8 independent groups within months; what remains open is "
                       "granularity, the onset/zero-resistance gap and phase purity.",
    },
    # ------------------------------------------------------------------ Hg-1223 PQP
    {
        "key": "hg1223_pressure_quench",
        "name": "151 K ambient-pressure superconductivity in pressure-quenched Hg-1223",
        "claim": "A pressure-quench protocol (PQP) retains Tc up to 151 K in HgBa2Ca2Cu3O8+d at "
                 "ambient pressure (record ambient Tc).",
        "material": "HgBa2Ca2Cu3O8+delta",
        "original_ids": ["arXiv:2603.12437"],
        "original_group": ["Ching-Wu Chu"],
        "topic_patterns": [r"pressure[- ]quench|\bPQP\b|Hg-?1223|HgBa2Ca2Cu3O"],
        "labels": {
            "arXiv:2502.01881": (N, EXP, "same group, earlier: PQP retains SC in Bi0.5Sb1.5Te3 (method precursor, not a follow-up)"),
            "arXiv:2602.05624": (N, EXP, "ARPES on ordinary Hg1223 (Tc 133 K), unrelated to PQP"),
            "arXiv:2606.08181": (N, TH, "ab initio Hg1223 mechanism, unrelated to PQP"),
        },
        "status": "unreplicated",
        "status_note": "Single-group result, peer reviewed (PNAS) but only ~6 months old; "
                       "no independent attempt (positive or null) in the corpus yet.",
    },
    # ------------------------------------------------------------------ LaSc2H24
    {
        "key": "lasc2h24_room_temperature_sc",
        "name": "Room-temperature superconductivity in LaSc2H24",
        "claim": "La-Sc alloy + ammonia borane at 250-260 GPa forms hexagonal LaSc2H24 with "
                 "Tc onset 271-298 K.",
        "material": "LaSc2H24 (megabar pressure)",
        "original_ids": ["arXiv:2510.01273", "doi:10.21203/rs.3.rs-7755852/v1"],
        "original_group": ["Yanming Ma", "Guangtao Liu"],
        "topic_patterns": [r"LaSc2H|La-Sc-H|La-Sc alloy|lanthanum[- ]scandium"],
        "labels": {
            "arXiv:2601.01398": (S, TH, "same group: isotropic single-gap theory of LaSc2H24"),
            "arXiv:2605.29985": (C, EXP, "7 synthesis attempts at 250-280 GPa, no SC at 245-300 K"),
            "arXiv:2509.22877": (N, RV, "ternary hydride review mentions LaSc2H24 as promising"),
        },
        "status": "contested",
        "status_note": "One positive group, one independent null (with the caveat that the null "
                       "used a different precursor route).",
    },
    # ------------------------------------------------------------------ hydride flux trapping
    {
        "key": "hydride_flux_trapping",
        "name": "Flux trapping / Meissner evidence for hydride superconductivity",
        "claim": "Trapped-flux and diamagnetic measurements establish bulk superconductivity in "
                 "megabar hydrides (H3S, LaH10).",
        "material": "H3S, LaH10, La-based superhydrides",
        "original_ids": ["arXiv:2206.14108"],
        "original_group": ["Mikhail I. Eremets", "Vasily S. Minkov"],
        "topic_patterns": [r"hydride|H3S|LaH10|superhydride", r"trapped flux|flux trapping|meissner|diamagnet"],
        "labels": {
            "arXiv:2510.21877": (S, EXP, "NV imaging: shielding and strong flux trapping in LaH9.6 (independent)"),
            "arXiv:2410.08730": (S, EXP, "trapped flux / memory effect in ternary La polyhydrides (Struzhkin group)"),
            "arXiv:2411.10522": (S, CM, "Nat Rev Phys Comment by 15 physicists: 'hydride superconductivity is real'"),
            "arXiv:2412.05291": (C, CM, "Hirsch-Marsiglio Reply maintaining the flux data are inconsistent with SC"),
            "arXiv:2501.01466": (C, CM, "Hirsch: questions the Nat Rev Phys Comment"),
            "arXiv:2412.07792": (C, CM, "Zen: flux-creep protocol in the Nat. Phys. correction is invalid"),
            "arXiv:2505.05176": (N, EXP, "methodology benchmark for diamagnetism in DACs"),
            "arXiv:2104.03925": (C, TH, "(pre-window) Hirsch-Marsiglio flux-trapping test proposal"),
            "arXiv:2207.01541": (C, CM, "(pre-window) Hirsch-Marsiglio 'evidence against' the trapped-flux data"),
            "arXiv:2312.04495": (S, CM, "(pre-window) Comment 'Is MgB2 a superconductor?' defending the data"),
        },
        "status": "contested",
        "status_note": "Independent groups now report flux trapping; the critique comes from a "
                       "small, persistent set of authors.",
    },
    # ------------------------------------------------------------------ kagome TRSB
    {
        "key": "av3sb5_trsb_loop_current",
        "name": "Time-reversal symmetry breaking / loop currents in kagome AV3Sb5",
        "claim": "The charge-density-wave state of AV3Sb5 (A = K, Rb, Cs) spontaneously breaks "
                 "time-reversal symmetry (orbital loop currents).",
        "material": "CsV3Sb5, KV3Sb5, RbV3Sb5",
        "original_ids": ["arXiv:2106.13443"],
        "original_group": ["Z. Guguchia"],
        "topic_patterns": [r"[CKR][sb]?V3Sb5|AV3Sb5|Cs3Sb5", r"time[- ]reversal|TRSB|kerr|loop[- ]current|orbital magnetism|imaginary|μSR|muon"],
        "labels": {
            "arXiv:2411.18744": (S, EXP, "muSR: depth-tunable TRSB onset (original group)"),
            "arXiv:2503.19032": (S, EXP, "single magnetic atoms: loop-current order below 30 K"),
            "arXiv:2505.05150": (S, EXP, "tuning fork: tiny c-axis moment, TRSB below 30 K"),
            "arXiv:2506.04601": (S, EXP, "field-trainable nonreciprocal Ic: loop-current CDW"),
            "arXiv:2605.05101": (S, EXP, "NQR: ~1 mT loop-current fields, imaginary CDW"),
            "arXiv:2606.25251": (S, EXP, "NMR: loop currents with broken C6"),
            "arXiv:2510.01305": (S, CM, "Madhavan Reply: field-induced CDW switching is intrinsic"),
            "arXiv:2608.24927": (S, CM, "Matsuda Reply: mosaicity cannot explain NQR asymmetry"),
            "arXiv:2608.26022": (S, EXP, "field-free SC diode linked to CDW TRSB"),
            "arXiv:2412.02469": (S, EXP, "resistive anisotropy 'implying possible' TRSB chiral order"),
            "arXiv:2510.26010": (C, EXP, "Sagnac Kerr: no spontaneous Kerr signal (< ~100 nrad)"),
            "arXiv:2509.22634": (C, CM, "Zeljkovic Comment: STM field effects are artifacts"),
            "arXiv:2608.13579": (C, CM, "Mitrovic Comment: iCDW claim unsupported by the NQR data"),
            "arXiv:2503.15849": (C, EXP, "low-field Hall anomaly from tiny high-mobility pockets, not AHE"),
            "arXiv:2411.04848": (C, EXP, "ALC-muSR: extra relaxation from charge rearrangement"),
            "arXiv:2512.11341": (N, EXP, "field-induced momentum-dependent symmetry breaking"),
        },
        "status": "contested",
        "status_note": "Many independent positive probes and several independent nulls, with two "
                       "live Comment/Reply exchanges in the trailing window.",
    },
    # ------------------------------------------------------------------ UTe2 chiral
    {
        "key": "ute2_chiral_sc",
        "name": "Chiral (TRSB) zero-field superconductivity in UTe2",
        "claim": "UTe2 is a chiral, two-component, time-reversal-breaking spin-triplet "
                 "superconductor at zero field.",
        "material": "UTe2",
        "original_ids": ["arXiv:2002.02539", "arXiv:2105.13721"],
        "original_group": ["Johnpierre Paglione", "Aharon Kapitulnik", "T. Shibauchi"],
        "known_venue": "Hayes et al., Science (2021) (scout notes)",
        "topic_patterns": [r"UTe2", r"chiral|time[- ]reversal|TRSB|kerr|two-component|multicomponent|order parameter"],
        "labels": {
            "arXiv:2501.16636": (C, EXP, "STM surface band: non-chiral B1u/B2u/B3u"),
            "arXiv:2503.17450": (C, EXP, "vortex STM: non-chiral p-wave"),
            "arXiv:2503.17761": (C, EXP, "QPI: time-reversal conserving B3u"),
            "arXiv:2602.02490": (C, EXP, "QSB: time-reversal conserving B3u"),
            "arXiv:2603.17905": (N, EXP, "multicomponent SC only near a pressure tetracritical point"),
            "arXiv:2604.25896": (N, EXP, "field-induced multicomponent SC (H || b)"),
            "arXiv:2504.01584": (N, TH, "topology classification assuming TRSB"),
        },
        "status": "refuted",
        "status_note": "No in-window supportive measurement; four STM studies (two groups) favour a "
                       "non-chiral B3u state. Multicomponent SC survives only in field/pressure.",
    },
    # ------------------------------------------------------------------ UTe2 PDW
    {
        "key": "ute2_pdw",
        "name": "Pair-density wave in UTe2",
        "claim": "UTe2 hosts a (bulk-relevant) pair-density-wave state intertwined with the "
                 "surface CDW seen by STM.",
        "material": "UTe2",
        "original_ids": ["arXiv:2209.10859", "arXiv:2207.09491"],
        "original_group": ["J. C. Séamus Davis", "Vidya Madhavan"],
        "originals_independent": True,
        "topic_patterns": [r"UTe2", r"pair[- ]density|PDW|charge density wave|CDW|charge order"],
        "labels": {
            "arXiv:2603.08688": (S, EXP, "parent PDW and descendant CDWs resolved (Madhavan)"),
            "arXiv:2601.02192": (N, EXP, "QPI and field-suppressed CDW (Madhavan)"),
            "arXiv:2504.12505": (C, EXP, "surface CDW, purely electron-driven, no bulk role"),
            "arXiv:2603.27211": (C, EXP, "charge orders disfavour Fermi-surface-nesting or primary-PDW pictures"),
            "arXiv:2603.12097": (N, EXP, "CDW manipulation and Kondo resonance"),
            "arXiv:2503.24390": (N, TH, "bulk-surface intertwining proposal"),
        },
        "status": "contested",
        "status_note": "Seen by two STM groups at origin, but in-window STM from other groups ties "
                       "the modulations to the surface and not to a primary PDW.",
    },
    # ------------------------------------------------------------------ RuCl3
    {
        "key": "rucl3_half_quantized_thermal_hall",
        "name": "Half-quantized thermal Hall effect in alpha-RuCl3",
        "claim": "alpha-RuCl3 shows a half-integer quantized thermal Hall plateau from chiral "
                 "Majorana edge modes of a Kitaev spin liquid.",
        "material": "alpha-RuCl3",
        "original_ids": ["arXiv:1805.05022"],
        "original_group": ["Y. Matsuda", "T. Shibauchi", "Y. Kasahara"],
        "topic_patterns": [r"RuCl3", r"thermal hall|half[- ]quantiz|quantized thermal|majorana"],
        "labels": {
            "arXiv:2410.18342": (S, EXP, "ultraclean crystals: plateau, with imperfections affecting quantization (original group)"),
            "arXiv:2505.00971": (S, EXP, "Majorana-like bulk dispersions in ultraclean crystals (original group)"),
            "arXiv:2608.18530": (S, EXP, "KQSL persists at high field (original group)"),
            "arXiv:2505.05417": (S, EXP, "geometry dependence: chiral fermion edge-mode contribution (ORNL)"),
            "arXiv:2510.06443": (C, EXP, "phonon Hall viscosity: thermal Hall is phononic (and intrinsic)"),
            "arXiv:2505.03879": (N, TH, "proposed geometry test"),
            "arXiv:2507.16558": (N, TH, "kappa_xy/T overshoots half-quantization in models"),
        },
        "status": "contested",
        "status_note": "Positive in-window results are mostly the original Kyoto/Tokyo team; one "
                       "independent geometry study is supportive, one high-profile study assigns "
                       "the signal to phonons.",
    },
    # ------------------------------------------------------------------ Ta2NiSe5
    {
        "key": "ta2nise5_excitonic_insulator",
        "name": "Excitonic-insulator ground state of Ta2NiSe5",
        "claim": "The 326 K transition of Ta2NiSe5 is driven mainly by exciton condensation "
                 "(electronic), not by the lattice.",
        "material": "Ta2NiSe5",
        "original_ids": [],
        "original_group": [],
        "known_venue": "Lu et al., Nat. Commun. 8, 14408 (2017) (scout notes; no arXiv record)",
        "topic_patterns": [r"Ta2NiSe5|Ta2Ni\(Se,S\)5"],
        "labels": {
            "arXiv:2504.10837": (S, EXP, "elastocaloric: transition largely excitonic"),
            "arXiv:2509.15771": (S, EXP, "NEXAFS: excitonic insulating state"),
            "arXiv:2512.03011": (S, EXP, "STM: dominant excitonic instability"),
            "arXiv:2512.12439": (S, EXP, "substrate tuning manifests excitonic interactions"),
            "arXiv:2601.23136": (S, TH, "metastable excitonic phase decoupled from the lattice"),
            "arXiv:2508.12363": (C, EXP, "UED: gap suppression explained structurally"),
            "arXiv:2509.09620": (C, EXP, "ultra-strong electron-phonon coupling drives transition"),
            "arXiv:2512.09751": (C, EXP, "gating 'rules out a dominant excitonic mechanism'"),
            "arXiv:2505.17324": (C, TH, "DFT: non-excitonic mechanism"),
            "arXiv:2607.11679": (N, EXP, "soft-phonon transport anomaly with excitonic fluctuations"),
            "arXiv:2007.02909": (C, EXP, "(pre-window) 'symmetry breaking is structural in nature'"),
        },
        "status": "contested",
        "status_note": "A genuine two-sided debate, each side with several independent groups.",
    },
    # ------------------------------------------------------------------ rhombohedral chiral SC
    {
        "key": "rhombohedral_graphene_chiral_sc",
        "name": "Chiral superconductivity in rhombohedral multilayer graphene",
        "claim": "Rhombohedral tetra/pentalayer graphene hosts a chiral, time-reversal-breaking "
                 "superconductor emerging from a spin-valley-polarized quarter metal.",
        "material": "rhombohedral 4-6 layer graphene",
        "original_ids": ["arXiv:2408.15233"],
        "original_group": ["Long Ju"],
        "topic_patterns": [r"rhombohedral|pentalayer|tetralayer|hexalayer", r"graphene", r"chiral supercond|superconduct"],
        "labels": {
            "arXiv:2605.13303": (S, EXP, "nanoSQUID imaging of TRSB chiral domains (Zeldov, with Ju)"),
            "arXiv:2607.06520": (S, EXP, "switchable chiral SC quartet in hexalayer (with Ju)"),
            "arXiv:2509.03295": (S, EXP, "family of unconventional SCs (Ju)"),
            "arXiv:2608.29873": (S, EXP, "chiral SC across a Lifshitz transition (X. Liu / T. Li)"),
            "arXiv:2504.05129": (S, EXP, "hexalayer SC with magnetism and hysteretic transitions (J.I.A. Li)"),
            "arXiv:2408.12584": (S, EXP, "(pre-window) SC next to QAH in rhombohedral graphene (independent)"),
            "arXiv:2605.30316": (N, EXP, "magnetization imaging bounds 'condensation magnetization' (Young)"),
            "arXiv:2606.05356": (N, EXP, "normal state richer than assumed; chirality of pairing open"),
            "arXiv:2508.15909": (N, EXP, "semimetallic hexalayer SC + orbital magnetism"),
            "arXiv:2606.31851": (N, TH, "proposed Hall-drag signature of chiral SC"),
            "arXiv:2608.12586": (N, TH, "proposed thermal Hall readout of the BdG Chern number"),
        },
        "status": "partially_replicated",
        "status_note": "Independent transport groups see SC from polarized parent states; direct "
                       "TRSB imaging so far includes the original group as co-authors.",
    },
    # ------------------------------------------------------------------ FQAH rhombohedral
    {
        "key": "rhombohedral_graphene_fqah",
        "name": "Fractional quantum anomalous Hall effect in rhombohedral graphene/hBN",
        "claim": "Zero-field fractional Chern insulators (FQAH plateaus) in rhombohedral "
                 "pentalayer graphene aligned to hBN.",
        "material": "rhombohedral multilayer graphene / hBN moire",
        "original_ids": ["arXiv:2309.17436"],
        "original_group": ["Long Ju"],
        "topic_patterns": [r"rhombohedral|pentalayer|multilayer graphene", r"fractional (?:quantum )?anomalous hall|FQAH|fractional chern"],
        "labels": {
            "arXiv:2505.01767": (S, EXP, "integer and fractional Chern insulators in RMG/hBN (independent)"),
            "arXiv:2606.06450": (S, EXP, "nu = 1/3 FQAH (Ashoori, with Ju)"),
            "arXiv:2609.09422": (S, EXP, "FCI transitions and gaps (Ju)"),
            "arXiv:2512.21612": (N, EXP, "fractional high-Chern insulator, different (twisted Bernal/rhombohedral) stack"),
            "arXiv:2408.10203": (N, EXP, "(pre-window) EQAH replaces FQAH at lower T (Ju)"),
            "arXiv:2608.24684": (N, EXP, "STM: moire modulation vanishes below ~10 nm period"),
            "arXiv:2507.20647": (N, EXP, "hBN alignment orientation controls moire strength"),
            "arXiv:2602.12737": (N, RV, "review"),
        },
        "status": "partially_replicated",
        "status_note": "Independent FCI observation exists; the mechanism (moire vs. interaction) "
                       "and the EQAH competition remain open.",
    },
    # ------------------------------------------------------------------ FQSH tMoTe2
    {
        "key": "tmote2_fqsh",
        "name": "Fractional quantum spin Hall effect in 2.1-degree twisted MoTe2",
        "claim": "A time-reversal-symmetric fractional QSH insulator at nu = 3 in 2.1-degree "
                 "twisted bilayer MoTe2.",
        "material": "twisted bilayer MoTe2",
        "original_ids": ["arXiv:2402.03294"],
        "original_group": ["Kin Fai Mak", "Jie Shan"],
        "known_venue": "Kang et al., Nature (2024) (scout notes)",
        "topic_patterns": [r"fractional quantum spin hall|FQSH|fractional topological insulator"],
        "labels": {
            "arXiv:2501.02525": (C, EXP, "same group: spontaneous TRSB at nu = 3 below 20 mT"),
            "arXiv:2601.18508": (N, EXP, "candidate FTI at nu = -4/3 in 3.7-3.9 degree devices (different state)"),
            "arXiv:2608.24989": (N, TH, "QSH crystals at fractional filling near 5 degrees (does not address the 2.1-degree claim)"),
        },
        "status": "unreplicated",
        "status_note": "No independent transport reproduction; the only in-window experiment is the "
                       "original group qualifying its own state.",
    },
    # ------------------------------------------------------------------ graphite RT SC
    {
        "key": "graphite_room_temperature_sc",
        "name": "Ambient-pressure room-temperature superconductivity in graphite",
        "claim": "Graphite (intercalated with Li alloys, wrinkled nanoflakes, or sorted grains) "
                 "hosts local superconductivity above room temperature at ambient pressure.",
        "material": "intercalated / defective graphite",
        "original_ids": ["arXiv:2410.18020", "arXiv:2510.03256", "arXiv:2609.15712"],
        "original_group": ["Didier Dufeu", "Mikhail I. Eremets", "Vasily S. Minkov", "Roman V. Yusupov"],
        "topic_patterns": [r"graphite|graphene", r"room[- ]temperature superconduct|above room temperature|high-temperature superconductivity|Tc.{0,4}>.{0,3}400|ideal diamagnetism"],
        "labels": {
            "doi:10.20944/preprints202510.2304.v1": (S, TH, "Talantsev: e-ph analysis of 2510.03256 resistivity"),
            "doi:10.21203/rs.3.rs-5876926/v1": (S, TH, "proton-mediated pairing at graphite-alkane interfaces"),
            "arXiv:2604.14395": (C, EXP, "authors retract their graphene-heptane 'ideal diamagnetism' (artifact)"),
        },
        "status": "unreplicated",
        "status_note": "Three unrelated preparations, three groups, each unreplicated; high-Tc "
                       "fractions < 0.1 %; the closest related ambient claim was withdrawn in "
                       "substance by its own authors.",
    },
    # ------------------------------------------------------------------ LK-99
    {
        "key": "lk99_apatite",
        "name": "Room-temperature superconductivity in Cu-doped lead apatite (LK-99)",
        "claim": "Pb10-xCux(PO4)6O is an ambient-pressure superconductor with Tc >= 400 K.",
        "material": "Cu-substituted lead apatite",
        "original_ids": ["arXiv:2307.12008"],
        "original_group": ["Sukbae Lee", "Young-Wan Kwon"],
        "topic_patterns": [r"LK-99|lead[- ]apatite|Pb10-xCux|copper[- ](?:doped|substituted) (?:lead )?apatite|Cu-doped apatite"],
        "labels": {
            "arXiv:2603.23377": (C, EXP, "reproducible anomalies are glassy CuS cluster magnetism, not SC"),
            "doi:10.21203/rs.3.rs-10086532/v1": (C, EXP, "high-purity Cu/S apatite: no transport or diamagnetic SC signature"),
            "osti:2586715": (C, EXP, "NMR: non-magnetic insulator"),
            "doi:10.5281/zenodo.20779430": (S, TH, "speculative 'Spacetime Ladder Theory' reinterpretation"),
            "arXiv:2410.03722": (N, TH, "post-mortem; apatite as flat-band platform"),
            "arXiv:2509.20260": (N, TH, "screening method for Cu-Pb apatites"),
        },
        "status": "refuted",
        "status_note": "Out-of-window original; every in-window experiment is null; the only "
                       "positive item is a non-peer-reviewed Zenodo theory note.",
    },
]

# Claims reported as the Q6 answer (6-10). Chosen to cover the four statuses, the
# highest noise scores, and low-score controls (La3Ni2O7 under pressure, RuCl3,
# AV3Sb5) that show the filter separates single-group claims from broadly
# reproduced or genuinely two-sided ones.
Q6_SELECTION = [
    "lk99_apatite",
    "msft_tgp_majorana",
    "lasc2h24_room_temperature_sc",
    "graphite_room_temperature_sc",
    "ruo2_bulk_altermagnet",
    "hg1223_pressure_quench",
    "av3sb5_trsb_loop_current",
    "ute2_chiral_sc",
    "rucl3_half_quantized_thermal_hall",
    "la3ni2o7_pressure_bulk",
]
