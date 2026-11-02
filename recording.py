

import csv

import constants as c

LOG_COLUMNS = [
    "jatek",                  # hanyadik jatek (R-rel / automatikusan ujrainditva)
    "dontes",                 # az ugynok hanyadik dontese ebben a jatekban
    "tick",                   # szimulacios ido (1 tick = 1/60 mp jatekido)
    "ido_ms",                 # ugyanez ezredmasodpercben, egeszre kerekitve
    "akcio_id",               # a modell kimenete (0..21), -1 = jatek vege sor
    "akcio",                  # ember-olvashato nev
    "sikeres",                # 1 = az akcio vegrehajtodott, 0 = ervenytelen volt
    "szint",                  # aktualis szint (a dontes PILLANATABAN)
    "hullam_fut",             # 1 = a hullam mar el van inditva
    "elet",
    "penz",
    "ellensegek",             # palyan levo ellensegek szama
    "tornyok",                # lerakott tornyok szama
    "torony_szintek_osszege", # a tornyok fejlesztesi szintjeinek osszege
    "hullam_megolt",          # az aktualis hullamban eddig megolt ellensegek
    "hullam_elszalasztott",   # az aktualis hullamban eddig atjutott ellensegek
]


def snapshot(game):
    """A jatek allapotanak pillanatfelvetele (sima szotar), amit a naplo
    sorai hasznalnak. A dontes ELOTT kell meghivni, hogy az legyen a
    naploban, amit az ugynok a dontesekor latott."""
    w = game.world
    return {
        "tick": w.tick,
        "szint": w.level,
        "hullam_fut": 1 if game.level_started else 0,
        "elet": w.health,
        "penz": w.money,
        "ellensegek": len(game.enemy_group),
        "tornyok": len(game.turret_group),
        "torony_szintek_osszege": sum(t.upgrade_level for t in game.turret_group),
        "hullam_megolt": w.killed_enemies,
        "hullam_elszalasztott": w.missed_enemies,
    }


class ActionLogger:
    """Az AI donteseit CSV-be irja.

    Alapbol a "varakozas" dontesek NEM kerulnek a naploba (minden
    masodpercben ~6 db van belole, elnyomna a lenyeget); a --log-waits
    kapcsolo (log_waits=True) ezeket is beleirja. A 'dontes' oszlop
    sorszama a kihagyott varakozasokat is szamolja, igy a hezagokbol
    latszik, mennyit varakozott az ugynok."""

    def __init__(self, path, log_waits=False):
        self.path = path
        self.log_waits = log_waits
        self._file = open(path, "w", newline="", encoding="utf-8-sig")
        self._writer = csv.writer(self._file, delimiter=";")
        self._writer.writerow(LOG_COLUMNS)
        self.rows_written = 0

    def _write(self, episode, decision, snap, action_id, action_label, success):
        self._writer.writerow([
            episode,
            decision,
            snap["tick"],
            round(snap["tick"] * c.MS_PER_TICK),
            action_id,
            action_label,
            1 if success else 0,
            snap["szint"],
            snap["hullam_fut"],
            snap["elet"],
            snap["penz"],
            snap["ellensegek"],
            snap["tornyok"],
            snap["torony_szintek_osszege"],
            snap["hullam_megolt"],
            snap["hullam_elszalasztott"],
        ])
        self.rows_written += 1

    def log_decision(self, episode, decision, snap, action_id, action_label,
                     success, is_wait):
        if is_wait and not self.log_waits:
            return
        self._write(episode, decision, snap, action_id, action_label, success)

    def log_game_over(self, episode, decision, snap, outcome_text):
        self._write(episode, decision, snap, -1, f"JATEK VEGE: {outcome_text}", True)
        self._file.flush()

    def close(self):
        if not self._file.closed:
            self._file.flush()
            self._file.close()


class VideoRecorder:
    """A kirajzolt kepkockakat MP4-fajlba irja.

    Minden szimulacios tick egy kepkocka, a video fps-e a jatek fps-e
    (c.fps) -- vagyis a felvetel MINDIG valos (1x) sebessegu, akkor is,
    ha az elo ablakot a --speed gyorsitva mutatja, vagy a --headless
    modban a gep ennel sokkal gyorsabban szamolja."""

    def __init__(self, path, fps):
        try:
            import imageio_ffmpeg  # noqa: F401  (csak a meglet ellenorzese)
            try:
                import imageio.v2 as imageio
            except ImportError:
                import imageio
        except ImportError:
            raise SystemExit(
                "A videofelvetelhez az imageio es az imageio-ffmpeg kell:\n"
                "    pip install imageio imageio-ffmpeg"
            )
        self._writer = imageio.get_writer(
            path,
            fps=fps,
            codec="libx264",
            quality=7,
            pixelformat="yuv420p",
            macro_block_size=2,   # a 1020x720 meret igy nem lesz atmeretezve
        )
        self.path = path
        self.frames = 0

    def add_frame(self, frame):
        """frame: (magassag, szelesseg, 3) uint8 numpy-tomb."""
        import numpy as np
        self._writer.append_data(np.ascontiguousarray(frame))
        self.frames += 1

    def close(self):
        if self._writer is not None:
            self._writer.close()
            self._writer = None
