#!/usr/bin/env python3
"""Keep the RaimAction and RAIMSTORM in-game RAIMZY playlists in step with Apple Music.

Owner (Dr. Ephraim Oviawe / RAIMZY), 2026-10-21: "All my future albums and songs, automatically
added or included itself" on RaimAction and RAIMSTORM, and "No instruments".

What one run does (it is safe to run any number of times; a run with nothing new changes nothing):

 1. Asks the iTunes Lookup API for every song by RAIMZY (Apple artist id 1559337601).
 2. Keeps only the songs a game may stream:
      - trackExplicitness == "notExplicit" (an explicit track would push the games to 17+),
      - no "Instrumental" in the title,
      - already released (no pre-orders).
 3. For each such song missing from a playlist, looks for the released master on this Mac:
    iCloud Drive "MY SONGS" and, when the drive is mounted, /Volumes/Lexar/03_MUSIC-RAIMZY.
    A file is accepted only when
      - its length is within +/-2 s of Apple's trackTimeMillis, AND
      - its audio matches Apple's 30-second preview of that very track (a band-energy
        cross-correlation), so a demo, a "RELOADED" remake or another song of the same
        length is never taken for the released version.
    iCloud files that are only in the cloud ("dataless") are fetched with `brctl download`,
    their size is checked until it is complete (a dataless copy truncates silently), and they
    are handed back to iCloud with `brctl evict` afterwards. Nothing is ever deleted.
 4. Encodes the master the same way as every existing song: 128 kb/s MP3, 44.1 kHz stereo,
    loudnorm to -16 LUFS, into music/<id>.mp3 (GitHub Pages serves it to the games).
 5. Adds the song to BOTH music/raimaction.json and music/raimstorm.json (appended; RAIMSTORM's
    "first" song, "I'm the Bang", stays first), with listen = https://song.link/i/<appleTrackId>,
    apple_music_id = Apple's trackId of the released version and apple_music_url = its trackViewUrl
    (the games play through Apple Music for subscribers, so those plays count for royalties). Every
    existing entry is kept as it is and gets the two Apple fields too (matched by title and length).
 6. Writes tools/music/raimzy-sync-status.md (what is in, what is waiting for audio, what is
    excluded and why), then commits and pushes ~/econteur-apps only if something changed.

A clean song with no matching master is listed as "waiting for audio" and NOT added: both games
skip entries without an .mp3, so a link-only entry would do nothing.

To pin a master by hand (for example a file whose name and length are fine but whose preview check
fails because Apple's preview comes from a different edit), add it to tools/music/masters.json:
    {"1812070055": "/absolute/path/to/OSALOBUA.wav"}
A pinned file still has to pass the +/-2 s length rule.

Usage:
    python3 tools/music/sync_raimzy.py            # full run: sync, commit, push
    python3 tools/music/sync_raimzy.py --dry-run  # report only, touch nothing
    python3 tools/music/sync_raimzy.py --no-push  # commit locally but do not push
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.request
from pathlib import Path

try:  # C speed for the RMS frames; removed from Python 3.13, so keep a fallback.
    import audioop  # type: ignore
except Exception:  # pragma: no cover
    audioop = None
import array

# ---------------------------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
MUSIC_DIR = REPO / "music"
PLAYLISTS = [MUSIC_DIR / "raimaction.json", MUSIC_DIR / "raimstorm.json"]
STATUS_FILE = REPO / "tools" / "music" / "raimzy-sync-status.md"
PINS_FILE = REPO / "tools" / "music" / "masters.json"

ARTIST_ID = 1559337601  # Apple Music artist "Raimzy"
LOOKUP_URL = f"https://itunes.apple.com/lookup?id={ARTIST_ID}&entity=song&limit=200&country=US"
LISTEN_FMT = "https://song.link/i/{}"

HOME = Path.home()
SOURCES = [
    HOME / "Library/Mobile Documents/com~apple~CloudDocs/MY SONGS",
    Path("/Volumes/Lexar/03_MUSIC-RAIMZY"),
]
AUDIO_EXT = {".wav", ".aif", ".aiff", ".flac", ".m4a", ".mp3", ".alac"}
LOSSLESS = {".wav", ".aif", ".aiff", ".flac", ".alac"}
# Stem separations and instrumentals are never a released vocal master.
SKIP_NAME = re.compile(r"instrumental|\[(?:music|vocals|drums|bass|other|piano)\]|\.stem\.", re.I)
SKIP_DIRS = {".git", "node_modules", ".Trash", "_codex-copy"}

TOLERANCE_S = 2.0          # owner rule: master length within +/-2 s of Apple's
MATCH_THRESHOLD = 0.60     # preview correlation to accept a master; calibrated 2026-10-21: true pairs 0.75-0.90, other songs <= 0.36
MAX_DOWNLOADS = 40         # iCloud files fetched per run at most (disk is tight on this Mac)
DOWNLOAD_TIMEOUT_S = 900

CACHE_DIR = HOME / "Library/Caches/raimzy-sync"
PROBE_CACHE = CACHE_DIR / "probe-cache.json"
LOCK_FILE = CACHE_DIR / "sync.lock"

FFMPEG = shutil.which("ffmpeg") or str(HOME / ".local/bin/ffmpeg")
FFPROBE = shutil.which("ffprobe") or str(HOME / ".local/bin/ffprobe")
SF_DATALESS = 0x40000000

SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "is", "nor", "of", "on",
               "or", "the", "to", "too", "with"}


def log(msg: str) -> None:
    print(f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}", flush=True)


# ---------------------------------------------------------------------------------------------
# Apple catalogue
# ---------------------------------------------------------------------------------------------
def fetch_catalogue() -> list[dict]:
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(LOOKUP_URL, headers={"User-Agent": "econteur-raimzy-sync/1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            results = data.get("results") or []
            artist = [x for x in results if x.get("wrapperType") == "artist"]
            songs = [x for x in results if x.get("wrapperType") == "track" and x.get("kind") == "song"
                     and x.get("artistId") == ARTIST_ID]
            if not artist or not songs:
                raise RuntimeError(f"lookup returned {len(results)} results, {len(songs)} songs")
            return songs
        except Exception as e:  # network blips: retry, then give up without touching anything
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"iTunes lookup failed: {last}")


def released(t: dict) -> bool:
    try:
        when = dt.datetime.strptime(t["releaseDate"][:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return False
    return when <= dt.datetime.utcnow()


def exclusion(t: dict) -> str | None:
    """Why a song may not be streamed in the games, or None when it may."""
    if t.get("trackExplicitness") != "notExplicit":
        return f"Apple marks it {t.get('trackExplicitness', 'unknown')}"
    name = f"{t.get('trackName', '')} {t.get('trackCensoredName', '')}"
    if re.search(r"instrumental", name, re.I):
        return "instrumental"
    if not released(t):
        return f"not released until {t.get('releaseDate', '')[:10]}"
    if not t.get("trackTimeMillis"):
        return "Apple lists no length"
    return None


def smart_title(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").strip()
    s = re.sub(r"\s*\((?:RELOADED|Reloaded|reloaded)\)\s*", " ", s).strip()
    s = re.sub(r"\s*[\(\[]\s*feat\.?[^\)\]]*[\)\]]", "", s, flags=re.I).strip()
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:  # ALL CAPS -> Title Case
        words = s.lower().split()
        out = []
        for i, w in enumerate(words):
            out.append(w if (i and w in SMALL_WORDS) else w[:1].upper() + w[1:])
        s = " ".join(out)
        s = re.sub(r"\bI'm\b|\bi'm\b", "I'm", s)
    return s


def album_name(t: dict) -> str:
    c = t.get("collectionName", "")
    if c == "THE RECLAMED VOICE":       # Apple's catalogue keeps the distributor's typo
        return "THE RECLAIMED VOICE"
    c = re.sub(r"\s*[\(\[]\s*feat\.?[^\)\]]*[\)\]]", "", c, flags=re.I)
    c = re.sub(r"\s+-\s+(Single|EP)$", "", c).strip()
    return c


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "track"


def norm_words(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\((?:reloaded|feat[^)]*|remaster(?:ed)?|mx|mix)\)|\[[^\]]*\]", " ", s)
    s = re.sub(r"^\s*\d+\s*[.\-_]\s*", " ", s)              # "7. TITLE"
    s = re.sub(r"\b(raimzy|raimsy|eniggie|final|master(?:ed)?|mix|low|copy)\b", " ", s)
    s = s.replace("&", " and ").replace("'", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


# ---------------------------------------------------------------------------------------------
# Files: probing, iCloud, fingerprints
# ---------------------------------------------------------------------------------------------
def load_cache() -> dict:
    try:
        return json.loads(PROBE_CACHE.read_text())
    except Exception:
        return {}


def save_cache(c: dict) -> None:
    """Merge into the cache on disk (another run may have added to it meanwhile)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / "cache.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        merged = load_cache()
        merged.update(c)
        c.update(merged)
        tmp = PROBE_CACHE.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(merged))
        tmp.replace(PROBE_CACHE)


def is_dataless(p: Path) -> bool:
    try:
        return bool(os.stat(p).st_flags & SF_DATALESS)
    except Exception:
        return False


def probe_duration(p: Path, cache: dict) -> float | None:
    st = p.stat()
    key = f"{p}|{st.st_size}|{int(st.st_mtime)}"
    if key in cache:
        return cache[key]
    try:
        out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of",
                              "default=nw=1:nk=1", str(p)], capture_output=True, text=True, timeout=60)
        d = float(out.stdout.strip())
    except Exception:
        d = None
    cache[key] = d
    return d


def size_durations(size: int) -> list[float]:
    """Possible lengths of a PCM WAV/AIFF of `size` bytes (header ignored)."""
    out = []
    for rate in (44100, 48000):
        for width in (2, 3, 4):
            out.append(size / (rate * width * 2))
    return out


def icloud_fetch(p: Path) -> bool:
    """Materialise an iCloud file and wait until every byte is local."""
    want = p.stat().st_size
    subprocess.run(["brctl", "download", str(p)], capture_output=True, timeout=60)
    t0 = time.time()
    while time.time() - t0 < DOWNLOAD_TIMEOUT_S:
        if not is_dataless(p):
            try:
                with open(p, "rb") as f:            # read the tail: proves the bytes are really here
                    f.seek(max(0, want - 4096))
                    f.read()
                if p.stat().st_size == want:
                    return True
            except OSError:
                pass
        time.sleep(3)
    return False


def icloud_evict(p: Path) -> None:
    subprocess.run(["brctl", "evict", str(p)], capture_output=True, timeout=60)


BANDS = ["lowpass=f=200", "highpass=f=200,lowpass=f=800", "highpass=f=800,lowpass=f=2000",
         "highpass=f=2000"]
FPS = 10  # feature frames per second
SR = 8000


def features(p: Path, start: float | None = None, length: float | None = None) -> list[list[float]]:
    """Log band energies, FPS frames a second, for the four BANDS."""
    with tempfile.TemporaryDirectory(prefix="raimzy-fp-") as td:
        split = "".join(f"[s{i}]" for i in range(len(BANDS)))
        graph = f"[0:a]aformat=sample_fmts=s16:sample_rates={SR}:channel_layouts=mono,asplit={len(BANDS)}{split};"
        graph += ";".join(f"[s{i}]{b}[o{i}]" for i, b in enumerate(BANDS))
        cmd = [FFMPEG, "-v", "error", "-nostdin"]
        if start is not None:
            cmd += ["-ss", f"{start:.2f}"]
        if length is not None:
            cmd += ["-t", f"{length:.2f}"]
        cmd += ["-i", str(p), "-filter_complex", graph]
        outs = []
        for i in range(len(BANDS)):
            o = Path(td) / f"b{i}.raw"
            outs.append(o)
            cmd += ["-map", f"[o{i}]", "-f", "s16le", "-acodec", "pcm_s16le", str(o)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        step = SR // FPS * 2
        feats = []
        for o in outs:
            raw = o.read_bytes()
            band = []
            for k in range(0, len(raw) - step + 1, step):
                chunk = raw[k:k + step]
                if audioop is not None:
                    r = audioop.rms(chunk, 2)
                else:
                    a = array.array("h", chunk)
                    r = math.sqrt(sum(x * x for x in a) / len(a))
                band.append(math.log(1.0 + r))
            feats.append(band)
        n = min(len(b) for b in feats)
        return [b[:n] for b in feats]


def best_correlation(master: list[list[float]], probe: list[list[float]]) -> tuple[float, float]:
    """Highest mean Pearson correlation of `probe` slid along `master`; returns (score, offset_s)."""
    m = len(probe[0])
    n = len(master[0])
    if m < 50 or n < m:
        return 0.0, 0.0
    pz = []
    for b in probe:
        mu = sum(b) / m
        sd = math.sqrt(sum((x - mu) ** 2 for x in b) / m) or 1e-9
        pz.append([(x - mu) / sd for x in b])
    best, best_off = -1.0, 0
    nb = len(master)
    # running sums for fast window mean / sd
    pre = []
    for b in master:
        s, s2 = [0.0], [0.0]
        for x in b:
            s.append(s[-1] + x)
            s2.append(s2[-1] + x * x)
        pre.append((s, s2))
    for off in range(0, n - m + 1):
        tot = 0.0
        for bi in range(nb):
            s, s2 = pre[bi]
            mu = (s[off + m] - s[off]) / m
            var = (s2[off + m] - s2[off]) / m - mu * mu
            if var <= 1e-12:
                continue
            sd = math.sqrt(var)
            seg = master[bi]
            pzb = pz[bi]
            acc = 0.0
            for j in range(m):
                acc += seg[off + j] * pzb[j]
            tot += (acc / m - mu * sum(pzb) / m) / sd
        score = tot / nb
        if score > best:
            best, best_off = score, off
    return best, best_off / FPS


def preview_features(t: dict) -> list[list[float]] | None:
    url = t.get("previewUrl")
    if not url:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / f"preview-{t['trackId']}.m4a"
    if not dest.exists() or dest.stat().st_size < 10000:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "econteur-raimzy-sync/1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
        except Exception as e:
            log(f"   preview download failed for {t['trackId']}: {e}")
            return None
    # Skip the preview's fade-in and fade-out.
    return features(dest, start=2.0, length=25.0)


# ---------------------------------------------------------------------------------------------
# Finding a master
# ---------------------------------------------------------------------------------------------
class SourceUnreadable(RuntimeError):
    pass


def walk_sources() -> list[Path]:
    """Audio files in SOURCES. A source that exists but cannot be listed (macOS privacy/TCC: a launchd
    job needs Full Disk Access for iCloud Drive and external drives) raises, so a run never mistakes
    "not allowed to look" for "no master"."""
    files = []
    for root in SOURCES:
        if not root.exists():
            log(f"source not available: {root}")
            continue
        try:
            os.listdir(root)
        except OSError as e:
            exe = Path(sys.executable).resolve()
            app = next((q / "Resources/Python.app" for q in exe.parents if q.name.startswith("3.")
                        and (q / "Resources/Python.app").exists()), exe)
            raise SourceUnreadable(
                f"cannot read {root}: {e.strerror}. ACTION FOR USER: System Settings > Privacy & Security > "
                f"Full Disk Access > + > add {app} (the Python this job runs; Cmd-Shift-G to type the path), then "
                f"`launchctl kickstart gui/$(id -u)/com.econteur.raimzy-sync`.") from e
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in filenames:
                if fn.startswith("._") or fn.startswith("."):
                    continue
                p = Path(dirpath) / fn
                if p.suffix.lower() in AUDIO_EXT and not SKIP_NAME.search(fn):
                    files.append(p)
    return files


def file_key(p: Path) -> str:
    st = p.stat()
    return f"{p}|{st.st_size}|{int(st.st_mtime)}"


class MasterFinder:
    """Finds the released master of a song. Everything learnt about a file (its length, and how well
    it matches a song's Apple preview) is cached by path+size+mtime, so an iCloud file is fetched
    once in its life, not every day, and is handed back to iCloud straight after it is checked."""

    def __init__(self, files: list[Path], cache: dict, dry_run: bool, max_downloads: int):
        self.files = files
        self.cache = cache
        self.dry_run = dry_run
        self.max_downloads = max_downloads
        self.downloads = 0
        self.previews: dict[int, list[list[float]] | None] = {}
        self._dirty = 0
        # An iCloud-only file with a local twin (same name and size, e.g. a Lexar copy) is not
        # fetched: the twin stands in for it.
        local = set()
        for p in files:
            try:
                if not is_dataless(p):
                    local.add((p.name.lower(), p.stat().st_size))
            except OSError:
                pass
        self.local_twins = local

    def _save_soon(self) -> None:
        self._dirty += 1
        if self._dirty >= 25:
            save_cache(self.cache)
            self._dirty = 0

    def duration(self, p: Path) -> float | None:
        k = file_key(p)
        if k not in self.cache:
            if is_dataless(p):
                return None
            probe_duration(p, self.cache)
            self._save_soon()
        return self.cache.get(k)

    def candidates(self, t: dict) -> list[Path]:
        want = t["trackTimeMillis"] / 1000.0
        title = norm_words(smart_title(t["trackName"]))
        out = []
        for p in self.files:
            try:
                k = file_key(p)
                if k in self.cache or not is_dataless(p):
                    d = self.duration(p)
                    if d is not None and abs(d - want) <= TOLERANCE_S:
                        out.append(p)
                elif (p.name.lower(), p.stat().st_size) in self.local_twins:
                    continue
                else:  # iCloud only: guess the length from the size, or go by the name
                    named = bool(title) and title in norm_words(p.stem)
                    sized = p.suffix.lower() in {".wav", ".aif", ".aiff"} and any(
                        abs(d - want) <= TOLERANCE_S + 1.0 for d in size_durations(p.stat().st_size))
                    if named or sized:
                        out.append(p)
            except OSError:
                continue
        out.sort(key=lambda p: (title not in norm_words(p.stem), p.suffix.lower() not in LOSSLESS, str(p)))
        return out

    def fetch(self, p: Path) -> bool:
        """Make an iCloud-only file local. Caller must hand it back with icloud_evict()."""
        if self.dry_run or self.downloads >= self.max_downloads:
            return False
        self.downloads += 1
        log(f"   fetching from iCloud: {p}")
        if icloud_fetch(p):
            return True
        log(f"   iCloud fetch did not complete: {p}")
        icloud_evict(p)
        return False

    def preview(self, t: dict) -> list[list[float]] | None:
        if t["trackId"] not in self.previews:
            self.previews[t["trackId"]] = preview_features(t)
        return self.previews[t["trackId"]]

    def score(self, p: Path, t: dict) -> tuple[float | None, str]:
        """(preview match, note) for one file, from the cache when known."""
        want = t["trackTimeMillis"] / 1000.0
        k = file_key(p)
        sk = f"score|{k}|{t['trackId']}"
        if sk in self.cache:
            d = self.cache.get(k)
            return self.cache[sk], f"{p.name}: {d:.1f} s, preview match {self.cache[sk]:.2f} (cached)"
        prev = self.preview(t)
        if prev is None:
            return None, f"{p.name}: Apple preview unavailable"
        cloud = is_dataless(p)
        if cloud and not self.fetch(p):
            return None, f"{p.name}: in iCloud only (not fetched this run)"
        try:
            d = probe_duration(p, self.cache)
            if d is None or abs(d - want) > TOLERANCE_S:
                return None, f"{p.name}: {d if d is None else round(d, 1)} s"
            try:
                sc, off = best_correlation(features(p), prev)
            except Exception as e:
                return None, f"{p.name}: decode failed ({e})"
            self.cache[sk] = round(sc, 4)
            self._save_soon()
            return sc, f"{p.name}: {d:.1f} s, preview match {sc:.2f} @ {off:.0f}s"
        finally:
            if cloud:
                icloud_evict(p)

    def find(self, t: dict, pinned: str | None) -> tuple[Path | None, str]:
        want = t["trackTimeMillis"] / 1000.0
        if pinned:
            p = Path(pinned).expanduser()
            if not p.exists():
                return None, f"pinned master missing: {p}"
            d = self.cache.get(file_key(p)) if is_dataless(p) else self.duration(p)
            if d is None and is_dataless(p):
                if not self.fetch(p):
                    return None, f"pinned master not downloadable yet: {p}"
                d = probe_duration(p, self.cache)
                icloud_evict(p)
            if d is None or abs(d - want) > TOLERANCE_S:
                return None, f"pinned master length {d} s vs Apple {want:.1f} s"
            return p, f"pinned in masters.json ({d:.1f} s vs Apple {want:.1f} s)"
        cands = self.candidates(t)
        if not cands:
            return None, "no released master on this Mac yet"
        tried, best = [], None
        for p in cands:
            sc, note = self.score(p, t)
            tried.append(note)
            if sc is None or sc < MATCH_THRESHOLD:
                continue
            lossless = p.suffix.lower() in LOSSLESS
            if best is None or sc > best[0] + 0.02 or (abs(sc - best[0]) <= 0.02 and lossless and not best[2]):
                best = (sc, p, lossless)
        for n in tried:
            log(f"      {n}")
        if best:
            d = self.cache.get(file_key(best[1]))
            return best[1], f"{d:.1f} s vs Apple {want:.1f} s, preview match {best[0]:.2f}"
        # Details go to the log; the committed status file gets a stable line (no counts or scores
        # that change with which drives happen to be mounted).
        scored = sorted((self.cache.get(f"score|{file_key(p)}|{t['trackId']}") or 0, p.name) for p in cands)
        if scored:
            log(f"      closest: {scored[-1][1]} at {scored[-1][0]:.2f} (needs {MATCH_THRESHOLD:.2f})")
        return None, "no released master on this Mac yet"


# ---------------------------------------------------------------------------------------------
# Encoding and playlists
# ---------------------------------------------------------------------------------------------
def encode(master: Path, dest: Path, title: str, album: str, want_s: float) -> None:
    tmp = dest.with_name(f".{dest.stem}.partial.mp3")
    # Two-pass loudnorm: measure, then normalise linearly to -16 LUFS integrated.
    target = "I=-16:TP=-1.5:LRA=11"
    meas = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-i", str(master), "-map", "0:a:0", "-af",
                           f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True, timeout=900)
    af = f"loudnorm={target}"
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", meas.stderr)
    if m:
        j = json.loads(m.group(0))
        af = (f"loudnorm={target}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    cmd = [FFMPEG, "-v", "error", "-nostdin", "-y", "-i", str(master), "-map", "0:a:0", "-map_metadata", "-1",
           "-af", af, "-ar", "44100", "-ac", "2",
           "-c:a", "libmp3lame", "-b:a", "128k",
           "-metadata", "artist=RAIMZY", "-metadata", f"title={title}", "-metadata", f"album={album}",
           str(tmp)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=900)
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(tmp)], capture_output=True, text=True)
    d = float(out.stdout.strip())
    if abs(d - want_s) > TOLERANCE_S or tmp.stat().st_size < 500_000:
        tmp.unlink()  # our own half-written output, never a source file
        raise RuntimeError(f"encoded file is {d:.1f} s / {tmp.stat().st_size if tmp.exists() else 0} bytes")
    tmp.replace(dest)


def apple_id(entry: dict) -> int | None:
    m = re.search(r"song\.link/i/(\d+)", entry.get("listen", ""))
    return int(m.group(1)) if m else None


def title_similarity(a: str, b: str) -> float:
    import difflib
    return difflib.SequenceMatcher(None, norm_words(smart_title(a)), norm_words(smart_title(b))).ratio()


def released_match(entry: dict, length_s: float | None, songs: list[dict], by_id: dict) -> dict | None:
    """The Apple track an entry is: its song.link id when title and length agree, else the best
    title+length match among Apple's songs. Lengths compare the hosted MP3 with trackTimeMillis."""
    def fits(t: dict) -> bool:
        if length_s is None or not t.get("trackTimeMillis"):
            return False
        return abs(t["trackTimeMillis"] / 1000.0 - length_s) <= TOLERANCE_S
    for i in (entry.get("apple_music_id"), apple_id(entry)):
        t = by_id.get(i) if i else None
        if t is not None and fits(t) and title_similarity(entry.get("title", ""), t["trackName"]) >= 0.6:
            return t
    scored = sorted(((title_similarity(entry.get("title", ""), t["trackName"]), t) for t in songs if fits(t)),
                    key=lambda x: -x[0])
    if scored and scored[0][0] >= 0.8:
        return scored[0][1]
    return None


def read_json(p: Path) -> tuple[dict, str]:
    s = p.read_text()
    return json.loads(s), s


def dump_json(d: dict) -> str:
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=check)


def git_prepare() -> None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"~/econteur-apps is on '{branch}', not main; not touching it")
    dirty = git("status", "--porcelain", "--", "music", "tools/music").stdout.strip()
    if dirty:
        raise RuntimeError("uncommitted changes under music/ or tools/music/; not touching them:\n" + dirty)
    git("fetch", "--quiet", "origin", "main")
    r = git("merge", "--ff-only", "--quiet", "origin/main", check=False)
    if r.returncode != 0:
        raise RuntimeError("cannot fast-forward main to origin/main: " + (r.stderr or r.stdout).strip())


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------
def _on_sigterm(*_args) -> None:
    raise KeyboardInterrupt("SIGTERM")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; change nothing")
    ap.add_argument("--no-push", action="store_true", help="commit but do not push")
    ap.add_argument("--no-git", action="store_true", help="no pull/commit/push (local testing)")
    ap.add_argument("--max-downloads", type=int, default=MAX_DOWNLOADS,
                    help=f"iCloud files to fetch this run at most (default {MAX_DOWNLOADS})")
    args = ap.parse_args()
    # launchd stops jobs with SIGTERM: turn it into an exception so the cache is saved and iCloud
    # files are handed back on the way out.
    signal.signal(signal.SIGTERM, _on_sigterm)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another sync is running; exiting")
        return 0

    log(f"RAIMZY sync start (repo {REPO}{', dry run' if args.dry_run else ''})")
    use_git = not (args.dry_run or args.no_git)
    if use_git:
        git_prepare()

    songs = fetch_catalogue()
    by_id = {t["trackId"]: t for t in songs}
    log(f"Apple lists {len(songs)} RAIMZY songs")

    allowed, excluded = [], []
    for t in sorted(songs, key=lambda x: (x.get("releaseDate", ""), x.get("collectionId", 0),
                                          x.get("discNumber", 1), x.get("trackNumber", 0))):
        why = exclusion(t)
        (excluded if why else allowed).append((t, why))
    allowed = [t for t, _ in allowed]

    lists = {}
    for p in PLAYLISTS:
        d, raw = read_json(p)
        lists[p] = (d, raw)

    # Entries already in any playlist, keyed by Apple id, so a song in one list is reused in the other.
    known: dict[int, dict] = {}
    for p, (d, _) in lists.items():
        for e in d.get("tracks", []):
            i = apple_id(e)
            if i and i not in known and (MUSIC_DIR / e.get("file", "")).is_file():
                known[i] = e

    changes: list[str] = []
    # Safety: a song Apple now marks explicit (or that is an instrumental) leaves the playlists.
    for p, (d, _) in lists.items():
        keep = []
        for e in d.get("tracks", []):
            i = apple_id(e)
            t = by_id.get(i) if i else None
            title = f"{e.get('title', '')}"
            if (t is not None and t.get("trackExplicitness") != "notExplicit") or re.search(r"instrumental", title, re.I):
                changes.append(f"removed '{title}' from {p.name} ({'explicit on Apple' if t is not None and t.get('trackExplicitness') != 'notExplicit' else 'instrumental'})")
                continue
            if i and t is None:
                log(f"note: '{title}' ({i}) in {p.name} is no longer in Apple's lookup; left as is")
            keep.append(e)
        d["tracks"] = keep

    pins = {}
    if PINS_FILE.exists():
        pins = {int(k): v for k, v in json.loads(PINS_FILE.read_text()).items() if not k.startswith("_")}

    need = [t for t in allowed if any(t["trackId"] not in {apple_id(e) for e in d["tracks"]}
                                      for d, _ in lists.values())]
    waiting: list[tuple[dict, str]] = []
    finder = None
    if any(t["trackId"] not in known for t in need):
        files = walk_sources()
        cache = load_cache()
        log(f"indexed {len(files)} audio files in {', '.join(str(s) for s in SOURCES if s.exists())}")
        finder = MasterFinder(files, cache, args.dry_run, args.max_downloads)

    try:
        for t in need:
            tid = t["trackId"]
            title = smart_title(t["trackName"])
            entry = known.get(tid)
            if entry is None:
                log(f"-> {title} ({album_name(t)}, {t['trackTimeMillis'] / 1000:.1f} s, Apple {tid})")
                master, why = finder.find(t, pins.get(tid))
                log(f"   {'MASTER ' + str(master) if master else 'waiting for audio'}: {why}")
                if master is None:
                    waiting.append((t, why))
                    continue
                sid = slug(title)
                taken = {e.get("id") for d, _ in lists.values() for e in d["tracks"]}
                fname = f"{sid}.mp3"
                n = 2
                while sid in taken or ((MUSIC_DIR / fname).exists() and sid not in taken):
                    sid, fname = f"{slug(title)}-{n}", f"{slug(title)}-{n}.mp3"
                    n += 1
                entry = {"id": sid, "title": title, "album": album_name(t), "file": fname,
                         "listen": LISTEN_FMT.format(tid), "apple_music_id": tid,
                         "apple_music_url": t.get("trackViewUrl", "")}
                if args.dry_run:
                    log(f"   (dry run) would encode {master.name} -> music/{fname}")
                else:
                    cloud = is_dataless(master)
                    if cloud and not icloud_fetch(master):
                        icloud_evict(master)
                        waiting.append((t, f"master {master.name} found but iCloud would not download it"))
                        continue
                    try:
                        encode(master, MUSIC_DIR / fname, title, album_name(t), t["trackTimeMillis"] / 1000.0)
                    finally:
                        if cloud:
                            icloud_evict(master)
                    log(f"   encoded music/{fname} from {master}")
                known[tid] = entry
            for p, (d, _) in lists.items():
                if tid not in {apple_id(e) for e in d["tracks"]}:
                    d["tracks"].append(dict(entry))
                    changes.append(f"added '{entry['title']}' ({entry['album']}) to {p.name}")
    finally:
        if finder is not None:
            save_cache(finder.cache)

    # Apple Music ids (lead, 2026-10-21): the games play songs through Apple Music for subscribers so
    # every play counts toward royalties. Each entry carries apple_music_id (the trackId of the RELEASED
    # version, matched by title and duration) and apple_music_url (trackViewUrl). Existing fields stay.
    mp3_len: dict[str, float | None] = {}
    backfilled: dict[str, int] = {}
    for p, (d, _) in lists.items():
        for e in d["tracks"]:
            f = e.get("file", "")
            if f not in mp3_len:
                mp3_len[f] = probe_duration(MUSIC_DIR / f, {}) if (MUSIC_DIR / f).is_file() else None
            t = released_match(e, mp3_len[f], songs, by_id)
            if t is None:
                log(f"WARNING: no released Apple track matches '{e.get('title')}' ({f}, {mp3_len[f]} s) by title and length")
                continue
            set_any = False
            for k, v in (("apple_music_id", t["trackId"]), ("apple_music_url", t.get("trackViewUrl", ""))):
                if v and e.get(k) != v:
                    e[k] = v
                    set_any = True
            if set_any:
                backfilled[p.name] = backfilled.get(p.name, 0) + 1
    for name, n in backfilled.items():
        changes.append(f"set apple_music_id + apple_music_url on {n} tracks in {name}")

    # RAIMSTORM: the song named in "first" opens the list.
    for p, (d, _) in lists.items():
        first = d.get("first")
        if first:
            idx = [i for i, e in enumerate(d["tracks"]) if e.get("id") == first]
            if idx and idx[0] != 0:
                d["tracks"].insert(0, d["tracks"].pop(idx[0]))
                changes.append(f"moved '{first}' back to the top of {p.name}")

    # Status file (deterministic: no clock in it, so an unchanged catalogue rewrites nothing).
    in_lists = {apple_id(e) for d, _ in lists.values() for e in d["tracks"]}
    lines = ["# RAIMZY in-game music sync: status", "",
             "Written by `tools/music/sync_raimzy.py` (runs daily at 09:30 and at login via",
             "`~/Library/LaunchAgents/com.econteur.raimzy-sync.plist`; log: `~/Library/Logs/raimzy-sync.log`).",
             "Rule: Apple `notExplicit` only, no instrumentals, released only, master within 2 s of Apple's length",
             "and matching Apple's preview.", "",
             f"## In both games ({sum(1 for t in allowed if t['trackId'] in in_lists)})", ""]
    for p, (d, _) in lists.items():
        lines.append(f"- `{p.name}`: {len(d['tracks'])} tracks")
    lines += ["", f"## Waiting for audio ({len(waiting)})", "",
              "Clean, released songs with no verified master on this Mac yet. Drop the released WAV into",
              "iCloud Drive `MY SONGS/<album>/` and the next run adds it to both games.", ""]
    for t, why in waiting:
        lines.append(f"- {smart_title(t['trackName'])} ({album_name(t)}, {t['releaseDate'][:10]}, "
                     f"{t['trackTimeMillis'] / 1000:.1f} s, Apple {t['trackId']}): {why}")
    if not waiting:
        lines.append("- none")
    lines += ["", f"## Excluded ({len(excluded)})", ""]
    for t, why in excluded:
        lines.append(f"- {smart_title(t['trackName'])} ({album_name(t)}): {why}")
    status = "\n".join(lines) + "\n"
    old_status = STATUS_FILE.read_text() if STATUS_FILE.exists() else ""

    touched: list[Path] = []
    if args.dry_run:
        log("dry run: " + ("; ".join(changes) if changes else "no playlist changes"))
        return 0
    for p, (d, raw) in lists.items():
        new = dump_json(d)
        if new != raw:
            p.write_text(new)
            touched.append(p)
    if status != old_status:
        STATUS_FILE.write_text(status)
        touched.append(STATUS_FILE)
    new_mp3 = [MUSIC_DIR / known[i]["file"] for i in known
               if git("ls-files", "--error-unmatch", f"music/{known[i]['file']}", check=False).returncode != 0]

    for c in changes:
        log("CHANGE " + c)
    log(f"waiting for audio: {len(waiting)}" + (" (" + ", ".join(smart_title(t['trackName']) for t, _ in waiting) + ")" if waiting else ""))

    if not use_git:
        log("--no-git: leaving the working tree uncommitted" if touched else "nothing changed")
        return 0
    if touched or new_mp3:
        git("add", "--", *[str(p.relative_to(REPO)) for p in touched + new_mp3])
        added = [c for c in changes if c.startswith("added") and c.endswith("raimaction.json")]
        names = [re.match(r"added '(.+?)'", c).group(1) for c in added]
        subject = ("RAIMZY sync: add " + ", ".join(names)) if names else "RAIMZY sync: update playlists/status"
        body = "\n".join(f"- {c}" for c in changes) or "- status file refreshed"
        msg = (f"{subject[:200]}\n\nAutomatic run of tools/music/sync_raimzy.py (Apple notExplicit only, "
               f"no instrumentals, master within 2 s of Apple and matching its preview).\n\n{body}\n\n"
               "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n")
        git("commit", "-q", "-m", msg)
        log("committed " + git("rev-parse", "--short", "HEAD").stdout.strip())
    else:
        log("nothing changed")
    ahead = git("rev-list", "--count", "origin/main..HEAD").stdout.strip()
    if ahead != "0" and not args.no_push:
        r = git("push", "-q", "origin", "main", check=False)
        log("pushed to origin/main" if r.returncode == 0 else "PUSH FAILED (retried next run): " + r.stderr.strip())
        if r.returncode != 0:
            return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException as e:  # noqa: B902 - log every way out, including SIGTERM
        if isinstance(e, SystemExit):
            raise
        log(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
