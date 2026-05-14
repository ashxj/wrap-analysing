# e-klase Analytics

Rīks e-klase.lv atzīmju izgūšanai, apstrādei un analīzei. Sastāv no divām daļām: **parsera** (Node.js) un **tīmekļa lietotnes** (Python/Flask).
<img width="2878" height="1430" alt="image" src="https://github.com/user-attachments/assets/ea0e156f-b37d-4954-a9e8-53248503e982" />

---

## Tehnoloģijas

### Parseris (`parser/`)
| Tehnoloģija | Izmantojums |
|---|---|
| Node.js (ESM) | Izpildes vide |
| Playwright | Pārlūkprogrammas automatizācija OIDC autentifikācijai |
| [Obscura](https://github.com/nicktindall/obscura) | Viegls CDP pārlūks (Rust), ko Playwright izmanto kā CDP mērķi |

### Tīmekļa lietotne (`web/`)
| Tehnoloģija | Izmantojums |
|---|---|
| Python 3.12 + Flask 3 | Servera puse un maršrutēšana |
| Flask-Login | Sesiju pārvaldība |
| Flask-SQLAlchemy + SQLite | Datu glabāšana |
| Playwright (Python) | OIDC autentifikācija pret e-klase.lv |
| Anthropic Claude API | AI ieteikumu ģenerēšana (haiku-4-5) |
| Jinja2 | HTML veidnes |
| Chart.js | Diagrammas priekšgalā |

---

## Kā darbojas parsēšana no e-klase

e-klase.lv izmanto **Keycloak OIDC** autentifikāciju ar PKCE papildinājumu. Tā kā nav publiski pieejamas API dokumentācijas, pieteikšanās tiek veikta ar pārlūkprogrammas automatizāciju:

1. **PKCE sagatavošana** — tiek ģenerēts `code_verifier` un `code_challenge` (SHA-256), kā arī `state` un `nonce`.

2. **Autorizācijas URL** — Playwright atver `https://auth.e-klase.lv/realms/family/protocol/openid-connect/auth` ar PKCE parametriem.

3. **Formas aizpildīšana** — JavaScript injekcija aizpilda lietotājvārda/paroles laukus un iesniedz formu, neizmantojot simulētu klikšķu notikumus (lai apietu bot noteikšanu).

4. **Koda saņemšana** — tiek uzraudzīti navigācijas notikumi. Kad pārlūks tiek novirzīts uz `https://family.e-klase.lv/redirect.html?code=...`, tiek izvilkts autorizācijas kods.

5. **Tokenu apmaiņa** — kods tiek apmainīts pret `access_token` caur `POST /token` endpointu (bez klienta slepenās atslēgas — publisks klients).

6. **Profila izvēle** — tiek izsaukts `GET /api/user/profiles` un izvēlēts pirmais aktīvais profils; pēc tam `POST /api/user/profiles/switch`.

7. **Atzīmju izgūšana** — `GET /api/evaluations/summary` atgriež rekursīvu atzīmju koku, kas tiek normalizēts saplacinot un atduplicējot pēc ID.

> Obscura ir viegls Rust bāzēts CDP serveris, kurš darbojas kā Playwright CDP mērķis, ļaujot izvairīties no pilna Chromium instalējuma un samazinot resursu patēriņu.

---

## Galvenās funkcijas

### Parseris
- **Pieteikšanās** un tokenu saglabāšana lokāli (`storage/`)
- **Atzīmju izgūšana** no `family.e-klase.lv` API
- **Normalizācija** — rekursīva atzīmju saplacināšana no ligzdotas struktūras, atduplicēšana pēc ID

### Tīmekļa lietotne
| Lapa | Apraksts |
|---|---|
| `/` (Panelis) | Kopsavilkums: kopējā vidējā, atzīmju skaits, vājo priekšmetu skaits, tendenču diagramma |
| `/grades` | Pilns atzīmju saraksts ar filtriem un meklēšanu |
| `/subjects` | Vidējā atzīme pa priekšmetiem ar visu atzīmju izklājumu |
| `/calculator` | Aprēķina nepieciešamo atzīmi, lai sasniegtu vēlamo vidējo |
| `/recommendations` | Claude AI ģenerē mācību resursus (uzdevumi.lv, skola2030.lv, letonika.lv u.c.) prioritizējot vājos priekšmetus |

**Papildu iespējas:**
- Divvalodu interfeiss (LV / EN) ar i18n JSON tulkojumiem
- Gaišs un tumšs motīvs
- Ieteikumu kešošana 7 dienas (SQLite), manuāla atsvaidzināšana pa priekšmetam

---

## Uzstādīšana

### Parseris
```bash
cd parser
cp .env.example .env   # aizpildīt EKLASE_USERNAME, EKLASE_PASSWORD
npm install
node src/login.mjs     # izgūt tokenus
node src/fetch-grades.mjs
```

### Tīmekļa lietotne
```bash
cd web
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # aizpildīt SECRET_KEY, FERNET_KEY, ANTHROPIC_API_KEY
flask db upgrade        # vai: python run.py (auto-izveido tabulas)
python run.py
```

Atver `http://localhost:5000`, piesakies ar e-klase.lv datiem.
