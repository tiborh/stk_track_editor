# Security policy

## Supported versions

Security fixes are maintained on the default branch (`main`). Reproduce issues
against the latest checkout where possible. This is an unofficial editor,
independent of the SuperTuxKart project.

## Reporting a vulnerability

Report suspected vulnerabilities privately through
[GitHub's vulnerability reporting form](https://github.com/tiborh/stk_track_editor/security/advisories/new).
Do not disclose vulnerabilities in public issues or pull requests before
coordinating a fix.

Include the affected commit, operating system, Python and browser versions,
minimal reproduction steps and expected impact. For layout-handling issues,
include a minimal JSON layout if it can be shared safely. For generation
issues, also include the Blender version and exporter revision.

Relevant boundaries include loopback-only editor access, Host/Origin checks,
layout validation, workspace file access and explicit external-program
execution. Browser interaction checks do not establish Blender/export or
gameplay safety. Do not execute untrusted Blender files or scripts to
reproduce a report.

Remove credentials, private paths, browser profiles, game settings and other
sensitive data from reproductions and logs.
