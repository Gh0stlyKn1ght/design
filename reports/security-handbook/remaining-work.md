# Remaining work and acceptance criteria

The four core security articles and five supporting passages have been updated. The lab has six passed runtime cases and one inconclusive case. The following work remains; the completed source revision should not be confused with a validated robot deployment.

| Priority | Open work | Evidence needed to close it |
| --- | --- | --- |
| 1 | Explain the independent-authority result. | Correlated discovery/handshake diagnostics showing where the untrusted peer is rejected, with a successful trusted control under the same settings. Zero delivered messages alone is insufficient. |
| 2 | Add a current robot case study. | A named mission, hardware, OS/ROS/RMW versions, topology, assets and trust boundaries; accountable owners, exposure/impact rationale and residual risk for each threat. The present example has no actuators. |
| 3 | Validate operational controls on that target. | Recorded tests for credential expiry, renewal, revocation and recovery; host/account access to keys; traffic protection; overload limits and recovery. Hardware-backed keys need their own integration test if selected. |
| 4 | Assess the actual release dependencies. | An inventory of the selected image and packages plus current vulnerability triage tied to its digest and versions. No SBOM or vulnerability scan was run in this revision. |
| 5 | Complete the publication checks. | A dated reconciliation of the six public research README checksum mismatches, a successful remote CI run and, after a publishing target is chosen, a deployed commit and PDF hash matching the approved revision. Local site/browser checks are complete; the current work has not been pushed or deployed. |
| 6 | Confirm the final reading experience. | Physical observation of the portrait and diagram proofs for orientation, clipping and readability. Two printer jobs completed; paper appearance remains unconfirmed. Tagged output is present, but PDF/UA and screen-reader conformance have not been assessed. |

Additional middleware/platform trials are conditional on the deployment choice: Lyrical, Cyclone DDS, Zenoh and cross-vendor combinations were not runtime-tested here. They should not delay the documented Jazzy/Fast DDS teaching exercise unless the project needs them.

Before publication, reconcile the public research writeup checksums without rewriting historical evidence. The next technical step is to close the independent-authority evidence gap. A real robot model and its bounded validation plan follow once the target platform and mission are known.
