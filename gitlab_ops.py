import os
import base64
import gitlab
import requests
from dotenv import load_dotenv

from resources import ignored_files

load_dotenv()

class GitlabOps:
  def __init__(self):
    self.gl = gitlab.Gitlab(
      url='https://git.original.com.br',
      private_token=os.getenv('GITLAB_TOKEN_COLLINS'),
      session=requests.Session())

  def get_project(self, project_name):
    return self.gl.projects.get(project_name, all=True)

  def get_repo_files(self, project):
    repo_files = None

    try:
      repo_files = project.repository_tree(ref='master', recursive=True, all=True)

      if repo_files is not None:
        repo_files = [file for file in repo_files if file.get('name') not in ignored_files]

        if len(repo_files) == 0:
          repo_files = None
    except gitlab.exceptions.GitlabGetError as e:
      if e.error_message == '404 Tree Not Found':
        print(f"Project {project.name} has no folder structure")
        repo_files = None

    return repo_files

  def get_file_data(self, project, path):
    file_content = project.files.get(ref='master', file_path=path)
    return base64.b64decode(file_content.content).decode("utf-8").replace('\\n', '\n')
