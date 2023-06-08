# Building 3scale-tests images

Build process is now covered in series of independent github actions. Here is
brief but comprehensive guide to create new build using these actions.

## 1. Pull request for release candidate

First step is creating pull request for new version. In this pull request
Pipefile.lock is frozen (and released again in next commit) and VERSION number
is increased.

Pull request can and should be created with `dispatch_1_rc_pullrequest` github
action. It has one parameter that should be kept empty usually. Only in case
that the version should be increased (should be aligned with 3scale) the
version should be defined in X.Y.Z form, e.g. 2.14.0, 2.13.1 etc.

RC pull request is created by this action. PR should go through standard
review process, it always contains 2 commits, first with version increase and
committed Pipfile.lock and second with freed Pipfile.lock. Final diff should
contain only version change (unless there are new versions of some resource
files, these can be included as well).

After the review the PR should be merged.

## 2. Create pre-release

This is done automatically for first release 'rc1'. For next rc builds (rc2,
rc3, ...) automation does not work and the release must be created manually
(meaning standard github release)

When manual, the release must be created from correct commit **not** from HEAD,
that commit is named by the rc version and it must be pre-release.

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

'smoke' is minimum that should be executed to verify the image

## 5. Release & Push

In case of successful test execution run `dispatch_5_github_release` github
action to create final release and push it to quay.io and github packages. All
happens automatically.

Just wait until `make_dist` github action is completed.

Congratulations! Awesome job!
