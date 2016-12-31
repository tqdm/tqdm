# Definition of the version number
import os

__all__ = ["__version__"]

# major, minor, patch, -extra
version_info = 4, 11, 1

# Nice string for the version
__version__ = '.'.join(map(str, version_info))


# auto -extra based on commit hash (if not tagged as release)
res = None
scriptdir = os.path.dirname(__file__)
gitdir = os.path.abspath(scriptdir + '/../.git')
if os.path.isdir(gitdir):
    # Open the HEAD file
    with open(os.path.join(gitdir,'HEAD'), 'r') as fh_head:
        res = fh_head.readline().strip()
    # If we are in a branch, HEAD will point to a file containing the latest commit
    if 'ref:' in res:
        # Get reference file path
        ref_file = res[5:]
        # Get branch name
        branch_name = ref_file.split('/')[-1]
        # Sanitize path of ref file
        # get full path to ref file
        ref_file_path = os.path.abspath(os.path.join(gitdir, ref_file))
        # check that we are in git folder (by stripping the git folder from the ref file path)
        if os.path.relpath(ref_file_path, gitdir).replace('\\', '/') != ref_file:
            # Trying to get out of git folder, not good!
            res = None
        else:
            # Else the file file is inside git, all good
            # Open the ref file
            with open(ref_file_path, 'r') as fh_branch:
                commit_hash = fh_branch.readline().strip()
                res = commit_hash[:8] + ' (branch: ' + branch_name + ')'
    # Else we are in detached HEAD mode, we directly have a commit hash
    else:
        res = res[:8]
    # Append to version string
    if res is not None:
        __version__ += '-' + res
