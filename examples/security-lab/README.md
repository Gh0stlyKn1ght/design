# Bounded SROS 2 teaching lab

**Juan Carlos Nevarez · Gh0stlyKn1ght** · October 20, 2026.

**Goal:** distinguish trusted identity, permitted data flow, and enforced startup using a talker/listener system with no actuators. The exercise targets Ubuntu 24.04 + ROS 2 Jazzy + `rmw_fastrtps_cpp`. It was exercised in isolated Ubuntu userspace; see the [recorded lab results](../../reports/security-handbook/runtime-lab-results.md) for six passed ROS cases and one inconclusive case. Lyrical, Cyclone DDS, and Zenoh require separately recorded compatibility runs.

## Prerequisites and boundaries

Use an isolated lab host with the Jazzy environment sourced and the distribution's `sros2`, `demo_nodes_cpp`, `rmw_fastrtps_cpp`, and Python `lxml` packages installed. Follow the official ROS installation instructions for your platform. Confirm that the chosen DDS package includes security support. Do not attach a moving robot. The exercise uses domain 42 and localhost discovery; neither setting is an authorization control.

The setup script creates signing keys and node private keys in a **new** directory with restrictive creation permissions. It refuses to overwrite an existing path. Keep the entire provisioning directory private, outside version control. The repository contains policy and unsigned example permissions only; it never contains a real keystore.

The policy grants `/chatter` publishing only to the talker, and subscription only to the listener. Both identities have explicit logging/parameter/time allowances and replies for their own parameter/type-description services. The transform adds the DDS ROS discovery topic. These allowances are part of the example's attack surface; the listener is not a principal that can perform no publishing at all.

## 1. Run the offline check

From the repository root:

```sh
python3 examples/security-lab/check_policy.py
python3 -m unittest discover -s examples/security-lab -p 'test_*.py' -v
```

The checker validates the policy and generated DDS XML against pinned schemas. It verifies exact topic direction sets, certificate subjects, domain 42, default denial, and no wildcard grants. It rejects DTD/entity declarations and XInclude, disables network resolution, and denies XSLT I/O. The vendored files have a source manifest and hashes. This protects the local check's defined input boundary; it is not a generic sandbox for arbitrary XML/XSLT.

`generated/permissions.xml` is **unsigned** and has an illustrative October 2026–October 2027 interval. It is evidence of transformation, not deployable credentials. Runtime SROS 2 derives permission validity from the actual certificate. Review that validity and use a deployment-specific renewal policy.

## 2. Provision on the ROS host

Choose a new absolute directory and run:

```sh
bash examples/security-lab/setup.sh "$HOME/ros2-security-lab"
```

The script runs the offline check before creating a keystore, creates separate talker/listener enclaves, and applies `policy.xml` using `create_permission`. It records package versions in the private lab directory. Check the capture result: package names differ, so resolve missing entries before treating the version inventory as complete. Review the generated `governance.xml`, `permissions.xml`, signed files, certificate subjects, domains and validity before proceeding. Capture their hashes, not their private-key contents. A new example keystore is not a production signing service.

## 3. Establish the authorized control case

In **each** terminal, source ROS Jazzy, then:

```sh
source examples/security-lab/environment.sh
export ROS_SECURITY_KEYSTORE="$HOME/ros2-security-lab/keystore"
```

Run the talker in terminal A:

```sh
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/talker
```

Run the listener in terminal B:

```sh
ros2 run demo_nodes_cpp listener --ros-args --enclave /security_lab/listener
```

Observe several messages, record the time window and logs, and stop both with Ctrl-C. If this control case fails, resolve credentials, governance, clock, version, network, type and QoS problems before interpreting a negative case.

## 4. Test denied behavior

Keep the same environment and vary one property at a time.

**Missing enclave:** use an enclave that was never created:

```sh
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/missing
```

Expected: the secured participant fails to initialize. Record the actual error and exit status. A fallback to unsecured startup fails this case.

**Forbidden remap:** retain the talker identity but change the application topic:

```sh
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/talker \
  --remap chatter:=not_chatter
```

Expected: the unauthorized endpoint is rejected and no forbidden messages are delivered. The process-level outcome can depend on implementation and node error handling. Record what occurs rather than copying an expected log message.

**Wrong direction:** run the talker executable under the listener enclave:

```sh
ros2 run demo_nodes_cpp talker --ros-args --enclave /security_lab/listener
```

Expected: this identity is denied publication on `/chatter`. The executable's default node name also changes its parameter-service names relative to the listener policy, so this is a whole-profile rejection case. The exact generated grant check separately isolates the application-direction assertion.

**Untrusted authority:** create a separate fresh lab directory with the setup script. Start the original talker using the first keystore; start the listener using the second keystore, with the same listener enclave path. The independently generated authorities should prevent trusted communication. Record the handshake or access evidence and compare it with the authorized control. Successful startup alone does not establish peer acceptance.

## 5. Record results honestly

| Case | Required observation | Initial status |
| --- | --- | --- |
| Offline policy/grant check | Named local assertions pass. | Run by the package author; see generated check record. |
| Authorized pair | Listener receives known talker messages. | Seven messages observed; pass. |
| Missing enclave | Enforced initialization failure. | Observed; exit 250, pass. |
| Forbidden remap | Forbidden endpoint/delivery denied. | Writer creation rejected; pass. |
| Wrong identity profile | Unauthorized application publication denied. | Profile rejected; focused write probe also rejected; pass. |
| Separate authority | Untrusted peer cannot exchange the protected application data. | Zero messages, no explicit rejection evidence; inconclusive. |

These are recorded author-run observations, not guaranteed outcomes on your host. Repeat the checks and retain your own results. The runtime runner can automate these bounded cases.

Copy `results-template.json` into the private lab directory, record each actual outcome, and link sanitized logs plus the version manifest. “No messages” without a working authorized control and rejection evidence is inconclusive. Do not change a result to pass because XML was generated successfully.

**Explain back:** What is authenticated? Which principal receives permissions? Why does default denial not stop an authorized process abusing an allowed topic? Which host file access would expose the identity?

**Artifact:** diagram, threat record, reviewed policy/governance, artifact hashes, version manifest, observed cases and limitations. Next, connect one deployment-specific robot control to the threat register and a separately bounded hardware test plan.

## Sources and notices

[SROS 2](https://github.com/ros2/sros2), the [official Jazzy security setup](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Introducing-ros2-security.rst), and [access controls](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Advanced/Security/Access-Controls.rst) inform the procedure. Vendored SROS 2 schemas/transform retain Apache 2.0 notices in `vendor/sros2/LICENSE`; W3C schema attribution and its source link are recorded in the vendor manifest and notice. The new scripts and examples use the repository's Apache 2.0 license. Handbook prose retains the design-document attribution context described in the updated PDF.


## Optional runtime automation

`run_runtime.py` executes the bounded software cases against two independently provisioned keystores. See the recorded runtime observations for its exact command, result interpretation and the remaining inconclusive case. It returns nonzero for failed or inconclusive cases. `probe_publish.py` isolates application writer creation after the listener node has initialized successfully. `authentication_probe.cpp` is a separate Fast DDS 2.14 callback diagnostic; its trusted acceptance and silent untrusted case are recorded separately from the ROS cases.
