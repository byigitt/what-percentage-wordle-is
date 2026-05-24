# Metodoloji Özeleştirisi

Bu dokümanda, ilk yaklaşımımın **neden eksik olduğunu** ve nasıl düzelttiğimi
açıklıyorum. Hem epistemik dürüstlük hem video için "yöntemi anlatma"
kısmında işine yarar.

---

## İlk yaklaşım ve verdiği cevap

İlk yaklaşımım üç oyuncu modeliydi:
- Saf rastgele (geri bildirim yok)
- Tutarlı rastgele (kurallı, strateji yok)
- Frekans-botu (kurallı + frekans skoru)

Ve sonucu:
> **~%97 şans, ~%3 beceri** (frekans-botu vs tutarlı rastgele tabanı).

Bu sayı **teknik olarak doğru** ama **yanıltıcı**. Üç sebep:

---

## Sorun 1 — Şans tabanı insanı overstate ediyor

"Tutarlı rastgele" modelim:
- 5.500 kelimelik tam Türkçe 5-harfli sözlüğü mükemmel hatırlıyor.
- Sarı/yeşil/gri geri bildirimini mükemmel takip ediyor.
- Çift harf kuralında hata yapmıyor.
- Tek "eksiği": strateji uygulamıyor (kalan adaylardan rastgele seçiyor).

Gerçek bir başlangıç seviyesi insan oyuncu bu modelin **hiçbirini** yapamaz:
- Tipik kullanıcı belki 800-1500 farklı 5-harfli kelime biliyor.
- Geri bildirim takibinde hata yapıyor (özellikle çift harfli kelimelerde).
- Açtığı kelimeleri hatırlamakta bile zorlanıyor.

Yani gerçek "şans tabanı" %96.97'den çok daha düşük olmalı.

### Düzeltme: vokabüler-kısıtlı insan modeli

K parametresiyle "bilinen kelime sayısı"nı sınırlayıp simüle ettim. La
listesindeki çoğaltı sayısını "yaygınlık skoru" olarak kullandım (bot
curator'ları zaten daha yaygın kelimeleri daha sık cevap olarak koymuş).

Sonuç:

| K | Kazanma (uniform) | Kazanma (ağırlıklı) |
|---:|---:|---:|
| 500 | %17 | %26 |
| **1000** | **%34** | **%47** |
| 1500 | %51 | %67 |
| 2000 | %67 | %84 |
| 2936 (full) | %97 | %97 |

Tipik insan (K≈1000) → **%34 (uniform) kazanma**. Bu, %97'lik baseline'ım
yerine kullanılması gereken sayı.

---

## Sorun 2 — Skill tavanını understate ediyor

Frekans skoru naif bir sezgisel. **Asıl** skill tavanı = entropy-greedy bot
(3Blue1Brown'un Wordle videosunda anlattığı yöntem). Her tur, her olası
tahmin için beklenen bilgi kazancını (Shannon entropisi) hesaplar ve en
yüksek olanı seçer.

### Düzeltme: entropy-bot

`scripts/entropy_bot.py` numpy ile vectorize edildi. Per-tahmin entropy:

```
H(g | C) = − Σ_p  P(p|g,C) · log₂ P(p|g,C)
```

Sonuç:

| Bot | Kazanma | Ort. tur | Açılış |
|---|---:|---:|---|
| Frekans | %99.18 | 3.77 | `salik` |
| Entropy | **%100** | **3.59** | `merak` |

Önemli detay: entropy-bot **HIÇ kaybetmiyor**. Yani gerçek skill tavanı =
%100, "irreducible bad luck" = %0 (bu cevap havuzunda).

Bu, "skill" payımızı yükseltiyor: tavan %99.18 değil %100.

---

## Sorun 3 — Şans/beceri tanımı tek değil

"Şans payı = X-tabanı kazanımı / Y-tavanı kazanımı" formülünde X ve Y
seçimi sonucu dramatik biçimde değiştiriyor:

| Şans tabanı | Şans payı | Beceri payı |
|---|---:|---:|
| Saf rastgele | %0.1 | %99.9 |
| İnsan K=500 | %17 | %83 |
| İnsan K=1000 | %34 | %66 |
| İnsan K=2000 | %67 | %33 |
| Tutarlı rastgele | %97 | %3 |

Aralık: **%3'ten %99'a** — sadece taban seçimine bağlı.

### Düzeltme: tek sayı yerine spektrum

Tek bir "%X şans" demek yerine **bu tabloyu** sunmak doğru yaklaşım. Soruyu
soran kişinin neyi "şans" saydığına göre cevap değişiyor.

Eğer **tek bir sayı** vermek gerekiyorsa, gerçekçi insan (K=1000) tabanı:
**~%34 şans, ~%66 beceri.**

---

## Yeni keşif: "Beceri" iki şey

Vokabüler-K eğrisini analiz ederken net bir desen ortaya çıktı:

```
P(kazan | K) ≈ vokabüler_kapsama(K) × 0.97
```

Yani kazanma oranı neredeyse tamamen "kelimeyi tanıyor musun?" sorusuyla
belirleniyor. Tanıyorsan ~%97 kazanıyorsun (consistent random); tanımıyorsan
~%0.

Bu, "beceri"yi iki bileşene ayırır:

1. **Vokabüler bilgisi** — Türkçe 5-harfli kelime stoku.
2. **Strateji** — frekans/entropy mantığı, açılış kelimesi seçimi.

Vokabüler katkısı: K = 1000 → K = 2936 atlaması = %47 → %97 = **%50 puan**.
Strateji katkısı: K = 2936 (strateji yok) → entropy-bot = %97 → %100 = **%3 puan**.

Yani **"oyunu iyi bilmek"in %95'i vokabüler, %5'i strateji**. Bu, ilk
yaklaşımın hiç gösteremediği bir içgörüydü.

---

## Hâlâ olmayan şeyler (gelecek iyileştirmeler)

1. **Çift harf hatası modeli.** İnsanın çift harfli kelimelerde (örn.
   `anane`, `kakao`) sarı/yeşil mantığını karıştırma olasılığı.
2. **Açılış kelimesinin önceden ezberlenmesi.** Gerçek insanlar tek bir
   sabit açılış kullanır (örn. `KALEM`). Strateji avantajını biraz daha
   düşürür.
3. **Variance ayrıştırması (ANOVA).** Şans/beceri'yi varyans bileşenleri
   olarak ölçmek (skill-explained variance vs irreducible variance). Şu anki
   yaklaşım "outcome counterfactual"; ANOVA "outcome variance" olur.
4. **Türkçe corpus'tan gerçek frekans.** La çoğaltı sayısını proxy olarak
   kullandık; TS Corpus gibi gerçek bir Türkçe corpus daha sağlıklı vokabüler
   modeli verirdi.
5. **Hard mode simulation.** Wordle'ın "hard mode" varyasyonu strateji
   alanını daraltır; bu da skill katkısını farklı bir biçimde değerlendirir.

Bunların hepsi yapılabilir ama mevcut sonucun **doğru hikâyesini** değiştirme
ihtimali düşük: kazanma çoğunlukla vokabülere bağlı, strateji küçük ama
sürekli bir avantaj.
