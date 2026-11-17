# Preparing and publishing a release

The repository is prepared as **1.0.0**. Updating version files does not publish
anything. No commit, tag, push or public release has been performed by the agent.

## Check and build

Use a machine with C++17, CMake, Node 22+, Python and network access:

```sh
python -m pip install -e '.[studio,test,docs]' build twine
python scripts/check_version.py
cmake -S . -B build -DENABLE_CUDA=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
python -m pytest -q
bash scripts/build_release.sh
python -m mkdocs build --strict
```

Artifacts are written to `dist/1.0.0/`. Do not commit native binaries, wheels,
build directories or local genomic data. Review the release notes and retain
all hardware/browser validation caveats until those checks actually pass.

## After you commit and push

First review and commit the intended changes yourself, then push your branch.
Check the CPU, packaging, frontend and Docker CI results. Once the selected
commit is ready, you can tag and push it explicitly:

```sh
git tag -a v1.0.0 -m "WarpAlign v1.0.0"
git push origin v1.0.0
```

Use your actual remote name if it is not `origin`. These commands are examples;
they have not been executed for you. Pushing a branch alone does not create a
release.

The tag workflow validates matching versions, builds/tests the CPU artifacts,
and creates a **draft GitHub release** with the source distribution, Linux
CPython 3.12 wheel and SHA256 checksums. Inspect the draft and attached artifacts
in GitHub Releases, then publish it manually. It does not upload to PyPI or claim
GPU validation. The Linux wheel is not repaired/audited as manylinux; source
installation remains the portable fallback.

If workflow changes are rejected when pushing, use GitHub authentication with
permission to update workflows (your earlier OAuth error concerned that scope).
Do not remove CI files merely to bypass that authentication requirement.
