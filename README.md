# Wordle Türkçe — Şans mı, Beceri mi?

[wordleturkce.bundle.app](https://wordleturkce.bundle.app/) sitesinin kelime
listesinden ve harf frekanslarından yola çıkarak şu soruyu cevaplayan bir araç:

> **"Wordle'da kazanmanın yüzde kaçı şans, yüzde kaçı oyunu iyi bilmek?"**

## Kısa cevap

Tek bir sayı yok — taban seçimine göre değişiyor:

| Şans tabanı | Şans % | Beceri % |
|---|---:|---:|
| Saf rastgele (geri bildirim yok) | %0.1 | %99.9 |
| Gerçekçi insan (K=500) | %17 | %83 |
| **Gerçekçi insan (K=1000)** | **%34** | **%66** |
| Gerçekçi insan (K=2000) | %67 | %33 |
| Tutarlı rastgele (tam sözlük) | %97 | %3 |

**Gerçekçi cevap:** ~%34 şans, ~%66 beceri.
Ve "beceri"nin neredeyse tamamı (~%63) **vokabüler** (kelime bilgisi),
küçük bir kısmı (~%3) **strateji** (frekans/entropy mantığı).

## Dokümanlar

| Doküman | Açıklama |
|---|---|
| 📄 [`docs/sonuc.md`](docs/sonuc.md) | Özet doküman — final cümlesi hazır |
| 📓 [`docs/hesaplama-defteri.md`](docs/hesaplama-defteri.md) | Adım adım hesap defteri (15 adım) |
| 🔍 [`docs/metodoloji-kritik.md`](docs/metodoloji-kritik.md) | Yöntem özeleştirisi ve iyileştirmeler |
| 📚 [`paper/wordle-turkish.pdf`](paper/wordle-turkish.pdf) | IEEE format akademik makale (5 sayfa, İngilizce) |

> Yazarın özel video script'i, indirilmiş Unsplash fotoğrafları ve Manim
> animasyonları `script/` klasöründedir; bu klasör `.gitignore` içinde olduğu
> için GitHub'da görünmez.

## Çalıştırma

```bash
pip install numpy matplotlib

python3 scripts/extract.py         # bundle'dan veri çıkar
python3 scripts/analyze.py         # frekans analizi
python3 scripts/simulate.py        # ilk üç oyuncu simülasyonu
python3 scripts/entropy_bot.py     # entropy-greedy bot (gerçek skill tavanı)
python3 scripts/human_baseline.py  # vokabüler-K duyarlılığı
python3 scripts/difficulty.py      # zorluk + üç-tanım + grafikler (Türkçe)
python3 scripts/plot_english.py    # paper için İngilizce-etiketli grafikler
```

Python 3.10+ gerekir. Tüm pipeline standart bir makinede ~3 dakika.

### Makaleyi derlemek için
```bash
brew install tectonic
cd paper && make
```

## Proje yapısı

```
data/                       ham veri + hesap çıktıları (JSON)
  figures/                  matplotlib grafikleri (PNG)
docs/
  sonuc.md                  özet doküman
  hesaplama-defteri.md      adım adım hesap defteri
  metodoloji-kritik.md      yöntem özeleştirisi ve iyileştirmeler
paper/
  wordle-turkish.tex        IEEE LaTeX kaynağı
  wordle-turkish.pdf        derlenmiş PDF (IEEE conference format)
  Makefile                  tectonic ile tek komutluk derleme
  figures/                  İngilizce-etiketli grafikler (plot_english.py üretir)
scripts/
  extract.py                bundle'dan kelime listelerini ayıklar
  analyze.py                harf + pozisyonel frekans
  simulate.py               saf/tutarlı rastgele + frekans-botu
  entropy_bot.py            3Blue1Brown stili entropy-greedy bot
  human_baseline.py         vokabüler-kısıtlı insan modeli (K parametreli)
  difficulty.py             kelime-başına zorluk + 3-tanım tablosu + Türkçe grafikler
  plot_english.py           aynı 4 grafiğin İngilizce-etiketli versiyonu (paper için)
```

## Veri kaynağı

- `https://wordleturkce.bundle.app/static/main.2023-04-23.js`
- İçinde iki dizi: `La` (11.470 günlük cevap, 2.936 benzersiz) ve
  `Ta` (5.531 ek sözlük). Geçerli tahmin = `La ∪ Ta` (5.500 benzersiz kelime).

## Önemli görseller

- `data/figures/turn_breakdown.png` — Dört oyuncu modelinin tur histogramı
- `data/figures/skill_decomposition.png` — Şans/beceri payları (5 taban)
- `data/figures/k_vs_winrate.png` — Vokabüler büyüklüğüne göre kazanma eğrisi
- `data/figures/difficulty_hist.png` — Entropy-bot'un tur dağılımı

## Lisans

Bu projeyi açık kaynak olarak yayınlıyoruz. Kelime listeleri kaynak siteden
analiz amacıyla çıkartılmıştır; ticari kullanımdan kaçınılması önerilir.
Hesaplama kodu ve çıktıları için MIT lisansı geçerlidir.
