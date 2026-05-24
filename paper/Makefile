# IEEE makalesini derle (tectonic kullanir, paketleri otomatik indirir).
#
# Gereksinim:
#   - tectonic   (brew install tectonic)
#   - data/figures/*.png mevcut olmali (../scripts/difficulty.py uretir)

PDF := wordle-turkish.pdf
TEX := wordle-turkish.tex
FIGS := figures/turn_breakdown.png figures/skill_decomposition.png \
        figures/k_vs_winrate.png figures/difficulty_hist.png

.PHONY: all clean figures view

all: $(PDF)

$(PDF): $(TEX) $(FIGS)
	tectonic $(TEX)

figures: $(FIGS)

# Ingilizce etiketli paper figurleri plot_english.py tarafindan uretilir.
# (Turkce versiyonlar data/figures/ altinda kalir, docs/ icin.)
figures/%.png: ../scripts/plot_english.py
	@mkdir -p figures
	cd .. && python3 scripts/plot_english.py

view: $(PDF)
	open $(PDF)

clean:
	rm -f *.aux *.log *.out *.bbl *.blg *.toc *.synctex.gz preview-*.png

distclean: clean
	rm -f $(PDF)
