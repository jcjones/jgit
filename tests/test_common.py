import logging
from unittest.mock import MagicMock, patch

import pytest

import common


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_branches(tmp_path, contents=None):
    """Set up a fake git repo and return a JGitBranches instance.

    If *contents* is given it is written to .git/jgit-branches.
    """
    dot_git = tmp_path / ".git"
    dot_git.mkdir()
    if contents is not None:
        (dot_git / "jgit-branches").write_text(contents)
    return common.JGitBranches(tmp_path, logging.getLogger("test"))


def git_mock(*lines):
    """Return a mock for the module-level ``common.git`` whose ``.branch()``
    yields the given lines (simulating ``git branch --list --verbose``).

    Uses side_effect so each call returns a fresh iterator, allowing
    a single mock to survive multiple calls to iter()/list()/contents().
    """
    mock = MagicMock()
    mock.branch.side_effect = lambda *a, **kw: iter(lines)
    return mock


# ---------------------------------------------------------------------------
# dot_git
# ---------------------------------------------------------------------------


class TestDotGit:
    def test_finds_in_current_dir(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert common.dot_git(tmp_path) == tmp_path / ".git"

    def test_finds_in_parent_dir(self, tmp_path):
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        assert common.dot_git(subdir) == tmp_path / ".git"

    def test_raises_when_not_found(self, tmp_path):
        with pytest.raises(common.NoGitRepoException):
            common.dot_git(tmp_path)


# ---------------------------------------------------------------------------
# JGitBranches – file operations (no git calls needed)
# ---------------------------------------------------------------------------


class TestJGitBranchesFileOps:
    def test_append_creates_entry(self, tmp_path):
        b = make_branches(tmp_path)
        # git only knows about main; feature/foo is new, so append() writes it
        with patch("common.git", git_mock("  main abc1234 initial commit")):
            b.append("feature/foo")
        assert "feature/foo" in b.path.read_text()

    def test_append_no_duplicates(self, tmp_path):
        # append() deduplicates by calling list() which reads from git.branch.
        # First call: git doesn't list feature/foo yet → written to file.
        # Second call: git now lists it → skipped.
        b = make_branches(tmp_path)
        with patch("common.git", git_mock("  main abc1234 initial commit")):
            b.append("feature/foo")
        with patch(
            "common.git",
            git_mock(
                "  main        abc1234 initial commit",
                "  feature/foo def5678 my feature",
            ),
        ):
            b.append("feature/foo")
        non_empty = [l for l in b.path.read_text().splitlines() if l.strip()]
        assert non_empty.count("feature/foo") == 1

    def test_remove_deletes_entry(self, tmp_path):
        b = make_branches(tmp_path, "feature/foo\nfeature/bar\n")
        b.remove("feature/foo")
        text = b.path.read_text()
        assert "feature/foo" not in text
        assert "feature/bar" in text

    def test_remove_missing_file_no_error(self, tmp_path):
        b = make_branches(tmp_path)  # no jgit-branches file written
        b.remove("feature/foo")  # must not raise

    def test_remove_leaves_file_when_nothing_matches(self, tmp_path):
        b = make_branches(tmp_path, "feature/bar\n")
        b.remove("feature/foo")
        assert "feature/bar" in b.path.read_text()


# ---------------------------------------------------------------------------
# JGitBranches.iter – parsing logic
# ---------------------------------------------------------------------------


class TestJGitBranchesIter:
    def test_iter_yields_all_branches(self, tmp_path):
        b = make_branches(tmp_path)
        with patch(
            "common.git",
            git_mock(
                "* main        abc1234 [origin/main] Initial commit",
                "  feature/foo def5678 My feature",
            ),
        ):
            names = [name for name, _ in b.iter()]
        assert "main" in names
        assert "feature/foo" in names

    def test_iter_marks_head_branch(self, tmp_path):
        b = make_branches(tmp_path)
        with patch(
            "common.git",
            git_mock(
                "* main abc1234 some commit",
            ),
        ):
            results = dict(b.iter())
        assert "[HEAD]" in results["main"]

    def test_iter_does_not_mark_non_head_as_head(self, tmp_path):
        b = make_branches(tmp_path)
        with patch(
            "common.git",
            git_mock(
                "* main        abc1234 some commit",
                "  feature/foo def5678 some other commit",
            ),
        ):
            results = dict(b.iter())
        assert "[HEAD]" not in results["feature/foo"]

    def test_iter_marks_tracked_branches(self, tmp_path):
        b = make_branches(tmp_path, "feature/foo\n")
        with patch(
            "common.git",
            git_mock(
                "  main        abc1234 some commit",
                "  feature/foo def5678 tracked branch",
            ),
        ):
            results = dict(b.iter())
        assert "[tracked]" in results["feature/foo"]
        assert "[tracked]" not in results.get("main", [])

    def test_iter_no_jgit_file(self, tmp_path):
        b = make_branches(tmp_path)  # no jgit-branches file
        with patch(
            "common.git",
            git_mock(
                "* main        abc1234 some commit",
                "  feature/foo def5678 another commit",
            ),
        ):
            results = list(b.iter())
        assert len(results) == 2

    def test_iter_skips_blank_and_comment_lines_in_branch_file(self, tmp_path):
        b = make_branches(tmp_path, "# a comment\n\nfeature/foo\n")
        with patch(
            "common.git",
            git_mock(
                "  feature/foo abc1234 a commit",
            ),
        ):
            results = list(b.iter())
        names = [name for name, _ in results]
        assert "feature/foo" in names
        assert "# a comment" not in names

    def test_iter_inline_comment_preserved(self, tmp_path):
        b = make_branches(tmp_path, "feature/foo # working on xyz\n")
        with patch(
            "common.git",
            git_mock(
                "  feature/foo abc1234 a commit",
            ),
        ):
            results = dict(b.iter())
        comments = results["feature/foo"]
        assert any("working on xyz" in c for c in comments)
        assert "[tracked]" in comments

    def test_iter_worktree_branch_prefix(self, tmp_path):
        """Branches checked out in another worktree have a '+' prefix."""
        b = make_branches(tmp_path)
        with patch(
            "common.git",
            git_mock(
                "+ feature/wt abc1234 worktree branch",
            ),
        ):
            results = list(b.iter())
        assert results[0][0] == "feature/wt"

    def test_iter_commented_strings_format(self, tmp_path):
        b = make_branches(tmp_path)
        with patch(
            "common.git",
            git_mock(
                "* main abc1234 a commit",
            ),
        ):
            strings = list(b.iter_commented_strings())
        assert len(strings) == 1
        assert strings[0].startswith("main")
        assert " # " in strings[0]

    def test_iter_list_and_contents_consistent(self, tmp_path):
        b = make_branches(tmp_path, "feature/foo\n")
        with patch(
            "common.git",
            git_mock(
                "  main        abc1234 a commit",
                "  feature/foo def5678 another commit",
            ),
        ):
            branch_list = b.list()
            contents = b.contents()
        assert "feature/foo" in branch_list
        assert "main" in branch_list
        for name in branch_list:
            assert name in contents
