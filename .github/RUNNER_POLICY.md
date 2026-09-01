# GitHub Actions runner policy

This repository uses GitHub-hosted runners only. Do not add `self-hosted`
labels to workflows. A source-cache verification that needs private local
archives or checkouts must be run explicitly on a local development machine;
it is not a GitHub Actions job.

This policy supersedes earlier runner instructions in repository documentation.
The `runner-policy` workflow rejects `self-hosted` and `self_hosted` labels in
workflow files.
