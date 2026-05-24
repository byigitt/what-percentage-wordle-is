# Hesaplama Defteri - Wordle Türkçe: Şans mı, Beceri mi?

Bu doküman, [wordleturkce.bundle.app](https://wordleturkce.bundle.app/) için
yapılan şans/beceri analizinin **adım adım hesap defteri**dir. Bütün sayılar
gerçek koddan ve gerçek simülasyon çıktılarından alınmıştır; her sonucu okur
kendisi tekrar üretebilir.

> **Bu defterin ilk yarısı (Adım 1-10) ilk yaklaşımı anlatır ve oradan
> %97 şans / %3 beceri sonucuna ulaşır.** İkinci yarısı (Adım 11-15) bu
> yaklaşımın eksiklerini gösterir ve daha gerçekçi sonuca varır
> (%34 şans / %66 beceri). İki bölüm de açık bırakılmıştır çünkü
> **metodolojinin evrimi**, sonuçtan en az kadar öğreticidir.

---

## Adım 0 - Soruyu netleştirme

> *"Wordle'da kazanmanın yüzde kaçı şans, yüzde kaçı oyunu iyi bilmek?"*

Bu soruyu cevaplamak için iki temel ölçüme ihtiyaç vardır:

1. Bir **şans tabanı** - strateji uygulamayan bir oyuncunun ne kadar
   kazandığı.
2. Bir **beceri tavanı** - en iyi stratejiyi uygulayan bir oyuncunun ne
   kadar kazandığı.

Aradaki fark beceri payını verir; tavanın altında kalan ise indirgenemez
şanstır.

> **Önemli uyarı:** Cevap, "şans tabanı"nın nasıl tanımlandığına göre
> **%3 ile %99 arasında** değişir. Bu yüzden tek bir sayı yerine birden
> fazla taban değerlendirilmiştir.

---

## Adım 1 - Oyunun veri tabanını çıkarma

Sayfanın kaynak kodu (`https://wordleturkce.bundle.app/static/main.2023-04-23.js`)
**iki JavaScript dizisi** içerir:

```js
var La = [ "körpe", "acele", "güneş", ... ]   // 11.470 eleman
var Ta = [ "abacı", "abadi", "abalı", ... ]   // 5.531 eleman
```

Kodun ileri kısmında bu iki dizinin nasıl kullanıldığı açıkça görülür:

```js
function Da(e) { var s = Ga(e); return La[s % La.length] }   // günlük kelime
... if (!Ta.includes(e) && !La.includes(e)) return invalid    // tahmin doğrulama
```

Yani:

- **`La`** = günlük cevap listesi (gün indeksi `mod 11470` ile seçilir).
- **`Ta`** = ek geçerli tahmin sözlüğü.
- **Geçerli tahmin** = `La` ∪ `Ta` içinde olan herhangi bir kelime.

`scripts/extract.py`, bu iki diziyi `data/solutions.json` ve `data/extras.json`
olarak diske kaydeder.

---

## Adım 2 - Listeleri temizleme ve gerçek boyutları görme

Ham sayılar:

| Liste | Toplam giriş | Benzersiz kelime |
|---|---:|---:|
| `La` (cevaplar) | 11.470 | **2.936** |
| `Ta` (ek sözlük) | 5.531 | 5.499 |
| Birleşik geçerli tahmin | 17.001 | **5.500** |

**Kritik bir gözlem:** `La` listesindeki 11.470 girişin sadece **2.936**'sı
farklı kelime. Yani bazı kelimeler defalarca tekrar eder. Örnek:

- `"buruk"` → 8 kez
- `"selam"` → 8 kez
- `"paket"`, `"vefat"`, `"piyaz"`, `"torba"`, `"çiçek"` → 7 kez

Bu tesadüf değildir: bundle, bu yöntemle bazı kelimelerin günlük cevap olma
**olasılığını artırır**. Yani günlük cevap dağılımı *uniform değildir*,
**ağırlıklıdır**. Bu çoğaltı bilgisi, ilerideki adımlarda **yaygınlık skoru**
olarak da kullanılacaktır.

---

## Adım 3 - Harf frekansı (`scripts/analyze.py`)

11.470 günlük cevabın 5'er harfini sayıp ilk 15 harfin yüzdeleri:

```
a    7479  13.04%       s    2429   4.24%
e    4888   8.52%       u    1989   3.47%
i    3960   6.90%       ı    1718   3.00%
k    3908   6.81%       o    1665   2.90%
r    3493   6.09%       y    1426   2.49%
t    2883   5.03%       b    1390   2.42%
m    2761   4.81%
l    2739   4.78%
n    2614   4.56%
```

`a`, `e`, `i`, `k`, `r` ilk beştedir; bu beş harf kelimelerin yaklaşık %41'ini
kapsar.

**Pozisyon-bazlı en sık 5 harf** (slot 1-5):

```
1. harf: k(1336), s(1121), t(841), b(751),  m(714)
2. harf: a(3199), e(1881), i(1142), o(938),  u(782)
3. harf: r(1435), l(1183), k(799),  n(757),  m(747)
4. harf: a(2308), i(1587), e(1530), ı(868),  u(843)
5. harf: k(1367), n(1189), r(1070), a(1052), e(971)
```

Bu desenden çıkan gözlem: tipik bir Türkçe Wordle cevabı **K-A-R-A-N** veya
**S-A-L-İ-K** kalıbına benzer. Sessiz harfle başlayıp ünlü-sessiz-ünlü-sessiz
ile biter - bu Türkçenin hece yapısının doğrudan yansımasıdır.

---

## Adım 4 - Frekans skoru ile en iyi açılış

Bir kelimenin **frekans skoru** tanımı:

> *Benzersiz* harflerin **pozisyonel** frekanslarının toplamı.
>
> `skor(w) = Σ pos_freq[i, w[i]]  for i where w[i] daha önce gelmemiş`

Benzersiz harf sayma motivasyonu: aynı harfin tekrarı yeni bilgi getirmez.

Bütün geçerli sözlük puanlandığında en yüksek skorlu kelimeler:

```
salik   8.457   <-- en yüksek
tarik   8.429
talik   8.177
serak   8.112
kalem   8.064
malik   8.050
karın   8.027
karun   8.002
```

**İlk bot için açılış kelimesi:** `salik` (skor 8.457).

> Not: İnsan oyuncuların kullandığı klasik açılış kelimeleri (`KALEM`,
> `TARİK`, `KIRAN`) zaten bu listenin en üstündedir - internette dolaşan
> "iyi açılış" tavsiyeleri tam olarak bu frekans mantığının çıktısıdır.

---

## Adım 5 - Üç oyuncu modeli (ilk yaklaşım)

Şans/beceri ayrıştırması için üç oyuncu simüle edilir:

| Oyuncu | Geri bildirim | Strateji |
|---|---|---|
| **Saf rastgele** | Hayır | Hayır |
| **Tutarlı rastgele** | Evet (kurallara uyar) | Hayır |
| **Frekans-botu** | Evet | Evet (frekans skoru) |

- **Saf rastgele**: 6 tur boyunca sözlükten rastgele kelime söyler.
- **Tutarlı rastgele**: Renk geri bildirimine sadık kalır, kalan adaylardan
  rastgele birini seçer.
- **Frekans-botu**: Her turda kalan adayların yerel pozisyonel frekansını
  yeniden hesaplayıp en yüksek skorlu adayı seçer.

---

## Adım 6 - Renk geri bildirimi (kontrol)

Wordle'ın standart kuralı (çift harf durumu dahil):

```python
def feedback(guess, answer):
    # 2 = doğru harf doğru yer (yeşil)
    # 1 = doğru harf yanlış yer (sarı)
    # 0 = harf cevapta yok (gri)
    res = [0]*5
    remaining = Counter()
    for i in range(5):
        if guess[i] == answer[i]: res[i] = 2
        else: remaining[answer[i]] += 1
    for i in range(5):
        if res[i] == 0 and remaining[guess[i]] > 0:
            res[i] = 1; remaining[guess[i]] -= 1
    return res
```

Önce yeşiller (2) işaretlenir, sonra kalan kontenjan üzerinden sarılar (1)
dağıtılır. Bu kural çift harfli kelimelerde (`anane`, `kakao` vs.) kritiktir.

---

## Adım 7 - Simülasyon: 2.936 benzersiz cevap × 3 oyuncu

`scripts/simulate.py` çıktıları:

### Saf rastgele
```
Kazanma oranı:   0.10%   (3 / 2936)
Histogram: {0:2933, 1:1, 6:2}
```

Beklenti ile uyumludur: 5.500 sözlükten rastgele tahmin başına olasılık
`1/5500`, 6 turda `1 - (1 - 1/5500)^6 ≈ 0.109%`. Simülasyon `0.10%` verir. ✅

### Tutarlı rastgele
```
Kazanma oranı:  96.97%   (2847 / 2936)
Kazanan oyunlarda ortalama tahmin: 4.21
Histogram: {0:89, 1:2, 2:94, 3:600, 4:1029, 5:855, 6:267}
```

Sadece geri bildirime sadık kalarak **%96.97 kazanma**. Bu sonuç çarpıcıdır:
Wordle'ın geri bildirim sistemi tek başına devasa miktarda bilgi sızdırır.

### Frekans-botu
```
Kazanma oranı:  99.18%   (2912 / 2936)
Kazanan oyunlarda ortalama tahmin: 3.77
Histogram: {0:24, 1:1, 2:147, 3:1011, 4:1222, 5:433, 6:98}
```

Stratejik seçim %99.18'e taşır ve ortalama tahmini 4.21 → 3.77'ye indirir.

---

## Adım 8 - Eşleştirmeli karşılaştırma (ilk ayrıştırma)

İki oyuncuyu aynı cevap üzerinde oynatınca (2.936 cevap):

```
Her ikisi kazanır       : 2825 / 2936  =  96.22%
Sadece bot kazanır      :   87 / 2936  =   2.96%
Sadece rastgele kazanır :   22 / 2936  =   0.75%
İkisi de kaybeder       :    2 / 2936  =   0.07%
```

İlk varılan sonuç:

| Bot kazanımının ayrıştırması | Sayı | Pay |
|---|---:|---:|
| **Şans** (rastgele de kazanırdı) | 2825 | **%97.01** |
| **Beceri** (sadece strateji ile kazanıldı) | 87 | **%2.99** |

---

## Adım 9 - Çapraz kontrol: Bilgi teorisi

Cevap dağılımının **Shannon entropisi**:

```
H = -Σ p_i · log2(p_i)
  = 11.36 bit   (ağırlıklı 11.470 günlük dağılım üzerinden)
H_max = log2(2936) = 11.52 bit    (uniform olsaydı)
```

Yani gün dağılımı uniform'a çok yakındır (%98.6 entropi verimliliği).

Bir tahminin **teorik bilgi tavanı**:

```
log2(3^5) = log2(243) = 7.92 bit / tur
```

Bu da teorik olarak en az **11.36 / 7.92 ≈ 1.43 tur**'da çözmek mümkün olduğunu
gösterir.

---

## Adım 10 - İlk sonucun zayıflıkları

İlk yaklaşımın özeti: *frekans-botu vs tutarlı rastgele* tabanı altında
**~%97 şans, ~%3 beceri**.

Bu sonuç teknik olarak doğru, ancak üç ciddi zayıflığı vardır:

1. **Şans tabanı insanı overstate eder.** "Tutarlı rastgele" modeli, 5.500
   kelimelik tüm sözlüğü mükemmel hatırlar ve geri bildirim takibinde hata
   yapmaz. Gerçek bir insan oyuncu hiçbirini yapamaz: tipik kullanıcı belki
   800-1500 farklı 5-harfli kelime bilir.

2. **Skill tavanını understate eder.** Frekans skoru naif bir sezgiseldir.
   Asıl skill tavanı bilgi-teorisi tabanlı (entropy-greedy) bottur.

3. **Şans/beceri tanımı tek değildir.** Tabanı değiştirince cevap dramatik
   biçimde değişir.

Aşağıdaki adımlar bunları sırasıyla düzeltir.

---

## Adım 11 - Entropy-greedy bot (gerçek skill tavanı)

`scripts/entropy_bot.py`, 3Blue1Brown'ın Wordle videosunda tanıttığı
bilgi-teorisi tabanlı bir bot implementeder. Her turda, her olası tahmin `g`
için **beklenen bilgi kazancını** hesaplar:

```
H(g | C) = − Σ_p  P(p|g,C) · log₂ P(p|g,C)

burada P(p|g,C) = #{a ∈ C : pattern(g,a) = p} / |C|
```

ve en yüksek `H(g)`'yi veren tahmini seçer. Sezgisel olarak: *"Şu tahmin,
kalan adayları ortalama olarak ne kadar dengeli bölecek?"*

### Performans optimizasyonu: pattern matrisi precompute

2.936 × 2.936 = ~8.6M çift için `feedback(guess, answer)` sonuçları **uint8
matrise** (base-3 encoded pattern: 0..242) yazılır. Bir kez 0.5s sürer,
sonraki her turda saniyenin altında çalışır.

Doğrulama: vektorize feedback fonksiyonu, Python referans fonksiyonuyla
5000 rastgele çiftte karşılaştırılmıştır → **0 fark**.

### Sonuç

```
En iyi entropy-açılışı: 'merak'   H = 5.81 bit
Top-10:  merak, kenar, kamer, kelam, kalem, malik, karne, katre, keman, karni

Simülasyon (2936 cevap):
  Kazanma: 100.00%   (2936 / 2936)
  Ortalama tur:      3.585
  Histogram: {1:1, 2:84, 3:1221, 4:1455, 5:175}   <-- 6. tur yok
```

Entropy-bot **hiç kaybetmez** ve ortalama 3.6 turda çözer. Frekans-botundan
ölçülebilir biçimde güçlüdür:

| Bot | Kazanma | Ortalama tur |
|---|---:|---:|
| Frekans | %99.18 | 3.77 |
| Entropy | **%100.00** | **3.59** |

> **Önemli fark:** Açılışlar değişir. Frekans `salik` derken, entropy `merak`
> seçer. Sebep: `merak` adayları daha dengeli partition'lara böler (5.81 bit
> beklenen bilgi). `salik` daha "popüler harfler" içerir ama partition'ı daha
> dengesizdir.

---

## Adım 12 - Vokabüler-kısıtlı insan tabanı

`scripts/human_baseline.py`, gerçekçi bir insan oyuncuyu modeller:

- Sözlüğün tamamını bilmez; sadece **bilinen-vokabüler** içinden kelime
  söyleyebilir.
- Vokabüler dışındaki bir kelime hâlâ aday olsa bile söyleyemez.
- "Bilinen" tanımı: La listesindeki çoğaltı sayısı yaygınlık sinyalidir -
  bundle curator'ları zaten daha tanıdık kelimeleri daha sık cevap olarak
  koymuştur.

K = vokabüler büyüklüğü parametresi. K duyarlılığı:

| K | Uniform kazanma | Ağırlıklı kazanma | Vokabüler kapsama |
|---:|---:|---:|---:|
| 200 | %6.81 | %10.92 | %10.92 |
| 500 | %17.00 | %25.74 | %25.79 |
| 1000 | %33.92 | %47.39 | %47.59 |
| 1500 | %50.72 | %67.00 | %67.50 |
| 2000 | %67.13 | %83.68 | %84.93 |
| 2500 | %83.58 | %94.46 | %96.20 |
| 2936 | %97.21 | %97.20 | %100.00 |

**Çok temiz bir desen:** kazanma oranı ≈ vokabüler kapsama oranı. Çünkü
vokabüler dışındaki kelimeyi *kazanmak imkânsız*; vokabüler içindeki
kelimelerde ise consistent-random ~%97 ile kazanır. Sonuç:

```
P(kazan | K) ≈ vokabüler_kapsama(K) × 0.97
```

Tipik bir Türkçe Wordle oyuncusu (K ≈ 1000) gerçek hayatta **~%47 ağırlıklı
kazanma oranına** sahiptir. Bu, "şans tabanı" olarak çok daha gerçekçidir.

---

## Adım 13 - Üç farklı tabana göre şans/beceri ayrıştırması

Aynı entropy-bot kazanımları (%100), farklı tabanlara göre ayrıştırılınca:

| Şans tabanı | Taban kazanma % | Şans payı | Beceri payı |
|---|---:|---:|---:|
| Saf rastgele (geri bildirim yok) | 0.10% | **%0.1** | **%99.9** |
| İnsan (K=500, ~%26 vokab.) | 17.00% | **%17.0** | **%83.0** |
| **İnsan (K=1000, ~%48 vokab.)** | **33.92%** | **%33.9** | **%66.1** |
| İnsan (K=2000, ~%85 vokab.) | 67.13% | **%67.1** | **%32.9** |
| Tutarlı rastgele (tam sözlük) | 96.97% | **%97.0** | **%3.0** |

> **Net içgörü:** "Şans %X, beceri %Y" rakamı **tek değildir** - taban
> seçimine tamamen bağlıdır. İlk yaklaşımın çıktısı (%97/%3) teknik olarak
> doğrudur, ancak insanı tüm sözlüğü ezbere bilen biri olarak modellediği
> için yanıltıcıdır.

### Gerçekçi insan tabanı (K=1000) ile sonuç

> **~%34 şans, ~%66 beceri.**

Ve bu "beceri"nin içine bakıldığında iki bileşen görülür:

| Bileşen | Açıklama | Ağırlık |
|---|---|---:|
| **Vokabüler** | Türkçe 5-harfli kelime bilgisi | ~%66 |
| **Strateji** | Frekans/entropy mantığı | ~%3 |

**Yani "oyunu iyi bilmek" demek, esas olarak çok kelime bilmek demektir.**
Frekans stratejisi/açılış kelimesi seçimi vs. küçük ama anlamlı ek bir
katkıdır.

---

## Adım 14 - Kelime-başına zorluk

Entropy-bot **kazanır** ama hangi kelimelerde zorlanır? `scripts/difficulty.py`
her cevap için kaç turda çözüldüğünü hesaplar:

| Tur sayısı | Kelime adedi |
|---:|---:|
| 1 | 1 (`merak`, açılışın kendisi) |
| 2 | 84 |
| 3 | 1.221 |
| 4 | 1.455 |
| **5** | **175** |
| 6 | 0 |

> Bot **hiçbir** kelimede 6. tura gitmez. 5. turda biten 175 kelime "en zor"
> kategorisidir.

En zor 20 örnek: `gıdık, ralli, reşit, savcı, fizik, galon, gayri, havan,
hazan, inanç, kapak, kaçak, kucak, pembe, siğil, yassı, yağma, çizgi, şehir,
şifon`.

Bunların ortak özelliği: aynı kalıbı paylaşan birçok yakın komşu vardır
(`KAPAK/KAÇAK/KAVAK/KAZAK` ailesi - sadece 3. harf değişiyor). Bot tek harf farklı tüm
varyantları tek tek denemek zorundadır; bu da fazladan 1-2 tur demektir.

Bu, "puzzle zorluğunun yapısal kaynağı"dır - strateji ile değiştirilemeyen
indirgenemez bir özellik. Günün cevabı bu ailelerden biriyse hem ortalama
bir insan hem en iyi bot uzun sürer; aradaki fark yine de **sadece** strateji
nedeniyle değildir.

---

## Adım 15 - Görseller

`scripts/difficulty.py` çalıştırıldığında dört grafik üretilir:

| Dosya | İçerik |
|---|---|
| `data/figures/turn_breakdown.png` | Dört oyuncu modelinin tur histogramı yan yana |
| `data/figures/difficulty_hist.png` | Entropy-bot'un her kelimeyi kaç turda çözdüğü |
| `data/figures/k_vs_winrate.png` | Vokabüler-K büyüklüğüne göre kazanma oranı eğrisi |
| `data/figures/skill_decomposition.png` | Şans/beceri payları beş tabana göre |

---

## Tekrarlanabilirlik

Tüm çıktıyı tekrar üretmek için (sıralı):

```bash
pip install numpy matplotlib

python3 scripts/extract.py         # bundle'dan veri çıkar
python3 scripts/analyze.py         # frekans analizi + açılış kelimeleri
python3 scripts/simulate.py        # ilk üç oyuncu simülasyonu
python3 scripts/entropy_bot.py     # entropy-greedy bot (gerçek skill tavanı)
python3 scripts/human_baseline.py  # vokabüler-K duyarlılığı
python3 scripts/difficulty.py      # zorluk + üç-tanım karşılaştırması + grafikler
```

Gereksinim: Python 3.10+, `numpy`, `matplotlib`.

### Üretilen veri dosyaları

| Dosya | İçerik |
|---|---|
| `data/solutions.json` | 11.470 günlük cevap (çoğaltılı) |
| `data/extras.json` | 5.531 ek sözlük |
| `data/letter_frequency.json` | Genel harf frekansı |
| `data/positional_frequency.json` | Pozisyonel harf frekansı |
| `data/opening_words.json` | En iyi açılış kelimeleri (frekans-skoru) |
| `data/simulation_results.json` | İlk üç oyuncu modelinin sonuçları |
| `data/entropy_bot_results.json` | Entropy-bot + per-kelime sonuç |
| `data/human_baseline_results.json` | K-duyarlılık (uniform) |
| `data/human_baseline_weighted.json` | K-duyarlılık (ağırlıklı) |
| `data/difficulty_per_word.json` | Her kelime için entropy-bot tur sayısı |
| `data/hardest_words.json` | En zor 50 kelime |
| `data/comparison_table.json` | Üç-tanım şans/beceri tablosu |
| `data/pattern_matrix_cand.npy` | Precomputed pattern matrisi (cache) |
| `data/figures/*.png` | Dört grafik |
