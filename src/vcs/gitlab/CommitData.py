import base64

from typing_extensions import Self
from ..CommitAuthor import CommitAuthor

class CommitData:

    __COMMIT_UPDATE_ACTION_KEY = "update"
    __COMMIT_CREATE_ACTION_KEY = "create"

    def __init__(self, author: CommitAuthor, message: str, branch: str, action: str, file_path: str, file_content: bytes) -> None:
        self.author = author
        self.message = message
        self.branch = branch
        self.action = action
        self.file_path = file_path
        self.base64_file_content = CommitData.to_base64(file_content)

    # https://docs.gitlab.com/ee/api/commits.html#create-a-commit-with-multiple-files-and-actions
    def to_payload(self):
        return {
            "author_name": self.author.getUsername(),
            "author_email": self.author.getEmail(),
            "branch": self.branch,
            "commit_message": self.message,
            "actions": [
                {
                    "action": self.action,
                    "file_path": self.file_path,
                    "content": self.base64_file_content,
                    "encoding": "base64"
                }
            ]
        }

    def update_commit_data(author: CommitAuthor, message: str, branch: str, file_path: str, file_content: str) -> Self:
        return CommitData(author, message, branch, CommitData.__COMMIT_UPDATE_ACTION_KEY, file_path, file_content)

    def create_commit_data(author: CommitAuthor, message: str, branch: str, file_path: str, file_content: str) -> Self:
        return CommitData(author, message, branch, CommitData.__COMMIT_CREATE_ACTION_KEY, file_path, file_content)

    def to_base64(content: bytes) -> bytes:
        return base64.b64encode(content)

    def __str__(self):
        return "CommitData [ author=" + str(self.author) + ", message=" + str(self.message) + ", branch=" + str(self.branch) + ", action=" + str(self.action) + ", file_path=" + str(self.file_path) + ", base64_file_content=" + str(self.base64_file_content) + " ]"