# -*- coding: utf-8 -*-
"""Manual verification log for the 2026-11 species feature audit (docs/SPECIES_AUDIT.md), keyed by slug.

status: "fixed" (a tag changed on outside evidence) or "checked" (outside reference agrees with the tags that were looked at).
Only what is written here was checked by hand; reports/species_xref.json adds an automatic comparison with one outside page
per species. Nothing here is a mycologist's review: "expert" names what a mycologist should still confirm.
"""
ME = "https://www.mushroomexpert.com/"
MK = "https://www.mykoweb.com/CAF/species/"

AUDIT = {
    "laetiporus-sulphureus": dict(status="fixed", sources=[ME + "laetiporus_sulphureus.html", MK + "Laetiporus_gilbertsonii.html"],
        notes="Pore surface: 2–4 pores per mm (MushroomExpert); western L. gilbertsonii 'lower surface finely pored' (MykoWeb). No stem, shelving clusters. "
              "Tags kept (pores, wood, white spore print); added alt other / ridges so a near-smooth or 'other form' answer keeps it as 冲突.",
        expert="Which Laetiporus species occur in the PNW (L. conifericola, L. gilbertsonii) and whether the page should name them."),
    "grifola-frondosa": dict(status="fixed", sources=[ME + "grifola_frondosa.html"],
        notes="1–3 angular to nearly tooth-like pores per mm; rosettes at the base of trees. Added alt other / ridges and substrate ground."),
    "fistulina-hepatica": dict(status="fixed", sources=[ME + "fistulina_hepatica.html"],
        notes="Tubes distinctly separated, visible with a hand lens; tongue-shaped. Added alt other."),
    "hypomyces-lactifluorum": dict(status="fixed", sources=[ME + "hypomyces_lactifluorum.html", MK + "Hypomyces_lactifluorum.html"],
        notes="Host gills 'reduced to folds' (MykoWeb): added alt ridges. Removed the old finder wording 「橙色硬壳」 from the fertile-surface options: the crust is the parasite on the cap and gills, not a fertile-surface type."),
    "omphalotus-illudens": dict(status="fixed", sources=[ME + "omphalotus_illudens.html"],
        notes="True gills running down the stem; clusters on stumps or buried roots; spore print white to creamy or pale yellow. Added alt ridges (looks like a chanterelle) and substrate ground (buried roots).",
        expert="The site's text says O. olivascens is the western species; confirm current PNW records."),
    "amanita-smithiana": dict(status="fixed", sources=[ME + "amanita_smithiana.html"],
        notes="Ring frequently torn or missing; universal veil fragments in zones at the top of the bulb. A 'volva = yes' answer now keeps it (冲突) instead of removing it; toxic species are never removed by a ring answer."),
    "galerina-marginata": dict(status="fixed", sources=[ME + "galerina_marginata.html"],
        notes="Thin ring or ring zone 'which may disappear'; rusty brown spore print; on wood. Marked ringVar and added substrate ground (the site's own text: sometimes appears to grow from the ground)."),
    "amanita-phalloides": dict(status="checked", sources=[ME + "amanita_phalloides.html"],
        notes="Sacklike white volva (sometimes underground or broken up); ring typically persists but sometimes lost; white spore print. Tags agree. Added the egg-stage alt (other).",
        expert="Egg-stage look-alike wording (puffball) for all volvate Amanita."),
    "amanita-bisporigera": dict(status="checked", sources=[ME + "amanita_bisporigera.html"], notes="White spore print, ring, volva. Tags agree. Added the egg-stage alt."),
    "lepiota-subincarnata": dict(status="fixed", sources=[MK + "Lepiota_subincarnata.html"],
        notes="Free white gills, banded veil on the stem (MykoWeb). The site's own sourced text says it grows on lawns, gardens and wood-chip mulch: added substrate wood (before, a 'wood' answer removed this deadly species) and ringVar.",
        expert="Confirm the wood-chip habitat with a second regional source."),
    "coprinus-comatus": dict(status="fixed", sources=[ME + "coprinus_comatus.html"],
        notes="'On lawns, wood chips, or hard-packed ground': substrate grass + wood + ground (was grass only)."),
    "armillaria-mellea": dict(status="fixed", sources=[ME + "armillaria_solidipes.html"],
        notes="Parasitic and saprobic on the wood and roots of conifers; well-developed ring; white spore print. Added substrate ground (buried roots, as the site's text says)."),
    "cantharellus-formosus": dict(status="fixed", sources=[ME + "cantharellus_formosus.html"],
        notes="Well developed false gills running down the stem; spore print whitish to pale yellowish: spore tags white + yellow (was yellow only)."),
    "cantharellus-tubaeformis": dict(status="fixed", sources=[ME + "craterellus_tubaeformis.html"],
        notes="Ridges and folds when young, false gills in age; in moss or on well-decayed, moss-covered logs: substrate ground + wood. Spore print white (agrees)."),
    "turbinellus-floccosus": dict(status="checked", sources=[ME + "turbinellus_floccosus.html"],
        notes="Shallow wrinkles and folds (ridges, agrees). Spore print only 'reported as yellowish', not verified by the author: kept as unknown (never used to exclude)."),
    "gyromitra-esculenta": dict(status="checked", sources=[ME + "gyromitra_esculenta.html"],
        notes="Brain-like cap; undersurface not generally exposed: 'other' fits. No spore print given: kept unknown."),
    "hericium": dict(status="fixed", sources=[ME + "hericium_americanum.html"],
        notes="Branched, long spines, no cap; white spore print. Added alt other (no cap underside). The eastern H. americanum page was used for structure only.",
        expert="Western Hericium species (H. abietis, H. coralloides group) for the page text."),
    "langermannia-gigantea": dict(status="checked", sources=[ME + "calvatia_gigantea.html"], notes="No cap; spore mass olive yellow to brown. 'other' and olive agree."),
    "lycoperdon-pyriforme": dict(status="checked", sources=[ME + "lycoperdon_pyriforme.html"], notes="Pear-shaped puffball on wood with white rhizomorphs; 'other' and wood agree."),
    "agaricus-augustus": dict(status="fixed", sources=[ME + "agaricus_augustus.html"], notes="Under conifers, roadsides, lawns and gardens: substrate ground + grass."),
    "chlorophyllum-rhacodes": dict(status="fixed", sources=[ME + "chlorophyllum_rhacodes.html"], notes="Lawns and disturbed ground: substrate ground + grass."),
    "flammulina-velutipes": dict(status="fixed", sources=[ME + "flammulina_velutipes.html"], notes="On stumps, logs and roots, 'sometimes appearing terrestrial': substrate wood + ground."),
    "paxillus-involutus": dict(status="fixed", sources=[ME + "paxillus_involutus.html"], notes="Mycorrhizal, 'apparently also capable of existing as a saprobe on wood': substrate ground + wood."),
    "morchella-esculenta": dict(status="fixed", sources=[],
        notes="The site's own text (and its North American note) says it also grows on bark mulch: substrate ground + wood. No outside page fetched this round.",
        expert="Honeycomb head vs Gyromitra / Verpa: confirm wording with a regional source."),
    "agaricus-silvaticus": dict(status="fixed", sources=[], notes="The site's own (book) text: on wood-chip mulch. Substrate ground + wood. Book-only species.", expert="No outside reference yet."),
    "tuber-aestivum": dict(status="fixed", sources=[], notes="Underground truffle: spore print not possible, now 'na' (was 'unknown')."),
    "tuber-magnatum": dict(status="fixed", sources=[], notes="Underground truffle: spore print 'na'."),
    "tuber-melanosporum": dict(status="fixed", sources=[], notes="Underground truffle: spore print 'na'."),
    "boletus-badius": dict(status="checked", sources=[ME + "imleria_badia.html"], notes="Mycorrhizal with conifers (the automatic 'wood' hit came from 'eastern hemlock', a tree name). Ground tag agrees."),
    "hypholoma-fasciculare": dict(status="checked", sources=[ME + "hypholoma_fasciculare.html"], notes="Spore print purple brown = our chocolate / purple-brown category (choc); tags agree. On wood, clustered."),
}
