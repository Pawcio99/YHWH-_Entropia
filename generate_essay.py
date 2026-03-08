#!/usr/bin/env python3
"""
YHWH i Entropia — Generator strony eseju
Uruchom: python3 generate_essay.py
Wynik:   yhwh_entropia.html  (otwórz w przeglądarce lub wrzuć na GitHub Pages)
"""

import math
import json

# ── Obliczenia fizyczne ──────────────────────────────────────────

def maxwell_boltzmann(T_K, G_frac=0.0, n_points=200):
    """Rozkład Maxwella-Boltzmanna z opcjonalnym gradientem"""
    kB, m = 1.38e-23, 6.64e-26          # stała Boltzmanna, masa argonu
    a2    = kB * T_K / m
    vp    = math.sqrt(2 * kB * T_K / m)
    vmax  = vp * 3.5
    vs    = [vmax * i / n_points for i in range(n_points + 1)]
    def f(v):
        base = 4 * math.pi * v * v * math.exp(-v*v / (2*a2)) / (2*math.pi*a2)**1.5
        return base * (1 + G_frac * math.sin(math.pi * v / vmax))
    fs = [f(v) for v in vs]
    mx = max(fs) or 1.0
    return vs, [x/mx for x in fs], vp, vmax

def sofar_wave(dT_frac, alpha_frac, omega, n_x=300):
    """Propagacja fali w gradiencie temperatury (model SOFAR)"""
    xs, ys_list, labels = [], [], []
    n_waves = 3 if dT_frac > 0.1 else 1
    for w in range(n_waves):
        phase_off = w * 2 * math.pi / n_waves
        amp = 1 - w * 0.22 if n_waves > 1 else 1.0
        xs_w, ys_w = [], []
        for i in range(n_x + 1):
            t     = i / n_x
            damp  = math.exp(-alpha_frac * t * 8)
            bend  = dT_frac * math.sin(t * math.pi) * 0.35
            spread = (1 - dT_frac) * 0.12 * w
            y     = 0.5 + bend + spread + math.sin(omega * t * 2*math.pi + phase_off) * 0.30 * damp * amp
            xs_w.append(t)
            ys_w.append(y)
        xs.append(xs_w)
        ys_list.append(ys_w)
        labels.append(f"fala {w+1}" if w > 0 else "fala główna")
    return xs, ys_list, labels

def quantum_spectrum(Z, n_max, series_n1):
    """Linie spektralne wg wzoru Rydberga"""
    RH = 1.097e7
    lines = []
    E = lambda n: -13.6 * Z * Z / (n * n)
    for n2 in range(series_n1 + 1, n_max + 1):
        inv_lam = RH * Z * Z * (1/series_n1**2 - 1/n2**2)
        lam_nm  = 1e9 / inv_lam
        dE_eV   = E(n2) - E(series_n1)
        lines.append({
            "n1": series_n1, "n2": n2,
            "lam_nm": lam_nm,
            "E1": E(series_n1), "E2": E(n2),
            "dE": abs(dE_eV)
        })
    levels = [{"n": n, "E": E(n)} for n in range(1, n_max + 1)]
    return lines, levels

def shannon_entropy_curve(n_points=300):
    """Krzywa H(p) Shannona"""
    ps, hs = [], []
    for i in range(1, n_points):
        p = i / n_points
        h = -(p * math.log2(p) + (1-p) * math.log2(1-p))
        ps.append(p)
        hs.append(h)
    return ps, hs

def wavelength_to_hex(nm):
    """Długość fali → kolor RGB"""
    if   380 <= nm < 440: r,g,b = (440-nm)/60, 0, 1
    elif 440 <= nm < 490: r,g,b = 0, (nm-440)/50, 1
    elif 490 <= nm < 510: r,g,b = 0, 1, (510-nm)/20
    elif 510 <= nm < 580: r,g,b = (nm-510)/70, 1, 0
    elif 580 <= nm < 645: r,g,b = 1, (645-nm)/65, 0
    elif 645 <= nm <= 780: r,g,b = 1, 0, 0
    else: r,g,b = 0.4, 0.4, 0.4
    return f"rgb({int(r*220)},{int(g*220)},{int(b*220)})"

# ── Pre-generate data sets for JavaScript ───────────────────────

def build_mb_datasets():
    """Kilka krzywych MB dla różnych T i G — JS wybierze"""
    datasets = {}
    for T in [300, 600, 900, 1200, 1800]:
        for G in [0, 25, 50, 75, 100]:
            vs, fs, vp, vmax = maxwell_boltzmann(T, G/100)
            datasets[f"T{T}_G{G}"] = {
                "v": [round(x, 2) for x in vs],
                "f": [round(x, 6) for x in fs],
                "vp_frac": round(vp/vmax, 4)
            }
    return datasets

def build_sofar_datasets():
    datasets = {}
    for dT in [0, 20, 40, 60, 80, 100]:
        for alpha in [0, 10, 20, 40, 60, 80]:
            for omega in [2, 5, 10, 15, 20]:
                key = f"dT{dT}_a{alpha}_w{omega}"
                xs, ys_list, labels = sofar_wave(dT/100, alpha/200, omega)
                datasets[key] = {
                    "xs": [[round(x,4) for x in row] for row in xs],
                    "ys": [[round(y,5) for y in row] for row in ys_list],
                    "labels": labels,
                    "sofar_y": round(0.5 - (dT/100)*0.14, 4)
                }
    return datasets

def build_spectrum_datasets():
    ELEM = ['H','He','Li','Be','B','C','N','O']
    SERIES = ['Lymana','Balmera','Paschena','Bracketta']
    datasets = {}
    for Z in range(1, 9):
        for nmax in range(3, 9):
            for si, sn in enumerate([1,2,3,4]):
                if sn >= nmax: continue
                lines, levels = quantum_spectrum(Z, nmax, sn)
                key = f"Z{Z}_n{nmax}_s{si+1}"
                datasets[key] = {
                    "lines": lines,
                    "levels": levels,
                    "elem": ELEM[Z-1],
                    "series": SERIES[si],
                    "n1": sn
                }
    return datasets

# Pre-compute Shannon curve (static)
ps_curve, hs_curve = shannon_entropy_curve()

# ── HTML Template ────────────────────────────────────────────────

ESSAY_SECTIONS = """
<section class="essay-section" id="s1">
  <div class="section-marker"><span class="snnum">§ 01</span><div class="snline"></div></div>
  <h2>YHWH jako ontologia processualna — <em>termodynamika nieequilibrium</em></h2>
  <p>Imię Boga zapisywane w tradycji hebrajskiej jako YHWH bywa interpretowane jako forma czasownika „być" — lecz nie w jego klasycznym, statycznym sensie. Chodzi raczej o formę niedokonaną: „będę, który będę", „staję się, którym się staję". Rzeczywistość w tej perspektywie nie jest strukturą zamkniętą — jest dynamicznym polem przemian, procesualnością bez zatrzymania.</p>
  <p>Ilya Prigogine, laureat Nagrody Nobla z chemii w roku 1977, odkrył coś, co rzuca na tę intuicję nieoczekiwane światło naukowe. Układy daleko od równowagi termodynamicznej nie tylko nie rozpadają się — one spontanicznie wytwarzają struktury o rosnącej złożoności. Prigogine nazwał je strukturami dysypatywnymi. Warunkiem ich istnienia jest stały przepływ energii przez układ — nie magazynowanie, lecz nieprzerwalny ruch.</p>
  <div class="pq"><p>Komórka, płomień świecy, huragan — wszystkie są strukturami dysypatywnymi. Istnieją wyłącznie jako procesy. Zatrzymany huragan to nie spokojny huragan — to brak huraganu.</p></div>
  <p>Jeśli byt istnieje wyłącznie przez nieustanny przepływ, to YHWH jako „hayah asher hayah" jest opisem tej samej zasady na poziomie fundamentalnym: rzeczywistości, która istnieje w akcie trwającego gradientu, nigdy jako zamknięty obiekt.</p>
  <div class="fbox" data-label="Prigogine 1977">\\[\\frac{dS}{dt} = \\frac{d_i S}{dt} + \\frac{d_e S}{dt} \\geq 0\\]<span class="fcomment">Całkowita zmiana entropii układu otwartego = produkcja wewnętrzna + wymiana z otoczeniem. Lokalne obniżenie S jest możliwe przy wystarczającym gradiencie zewnętrznym.</span></div>
  <p>Biblijna metafora „ciernia i ostu" nabiera w tej perspektywie precyzji fizycznej. Budowanie struktury to lokalne zmniejszenie \\(\\Omega\\) — liczby mikrostanów dostępnych układowi. Koszt musi być ponoszony gdzieś w otoczeniu.</p>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s2">
  <div class="section-marker"><span class="snnum">§ 02</span><div class="snline"></div></div>
  <h2>Geometria przestrzeni fazowej — <em>czym naprawdę jest entropia</em></h2>
  <p>Ludwig Boltzmann w roku 1877 zapisał na tablicy równanie, które kilkadziesiąt lat po jego śmierci zostanie wyryte na jego nagrobku w Wiedniu. Entropia \\(S\\) jest iloczynem stałej Boltzmanna i logarytmu naturalnego z liczby \\(\\Omega\\) — liczby mikrostanów, przez które może być zrealizowany dany stan makroskopowy układu.</p>
  <p>Entropia nie jest siłą. Nie jest dążnością. Nie jest kosmicznym wyrokiem ciągnącym rzeczy ku rozpadowi. Jest miarą statystyczną — opisem geometrii przestrzeni fazowej. Układ „zmierza ku większej entropii" wyłącznie dlatego, że stanów o wysokim \\(\\Omega\\) jest przytłaczająco więcej.</p>
  <div class="snote"><p>Mówienie o entropii jako „sile rozpadu" jest błędem kategorii. Determinantem dynamiki jest gradient różnicy potencjałów — nie entropia jako aktywny aktor.</p></div>
  <div class="fbox" data-label="Boltzmann 1877">\\[S = k_B \\ln \\Omega \\qquad k_B = 1{,}38 \\times 10^{-23}\\ \\frac{\\text{J}}{\\text{K}}\\]<span class="fcomment">\\(\\Omega\\) — liczba mikrostanów. Entropia rośnie bo stanów o wysokim \\(\\Omega\\) jest statystycznie więcej — geometria, nie siła.</span></div>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s3">
  <div class="section-marker"><span class="snnum">§ 03</span><div class="snline"></div></div>
  <h2>Zasada nieoznaczoności jako <em>fundament struktury</em></h2>
  <p>Elektrony w atomach nie zajmują sztywnych orbit w sensie klasycznym. Kluczowe pytanie brzmi: dlaczego elektron nie „spada" na najniższy możliwy poziom energetyczny? Odpowiedź daje zasada nieoznaczoności Heisenberga. Zerowa energia kinetyczna wymagałaby nieskończonej precyzji lokalizacji elektronu — co narusza zasadę nieoznaczoności.</p>
  <div class="pq"><p>Porządek na poziomie atomowym jest wbudowany w geometrię przestrzeni fazowej przez zasadę nieoznaczoności — nie przez zewnętrzną interwencję. Pewne stany są strukturalnie wykluczone z przestrzeni możliwości.</p></div>
  <div class="fbox" data-label="Heisenberg 1927">\\[\\Delta x \\cdot \\Delta p \\geq \\frac{\\hbar}{2} \\qquad \\Delta E \\cdot \\Delta t \\geq \\frac{\\hbar}{2}\\]<span class="fcomment">Zasada nieoznaczoności nie jest ograniczeniem pomiaru — jest fundamentalną własnością przestrzeni fazowej kwantowej.</span></div>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s4">
  <div class="section-marker"><span class="snnum">§ 04</span><div class="snline"></div></div>
  <h2>Widma jako podpis gradientu — <em>tożsamość jest różnicą potencjałów</em></h2>
  <p>Każdy pierwiastek posiada charakterystyczne widmo emisyjne i absorpcyjne. Gdy elektron w atomie wodoru przeskakuje z poziomu \\(n=3\\) na \\(n=2\\), emituje foton o długości fali 656 nm — czerwona linia \\(H_\\alpha\\), widoczna w widmie każdej gwiazdy zawierającej wodór, niezależnie od odległości.</p>
  <p>Tożsamość pierwiastka jest opisywana przez jego charakterystyczne gradienty energetyczne — przez wzorzec skoków między poziomami kwantowymi, nie przez masę czy objętość. To, czym coś jest, wyraża się przez to, jak i gdzie przenosi energię.</p>
  <div class="fbox" data-label="Bohr 1913 / Rydberg">\\[\\frac{1}{\\lambda} = R_H \\cdot Z^2 \\left(\\frac{1}{n_1^2} - \\frac{1}{n_2^2}\\right) \\qquad R_H = 1{,}097 \\times 10^{7}\\ \\text{m}^{-1}\\]<span class="fcomment">Każda linia spektralna jest zapisem gradientu energetycznego między dwoma stanami kwantowymi.</span></div>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s5">
  <div class="section-marker"><span class="snnum">§ 05</span><div class="snline"></div></div>
  <h2>Entropia informacyjna — <em>Landauer i fizyczność wiedzy</em></h2>
  <p>W roku 1948 Claude Shannon opublikował matematyczną teorię komunikacji. Miara niepewności, którą zaproponował, miała identyczną formę matematyczną co entropia termodynamiczna Boltzmanna. Rolf Landauer w roku 1961 pokazał, że ta zbieżność nie jest metaforyczna — skasowanie jednego bitu informacji generuje co najmniej \\(k_B T \\ln 2\\) ciepła. Informacja jest fizyczna.</p>
  <div class="pq"><p>Propaganda nie jest tylko moralnym złem — jest termodynamicznym marnotrawstwem. Niszczy gradient informacyjny, który umożliwia efektywną koordynację układów złożonych.</p></div>
  <div class="fbox" data-label="Shannon 1948 / Landauer 1961">\\[H = -\\sum_i p_i \\log_2 p_i \\qquad E_{\\min} = k_B T \\ln 2 \\approx 2{,}87 \\times 10^{-21}\\ \\text{J}\\]<span class="fcomment">Kasowanie informacji ma nieusuwalne koszty fizyczne — informacja i entropia termodynamiczna są dwoma aspektami tej samej rzeczywistości.</span></div>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s6">
  <div class="section-marker"><span class="snnum">§ 06</span><div class="snline"></div></div>
  <h2>Świadomość jako <em>modulator przestrzeni fazowej</em></h2>
  <p>Świadomość — jeśli potraktować ją poważnie jako strukturę dysypatywną mózgu — nie jest biernym obserwatorem gradientu entropii. Jest aktywnym modulatorem przestrzeni fazowej: przez wybory, przez uwagę, przez budowanie struktur informacyjnych, zmienia topografię gradientów dostępnych innym układom.</p>
  <div class="snote"><p>Mózg ludzki zużywa około 20 watów przy masie stanowiącej 2% masy ciała. Jest strukturą dysypatywną o wyjątkowo wysokiej gęstości przepływu energii — co odpowiada możliwości utrzymywania wyjątkowo złożonych struktur stacjonarnych.</p></div>
  <p>Świadomość jest jedynym układem dysypatywnym, który może świadomie projektować własne warunki brzegowe. To jest fizyczny opis wolności: nie brak determinizmu, lecz zdolność do rekonfiguracji własnej przestrzeni fazowej.</p>
</section>

<div class="divider">· · ·</div>

<section class="essay-section" id="s7">
  <div class="section-marker"><span class="snnum">§ 07</span><div class="snline"></div></div>
  <h2>Kosmiczny gradient — <em>strzałka czasu i jej źródło</em></h2>
  <p>Strzałka czasu ma swoje źródło w niezwykle niskiej entropii Wszechświata tuż po Wielkim Wybuchu. Roger Penrose szacował, że prawdopodobieństwo wylosowania stanu o tak niskim \\(\\Omega\\) wynosi \\(1\\) do \\(10^{10^{123}}\\). Słońce jest pośrednikiem między niską entropią jądrową a wysoką entropią promieniowania podczerwonego — życie istnieje w tym gradiencie jak turbina w strumieniu wody.</p>
  <div class="pq"><p>Człowiek budujący kulturę i instytucje nie jest anomalią w kosmosie — jest jego najbardziej zaawansowanym narzędziem realizacji gradientu. Świadomość jest gradientem, który patrzy na siebie.</p></div>
</section>
"""

def generate_html(mb_data, sofar_data, spec_data):
    mb_json   = json.dumps(mb_data)
    sofar_json = json.dumps(sofar_data)
    spec_json  = json.dumps(spec_data)
    hp_ps     = json.dumps([round(x,4) for x in ps_curve])
    hp_hs     = json.dumps([round(x,6) for x in hs_curve])

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>YHWH i Entropia</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=Crimson+Pro:ital,wght@0,300;0,400;1,300;1,400&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'\\\\[',right:'\\\\]',display:true}},{{left:'$',right:'$',display:false}},{{left:'\\\\(',right:'\\\\)',display:false}}],throwOnError:false}});"></script>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
:root{{
  --void:#06080d; --deep:#0b0f1a; --panel:#161e2e;
  --border:rgba(180,150,60,0.22);
  --gold:#c8a84b; --gold-dim:#8a6e2a; --amber:#e8b84b;
  --cyan:#4bc8c8; --rust:#c85a2a;
  --text:#d4c9b0; --text-soft:#b0a488;
  --display:'Playfair Display',Georgia,serif;
  --body:'Crimson Pro',Georgia,serif;
  --mono:'Share Tech Mono',monospace;
  --max:760px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{font-size:18px;scroll-behavior:smooth;}}
body{{background:var(--void);color:var(--text);font-family:var(--body);line-height:1.85;overflow-x:hidden;}}
#bar{{position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,var(--gold-dim),var(--amber));width:0;z-index:8000;}}

/* HERO */
.hero{{min-height:100vh;display:flex;flex-direction:column;justify-content:center;
  align-items:flex-start;padding:8rem 4rem 6rem;position:relative;overflow:hidden;
  border-bottom:1px solid var(--border);}}
.hero-grid{{position:absolute;inset:0;
  background-image:linear-gradient(rgba(200,168,75,0.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(200,168,75,0.04) 1px,transparent 1px);
  background-size:60px 60px;
  mask-image:radial-gradient(ellipse 80% 80% at 20% 50%,black 0%,transparent 70%);}}
.hero-eyebrow{{font-family:var(--mono);font-size:.65rem;letter-spacing:.3em;
  color:var(--gold-dim);text-transform:uppercase;margin-bottom:2rem;}}
.hero h1{{font-family:var(--display);font-size:clamp(2.8rem,6vw,5rem);font-weight:900;
  line-height:1.0;color:#fff;max-width:700px;}}
.hero h1 em{{font-style:italic;color:var(--gold);}}
.hero-sub{{font-family:var(--display);font-style:italic;font-size:1.1rem;
  color:var(--text-soft);margin-top:1.5rem;max-width:520px;line-height:1.6;}}
.hero-katex{{margin-top:3rem;padding:1rem 1.5rem;border:1px solid var(--border);
  background:rgba(200,168,75,0.07);display:inline-block;}}
.hero-katex .katex{{color:var(--gold);font-size:1rem;}}

/* MAIN */
.main{{max-width:var(--max);margin:0 auto;padding:6rem 2rem 10rem;}}
.essay-section{{margin-bottom:6rem;}}
.section-marker{{display:flex;align-items:center;gap:1rem;margin-bottom:2.5rem;}}
.snnum{{font-family:var(--mono);font-size:.6rem;color:var(--gold-dim);letter-spacing:.2em;}}
.snline{{flex:1;height:1px;background:linear-gradient(to right,var(--border),transparent);}}
h2{{font-family:var(--display);font-size:clamp(1.5rem,3vw,2rem);font-weight:700;
  line-height:1.2;color:#fff;margin-bottom:2rem;}}
h2 em{{color:var(--gold);font-style:italic;}}
p{{font-size:1.05rem;color:var(--text);margin-bottom:1.4rem;text-align:justify;hyphens:auto;}}
.pq{{border-left:2px solid var(--gold);padding:1.2rem 0 1.2rem 2rem;margin:2.5rem 0;}}
.pq p{{font-family:var(--display);font-style:italic;font-size:1.1rem;color:var(--amber);text-align:left;margin:0;}}
.fbox{{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--gold);
  padding:1.4rem 1.6rem;margin:2rem 0;position:relative;}}
.fbox::before{{content:attr(data-label);position:absolute;top:-1px;right:1rem;
  font-family:var(--mono);font-size:.55rem;letter-spacing:.2em;color:var(--gold-dim);
  text-transform:uppercase;background:var(--panel);padding:0 .5rem;}}
.fbox .katex-display{{margin:.4rem 0;text-align:left;}}
.fbox .katex-display>.katex,.fbox .katex{{color:var(--gold);}}
.fcomment{{display:block;margin-top:.7rem;font-size:.82rem;color:#c8bfa8;
  font-family:var(--body);font-style:italic;line-height:1.5;}}
.snote{{background:rgba(75,200,200,0.05);border:1px solid rgba(75,200,200,0.15);
  padding:1.2rem 1.5rem;margin:2rem 0;}}
.snote::before{{content:'nota naukowa';font-family:var(--mono);font-size:.55rem;
  letter-spacing:.2em;color:var(--cyan);text-transform:uppercase;display:block;margin-bottom:.5rem;}}
.snote p{{font-size:.93rem;color:#c8bfa8;margin:0;text-align:left;}}
.divider{{text-align:center;margin:4rem 0;color:var(--gold-dim);letter-spacing:.8em;font-size:.7rem;}}

/* CHARTS */
.charts-section{{margin:5rem 0;}}
.charts-title{{font-family:var(--mono);font-size:.65rem;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold-dim);border-bottom:1px solid var(--border);
  padding-bottom:1rem;margin-bottom:0;}}
.tabs{{display:flex;border-bottom:1px solid var(--border);margin-bottom:0;}}
.tab-btn{{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
  color:#6a6050;background:none;border:none;padding:.7rem 1.2rem;cursor:pointer;
  border-bottom:2px solid transparent;position:relative;top:1px;transition:color .2s,border-color .2s;}}
.tab-btn:hover{{color:var(--gold-dim);}}
.tab-btn.active{{color:var(--gold);border-bottom-color:var(--gold);}}
.chart-panel{{display:none;}}
.chart-panel.active{{display:block;}}
.plotly-chart{{width:100%;border:1px solid var(--border);border-top:none;background:var(--panel);}}
.controls{{display:flex;flex-wrap:wrap;gap:1.5rem;padding:1.2rem 1.5rem;
  background:#0b0f1a;border:1px solid var(--border);border-top:none;}}
.ctrl{{display:flex;flex-direction:column;gap:.4rem;min-width:120px;flex:1;}}
.ctrl-label{{font-family:var(--mono);font-size:.56rem;letter-spacing:.15em;
  text-transform:uppercase;color:#6a6050;}}
input[type=range]{{-webkit-appearance:none;width:100%;height:2px;
  background:var(--border);outline:none;cursor:pointer;}}
input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:12px;height:12px;
  background:var(--gold);border-radius:50%;cursor:pointer;box-shadow:0 0 6px rgba(200,168,75,.5);}}
.ctrl-val{{font-family:var(--mono);font-size:.68rem;color:var(--gold);}}
.chart-desc{{font-family:var(--body);font-style:italic;font-size:.88rem;
  color:#d4c8a8;background:#0e1420;padding:1rem 1.5rem;
  border:1px solid var(--border);border-top:none;line-height:1.6;}}

/* FOOTER */
.foot{{border-top:1px solid var(--border);padding:3rem 2rem;max-width:var(--max);
  margin:0 auto;font-family:var(--mono);font-size:.6rem;color:#8a8070;
  letter-spacing:.08em;line-height:2;}}

@media(max-width:768px){{
  .hero{{padding:6rem 1.5rem 4rem;}}
  .main{{padding:4rem 1.5rem 6rem;}}
  .controls{{gap:1rem;}}
}}
</style>
</head>
<body>
<div id="bar"></div>

<header class="hero">
  <div class="hero-grid"></div>
  <p class="hero-eyebrow">Esej naukowy · 2026</p>
  <h1>YHWH<br>i <em>Entropia</em></h1>
  <p class="hero-sub">O stawaniu się rzeczywistości — od geometrii przestrzeni fazowej do świadomości jako struktury dysypatywnej</p>
  <div class="hero-katex">
    \\(S = k_B \\ln \\Omega \\quad\\cdot\\quad \\Delta x \\cdot \\Delta p \\geq \\dfrac{{\\hbar}}{{2}} \\quad\\cdot\\quad H = -\\sum p_i \\log_2 p_i\\)
  </div>
</header>

<main class="main">
{ESSAY_SECTIONS}

<div class="divider">· · ·</div>

<!-- ══ WYKRESY ══ -->
<div class="charts-section" id="viz">
  <div class="charts-title">Wizualizacje interaktywne — modyfikuj parametry</div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('t1',this)">Przestrzeń fazowa</button>
    <button class="tab-btn" onclick="switchTab('t2',this)">Gradient &amp; Przepływ</button>
    <button class="tab-btn" onclick="switchTab('t3',this)">Widmo kwantowe</button>
    <button class="tab-btn" onclick="switchTab('t4',this)">Entropia inf.</button>
  </div>

  <!-- T1: Maxwell-Boltzmann -->
  <div class="chart-panel active" id="t1">
    <div id="plot1" class="plotly-chart"></div>
    <div class="controls">
      <div class="ctrl">
        <span class="ctrl-label">Temperatura T [K]</span>
        <input type="range" id="s1T" min="100" max="2000" value="600" oninput="updateMB()">
        <span class="ctrl-val" id="v1T">600 K</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Gradient G [%]</span>
        <input type="range" id="s1G" min="0" max="100" value="0" oninput="updateMB()">
        <span class="ctrl-val" id="v1G">0 %</span>
      </div>
    </div>
    <div class="chart-desc">Rozkład Maxwella-Boltzmanna prędkości cząstek gazu idealnego. Przy G=0 przestrzeń fazowa jest izotropowa — rozkład symetryczny. Gdy gradient G rośnie, pewne prędkości stają się statystycznie uprzywilejowane: przestrzeń stanów zostaje spolaryzowana bez zmiany praw fizyki. To jest mechanizm falowodu.</div>
  </div>

  <!-- T2: SOFAR Wave -->
  <div class="chart-panel" id="t2">
    <div id="plot2" class="plotly-chart"></div>
    <div class="controls">
      <div class="ctrl">
        <span class="ctrl-label">Gradient ΔT</span>
        <input type="range" id="s2dT" min="0" max="100" value="40" oninput="updateSOFAR()">
        <span class="ctrl-val" id="v2dT">40</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Tłumienie α</span>
        <input type="range" id="s2a" min="0" max="80" value="20" oninput="updateSOFAR()">
        <span class="ctrl-val" id="v2a">20</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Częstość ω</span>
        <input type="range" id="s2w" min="2" max="20" value="5" oninput="updateSOFAR()">
        <span class="ctrl-val" id="v2w">5</span>
      </div>
    </div>
    <div class="chart-desc">Propagacja fali w gradiencie ośrodka — model kanału SOFAR. Gdy ΔT=0, fala rozprasza się izotropowo i szybko zanika. Gdy gradient rośnie, fala zostaje schwytana w warstwie minimalnej prędkości dźwięku i może propagować się przez oceany bez strat. Idea złapana w gradiencie medium przemierza tysiące kilometrów.</div>
  </div>

  <!-- T3: Spectrum -->
  <div class="chart-panel" id="t3">
    <div id="plot3" class="plotly-chart"></div>
    <div class="controls">
      <div class="ctrl">
        <span class="ctrl-label">Pierwiastek Z</span>
        <input type="range" id="s3Z" min="1" max="8" value="1" oninput="updateSpec()">
        <span class="ctrl-val" id="v3Z">H (Z=1)</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Poziom n_max</span>
        <input type="range" id="s3n" min="3" max="8" value="5" oninput="updateSpec()">
        <span class="ctrl-val" id="v3n">n = 5</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Seria emisji</span>
        <input type="range" id="s3s" min="1" max="4" value="2" oninput="updateSpec()">
        <span class="ctrl-val" id="v3s">Balmera</span>
      </div>
    </div>
    <div class="chart-desc">Widmo emisyjne pierwiastków obliczone ze wzoru Rydberga. Każda linia to skok elektronu między poziomami kwantowymi — emisja fotonu o energii równej różnicy potencjałów. Tożsamość pierwiastka jest jego unikalnym wzorcem gradientów energetycznych, czytelnym spektroskopowo na odległość miliardów lat świetlnych.</div>
  </div>

  <!-- T4: Shannon -->
  <div class="chart-panel" id="t4">
    <div id="plot4" class="plotly-chart"></div>
    <div class="controls">
      <div class="ctrl">
        <span class="ctrl-label">Wiarygodność p</span>
        <input type="range" id="s4p" min="1" max="99" value="70" oninput="updateShannon()">
        <span class="ctrl-val" id="v4p">70 %</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Szum σ [%]</span>
        <input type="range" id="s4s" min="0" max="100" value="20" oninput="updateShannon()">
        <span class="ctrl-val" id="v4s">20 %</span>
      </div>
      <div class="ctrl">
        <span class="ctrl-label">Temperatura T [K]</span>
        <input type="range" id="s4T" min="100" max="1000" value="300" oninput="updateShannon()">
        <span class="ctrl-val" id="v4T">300 K</span>
      </div>
    </div>
    <div class="chart-desc">Entropia informacyjna Shannona H(p) i koszt fizyczny Landauera E=kT·ln(2) na bit. Złoty punkt — czysty sygnał. Czerwony — sygnał zaszumiony. Gdy entropia informacyjna układu społecznego rośnie (propaganda, manipulacja), każda decyzja kosztuje więcej energii poznawczej. Gradient informacyjny ma swój fizyczny rachunek.</div>
  </div>
</div>

<div class="divider">· · ·</div>

<section class="essay-section" id="s8">
  <div class="section-marker"><span class="snnum">§ 08</span><div class="snline"></div></div>
  <h2>Coda: <em>gradient, który patrzy na siebie</em></h2>
  <p>YHWH jako „będę, który będę" — i Boltzmann jako \\(S = k_B \\ln \\Omega\\) — opisują tę samą rzeczywistość z dwóch stron tej samej granicy. Jeden mówi językiem objawienia, drugi językiem równań. Oba mówią: rzeczywistość jest procesem, nie bytem. Tożsamość jest gradientem, nie substancją. I koszt istnienia w tej rzeczywistości jest rzeczywisty, fizyczny, nieusuwany — ale nie jest wyrokiem. Jest zaproszeniem do bycia kanałem przepływu.</p>
  <div class="pq"><p>Świadomość jest gradientem, który patrzy na siebie. I właśnie to czyni historię życia tak osobliwą w kosmicznej skali — nie rozmiar, lecz zdolność do refleksji nad własnym miejscem w rozładowywaniu pierwotnej asymetrii Wielkiego Wybuchu.</p></div>
</section>
</main>

<footer class="foot">
  <div>© 2026 · Esej naukowy · CC BY-NC-ND 4.0</div>
  <div>Źródła: Boltzmann 1877 · Prigogine 1977 · Heisenberg 1927 · Shannon 1948 · Landauer 1961 · Penrose 2004</div>
  <div>Wykresy: Python 3 + Plotly.js 2.27 · Wzory: KaTeX 0.16</div>
</footer>

<!-- ══ DATA (pre-computed by Python) ══ -->
<script>
const MB_DATA    = {mb_json};
const SOFAR_DATA = {sofar_json};
const SPEC_DATA  = {spec_json};
const HP_PS      = {hp_ps};
const HP_HS      = {hp_hs};
const ELEM_NAMES = ['H','He','Li','Be','B','C','N','O'];
const SERIES_NAMES = ['Lymana','Balmera','Paschena','Bracketta'];
</script>

<script>
// ── Plotly theme ──
const BG   = '#161e2e', PAPER = '#161e2e';
const GOLD = '#c8a84b', AMBER = '#e8b84b', CYAN = '#4bc8c8', RUST = '#c85a2a';
const GRIDCOL = 'rgba(180,150,60,0.12)', LINECOL = 'rgba(180,150,60,0.4)';
const FONT = {{'family':"'Share Tech Mono', monospace", 'size':10, 'color':'#9a9080'}};

const LAYOUT_BASE = {{
  paper_bgcolor: PAPER, plot_bgcolor: BG,
  font: FONT, margin: {{l:52, r:20, t:24, b:48}},
  xaxis: {{gridcolor:GRIDCOL, zerolinecolor:LINECOL, tickfont:FONT}},
  yaxis: {{gridcolor:GRIDCOL, zerolinecolor:LINECOL, tickfont:FONT}},
  showlegend: false,
  autosize: true
}};

const PLOTLY_CFG = {{
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['select2d','lasso2d','autoScale2d'],
  displaylogo: false,
  toImageButtonOptions: {{format:'png', filename:'wykres_entropia'}}
}};

function tab(id) {{
  document.querySelectorAll('.chart-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}}
function switchTab(id, btn) {{
  tab(id);
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if(id==='t1') initMB();
  if(id==='t2') initSOFAR();
  if(id==='t3') initSpec();
  if(id==='t4') initShannon();
}}

// ════════════════════════════
// C1 — Maxwell-Boltzmann
// ════════════════════════════
let mb_init = false;
function snapT(v) {{
  const steps = [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000];
  return steps.reduce((a,b)=>Math.abs(b-v)<Math.abs(a-v)?b:a);
}}
function snapG(v) {{
  const steps = [0,25,50,75,100];
  return steps.reduce((a,b)=>Math.abs(b-v)<Math.abs(a-v)?b:a);
}}

function getMBdata(T, G) {{
  const key = `T${{T}}_G${{G}}`;
  return MB_DATA[key];
}}

function initMB() {{
  mb_init = true;
  updateMB();
}}

function updateMB() {{
  const rawT = parseInt(document.getElementById('s1T').value);
  const rawG = parseInt(document.getElementById('s1G').value);
  const T = snapT(rawT), G = snapG(rawG);
  document.getElementById('v1T').textContent = rawT + ' K';
  document.getElementById('v1G').textContent = rawG + ' %';
  const d = getMBdata(T, G);
  if (!d) return;

  const traces = [{{
    x: d.v, y: d.f, type:'scatter', mode:'lines',
    fill:'tozeroy',
    fillcolor:'rgba(200,168,75,0.15)',
    line:{{color:GOLD, width:2}},
    name:'f(v)',
    hovertemplate:'v: %{{x:.0f}}<br>f(v): %{{y:.4f}}<extra></extra>'
  }}];

  if (G > 0) {{
    traces.push({{
      x: d.v, y: d.v.map(v => 0),
      type:'scatter', mode:'lines',
      fill:'none', line:{{color:'rgba(75,200,200,0.3)', width:0}},
      showlegend:false
    }});
  }}

  // vp line
  const vp_x = d.vp_frac * Math.max(...d.v);
  traces.push({{
    x:[vp_x, vp_x], y:[0,1],
    type:'scatter', mode:'lines',
    line:{{color:'rgba(200,168,75,0.4)', width:1, dash:'dot'}},
    name:'v_p'
  }});

  const layout = Object.assign({{}}, LAYOUT_BASE, {{
    xaxis: Object.assign({{}}, LAYOUT_BASE.xaxis, {{title:{{text:'prędkość v', font:FONT}}}}),
    yaxis: Object.assign({{}}, LAYOUT_BASE.yaxis, {{title:{{text:'f(v)', font:FONT}}}})  ,
    title: {{text:`Maxwell-Boltzmann  T=${{T}}K  G=${{G}}%`, font:{{color:GOLD, size:11, family:FONT.family}}}},
    annotations: [{{
      x:vp_x, y:0.95, text:'v_p', showarrow:false,
      font:{{color:'rgba(200,168,75,0.7)', size:10, family:FONT.family}},
      xref:'x', yref:'paper'
    }}]
  }});

  if (!mb_init || !document.getElementById('plot1').data) {{
    Plotly.newPlot('plot1', traces, layout, PLOTLY_CFG);
  }} else {{
    Plotly.react('plot1', traces, layout, PLOTLY_CFG);
  }}
}}

// ════════════════════════════
// C2 — SOFAR wave
// ════════════════════════════
function snapSOFAR(id, steps) {{
  const v = parseInt(document.getElementById(id).value);
  return steps.reduce((a,b)=>Math.abs(b-v)<Math.abs(a-v)?b:a);
}}

function initSOFAR() {{ updateSOFAR(); }}

function updateSOFAR() {{
  const dT_raw = parseInt(document.getElementById('s2dT').value);
  const a_raw  = parseInt(document.getElementById('s2a').value);
  const w_raw  = parseInt(document.getElementById('s2w').value);
  document.getElementById('v2dT').textContent = dT_raw;
  document.getElementById('v2a').textContent  = a_raw;
  document.getElementById('v2w').textContent  = w_raw;

  const dTsnap = [0,20,40,60,80,100].reduce((a,b)=>Math.abs(b-dT_raw)<Math.abs(a-dT_raw)?b:a);
  const asnap  = [0,10,20,40,60,80].reduce((a,b)=>Math.abs(b-a_raw)<Math.abs(a-a_raw)?b:a);
  const wsnap  = [2,5,10,15,20].reduce((a,b)=>Math.abs(b-w_raw)<Math.abs(a-w_raw)?b:a);

  const key = `dT${{dTsnap}}_a${{asnap}}_w${{wsnap}}`;
  const d = SOFAR_DATA[key];
  if (!d) return;

  const colors = [GOLD, 'rgba(200,168,75,0.5)', 'rgba(200,168,75,0.3)'];
  const widths = [2, 1, 0.8];
  const traces = d.xs.map((xs, i) => ({{
    x: xs, y: d.ys[i], type:'scatter', mode:'lines',
    line:{{color:colors[i]||GOLD, width:widths[i]||1}},
    name: d.labels[i],
    hovertemplate:'x: %{{x:.3f}}<br>y: %{{y:.3f}}<extra></extra>'
  }}));

  // SOFAR channel marker
  if (dTsnap > 5) {{
    traces.push({{
      x:[0,1], y:[d.sofar_y, d.sofar_y],
      type:'scatter', mode:'lines',
      line:{{color:`rgba(75,200,200,${{dTsnap/200}})`, width:1, dash:'dot'}},
      name:'kanał SOFAR'
    }});
  }}

  const layout = Object.assign({{}}, LAYOUT_BASE, {{
    xaxis: Object.assign({{}}, LAYOUT_BASE.xaxis, {{
      title:{{text:'odległość →', font:FONT}}, range:[0,1]}}),
    yaxis: Object.assign({{}}, LAYOUT_BASE.yaxis, {{
      title:{{text:'amplituda', font:FONT}}, range:[0,1]}}),
    title: {{text:`SOFAR  ΔT=${{dTsnap}}  α=${{asnap}}  ω=${{wsnap}}`,
             font:{{color:GOLD,size:11,family:FONT.family}}}}
  }});

  Plotly.react('plot2', traces, layout, PLOTLY_CFG);
}}

// ════════════════════════════
// C3 — Quantum spectrum
// ════════════════════════════
function initSpec() {{ updateSpec(); }}

function updateSpec() {{
  const Z    = parseInt(document.getElementById('s3Z').value);
  const nmax = parseInt(document.getElementById('s3n').value);
  const si   = parseInt(document.getElementById('s3s').value);
  document.getElementById('v3Z').textContent = ELEM_NAMES[Z-1]+' (Z='+Z+')';
  document.getElementById('v3n').textContent = 'n = '+nmax;
  document.getElementById('v3s').textContent = 'Seria '+SERIES_NAMES[si-1];

  const key = `Z${{Z}}_n${{nmax}}_s${{si}}`;
  const d = SPEC_DATA[key];
  if (!d) return;

  const traces = [];

  // energy levels (horizontal lines)
  d.levels.forEach(lv => {{
    traces.push({{
      x:[0, 0.25], y:[lv.E, lv.E],
      type:'scatter', mode:'lines',
      line:{{color: lv.n===1?GOLD:'rgba(200,168,75,0.35)', width:lv.n===1?2:1}},
      showlegend:false,
      hovertemplate:`n=${{lv.n}}  E=${{lv.E.toFixed(2)}} eV<extra></extra>`
    }});
    traces.push({{
      x:[0.27], y:[lv.E],
      type:'scatter', mode:'text',
      text:[`n=${{lv.n}}`],
      textfont:{{color:'rgba(200,168,75,0.6)',size:9,family:FONT.family}},
      showlegend:false, hoverinfo:'none'
    }});
  }});

  // transitions
  d.lines.forEach((ln, idx) => {{
    const col = ln.lam_nm>=380&&ln.lam_nm<=780 ? wlColor(ln.lam_nm) : 'rgba(120,120,120,0.4)';
    const ax = 0.4 + idx * 0.06;
    traces.push({{
      x:[ax, ax], y:[ln.E1, ln.E2],
      type:'scatter', mode:'lines',
      line:{{color:col, width:2, dash:'dot'}},
      showlegend:false,
      hovertemplate:`${{Math.round(ln.lam_nm)}} nm  (${{ln.n1}}→${{ln.n2}})<extra></extra>`
    }});
    if (ln.lam_nm>=380&&ln.lam_nm<=780) {{
      traces.push({{
        x:[ax], y:[ln.E2+0.3],
        type:'scatter', mode:'text',
        text:[Math.round(ln.lam_nm)+'nm'],
        textfont:{{color:col, size:8, family:FONT.family}},
        showlegend:false, hoverinfo:'none'
      }});
    }}
  }});

  const layout = Object.assign({{}}, LAYOUT_BASE, {{
    xaxis: Object.assign({{}}, LAYOUT_BASE.xaxis, {{
      title:{{text:'przejścia / poziomy', font:FONT}},
      showticklabels:false, range:[0,1]}}),
    yaxis: Object.assign({{}}, LAYOUT_BASE.yaxis, {{
      title:{{text:'energia [eV]', font:FONT}}}}),
    title: {{text:`${{d.elem}}  Seria ${{d.series}}  n₁=${{d.n1}}`,
             font:{{color:GOLD,size:11,family:FONT.family}}}}
  }});

  Plotly.react('plot3', traces, layout, PLOTLY_CFG);
}}

function wlColor(nm) {{
  let r,g,b;
  if(nm>=380&&nm<440){{r=(440-nm)/60;g=0;b=1;}}
  else if(nm>=440&&nm<490){{r=0;g=(nm-440)/50;b=1;}}
  else if(nm>=490&&nm<510){{r=0;g=1;b=(510-nm)/20;}}
  else if(nm>=510&&nm<580){{r=(nm-510)/70;g=1;b=0;}}
  else if(nm>=580&&nm<645){{r=1;g=(645-nm)/65;b=0;}}
  else{{r=1;g=0;b=0;}}
  return `rgb(${{Math.round(r*220)}},${{Math.round(g*220)}},${{Math.round(b*220)}})`;
}}

// ════════════════════════════
// C4 — Shannon entropy
// ════════════════════════════
function initShannon() {{ updateShannon(); }}

function updateShannon() {{
  const p0    = parseInt(document.getElementById('s4p').value)/100;
  const noise = parseInt(document.getElementById('s4s').value)/100;
  const T     = parseInt(document.getElementById('s4T').value);
  document.getElementById('v4p').textContent = Math.round(p0*100)+' %';
  document.getElementById('v4s').textContent = Math.round(noise*100)+' %';
  document.getElementById('v4T').textContent = T+' K';

  const Elv = (1.38e-23 * T * Math.log(2) / 1.6e-19).toExponential(2);
  const Hbit = p => (p<=0||p>=1)?0:-(p*Math.log2(p)+(1-p)*Math.log2(1-p));
  const pn = Math.max(0.01, Math.min(0.99, p0 + noise*0.4*Math.sin(p0*17+noise*13)));

  const traces = [
    // curve
    {{x:HP_PS, y:HP_HS, type:'scatter', mode:'lines',
      fill:'tozeroy', fillcolor:'rgba(200,168,75,0.08)',
      line:{{color:'rgba(200,168,75,0.4)',width:1.5}},
      name:'H(p)', hovertemplate:'p: %{{x:.3f}}<br>H: %{{y:.4f}} bit<extra></extra>'}},
    // clean point
    {{x:[p0], y:[Hbit(p0)], type:'scatter', mode:'markers',
      marker:{{color:GOLD,size:12,symbol:'circle',
               line:{{color:'rgba(200,168,75,0.4)',width:2}}}},
      name:`H(p₀)=${{Hbit(p0).toFixed(3)}} bit`,
      hovertemplate:`p₀=${{p0.toFixed(2)}}<br>H=${{Hbit(p0).toFixed(3)}} bit<extra></extra>`}},
    // noisy point
    {{x:[pn], y:[Hbit(pn)], type:'scatter', mode:'markers',
      marker:{{color:RUST,size:10,symbol:'circle-open',
               line:{{color:RUST,width:2}}}},
      name:`H(pₙ)=${{Hbit(pn).toFixed(3)}} bit`,
      hovertemplate:`pₙ=${{pn.toFixed(2)}}<br>H=${{Hbit(pn).toFixed(3)}} bit<extra></extra>}}`,
    // vertical guide
    {{x:[p0,p0], y:[0,Hbit(p0)], type:'scatter', mode:'lines',
      line:{{color:'rgba(200,168,75,0.25)',width:1,dash:'dot'}},
      showlegend:false, hoverinfo:'none'}}
  ];

  const layout = Object.assign({{}}, LAYOUT_BASE, {{
    xaxis: Object.assign({{}}, LAYOUT_BASE.xaxis, {{
      title:{{text:'prawdopodobieństwo p',font:FONT}}, range:[0,1]}}),
    yaxis: Object.assign({{}}, LAYOUT_BASE.yaxis, {{
      title:{{text:'H(p) [bit]',font:FONT}}, range:[0,1.05]}}),
    showlegend: true,
    legend: {{font:{{color:'#c8a84b',size:9,family:FONT.family}},
              bgcolor:'rgba(22,30,46,0.8)',bordercolor:'rgba(180,150,60,0.2)',borderwidth:1}},
    title: {{text:`Shannon H(p)  |  E_Landauer=${{Elv}} eV/bit  |  T=${{T}}K`,
             font:{{color:GOLD,size:11,family:FONT.family}}}}
  }});

  Plotly.react('plot4', traces, layout, PLOTLY_CFG);
}}

// ── Progress bar ──
window.addEventListener('scroll', () => {{
  const h = document.documentElement;
  document.getElementById('bar').style.width =
    (h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';
}}, {{passive:true}});

// ── Init ──
window.addEventListener('DOMContentLoaded', () => {{
  initMB();
  // pre-init hidden charts so they're ready
  setTimeout(()=>{{ initSOFAR(); initSpec(); initShannon(); }}, 200);
}});
</script>
</body>
</html>"""

# ── Main ─────────────────────────────────────────────────────────

print("Generuję zbiory danych (Maxwell-Boltzmann)...")
mb_data = build_mb_datasets()
print(f"  → {len(mb_data)} wariantów MB")

print("Generuję zbiory danych (SOFAR)...")
sofar_data = build_sofar_datasets()
print(f"  → {len(sofar_data)} wariantów SOFAR")

print("Generuję zbiory danych (widma kwantowe)...")
spec_data = build_spectrum_datasets()
print(f"  → {len(spec_data)} wariantów spektralnych")

print("Składam HTML...")
html = generate_html(mb_data, sofar_data, spec_data)

out = "yhwh_entropia.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = len(html.encode()) // 1024
print(f"\n✓ Wygenerowano: {out}  ({size_kb} KB)")
print("  Otwórz w przeglądarce lub wrzuć na GitHub Pages jako index.html")
print("\n  GitHub Pages:")
print("  1. Zmień nazwę na index.html")
print("  2. Wrzuć do repozytorium")
print("  3. Settings → Pages → Source: main / root")
