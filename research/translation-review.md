# Translation review checklist

Four draft translations exist: `docs/snow/i18n/es.js` (Spanish), `pt.js` (Brazilian Portuguese), `ht.js` (Haitian Creole), `ne.js` (Nepali). An AI wrote them, so they are **not** in the language switcher yet. Preview one at `index.html?lang=es` (or `pt`, `ht`, `ne`); a yellow banner marks it as a draft.

The City's snow page has no translated snow rules to borrow terms from (its language links were placeholders or only covered City Alerts sign-up), so every term below is the AI's choice.

## To publish a language

1. A native speaker reads the whole page at `?lang=<code>`, on a phone, and fixes the file.
2. Move the language from `docs/snow/i18n/drafts.js` to `docs/snow/i18n/languages.js`. The switcher appears automatically.

## Added later (by the same AI, after the first drafts)

The "Replay a past storm" section (`header.10`, `replay.01`–`07`, `ui.replay.*`) and the footer link `footer.storm`. Check these with the rest.

**Not translated yet:** the live storm-mode banner (`ui.live` in `en.js`, about 30 short strings). Until it's translated, draft pages show it in English. Preview it with `?lang=es&live=stopped`.

## Ask the reviewer to check

**All languages**
- Legal meaning holds: businesses *must* clear curb ramps; homes are only *asked*. "Not an official City page" is not softened.
- "Lien" (`fines.10`) has no everyday equivalent; check the wording reads as "the City can put a debt on the property".
- Units stay in inches/feet and °F, as in the law. Consider adding "(91 cm)" next to 36 inches for metric readers.
- The brand "Somerville Snow" was translated in some files; keep or revert.

**Spanish (es)**: uses informal *tú*. Terms: acera, rampa de la acera, cruce peatonal, gravamen (lien), objetos para apartar lugar (space savers), carro, descongelantes, "Dueños que alquilan" (landlords), alcantarilla (storm drain). "Wards" and "Community Path" left in English.

**Portuguese (pt)**: "Prefeitura" for the City; calçada; faixa de pedestres; rampa da calçada; "Guardar vaga" (space savers); "Ou dívida no imóvel" (lien); "permit" left in English (`emergency.22`). Times in Brazilian style (15h). "&amp;" kept in headings ("Neve & gelo"); "e" may read more naturally.

**Haitian Creole (ht)**: twotwa (sidewalk), ranp twotwa (curb ramp), pasaj pyeton (crosswalk), "yon dèt sou kay la" (lien), "bagay pou kenbe plas" (space savers), "beton an" (pavement), "atè a" (pavement temperature), bò pè (even side), "Ou lwe" (Renting). Check `top.03` reads well. Dates in the calculator stay in English (browsers don't format Creole dates).

**Nepali (ne)**: कर्ब र्याम्प (curb ramp), जेब्रा क्रसिङ (crosswalk), प्लो (plow), सिटी (City), लियन (lien, transliterated), ठाउँ ओगट्ने सामान (space savers), जोर नम्बर पट्टि (even side), भुइँसम्मै (down to the pavement). Western digits are used on purpose to match the numbers on the page. Dates in the calculator stay in English in most browsers.
