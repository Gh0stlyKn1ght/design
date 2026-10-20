# Revised ROS 2 security handbook

**Juan Carlos Nevarez · Gh0stlyKn1ght** · [@Gh0stlyKn1ght](https://github.com/Gh0stlyKn1ght) · October 20, 2026.

**Start with [security-handbook.pdf](security-handbook.pdf).** This is the revised technical material, not the earlier review or historical extraction. It contains the four rewritten security chapters, eight full threat records, technology decisions, a complete non-actuating lab, recorded software lab results, the example policy and attribution. [update-summary.pdf](update-summary.pdf) provides the revision and technology review plus the prioritized remaining work. Website, publishing and printer status stay in this README and [runtime-observations.md](runtime-observations.md). [trust-boundaries-landscape.pdf](trust-boundaries-landscape.pdf) is a separate one-page diagram sheet.

Print the handbook and summary on **US Letter, portrait, actual size (100%)**. Print the diagram sheet separately in **US Letter, landscape**. The HTML versions work offline with embedded vector assets. The PDFs include bookmarks, text and embedded fonts, and are tagged; no PDF/UA conformance claim is made.

The original four article versions are preserved byte for byte in `articles/security_history`. The earlier 139-page reader and 16-page raster figure atlas remain in `reports/security-review`, whose build now reads its fixed historical Git revision. The current articles retain their public permalinks and original authors. All five supporting articles have security-boundary clarifications. See [changes.md](changes.md) for issue-by-issue status.

## Rebuild and verify

From the repository root:

```sh
python -m venv /tmp/ros2-security-handbook-env
/tmp/ros2-security-handbook-env/bin/pip install -r tools/security-handbook/requirements.txt
/tmp/ros2-security-handbook-env/bin/python tools/security-handbook/build.py
/tmp/ros2-security-handbook-env/bin/python tools/security-handbook/verify.py
```

Graphviz `dot` and Poppler's `pdfinfo`, `pdftotext`, and `pdffonts` must be installed. WeasyPrint needs its platform font/text libraries. The build uses local inputs and pinned vendored XML tooling; it does not run ROS or refresh online research. `source-review.json` records the primary references and repository snapshots reviewed for this edition. Runtime setup and result recording are in `examples/security-lab/README.md`.

The builder records input hashes and tool versions in `build-manifest.json`. The verifier checks all PDF page sizes, font embedding, text/template integrity, internal links, source hashes, archive fidelity and eight policy-boundary tests. Rendered pages were inspected separately. `verification.json` records checks and limits.

## Evidence and remaining work

Completed: technical source rewrite; XML/schema/transform and exact privilege checks; eight input-boundary tests; vector diagrams; PDF checks; Jekyll build and Chromium checks; and a recorded software runtime run with six passes and one inconclusive separate-authority case. The generated permissions example is unsigned and uses an illustrative validity interval, not a deployed certificate policy.

Still unverified: the explicit rejection mechanism in the separate-authority case; host key-access boundaries; revocation/recovery behavior; any physical robot; and the paper appearance of two completed printer jobs. ROS ran in an isolated Ubuntu userspace, not in the host Kali OS. Publication remains separately tracked. See runtime-observations.md and runtime-evidence/ for the actual evidence.


## Site validation

Build with `python tools/site/build.py` after `bundle install`, then run `python tools/site/verify.py`. The wrapper copies historical sources as static downloads after Jekyll so their original front matter cannot override the revised pages. Browser checks use `tools/site/verify_browser.py` and the separately pinned `tools/site/requirements-browser.txt`.

The `verify.yml` workflow checks the committed handbook, historical reader and site. The manual `pages.yml` workflow can publish the verified fork when GitHub Pages is enabled. No upstream custom domain is claimed. Publication must be checked using the deployed `site-build.json` source commit and PDF hash.

## PDF production tools

Production instructions are kept here rather than in the reading material. Markdown and WeasyPrint 69.0 provide paged CSS, bookmarks, tagged output and embedded fonts. Poppler checks page geometry, extracted text and font embedding. These checks do not establish PDF/UA compliance or physical printing correctness. See the [WeasyPrint PDF documentation](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html#pdf) for its supported export options.

The handbook omits the maintenance change log, website status and printer-job history. Its software evidence chapter is [runtime-lab-results.md](runtime-lab-results.md); the complete execution and production record remains [runtime-observations.md](runtime-observations.md). Print settings appear above. [remaining-work.md](remaining-work.md) records the open work and the evidence needed to close it.
