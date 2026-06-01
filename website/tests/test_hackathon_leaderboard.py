import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from website.models import GitHubIssue, Hackathon, Organization, Repo, UserProfile


class HackathonLeaderboardTestCase(TestCase):
    """Test case for the hackathon leaderboard functionality."""

    @staticmethod
    def _extract_username(entry):
        """Helper method to extract username from leaderboard entry."""
        user = entry.get("user")
        if hasattr(user, "username"):
            return user.username
        elif isinstance(user, dict):
            return user.get("username")
        return None

    def setUp(self):
        """Set up test data for the hackathon leaderboard tests."""
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", email="test1@example.com", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="testpass123")
        self.user3 = User.objects.create_user(username="testuser3", email="test3@example.com", password="testpass123")

        # Ensure UserProfiles exist
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.profile3 = UserProfile.objects.create(user=self.user3)

        # Create organization
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-organization",
            url="https://example.com",
        )

        # Create repositories
        self.repo1 = Repo.objects.create(
            name="Test Repo 1",
            slug="test-repo-1",
            repo_url="https://github.com/test/repo1",
            organization=self.organization,
        )
        self.repo2 = Repo.objects.create(
            name="Test Repo 2",
            slug="test-repo-2",
            repo_url="https://github.com/test/repo2",
            organization=self.organization,
        )

        # Create hackathon
        now = timezone.now()
        self.hackathon = Hackathon.objects.create(
            name="Test Hackathon",
            slug="test-hackathon",
            description="A test hackathon for unit testing",
            organization=self.organization,
            start_time=now - datetime.timedelta(days=5),
            end_time=now + datetime.timedelta(days=5),
            is_active=True,
            rules="# Test Rules\n1. Submit PRs\n2. Be awesome",
        )
        self.hackathon.repositories.add(self.repo1, self.repo2)

        # Create pull requests for the hackathon
        # User 1 has 3 PRs (2 in repo1, 1 in repo2)
        for i in range(1, 4):
            repo = self.repo1 if i <= 2 else self.repo2
            GitHubIssue.objects.create(
                issue_id=1000 + i,
                title=f"Test PR {i} by User 1",
                body="Test PR body",
                state="closed",
                type="pull_request",
                created_at=now - datetime.timedelta(days=3),
                updated_at=now - datetime.timedelta(days=2),
                merged_at=now - datetime.timedelta(days=1),
                is_merged=True,
                url=f"https://github.com/test/repo/pull/{1000 + i}",
                repo=repo,
                user_profile=self.profile1,
            )

        # User 2 has 2 PRs (both in repo2)
        for i in range(1, 3):
            GitHubIssue.objects.create(
                issue_id=2000 + i,
                title=f"Test PR {i} by User 2",
                body="Test PR body",
                state="closed",
                type="pull_request",
                created_at=now - datetime.timedelta(days=3),
                updated_at=now - datetime.timedelta(days=2),
                merged_at=now - datetime.timedelta(days=1),
                is_merged=True,
                url=f"https://github.com/test/repo/pull/{2000 + i}",
                repo=self.repo2,
                user_profile=self.profile2,
            )

        # User 3 has 1 PR (in repo1)
        GitHubIssue.objects.create(
            issue_id=3001,
            title="Test PR 1 by User 3",
            body="Test PR body",
            state="closed",
            type="pull_request",
            created_at=now - datetime.timedelta(days=3),
            updated_at=now - datetime.timedelta(days=2),
            merged_at=now - datetime.timedelta(days=1),
            is_merged=True,
            url="https://github.com/test/repo/pull/3001",
            repo=self.repo1,
            user_profile=self.profile3,
        )

        # Create a PR that's outside the hackathon timeframe (should not be counted)
        GitHubIssue.objects.create(
            issue_id=4001,
            title="PR outside timeframe",
            body="This PR is outside the hackathon timeframe",
            state="closed",
            type="pull_request",
            created_at=now - datetime.timedelta(days=10),
            updated_at=now - datetime.timedelta(days=9),
            merged_at=now - datetime.timedelta(days=8),
            is_merged=True,
            url="https://github.com/test/repo/pull/4001",
            repo=self.repo1,
            user_profile=self.profile1,
        )

        # Create a PR that's not merged (should not be counted)
        GitHubIssue.objects.create(
            issue_id=5001,
            title="Unmerged PR",
            body="This PR is not merged",
            state="open",
            type="pull_request",
            created_at=now - datetime.timedelta(days=3),
            updated_at=now - datetime.timedelta(days=2),
            merged_at=None,
            is_merged=False,
            url="https://github.com/test/repo/pull/5001",
            repo=self.repo1,
            user_profile=self.profile1,
        )

        self.client = Client()