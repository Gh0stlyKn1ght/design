# Libraries and technology choices

**Juan Carlos Nevarez · Gh0stlyKn1ght** · Reviewed October 20, 2026.

Use SROS 2 for DDS identity and permissions, a bounded XML checker for the example policy, and an editable threat register and architecture diagram. The choices below distinguish tools used in the lab from deployment options that need a target-system trial.

## Tools used in the lab and threat model

| Technology | Purpose and reason | Limit |
| --- | --- | --- |
| SROS 2 policy 0.2.0 | ROS-oriented privileges and a path to signed DDS permission artifacts. The offline example uses a pinned upstream schema and transform. | A valid policy and signed file still need actual middleware enforcement tests. |
| Python + lxml | Schema validation, the upstream XSLT, exact grant assertions and input-boundary checks. Schema resolution is local; DTDs and XInclude are rejected for this example. | The checker accepts this defined format, not arbitrary external XML/XSLT. |
| Graphviz DOT → SVG/PDF | Editable architecture source with explicit processes, assets and trust boundaries. | Diagram boundaries are design claims until their controls are verified. |
| JSON threat register and result template | Stable IDs, prerequisites, owners, evidence states and residual-risk notes, rendered into printable records. | No automatic risk score substitutes for a deployment-specific judgment. |

Primary documentation: [SROS 2](https://github.com/ros2/sros2), [lxml resolution and XSLT access control](https://lxml.de/resolvers.html), and [Graphviz SVG](https://graphviz.org/docs/outputs/svg/).

## Middleware and platform decisions

**For the included exercise:** use Jazzy on Ubuntu 24.04 with `rmw_fastrtps_cpp`. This keeps the commands and policy aligned with a reviewed official tutorial and the pinned Jazzy transformation. Capture installed package versions; do not infer package versions from the ROS distribution name. The isolated run recorded six passed ROS cases and one inconclusive separate-authority case; consult the runtime observations before relying on a particular claim.

**For a new long-lived robot:** evaluate Lyrical on Ubuntu 26.04 when its hardware/application dependencies are supported. Lyrical's official support horizon is May 2031; Jazzy remains listed through May 2029. The decision depends on drivers, vendor support, package availability, and a measured migration run. See the [official release table](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases.rst) and [Lyrical platform matrix](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases/lyrical/supported-platforms.rst).

**Fast DDS** is a suitable starting point for this DDS-focused lab. **Cyclone DDS** is a credible alternate implementation for a separately tested deployment; both document security plugins and signed governance/permissions. Neither is declared “more secure” here, and no performance benchmark was run. Choose based on supported packaging, required features, operational evidence and vendor support. The Jazzy tutorial does not support secure cross-vendor communication. Sources: [Fast DDS security](https://fast-dds.docs.eprosima.com/en/latest/fastdds/security/security.html), [Cyclone DDS security](https://cyclonedds.io/docs/cyclonedds/latest/security.html), and [Jazzy tutorial](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Introducing-ros2-security.rst).

**Zenoh** is an option when its routing/topology model fits the application. The current `zenoh_security_tools` can generate session configs using SROS 2 policy and keystore material. Its router/session settings and bridge boundaries need their own review; switching `RMW_IMPLEMENTATION` is not a complete migration of DDS security. Source: [official Zenoh security tools](https://github.com/ros2/rmw_zenoh/tree/rolling/zenoh_security_tools). This option is documented, not installed or validated in this package.

## Useful next-stage tools

- **OWASP Threat Dragon desktop:** useful when several people want a visual data-flow editor with threat/remediation records and local files. Keep the JSON register as a reviewable artifact and check export compatibility with old diagrams. It is optional; the authored DOT/SVG figure already works offline. [Threat Dragon documentation](https://www.threatdragon.com/docs/).
- **Syft + Grype:** useful for dependency inventory and vulnerability triage of a selected deployment image/filesystem. Record tool versions, artifact digest, database age and exceptions. An SBOM is not evidence that a vulnerability is exploitable; a clean scan does not prove safety. These tools were researched, not run. [Syft](https://github.com/anchore/syft), [Grype](https://github.com/anchore/grype).
- **Cosign:** useful when an actual release pipeline needs artifact-signature verification. Define the accepted signing identity/issuer or trusted key and verify the intended artifact digest. Keep this release-signing trust separate from DDS identities. No signing integration was configured. [Cosign verification](https://docs.sigstore.dev/cosign/verifying/verify/).

The most useful next investment is stronger instrumentation for the inconclusive separate-authority case, followed by a small current-robot case study. Introducing more tooling before those results would not strengthen the handbook's evidence.
