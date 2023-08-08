# Pull Requests

Contributions to this repository are accepted via GitHub Pull Requests.

## Commit Messages

### DCO and Signed-off-by

When contributing changes to this project, you must agree to the [DCO](DCO).
Commits must include a `Signed-off-by:` header which certifies agreement with
the terms of the [DCO](DCO).

Using `-s` with `git commit` will automatically add this header.

## Requesting Reviews

Use the GitHub reviewers field to request reviews from a specific individual. Be sure to also select "re-request review" after making changes in response to a past review to ensure the reviewer knows it's ready for another look.

## Merge Criteria

* Pull requests should receive at least one approval before merging.
* CI should be passing.
* Every person who is on the list of reviewers should be given a chance to weigh in before merging. 24 hours is a good general rule, but if the PR is small and the reviewers are all active, it's fine to merge sooner. If a PR is large, complex, or controversial, waiting longer would make sense. Use your best judgment. Note that a PR will not automatically merge until the review is complete or the review request is removed.
* The `hold` label must not be present on the PR. Ensure that whoever added the `hold` is OK with removing the label before the PR is merged. There is no timeout on the `hold` label for when someone else should remove it unless the reviewer who placed the hold is unavailable for a significant period.
* PRs must have either the `has-design` or `no-design-requied` label applied. This is to confirm that a design document has been produced if appropriate.
* PRs must have either the `has-docs` or `no-docs-required` label applied. This is to confirm that user-facing documentation has been produced if appropriate.
* PRs must have either the `has-tests` or `no-tests-required` label applied. This is to confirm that tests have been produced if appropriate.

We use [Mergify](https://mergify.io/) to automatically merge PRs that meet the above criteria. See the [Mergify configuration](https://github.com/nexodus-io/nexodus/blob/main/.github/mergify.yml) for more details.

## Exceptions

These are guidelines, not hard rules. Committers have earned the trust of others to use their best judgment in each situation.
