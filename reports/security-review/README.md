# ROS 2 security review package

Prepared for **Juan Carlos Nevarez · Gh0stlyKn1ght** · [@Gh0stlyKn1ght](https://github.com/Gh0stlyKn1ght) · October 20, 2026.

**Current technical revision:** see [the updated handbook](../security-handbook/security-handbook.pdf). This folder preserves the earlier review and historical extraction.

For the original review, start with `security-review-report.pdf` (8 pages). It inventories the security material, distinguishes factual errors from historical assumptions, proposes additions, and gives a phased revision plan.

`security-reference-reader.pdf` contains all four dedicated security articles and supporting passages. It preserves the historical technical content and original author credits. Three wide matrices become 125 vertical threat records. Four malformed MARA rows are explicitly flagged and retained in source order; no column alignment is guessed. `security-figure-atlas.pdf` contains a cover and all 15 original figures on separate landscape pages.

Print the report and reader on **US Letter, portrait, actual size (100%)**. Print the atlas as a separate **US Letter, landscape** job. Use long-edge duplex for portrait; check the driver's short-edge duplex preview for landscape. Low-resolution original diagrams need redrawing for the revised handbook.

Editable sources: `report.md`, `inventory.md`, and `inventory.json`. The HTML companions embed the figures and work offline. PDF bookmarks and source links support navigation. The source revision and original license notices are retained in the reader. Publication state is tracked with the revised handbook; this folder preserves the historical extraction inputs and review.

Rebuild from the repository root with Python 3:

```sh
python -m venv /tmp/ros2-security-print-env
/tmp/ros2-security-print-env/bin/pip install -r tools/security-review/requirements.txt
/tmp/ros2-security-print-env/bin/python tools/security-review/build.py
/tmp/ros2-security-print-env/bin/python tools/security-review/verify.py
```

WeasyPrint requires its platform text/font libraries; verification uses Poppler's `pdfinfo`, `pdftotext`, and `pdffonts`. The build runs offline against the local checkout. The upstream comparison and modernization research were performed during the review; rebuilding does not repeat that online research. `build-manifest.json` records dependencies, record counts, original source table defects, image dimensions and layout checks. `verification.json` records PDF checks and their limits. The source snapshot is fixed to the revision named in the report; use a new review date and revision when updating the source baseline.

Validation covers page geometry, embedded fonts, extracted record IDs and symbols, original table-cell preservation, source hashes, template resolution, and rendered overflow. Representative rendered pages were also inspected. Physical printing and ROS runtime security behavior have not been verified. This historical package does not contain the subsequent technical revision; the updated handbook and lab are in `reports/security-handbook` and `examples/security-lab`.
