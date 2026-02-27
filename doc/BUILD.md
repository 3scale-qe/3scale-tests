# Building 3scale-tests images

Build process is now covered in series of independent github actions. Here is
brief but comprehensive guide to create new build using these actions.

## Version format

Version consists of four parts separated by dots:

```
{MAJOR}.{MINOR}.{PATCH}.{REVISION}rc{RCVERSION}
```

Example: `2.14.0.1rc1`

## 1. Pull request for release candidate

**TL;DR**: Just run the `dispatch_1_rc_pullrequest` action with no parameters.
Only provide the version parameter if you need to bump the MAJOR or MINOR version.

First step is creating pull request for new version. In this pull request
Pipefile.lock is frozen (and released again in next commit) and VERSION number
is increased.

Pull request can and should be created with `dispatch_1_rc_pullrequest` github
action. It accepts an optional version parameter.

### Version parameter behavior

**Custom version provided** (dot-separated numbers, e.g. `2.14` or `2.14.0`):
- If exactly two numbers are given (e.g. `2.14`), PATCH is automatically set to `0`, resulting in `2.14.0`.
- There is no limit on the number of parts otherwise.
- The action searches existing git tags to find the next available REVISION for that version, and sets RCVERSION to the lowest unused value (numbering starts at `1`).

**No version provided**:
- Version is read from the `VERSION` file (first three fields: MAJOR.MINOR.PATCH).
- REVISION is determined as the highest existing value found in git tags.

RC pull request is created by this action. PR should go through standard
review process, it always contains 2 commits, first with version increase and
committed Pipfile.lock and second with freed Pipfile.lock. Final diff should
contain only version change (unless there are new versions of some resource
files, these can be included as well).

After the review the PR should be merged.

## 2. Create pre-release

This is done automatically for the first release candidate (`rc1`). For
subsequent rc builds (`rc2`, `rc3`, ...) automation does not work and the
release must be created manually on GitHub.

### Manual pre-release steps

1. Go to the repository on GitHub and click **Releases** in the right sidebar.
2. Click **Draft a new release**.
3. Select the correct tag created in step 1 from the tag dropdown. If the tag
   is missing, create and push it manually before proceeding.
4. Check **Set as a pre-release**.
5. Click **Publish release**.

## 3. Build & Push

This is done automatically whenever release is created, it is pushed to quay.io
and also to github packages (not versioned here).

Just wait until `make_dist` github action is completed.

## 4. Test

This has to be done manually, either image from quay.io or github packages
should be used. One possible method to test it is this:

`NAMESPACE=${REPLACEME} make test-in-docker flags=--ui pull=1`

`pull=1` is important, also version in the output of the tests should be
verified.

'smoke' is minimum that should be executed to verify the image.

Alternatively, you can run the Jenkins pipeline with the new RC image from quay.io.

## 5. Release & Push

In case of successful test execution run `dispatch_5_github_release` github
action to create final release and push it to quay.io and github packages. All
happens automatically.

Just wait until `make_dist` github action is completed.

Congratulations! Awesome job!
