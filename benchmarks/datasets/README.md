# Dataset provenance

The built-in generator uses Python's seeded `random.Random(1729)` to create uniform A/C/G/T sequences and independently sampled substitutions. No biological/private sequence data is included. Generated synthetic datasets are dedicated to the public domain under CC0-1.0. The source generator is MIT-licensed with the project. Each benchmark row records its seed and substitution probability. These workloads are not a model of any sequencing platform.

Real-data experiments must record download URL, accession, licence/usage conditions, file checksum and preprocessing command before use. Large raw inputs must remain outside Git.
