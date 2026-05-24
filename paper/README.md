# IEEE Conference Paper

Bu klasör, projenin akademik makaleleştirilmiş hâlini içerir.

## Dosyalar

- `wordle-turkish.tex` — IEEEtran format LaTeX kaynağı (İngilizce, conference template)
- `wordle-turkish.pdf` — Derlenmiş PDF (5 sayfa)
- `figures/` — İngilizce-etiketli PNG grafikler (`../scripts/plot_english.py` üretir; Türkçe versiyonlar `data/figures/` altında, docs/ için)
- `Makefile` — Tek komutluk derleme

## Derleme

```bash
brew install tectonic   # macOS; veya: cargo install tectonic
cd paper
make                    # tectonic ile derler; paketleri otomatik indirir
make view               # PDF'i ac (macOS)
make clean              # ara dosyalari temizle
```

İlk derleme ~30 saniye (CTAN'dan IEEEtran ve diğer paketleri indirir; sonraki
derlemeler önbellekten 2-5 saniye).

## Bibliyografya

Inline `thebibliography` ortamı kullanılıyor (BibTeX yok). On beş referans:
- Shannon 1948 (bilgi teorisi)
- Sanderson / 3Blue1Brown 2022 (entropy-greedy Wordle bot, YouTube)
- Bertsimas & Paskov (Operations Research, 2025; "An Exact Solution to Wordle")
- Mauboussin 2012 (skill/luck framework)
- Levitt & Miles 2014 (poker skill/luck)
- Wardle 2021 (orijinal Wordle)
- Wordle Türkçe (oyun)
- Aladaileh et al. 2026 (NEJCS; peer-reviewed information-theory Wordle solver)
- Harris et al. 2020 (NumPy, Nature)
- Hunter 2007 (Matplotlib, CSE)
- Liang et al. 2024 (arXiv; semantic/orthographic biases in human Wordle play)
- Göksel & Kerslake 2005 (Routledge; Turkish grammar — CVCVC syllable claim)
- **Akbulut & Senturk 2026** (Entertainment Computing 57:101117; *önceki Türkçe Wordle çalışması* — LSTM/MaxEnt/rule-based solver karşılaştırması)
- **Qiu & Zhong 2024** (HSW model, IOS Press; vokabüler-population modelinin parallel'i)
- **Dilger 2023** (arXiv 2309.02110; İngilizce Wordle için ilk skill/luck info-theory analizi)

## Yeniden üretim

Bütün figürler `../scripts/difficulty.py` tarafından üretilir. Veri pipeline'ı
projenin kök README'sinde anlatılmıştır.
