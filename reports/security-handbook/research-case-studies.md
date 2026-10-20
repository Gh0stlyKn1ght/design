# Published middleware case studies

**Research: Juan Carlos Nevarez · [@Gh0stlyKn1ght](https://github.com/Gh0stlyKn1ght)**  
ROS2X Research · NEONSHELL Security Research Group.

## Goal and prerequisites

Use an affected-versus-fixed comparison to connect a threat to a specific implementation, control and observed result. You should understand DDS identities, permissions and the difference between DDS middleware and a ROS application.

These case studies summarize the author's published research at [ROS2XRESEARCH revision 30ce3dd](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/tree/30ce3dd0eb22b384f010e5f9679e459517be6965). They are separate, earlier experiments; they were not rerun for this handbook. The tested version pairs describe those experiments, rather than a complete list of affected or currently supported releases. None establishes exposure of the handbook's Jazzy/Fast DDS baseline or a physical robot.

## Why a signed policy still needs enforcement tests

In [CVE-2019-15136](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2019-15136/README.md), the publisher held real CA-signed permissions that denied a DDS partition. The researcher bypassed that publisher's own local self-check to represent a peer that would not obey its restrictions. The receiving subscriber used an unmodified defender build throughout.

The affected Fast DDS 2.0.3 defender accepted the peer and received ten of ten messages. Fast DDS 2.1.0 rejected the same peer through its remote-writer permission check and received zero messages. Honest-publisher controls delivered ten of ten on both versions.

The important boundary is the defender's independent authorization of a remote writer. A remote program cannot be trusted to enforce its own restrictions. This illustrates the concern behind TM-002, while remaining a distinct DDS partition test: the handbook's topic-policy exercise does not reproduce this CVE. The reverse remote-reader direction was not separately tested, and no ROS graph or robot was involved.

## Why a working secure data path does not finish availability testing

In [CVE-2023-50257](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2023-50257/README.md), DDS Security-enabled example endpoints first established a working match. A forged participant-disposal message then broke that match on Fast DDS 2.6.6. The affected condition delivered none of five post-condition messages during the 150-second observation window. On 2.6.7, the same condition left the match working and all five were delivered. Both no-forgery controls also delivered all five.

This result concerns RTPS control-plane handling and bounded recovery observation. It does not establish an unlimited outage, a universal DDS Security bypass, or robot impact. The experiment used diagnostic logging changes without changing the tested security/control flow. No detector was evaluated.

The lesson is to include discovery and lifecycle/control messages in the threat model, alongside protected application data. Endpoint matching, post-condition delivery and recovery time are separate observations.

## Six published comparisons

| Case | Tested Fast DDS pair | Recorded result | Interpretation limit |
| --- | --- | --- | --- |
| [CVE-2019-15136](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2019-15136/README.md) | 2.0.3 / 2.1.0 | Unauthorized remote partition match on the affected defender; explicit rejection on the fixed defender. | Modified peer self-check; unmodified defender. One direction tested. |
| [CVE-2023-39948](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2023-39948/README.md) | 2.6.4 / 2.6.5 | A malformed CDR encapsulation caused an uncaught exception on the affected endpoint; the fixed endpoint rejected the input safely. | Dynamic-type DDS path. The record preserves an unresolved exact exit-signal discrepancy. |
| [CVE-2023-50257](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2023-50257/README.md) | 2.6.6 / 2.6.7 | Forged disposal disrupted the affected match; the fixed pair kept delivering. | One direction and a bounded 150-second recovery window. |
| [CVE-2024-28231](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2024-28231/README.md) | 2.6.7 / 2.6.8 | RTPS DATA payload-size handling produced an AddressSanitizer-confirmed heap overflow on the affected version; the fixed comparison was unaffected. | Parser/crash evidence; no code execution or robot consequence demonstrated. |
| [CVE-2025-62799](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2025-62799/README.md) | 3.4.0 / 3.4.1 | Fragment reassembly produced an AddressSanitizer-confirmed heap overflow on the affected version; the fixed comparison was unaffected. | One construction and release pair; no further exploitation or detector evaluated. |
| [CVE-2026-45097](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/cases/CVE-2026-45097/README.md) | 3.6.1 / 3.6.2 | The affected deserializer exhausted a 256 MiB limit; the fixed implementation bounded allocation and completed. | Standalone in-process harness with no participant, ROS node or network. Remote reachability was not tested. |

The parser/resource examples extend the questions behind TM-005: identify where input is parsed, which resource limits apply, and what a process failure would mean for the actual application. They do not establish that an authenticated publisher was required for every trigger.

## Evidence-reading exercise

Choose one linked public case and read its claim, result table, interpretation boundary and redaction record. For one affected run and its fixed comparison, identify the control, exact version, measured effect and observation window. Separate the sender's action from evidence of the receiver's behavior.

**Artifact:** a short claim/evidence table with the source revision, relevant log or sanitizer report, tested boundary, comparison result and one unresolved deployment question. This is a document-analysis exercise; it does not require running the reproduction tools.

**Explain back:** Why is a trusted certificate insufficient evidence that every remote permission was enforced? Why does a middleware crash fail to establish physical robot impact? Why does the no-network allocation harness leave remote reachability unresolved?

Next, apply the same claim/evidence distinction to the included talker/listener lab. Resolve its inconclusive independent-authority case using its own controls and diagnostics; these earlier CVE results do not close that gap.

## Sources and attribution

Adapted and condensed from Juan Carlos Nevarez's published [ROS2X Research case studies](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/tree/30ce3dd0eb22b384f010e5f9679e459517be6965/cases) and [methodology](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/METHODOLOGY.md). The summaries reorganize the research for teaching and omit reproduction commands and packet-construction details. Copyright © 2026 Juan Carlos Nevarez. This chapter and its source research writeups are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); harness code is separately Apache-2.0. Original ROS design chapters retain their own attribution and license context. See the research repository's [licensing matrix](https://github.com/Gh0stlyKn1ght/ROS2XRESEARCH/blob/30ce3dd0eb22b384f010e5f9679e459517be6965/LICENSING.md).
