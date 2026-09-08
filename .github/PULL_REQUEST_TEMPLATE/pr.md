---
name: Pull Request
about: Use this template for proposing change(s)
---

- [ ] I have marked all applicable categories:
    + [ ] exception-raising fix
    + [ ] visual output fix
    + [ ] documentation modification
    + [ ] new feature
- [ ] If applicable, I have mentioned the relevant/related issue(s)
- [ ] Any AI-assisted commits are clearly marked ([author], [Co-authored-by] or [Assisted-by])

Less important but also useful:

- [ ] I have visited the [source website], and in particular
  read the [known issues]
- [ ] I have searched through the [issue tracker] for duplicates
- [ ] I have mentioned version numbers, operating system and
  environment, where applicable:
  ```python
  import tqdm, sys
  print(tqdm.__version__, sys.version, sys.platform)
  ```

[source website]: https://github.com/tqdm/tqdm/
[known issues]: https://github.com/tqdm/tqdm/#faq-and-known-issues
[issue tracker]: https://github.com/tqdm/tqdm/issues?q=
[author]: https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---authorauthor
[Co-authored-by]: https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors
[Assisted-by]: https://allthingsopen.org/articles/open-source-ai-contributions-assisted-by-git-trailer-standard
