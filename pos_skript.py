import json
from collections import Counter
import stanza
from tqdm import tqdm
import os
import sys
import tempfile
import datetime

failinimi = "etnc19_reference_corpus_clean_refcorp_koondkorpus.txt"
juppi_suurus = 200_000
vahefail = "baas_osakaalud_vahe.json"
valmisfail = "baas_osakaalud.json"
logifail = "baas_osakaalud.log"

def logi(sonum: str):
    aeg = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rida = f"[{aeg}] {sonum}"
    print(rida)
    with open(logifail, "a", encoding="utf-8") as f:
        f.write(rida + "\n")

if not os.path.isdir(os.path.expanduser("~/.stanza_resources/et")):
    logi("Laen alla Stanza eesti mudeli... (üks kord)")
    stanza.download("et")

toru = stanza.Pipeline("et", processors="tokenize,mwt,pos", package="edt", use_gpu=False)
if getattr(toru, "lang", None) != "et":
    logi(f"Stanza pipeline ei ole 'et'! Laaditi: {getattr(toru, 'lang', None)}")
    sys.exit(1)
else:
    logi("Laetud Stanza eesti mudel (EDT).")

koond_loendurid = {k: Counter() for k in range(1, 6)}

toodeldud_marke = 0
if os.path.exists(vahefail):
    logi(f"Leidsin vahefaili: {os.path.abspath(vahefail)} — laen andmed...")
    with open(vahefail, "r", encoding="utf-8") as f:
        eelinfo = json.load(f)
    for k in range(1, 6):
        koond_loendurid[k].update({tuple(h.split(",")): v for h, v in eelinfo[str(k)]["jarjestused"].items()})
    toodeldud_marke = int(eelinfo.get("chars_processed", 0))
    logi(f"Laaditud eelmine progress (töödeldud {toodeldud_marke} märki). Jätkan sealt.\n")
else:
    logi("Alustan uut töötlemist nullist.\n")

def atomaarne_kirjuta_json(tee: str, payload: dict):
    kataloog = os.path.dirname(os.path.abspath(tee)) or "."
    fd, ajutine = tempfile.mkstemp(prefix=".tmp_", dir=kataloog, text=True)
    os.close(fd)
    try:
        with open(ajutine, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(ajutine, tee)
    finally:
        if os.path.exists(ajutine):
            try:
                os.remove(ajutine)
            except Exception:
                pass

def koosta_dump(loendurid, lisa_marked=False):
    andmed = {}
    for k in range(1, 6):
        kokku = sum(loendurid[k].values())
        andmed[k] = {
            "kokku": kokku,
            "jarjestused": {",".join(h): v for h, v in loendurid[k].items()}
        }
    if lisa_marked:
        andmed["chars_processed"] = toodeldud_marke
    return andmed

def salvesta_vahefail():
    atomaarne_kirjuta_json(vahefail, koosta_dump(koond_loendurid, lisa_marked=True))
    logi(f"Vahefail salvestatud (progress: {toodeldud_marke} märki).")

def protsessi_lause(lause):
    sildid = []
    for sona in lause.words:
        tag = sona.xpos
        if not tag:
            continue

        orig_tag = tag

        if len(tag) != 1:
            logi(f"Asendan tundmatu XPOS '{orig_tag}' sõnal '{sona.text}' märgendiga 'T'.")
            tag = "T"

        if tag == "Z":
            continue

        if tag == "T":
            logi(f"Sõnal '{sona.text}' on XPOS 'T' (tundmatu).")

        sildid.append(tag)

    n = len(sildid)
    for pikkus in range(1, min(6, n + 1)):
        for i in range(n - pikkus + 1):
            koond_loendurid[pikkus][tuple(sildid[i:i+pikkus])] += 1

try:
    logi(f"Töötlen faili: {os.path.abspath(failinimi)}")

    with open(failinimi, "r", encoding="utf-8", errors="replace") as f:
        if toodeldud_marke > 0:
            vahele_jaetud = f.read(toodeldud_marke)
            tegelik = len(vahele_jaetud)
            if tegelik < toodeldud_marke:
                logi(f"Sisendfail on lühem kui varem (ootasin {toodeldud_marke}, sain {tegelik}). Jätkan tegelikust kohast.")
            toodeldud_marke = tegelik
            logi(f"Hüppan faili {toodeldud_marke} märgi kohale.")

        jupp = ""
        saba = ""
        edenemisriba = tqdm(desc="Töötlen faili", unit="char", disable=not sys.stdout.isatty())
        edenemisriba.update(toodeldud_marke)

        for rida in f:
            jupp += rida
            if len(jupp) >= juppi_suurus:
                blokk = saba + jupp

                dok = toru(blokk)

                if not dok.sentences:
                    saba = blokk
                elif len(dok.sentences) == 1:
                    saba = blokk
                else:
                    for lause in dok.sentences[:-1]:
                        protsessi_lause(lause)

                    eelviimane = dok.sentences[-2]
                    if eelviimane.tokens:
                        cut = eelviimane.tokens[-1].end_char
                    else:
                        cut = len(blokk)

                    toodeldud_marke += cut
                    edenemisriba.update(cut)
                    salvesta_vahefail()

                    saba = blokk[cut:]

                jupp = ""

        if jupp or saba:
            lopp_tekst = saba + jupp
            dok = toru(lopp_tekst)
            for lause in dok.sentences:
                protsessi_lause(lause)
            toodeldud_marke += len(lopp_tekst)
            edenemisriba.update(len(lopp_tekst))
            salvesta_vahefail()

        edenemisriba.close()

    atomaarne_kirjuta_json(valmisfail, koosta_dump(koond_loendurid, lisa_marked=False))
    logi(f"Töö valmis! Salvestatud fail: {valmisfail}")

    if os.path.exists(vahefail):
        os.remove(vahefail)
        logi("Vahefail eemaldatud. Töö lõppes edukalt.")

except KeyboardInterrupt:
    logi("Töö katkestati käsitsi. Vahefail jäeti alles, et saaksid jätkata.")
    sys.exit(1)

except Exception as viga:
    logi(f"Tekkis viga: {viga}")
    sys.exit(1)
