## Coding rules/guidelines
 - Each fixture must have reasonable docstring (to reproduce setup manually)
 - Each test must have reasonable docstring (to reproduce action(s) manually)
 - Test module docstring for highlevel description of purpose is highly desirable
 - [doc/examples.py] is collection of code snippets showing common actions
 - `make commit-acceptance` has to be used for lint analysis

## Pull Requests
 - Fork on github
 - Push your changes to branch in your fork
 - Create pull request
 - Change(s) should be always rebased before pushing for PR (even updates)
 - Changes requested during review should be amended to original commit
 - Read more https://docs.github.com/en/pull-requests/collaborating-with-pull-requests

## Pull Request Review
 - Review from two reviewers is required
 - No pending change requests in reviews
 - No unresolved conversations
 - All checks have to pass

## Ignore format commits with `git blame`

When making commits that are strictly formatting/style changes (e.g., after running a new version of black or running pyupgrade after dropping an old Python version), add the commit hash to `.git-blame-ignore-revs`, so git blame can ignore the change.

For more details, see:
https://git-scm.com/docs/git-config#Documentation/git-config.txt-blameignoreRevsFile
https://github.com/pydata/pydata-sphinx-theme/pull/713
