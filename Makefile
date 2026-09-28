# Makefile — Labor Market Intelligence
# Windows: dùng `python scripts/run_pipeline.py <step>` thay cho make.
# Linux/macOS: `make <target>`

PYTHON := python

.PHONY: help pilot crawl parse clean skills rules cluster classify figures all test manifest fixtures

help:
	@echo "Targets:"
	@echo "  pilot     Crawl thử 10 tin"
	@echo "  crawl     Crawl đầy đủ"
	@echo "  parse     Parse HTML → parquet"
	@echo "  clean     Dedup + chuẩn hóa lương"
	@echo "  skills    Trích kỹ năng → ma trận"
	@echo "  rules     Apriori association rules"
	@echo "  cluster   Hierarchical clustering"
	@echo "  classify  Decision tree (tùy chọn)"
	@echo "  figures   Xuất hình vẽ"
	@echo "  all       Chạy toàn bộ pipeline"
	@echo "  test      Chạy pytest"
	@echo "  manifest  Tạo SHA-256 manifest"
	@echo "  fixtures  Tạo lại fixture parquet"

pilot:
	$(PYTHON) scripts/run_pipeline.py pilot

crawl:
	$(PYTHON) scripts/run_pipeline.py crawl

parse:
	$(PYTHON) scripts/run_pipeline.py parse

clean:
	$(PYTHON) scripts/run_pipeline.py clean

skills:
	$(PYTHON) scripts/run_pipeline.py skills

rules:
	$(PYTHON) scripts/run_pipeline.py rules

cluster:
	$(PYTHON) scripts/run_pipeline.py cluster

classify:
	$(PYTHON) scripts/run_pipeline.py classify

figures:
	$(PYTHON) scripts/run_pipeline.py figures

all:
	$(PYTHON) scripts/run_pipeline.py all

test:
	$(PYTHON) -m pytest -v

manifest:
	$(PYTHON) scripts/make_manifest.py

fixtures:
	$(PYTHON) scripts/generate_fixtures.py
