# Sõnaliigijärjendite eristaja võrdlusandmestiku loomine

See repositoorium sisaldab skripti ja töötluse logifaili, mis on seotud võrdlusandmestiku `baas_osakaalud.json` koostamisega projekti [`sonaliigijarjendite-eristaja-demo`](https://github.com/esteroja/sonaliigijarjendite-eristaja-demo) jaoks.

Loodud JSON-faili kasutab projekti `sonaliigijarjendite-eristaja-demo` taustarakendus, mis võrdleb sisendteksti sõnaliigijärjendeid siin genereeritud baassagedustega.

## Eesmärk

Skript töötleb eestikeelset võrdluskorpust Stanza abil, eraldab sõnaliigijärjendid ja loendab 1- kuni 5-gramme. Tulemuseks saadud sagedused salvestatakse JSON-faili, mida saab hiljem kasutada demorakenduse võrdlusandmestikuna.

## Repositooriumi sisu

- `pos_skript.py` genereerib sõnaliigijärjendite sagedused.
- `baas_osakaalud.json` on skripti väljundfail.
- `baas_osakaalud.log` on töötluse käigus kirjutatud logifail.

## Sisend ja väljund

Eeldatav sisendfail:

- `etnc19_reference_corpus_clean_refcorp_koondkorpus.txt`

Sisendkorpuse faili repositooriumis ei ole, sest fail on GitHubis hoidmiseks liiga mahukas.

Genereeritavad failid:

- `baas_osakaalud.json`
- `baas_osakaalud.log`
- `baas_osakaalud_vahe.json` tekib ajutise vahefailina, et katkestatud töötlust saaks jätkata.

## Tööpõhimõte

`pos_skript.py`:

1. laadib Stanza eestikeelse sõnaliigimärgendi mudeli,
2. loeb võrdluskorpust juppide kaupa,
3. jätab kirjavahemärkide märgendi `Z` loendusest välja,
4. teisendab ootamatud või mittestandardse kujuga märgendid väärtuseks `T`,
5. loendab 1- kuni 5-pikkused sõnaliigijärjendid,
6. salvestab koondtulemuse faili `baas_osakaalud.json`.

Skript salvestab töö käigus ka vahepealse seisu, et pika töötluse korral ei peaks katkestuse järel nullist alustama.

## Käivitamine

Enne käivitamist peab fail `etnc19_reference_corpus_clean_refcorp_koondkorpus.txt` asuma repositooriumi juurkaustas.

Vajalikud Pythoni paketid tuleb vajadusel paigaldada käsuga:

```bash
pip install stanza tqdm
```

Seejärel saab skripti käivitada repositooriumi juurkaustast käsuga:

```bash
python pos_skript.py
```

Kui Stanza eestikeelne mudel puudub, laadib skript selle esmakordsel käivitamisel automaatselt alla.

## Seos demo repositooriumiga

See repositoorium on projekti võrdlusandmestiku loomise osa.

Seotud repositoorium:

- `sonaliigijarjendite-eristaja-demo`

Demo repositoorium sisaldab Flaski taustarakendust ja Reacti kasutajaliidest. Selle taustarakendus loeb siin loodud faili `baas_osakaalud.json` ning kasutab seda sisendteksti sõnaliigijärjendite võrdlemiseks baaskorpusega.

## Märkused

- Genereeritud `baas_osakaalud.json` on mahukas ja mõeldud korduvkasutatava võrdlusandmestikuna.
- Skript on mõeldud pikaajaliseks korpusetöötluseks ning toetab katkestuse järel jätkamist.
- Kui sisendkorpust muudetakse, tuleb `baas_osakaalud.json` uuesti genereerida.