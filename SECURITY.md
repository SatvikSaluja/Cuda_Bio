# Security

WarpAlign is research software, not clinically validated. Studio is an unauthenticated local service and must remain bound to loopback. Do not expose it through a public proxy.

Studio stores result sequences on local disk in SQLite. Downloaded JSONL contains sequence data. Finished-job cleanup removes database records but is not guaranteed secure erasure. Normal job completion/cancellation deletes temporary upload directories; hard crashes may require manual cleanup. There is no sequence telemetry.

Use the repository's private vulnerability-reporting facility if it is enabled: https://github.com/SatvikSaluja/Cuda_Bio/security . If unavailable, contact the repository owner privately to establish a reporting channel before sharing details. Do not place sensitive sequencing data or credentials in public issues. The development 0.2.x series has no long-term security-support commitment.
