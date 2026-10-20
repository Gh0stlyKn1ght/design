---
layout: default
title: ROS 2 DDS-Security integration
permalink: articles/ros2_dds_security.html
abstract: DDS security properties, transport scope, enforced configuration, credentials, and a bounded SROS 2 lab.
author: '[Kyle Fazzari](https://github.com/kyrofa)

  '
date_written: 2019-07
last_modified: 2026-10
published: true
categories: Security
revision_date: '2026-10-20'
revision_author: '[Juan Carlos Nevarez · Gh0stlyKn1ght](https://github.com/Gh0stlyKn1ght)'
---

{:toc}

# {{ page.title }}

Original authors: {{ page.author }}

2026 revision, security review, and additional material: {{ page.revision_author }}

Originally written: {{ page.date_written }} · Revised: {{ page.revision_date }}

[Original article](security_history/180_ros2_dds_security.md.txt).

## Goal and prerequisites

Explain which threats DDS security can address, configure enforcement deliberately, and identify controls that belong to the operating system or application.
You should understand ROS nodes, topics, services, contexts, processes, and basic public-key certificates.
Use the [access-control chapter](ros2_access_control_policies.html) for authorization and the [enclaves chapter](ros2_security_enclaves.html) for credential placement.

**Practical question:** If a participant presents a trusted certificate, should it be allowed to publish an actuator command?
Authentication establishes an identity; permissions decide which operations it may perform, and the application still decides whether a permitted command is valid and safe.

## Scope and platform choice

This chapter describes **DDS-based ROS 2 middleware with DDS security support**.
ROS 2 is middleware running on an operating system; it does not replace host access control, patching, network policy, or an independent safety system.

Use one ROS distribution and one DDS implementation for the first exercise.
The accompanying lab targets **Ubuntu 24.04, ROS 2 Jazzy, and `rmw_fastrtps_cpp`**, with exact installed package versions captured by the operator.
This configuration was exercised in the isolated Ubuntu userspace described in the [runtime observations](../reports/security-handbook/runtime-observations.md): six ROS cases passed and the separate-authority case remained inconclusive.

For a new deployment, evaluate **Lyrical on Ubuntu 26.04** when hardware drivers and application packages support it.
The official release table lists Lyrical support through May 2031 and Jazzy through May 2029.
Crystal is end of life and belongs only in the historical case studies.
Do not mix distribution-specific installation instructions or assume an existing robot can be upgraded without vendor validation.
See the [official release table](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases.rst) and [Lyrical platform support](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases/lyrical/supported-platforms.rst).

`rmw_zenoh_cpp` has a different configuration and trust model.
Its security tooling can reuse SROS 2 policies and key material, but applies them through generated Zenoh session/router configurations.
DDS governance files and these environment variables are not a universal recipe for every RMW.
See the [Zenoh security tool documentation](https://github.com/ros2/rmw_zenoh/tree/rolling/zenoh_security_tools).

## DDS security properties

The DDS Security architecture defines authentication, access-control, cryptographic, logging, and data-tagging plugin interfaces.
The first three establish the main identity, authorization, and message-protection functions used here.
Audit logging availability and data-tagging behavior depend on the vendor and build; do not infer that a usable audit trail exists because encryption is enabled.

| Property | What it establishes | What remains outside it |
| --- | --- | --- |
| Authentication | A participant can demonstrate an identity trusted by the configured authority. | Whether the holder is uncompromised or its command is appropriate. |
| Access control | Signed governance and permissions authorize configured operations. | Host file access, process isolation, or command semantics. |
| Cryptographic protection | Configured DDS traffic can receive integrity/authenticity and confidentiality protection. | Data after decryption, all metadata, non-DDS links, or availability under overload. |
| Logging | Supported, configured security events can aid investigation. | Complete forensic evidence, retention policy, or tamper resistance by default. |

The builtin plugin names commonly used in DDS security are `DDS:Auth:PKI-DH`, `DDS:Access:Permissions`, and `DDS:Crypto:AES-GCM-GMAC`.
The access-control name is plural **Permissions**.
Use your vendor's documentation for supported algorithms, protection settings, and plugin-loading requirements; do not design a new cryptographic scheme for a tutorial.

The original design cited DDS Security 1.1.
[OMG now publishes version 1.2](https://www.omg.org/spec/DDS-SECURITY/1.2).
That does not prove a particular ROS package implements every 1.2 feature.
Record the standard basis supported by the actual middleware and avoid copying old section numbers into a new compatibility claim.

### Interoperability is a test obligation

The official Jazzy [security setup source](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Introducing-ros2-security.rst) says secure cross-vendor communication is not supported.
Keep the same vendor for this lab.
If a project requires a different combination, verify its support statement and test the exact versions, governance, permissions, discovery behavior, and recovery paths.
Using standard plugin names alone is not proof that the combination works.

## Governance, permissions, and identity

**Identity certificates** bind a participant's public key to a subject trusted by the identity authority.
**Governance** specifies domain/topic protection and admission behavior.
**Permissions** grant operations to a certificate subject for domains and topics during a validity interval.
Permissions need signing; editing XML without producing a matching signed permissions file does not update the runtime policy.

Review governance explicitly: unauthenticated-participant admission, join access control, discovery protection, metadata protection, and payload protection.
A participant joining a domain is not the same operation as publishing or subscribing to a particular topic.
Inspect generated governance and permissions rather than assuming a tool's example defaults meet your deployment requirements.

Neither the ROS node name, its namespace, nor `ROS_DOMAIN_ID` is an authenticated security identity.
A domain ID separates discovery domains by convention; it is not an access-control boundary.
An authorized process can still misuse the permissions granted to its identity.

## Configure enforcement deliberately

For a DDS RMW, set the environment in **every participating terminal or service**, and select an absolute enclave path separately:

```sh
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_SECURITY_KEYSTORE="$HOME/ros2-security-lab/keystore"
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/talker
```

`ROS_SECURITY_KEYSTORE` points to the **keystore root containing `enclaves/`**.
The expected runtime files normally include `cert.pem`, `key.pem`, `identity_ca.cert.pem`, `permissions_ca.cert.pem`, `governance.p7s`, and `permissions.p7s`.
The process needs read access only to its required material.

`ROS_SECURITY_ENABLE=true` enables the DDS security path; `ROS_SECURITY_STRATEGY=Enforce` requests failure when required security configuration cannot be established.
Without the deliberate enforcement setting, permissive fallback can permit unsecured startup when material is missing.
Treat a successful process launch as insufficient evidence: test authorized delivery and rejection separately.

`ROS_SECURITY_ENCLAVE_OVERRIDE` overrides the selected enclave path.
It does not replace the keystore root.
Remove an unexpected inherited override before a controlled exercise:

```sh
unset ROS_SECURITY_ENCLAVE_OVERRIDE
```

A CLI or daemon is another participant and needs an appropriate identity and policy.
Use a dedicated inspection identity in a deployed system; copying a production participant's keys into an administrator's shell enlarges its trust boundary.

## Credential lifecycle and host controls

Keep signing-authority private keys away from runtime robots.
An enclave private key is still a secret even though it is inside the `enclaves/` directory.
An SROS 2 enclave is a credential/policy grouping, not a hardware protected execution environment.

Define provisioning, expiry, renewal, compromise response, backup, policy signing, clock requirements, and recovery ownership.
For revocation or hardware-backed keys, obtain a vendor/version-specific implementation and test it.
Do not assume an online revocation service or hardware key integration is available in every DDS security stack.
Keep software-update signing separate from participant identity and permission signing.

Run services with separate OS identities where meaningful, restrict file access and capabilities, patch supported packages, and protect remote administration.
Middleware authentication does not stop a privileged local attacker from reading accessible keys or replacing an application binary.
A firewall, VPN, or container can add boundaries; none substitutes for a tested participant policy.

## Bounded exercise and evidence

Use the [included lab](https://github.com/Gh0stlyKn1ght/design/blob/gh-pages/examples/security-lab/README.md) on an isolated, non-actuating workstation.
It supplies a policy, an offline schema/transform check, a setup script that refuses to overwrite a keystore, and expected positive/negative cases.
The offline checks validate generated permission structure and scope; the ROS communication cases must be run on the selected ROS host.

Produce a version manifest, a diagram, the reviewed governance and signed permissions hashes, and observations for authorized delivery, a missing enclave, an untrusted identity, and a forbidden topic.
A silent listener alone is not evidence of authorization working; rule out networking, type, and QoS failures using the authorized control case and logs.

**Explain back:** Why can an authenticated participant be forbidden from publishing `/cmd_vel`? Why can a stolen authorized key still be dangerous when traffic is encrypted?

**Common misconceptions:** enabling security is not the same as enforcing a restrictive policy; encrypting a channel does not validate application commands; distinct node names do not isolate shared process memory.

**Limit:** the recorded software tests do not establish physical-robot safety, host isolation, revocation behavior, or packet-level confidentiality. The separate-authority result still needs stronger rejection evidence.
Next, define the exact publish/subscribe/service/action privileges in the access-control chapter.

## Sources

- [SROS 2 project](https://github.com/ros2/sros2), using distribution branches and pinned versions.
- [Fast DDS security](https://fast-dds.docs.eprosima.com/en/latest/fastdds/security/security.html).
- [Cyclone DDS security](https://cyclonedds.io/docs/cyclonedds/latest/security.html).
- [DDS Security 1.1](https://www.omg.org/spec/DDS-SECURITY/1.1) and [1.2](https://www.omg.org/spec/DDS-SECURITY/1.2).
