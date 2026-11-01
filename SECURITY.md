# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Email **[atilioobadia@gmail.com](mailto:atilioobadia@gmail.com)** with:

- the repository and version affected,
- a description of the issue and its impact,
- steps to reproduce, or a proof of concept where possible,
- any suggested remediation.

You will get an acknowledgement within a few working days, an assessment of severity, and an
update when a fix ships. Please give reasonable time for a fix before publishing details.

## Scope

This policy covers the repositories on this profile and any deployed service I operate for a
client. Client systems are covered by their own agreements; report those directly to me and I
will route it.

## Out of scope

- Findings that require physical access to a device.
- Reports generated solely by an automated scanner without a demonstrated impact.
- Social engineering, spam or denial-of-service testing against production systems.
- Dependency version warnings with no exploitable path in this code.

## Handling

- Secrets are never committed; `.env` files and credentials stay out of the repository.
- Dependencies are kept current, and security-relevant upgrades take priority over feature work.
- Confirmed issues are fixed on a private branch, released, and only then described publicly.
