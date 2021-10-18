## Coding rules/guidelines
 - each fixture must have reasonable docstring (to reproduce setup manually)
 - each test must have reasonable docstring (to reproduce action(s) manually)
 - test module docstring for highlevel description of purpose is highly desirable
 - [doc/examples.py] is collection of code snippets showing common actions
 - `./quality-check` or `make commit-acceptance` has to be used for lint analysis

## Merge Requests
 - Commit(s) for MR should be pushed to new branch within this project
 - MR from forked project shouldn't be created
 - Only branches to be merged can be pushed to this project (no working branches)
 - Working branches if needed should be pushed to forked project(s)
 - Change(s) should be always rebased before pushing for MR (even updates)
 - Changes requested during review should be amended to original commit

## Merge Review
 - MR has to pass quality-check without a failure - passing Pipeline
 - two peers have to approve MR
 - approval is indicated by giving +1 (clicking the button or commnet: /award :+1:)
 - any MR without 'WIP:' prefix in title is considered ready for review
 - to request change reviewer toggles MR to WIP
 - (WIP status can be toggled by /wip quick action in comment)
 - MR with +2 together with passing Pipeline can be merged
 - Source branch should be deleted with merge


## And now if I want...

### To work with forked project (optional)
```
# make a fork on gitlab
$ git clone <your-fork>
$ git remote add upstream git@gitlab.cee.redhat.com:3scale-qe/3scale-py-testsuite.git
```

### To make a change
```
$ git checkout -b <new-feature>
# make the changes
$ git add <file>...
$ git commit  # and phrase commit/MR message
```

### To push a change
```
$ git push upstream <new-feature>  # use 'origin' if you don't use fork
# go to gitlab, create MR, find 'New merge request' button in 'Merge Requests'
```

### To push an update to existing MR (e.g. requested by review)
```
$ git fetch --all
$ git checkout <new-feature>
$ git rebase upstream/master  # use 'origin/master' if you don't use fork
# make your updates
$ git add <file>...
$ git commit --amend # to avoid multiple commits for one change
$ git push -f upstream <new-feature> # use 'origin' if you don't use fork; force is needed due to --amend
```

### To approve Merge request
 - Either click 'thumb up' button
 - or submit comment: /award :+1:

### To handoff MR back and request changes
 - Make a comment to express what should be changed
 - To toggle WIP state submit a comment: /wip

### To request review again after updates
 - push updates as described above
 - To toggle WIP state submit a comment: /wip

### To merge
 - Ensure MR received +2
 - Ensure Pipeline passed (Pipeline result is included, it is green and 'Merge' button isn't red)
 - Ensure 'Delete source branch' option is on
