---
layout: default
title: ROS 2 Security Enclaves
permalink: articles/ros2_security_enclaves.html
abstract: Enclave identity, context/process boundaries, correct keystore layout, and deployment of runtime credentials.
author: '[Ruffin White](https://github.com/ruffsl), [Mikael Arguedas](https://github.com/mikaelarguedas)

  '
date_written: 2020-05
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

[Original article](security_history/182_ros2_security_enclaves.md.txt).

## Goal and prerequisites

Choose an enclave scope that reflects a real trust boundary and deploy its runtime artifacts without distributing authority private keys.
Read the [DDS security](ros2_dds_security.html) and [access-control](ros2_access_control_policies.html) chapters first.

**Practical question:** Do two different enclave paths inside one process isolate a trusted actuator component from untrusted code?
They do not create a memory boundary.
If one component can read another's memory or credentials, distinct participant identities cannot repair that shared-process trust assumption.

## Names, contexts, participants, and processes

| Term | Role | Security implication |
| --- | --- | --- |
| Node name / namespace | Names ROS graph resources. | Useful for organization; not an authenticated identity. |
| Context | ROS client-library execution scope. | In the DDS mapping discussed here, associated with a participant and its credentials. |
| DDS participant | Middleware communication entity. | Uses an identity and effective permissions. |
| SROS 2 enclave | Path-selected set of security artifacts and policy scope. | Credential grouping; not a hardware enclave or OS sandbox. |
| OS process / account | Host execution and access-control boundary. | Governs shared memory and who can read files or inspect another process. |

A process can contain multiple nodes and contexts.
Describe the actual mapping for the selected RMW/version instead of assuming “one node, one certificate” or “one process always means one context.”
All nodes using the same participant identity receive that identity's effective permission set.
Shared OS privileges and shared memory can be an even wider boundary.

## Keystore root and artifact layout

Set `ROS_SECURITY_KEYSTORE` to the root **containing** `enclaves`, not to the `enclaves` directory itself.
The latter instruction in the original article was incorrect.
A representative provisioning layout is:

```text
keystore/
  public/                 # authority certificates
  private/                # authority signing keys; provisioning only
  enclaves/
    security_lab/
      talker/
        cert.pem
        key.pem            # this identity's private key
        identity_ca.cert.pem
        permissions_ca.cert.pem
        governance.p7s
        permissions.p7s
      listener/
        ...
```

Public authority certificates establish trust; they are not secret signing keys.
The `private/` authority directory stays off the runtime robot.
The runtime enclave's `key.pem` is also private material and needs restrictive access.
Do not mistake the directory name `enclaves` for permission to distribute its entire contents.

A runtime deployment may contain a reduced keystore tree with only the required enclave path and certificates.
If generated artifacts contain symlinks to `public/`, preserve the required target certificates or materialize the required copies.
Check file readability as the actual service account before starting the process.
Copying a broken symlink is not a successful credential deployment.

## Select an enclave explicitly

```sh
export ROS_SECURITY_KEYSTORE="$HOME/ros2-security-lab/keystore"
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
unset ROS_SECURITY_ENCLAVE_OVERRIDE
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/talker
```

The path `/security_lab/talker` identifies the enclave within the keystore.
It does not automatically change the ROS namespace or make the executable's node name an authenticated identity.
`ROS_SECURITY_ENCLAVE_OVERRIDE` can override the selected path and should be tracked in service/launch configuration.

### Launch configuration

Use explicit enclave arguments in a reviewed launch file, for example:

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            arguments=['--ros-args', '--enclave', '/security_lab/talker'],
            output='screen',
        ),
    ])
```

The surrounding service or environment supplies the keystore root, enable flag, enforcement strategy, and selected RMW.
The snippet is illustrative and has not been executed here.
Avoid hidden enclave overrides in included launch files.
The original proposals for automatically pushing relative enclave paths with namespaces are design history, not behavior this edition promises is implemented.

## Choose the smallest practical trust scope

Start with separate processes and enclave material for components with different trust or command authority.
Use separate OS identities and restrictive key-file permissions where the host design supports them.
A policy can describe a union of privileges for deliberately composed nodes, but it should not conceal that union.

Per-robot or per-fleet identities can simplify provisioning and also enlarge the impact of key theft.
A shared identity reduces attribution and complicates replacement of one compromised robot.
Record the operational tradeoff rather than treating a larger enclave scope as a free simplification.

Containers share a host kernel unless stronger isolation is deliberately supplied.
Host mounts, shared IPC, excessive capabilities, and shared credentials can cross the boundary the diagram appears to draw.
A container name or a separate enclave directory is not evidence of isolation.

Hardware roots of trust and trusted execution environments are additional platform capabilities.
Verify compatibility with the middleware's key-loading interface, provisioning workflow, and recovery design before claiming keys cannot be extracted.
A TPM cannot by itself make a compromised authorized application safe.

## Credential operations checklist

| Operation | Required decision or artifact |
| --- | --- |
| Provision | Identity owner, enclave path, subject, permissions, authority certificates. |
| Deploy | Required runtime files only, resolved symlinks, actual service account and file access. |
| Renew | Certificate/permission validity, clock source, rollout and rollback sequence. |
| Compromise | Isolate participant, replace credentials/policy, assess exposed keys and affected robots. |
| Recover | Restore trusted software and verify denied/authorized behavior before reconnecting. |
| Audit | Retained hashes, versions, issuance/change records and sanitized logs. |

Revocation behavior is implementation dependent.
Test how a peer handles changed permissions and revoked or expired material, including already-established sessions and restarts.
Document what must happen to remove access; do not promise immediate revocation from a paper policy alone.

## Exercise and explain-back

Draw the node → context → participant → enclave → process/account mapping for two components.
List the files each account can read and the union of operations each identity can perform.
Then add a third-party plugin to one process and redraw the trust boundary.

**Artifact:** mapping diagram, deployment file list, key-access review, and renewal/recovery procedure.

**Explain back:** Why is `key.pem` secret even after removing `private/`? Why does an absolute enclave path not select a ROS namespace? When would two processes still share an unsafe credential boundary?

**Misconceptions:** SROS 2 enclaves are not hardware enclaves; public certificate files are not signing authority keys; separate paths do not create separate process memory.

**Limit:** this is a reviewed design exercise, not proof of host isolation or physical hardware protection.
Next, connect the mapping to the threat records in the threat-model chapter.

## Sources

- [ROS security setup and keystore root](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Introducing-ros2-security.rst).
- [ROS command-line enclave arguments](ros_command_line_arguments.html#enclave-assignments).
- [Node-to-participant design](Node_to_Participant_mapping.html).
- [SROS 2 project](https://github.com/ros2/sros2).
