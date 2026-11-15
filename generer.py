import gzip
import os
import re
import urllib.request

SOURCE = os.environ.get("XMLTV_SOURCE", "https://xmltvfr.fr/xmltv/xmltv.xml.gz")
AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

with open("favoris.txt", encoding="utf-8") as f:
    FAVORIS = [
        ligne.split("#")[0].strip()
        for ligne in f
        if ligne.split("#")[0].strip()
    ]

requete = urllib.request.Request(SOURCE, headers=AGENT)
brut = urllib.request.urlopen(requete).read()
if SOURCE.endswith(".gz"):
    brut = gzip.decompress(brut)
src = brut.decode("utf-8", errors="replace")

connus = {}          # id -> (nom, logo, bloc <channel> complet)
for m in re.finditer(r'<channel id="([^"]+)">(.*?)</channel>', src, re.S):
    cid, bloc_interieur = m.group(1), m.group(2)
    nom = re.search(r"<display-name>([^<]+)</display-name>", bloc_interieur)
    icone = re.search(r'<icon src="([^"]+)"', bloc_interieur)
    connus[cid] = (
        nom.group(1) if nom else cid,
        icone.group(1) if icone else None,
        m.group(0),
    )

ids = set(FAVORIS)
canaux_xml = []
programmes_xml = []
for m in re.finditer(
    r"<programme .*?</programme>|<programme [^>]*/>", src, re.S
):
    bloc = m.group(0)
    ch = re.search(r'channel="([^"]+)"', bloc)
    if ch and ch.group(1) in ids:
        programmes_xml.append(bloc)
    if ch and ch.group(1) in ids:
        pass

# --- guide.m3u : squelette de playlist, dans l'ordre de favoris.txt ---
with open("guide.m3u", "w", encoding="utf-8") as out:
    out.write('#EXTM3U x-tvg-url="guide-favoris.xml"\n')
    for cid in FAVORIS:
        if cid not in connus:
            print(f"Introuvable dans la source : {cid}")
            continue
        nom, icone, _ = connus[cid]
        ligne = f'#EXTINF:-1 tvg-id="{cid}"'
        if icone:
            ligne += f' tvg-logo="{icone}"'
        ligne += f",{nom}"
        out.write(ligne + "\n" + f"http://localhost/{cid}\n")

# --- guide-favoris.xml : XMLTV allégé
for cid in FAVORIS:
    if cid in connus:
        canaux_xml.append(connus[cid][2])

with open("guide-favoris.xml", "w", encoding="utf-8") as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n<tv>\n')
    out.write("\n".join(canaux_xml) + "\n")
    out.write("\n".join(programmes_xml) + "\n</tv>\n")

print(f"{len(canaux_xml)} chaînes, {len(programmes_xml)} programmes écrits")
