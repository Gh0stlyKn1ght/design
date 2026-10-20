---
layout: default
title: ROS 2 Access Control Policies
permalink: articles/ros2_access_control_policies.html
abstract: Least privilege, policy-to-DDS transformation, schema validation, and an auditable SROS 2 policy example.
author: '[Ruffin White](https://github.com/ruffsl), [Kyle Fazzari](https://github.com/kyrofa)

  '
date_written: 2019-08
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

> **Edition notice:** This is the October 2026 fork revision. It updates the technical guidance and preserves the original author credits. The [original article source](security_history/181_ros2_access_control_policies.md.txt) and the [historical print reader](../reports/security-review/security-reference-reader.pdf) remain available for comparison. Documentation and offline checks do not establish runtime security.

## Goal and prerequisites

Turn a data-flow requirement into a reviewable policy and explain the difference between structural validation and runtime enforcement.
Read the [DDS security chapter](ros2_dds_security.html) first.
You need basic XML knowledge and familiarity with ROS topics, services, actions, namespaces, and remapping.

**Practical question:** Can a listener identity also publish the data it is meant to read?
Our example grants subscription to the application topic only; it separately grants the infrastructure operations needed by the chosen nodes.

## Access-control model

Apply least privilege to the actual authenticated principal, which in a DDS deployment is associated with a participant and its enclave material.
A ROS node name is useful for policy authoring but is not, by itself, a cryptographic principal.
Nodes sharing a context share its participant identity and effective permissions; processes sharing memory cannot be treated as mutually isolated merely because policy profiles differ.

A mandatory policy is enforced outside the application's discretionary choices, but a compromised enforcement process or privileged host can still defeat the assumed boundary.
Document which system component is trusted to enforce each rule.

Separate these representations:

1. **Requirements:** intended data flows and operations, including denied flows.
2. **SROS 2 policy:** named enclaves and ROS-oriented profiles.
3. **DDS permissions:** generated transport names, certificate subject, domains, and validity.
4. **Signed runtime material:** permissions and governance accepted by the middleware.
5. **Evidence:** actual authorized and rejected behavior on the recorded implementation.

A schema-valid policy can still be too broad, mapped incorrectly, expired, signed by the wrong authority, or deployed to the wrong process.

## Policy format and version

The included example uses SROS 2 policy **0.2.0**.
It is checked against the pinned Jazzy schema in [the offline vendor bundle](https://github.com/Gh0stlyKn1ght/design/blob/gh-pages/examples/security-lab/vendor/sources.json).
The XML below is intentionally small; the runnable lab policy additionally accounts for logging, parameter infrastructure, and time-related behavior used by the example nodes.
Do not deploy this abbreviated fragment as a complete node policy.

```xml
<policy version="0.2.0">
  <enclaves>
    <enclave path="/security_lab/talker">
      <profiles>
        <profile ns="/" node="talker">
          <topics publish="ALLOW">
            <topic>/chatter</topic>
          </topics>
        </profile>
      </profiles>
    </enclave>
    <enclave path="/security_lab/listener">
      <profiles>
        <profile ns="/" node="listener">
          <topics subscribe="ALLOW">
            <topic>/chatter</topic>
          </topics>
        </profile>
      </profiles>
    </enclave>
  </enclaves>
</policy>
```

An `enclave` selects credential scope; a `profile` describes a node name and namespace for expressing resource names.
A profile does not create an OS sandbox.
The `topics`, `services`, and `actions` elements specify direction-specific operations.
Confirm the exact schema and transformations shipped with the chosen SROS 2 package before adopting an example from another distribution.

### Direction and generated resources

| Requirement | Policy operation | Review question |
| --- | --- | --- |
| Publish or read data | `publish` / `subscribe` | Can this principal also write a topic it should only read? |
| Call or provide a service | `request` / `reply` | Are both request and response transport directions correct? |
| Use or provide an action | `call` / `execute` | Are goal, result, cancellation, feedback and status covered? |

A ROS service or action expands into more than one DDS resource.
Review the generated permissions as well as the friendly policy.
Changing the selected RMW, namespace, node name, or a remapped topic can change those resources.

Prefer explicit names for the first lab.
A wildcard is a deliberate grant over a set of names, including future matching names; record why that set is acceptable.
Do not grant every resource under a prefix merely to eliminate startup errors.

## XML and tooling trust boundary

The original design describes XInclude and XSLT composition.
These features can read additional resources, so accept policies and transforms only from reviewed sources.
This edition's example has **no XInclude** and no DTD/entity declarations.
The offline checker rejects those constructs, restricts schema resolution to an explicit local file, disables network resolution, and denies transform file/network access.

The pinned `lxml`-based check validates both the policy and generated DDS XML.
It also checks actual topic direction, default denial, certificate subjects, domain scope, and absence of unrelated application resources.
This is a useful local check, not a replacement DDS authorization engine or a generic validator for arbitrary externally supplied policy bundles.

## Generate and inspect permissions

On the selected ROS host, the lab uses `ros2 security create_keystore`, `create_enclave`, and `create_permission`.
The setup script applies the reviewed policy to each enclave rather than leaving the broadly useful demo permissions in place.
Use the installed command's help for supported options and verify generated validity dates.
The offline reference transform's default dates are not an operational certificate-rotation policy.

Before running a participant:

- Check the certificate subject matches the permission grant.
- Check the domain includes the intended lab domain and no unintended domains.
- Inspect allow and deny rules, especially wildcard expressions and infrastructure topics.
- Inspect governance admission and protection settings.
- Verify signatures and time validity with the chosen tools.
- Ensure the signed file actually deployed is the one reviewed.

The [official access-control tutorial](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Access-Controls.rst) demonstrates policy signing and remap rejection.
Keep signing keys on the provisioning system; the robot ordinarily needs runtime artifacts rather than authority private keys.

## Policy changes and composition

Regenerate and sign permissions after a relevant name or privilege change.
A different enclave path does not automatically make a profile's topic names match a new namespace.
Record the effective namespace and remappings from launch configuration.
If components share an enclave, review the union of their permissions as the actual attack surface.

Treat a policy inferred from a running graph as a starting observation.
It can miss rarely used service calls, startup paths, faults, and dynamic operations, and can learn unnecessary or malicious behavior already present in the observed system.
Review it against intended behavior and explicit negative requirements.

## Exercise, misconceptions, and next step

Run the offline checker in the lab directory.
Inspect the generated listener grant and identify which topics it can publish for infrastructure and which application topic it can only read.
Then, on a ROS host, compare authorized `/chatter` delivery with a remap to `/not_chatter` using the same restricted identity.
Record initialization rejection or forbidden endpoint behavior as observed; do not invent a uniform error message across vendors.

**Artifact:** reviewed policy, generated permissions, version manifest, and a result table with logs.

**Explain back:** Why does “valid XML” not imply least privilege? Which permissions would two components effectively have after sharing one enclave?

**Misconceptions:** authorization is not achieved by encryption alone; node names are not protected principals; default denial does not make a broad allow rule narrow; a domain ID is not a firewall.

**Limit:** offline checks and the recorded Jazzy/Fast DDS run establish the specific observed grant/startup behavior. The separate-authority rejection mechanism remains inconclusive; other deployments need their own run.
Next, choose enclave and process boundaries before applying this policy to a robot.

## Sources and schema

- [Pinned SROS 2 policy schema](https://github.com/ros2/sros2/blob/80a08ffa1bccd2de602c2acd120b209ad5f8ce83/sros2/sros2/policy/schemas/policy.xsd).
- [Pinned permission transform](https://github.com/ros2/sros2/blob/80a08ffa1bccd2de602c2acd120b209ad5f8ce83/sros2/sros2/policy/templates/dds/permissions.xsl).
- [lxml document resolution and XSLT access controls](https://lxml.de/resolvers.html).
- [Original schema retained in this repository](ros2_access_control_policies/policy.xsd); historical reference only, not a promise about every installed distribution.
