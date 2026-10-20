# October 2026 security revision

**Juan Carlos Nevarez · Gh0stlyKn1ght** · github.com/Gh0stlyKn1ght

This edition **changes the four security article sources**. It is a technical revision beyond the earlier extraction/report. Original author credits and exact historical sources remain available. The updated handbook is the current reading path; the earlier 139-page reader remains a historical reference.

| Review finding | Change made | Remaining validation |
| --- | --- | --- |
| F01 · Keystore path | Corrected to the root containing `enclaves/`; startup and missing-path cases observed. | Repeat on the target deployment. |
| F02 · STRIDE error | Corrected Information Disclosure and added an evidence-aware method. | Model review against an actual mission. |
| F03 · Interoperability promise | Replaced with distribution/vendor scope and tested-combination requirements. | A separately recorded trial for each required combination. |
| F04 · Ambiguous SROS enabled field | Current records name prerequisites, controls, evidence and residual risk. | Runtime observations; historical table legend stays archived. |
| F05 · Mixed identity/hardware/signing roles | Separated DDS credentials, host/process boundaries, hardware protection and update signing. | Platform-specific key loading, recovery and revocation tests. |
| F06 · Crystal baseline | Current non-actuating Jazzy/DDS exercise; separate Lyrical platform decision. Historical robot models archived. | Target hardware and package compatibility. |
| F07 · DDS standard | Added 1.2 reference while retaining the distinction from actual implementation support. | Vendor-specific feature/standard matrix. |
| F08 · Transport scope | DDS-specific recipe labeled; Zenoh configuration and bridges discussed separately. | Zenoh/bridge deployment tests if selected. |
| F09 · Scores/evidence | Added 8 structured threat records with owners, prerequisites and residual risk. Old DREAD/RVSS scores remain historical. | Deployment-specific likelihood/impact and accountable owners. |
| F10 · Proposed claims | Added explicit evidence states, runtime logs and result templates. Six ROS cases passed. | Separate-authority rejection evidence remains inconclusive. |
| Print layout | New editable vector figure and portrait updated handbook. | Physical printer proof remains absent. |

Additional material includes a full lab recipe, restrictive policy, offline schema/XSLT generation and semantic grant checks, eight boundary tests, non-overwriting provisioning script, version capture, and technology recommendations. All five supporting articles now clarify the relevant security boundary: enclave commands, participant mapping, action names, the historical DDS overview, and the network-flow API discussion.

The follow-up repaired the served OAuth surface, pinned the Jekyll build, corrected the fork URL/base path, and checked the site in Chromium. A manual Pages workflow is prepared; publication is separately tracked. This does not imply a current CVE audit, robot deployment or hardware assessment.
