# CI

Calino CI is executed on the dedicated self-hosted GitHub Actions runner on `msk-1-vm-0w12`.

Runner labels:

- `self-hosted`
- `Linux`
- `X64`
- `ci-runner`
- `calino`

The workflow still uses GitHub Actions for orchestration, PR checks and artifact publication, but build/test/lint/Gradle execution runs on our VPS rather than a GitHub-hosted `ubuntu-*` worker.

The Android toolchain is bootstrapped reproducibly in the workflow with Java 17 and `android-actions/setup-android`, then installs Android platforms 36/37 and Build Tools 36.0.0.
