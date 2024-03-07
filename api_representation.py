import base64
import json
import os
import re

import gitlab
import requests
from dotenv import load_dotenv

from resources import (
  application_properties_files,
  application_properties_regex,
  bootstrap_regex,
  feign_folder_regex,
  feign_url_regex, ignored_files,
  other_projects_acronym
)

load_dotenv()

def gitlab_api():
  session = requests.Session()
  return gitlab.Gitlab(
    'https://git.original.com.br',
    private_token=os.getenv('GITLAB_TOKEN_COLLINS'),
    session=session)

def generate_csv_bootstrap(file_name, csv_matrix):
  rows = ["{},{},{}".format(i, j, k) for i, j, k in csv_matrix]
  text = "\n".join(rows)

  with open(f'files/{file_name}.csv', 'w') as f:
    f.write(text)

def generate_csv_application(file_name, csv_matrix):
  rows = ["{},{},{},{},{}".format(i, j, k, l, m) for i, j, k, l, m in csv_matrix]
  text = "\n".join(rows)

  with open(f'files/{file_name}.csv', 'w') as f:
    f.write(text)

def filter_files_by_regex(repo_files, regex):
  file_filter = []

  for file in repo_files:
    file_name = file.get('name')

    if re.match(regex, file.get('path')):
      file_info = {'name': file_name, 'path': file.get('path')}
      file_filter.append(file_info)

  return None if len(file_filter) == 0 else file_filter

def filter_files_by_list(repo_files, relevant_files):
  file_filter = []

  for file in repo_files:
    file_name = file.get('name')

    if file_name in relevant_files:
      file_info = {'name': file_name, 'path': file.get('path')}
      file_filter.append(file_info)

  return None if len(file_filter) == 0 else file_filter

def get_repo_files(project):
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

def get_file_data(project, path):
  file_content = project.files.get(ref='master', file_path=path)
  return base64.b64decode(file_content.content).decode("utf-8").replace('\\n', '\n')

def feign_data_mapping(project, filtered_list):
  data = []

  for filtered_file in filtered_list:
    file_data = get_file_data(project, filtered_file.get('path'))
    match = re.search(feign_url_regex, file_data)

    if match:
      url_text = match.group("url_text")
      url_text = url_text.replace('"${', '').replace('}"', '')
      data.append({'file': filtered_file.get('name'), 'url': url_text})

  return None if len(data) == 0 else data

def application_properties_data_mapping(project, filtered_list):
  file_dictionary = {}

  for filtered_file in filtered_list:
    file_name = filtered_file.get('name')
    file_dictionary[file_name] = []
    file_data = get_file_data(project, filtered_file.get('path'))

    for line in file_data.splitlines():
      match = re.search(application_properties_regex, line)

      if match:
        variable_name = match.group("name")
        url_text = match.group("url_text")

        if variable_name.startswith('#'):
          continue

        file_dictionary[file_name].append({'variable_name': variable_name, 'url_text': url_text})

    if len(file_dictionary[file_name]) == 0:
      del file_dictionary[file_name]

  return None if len(file_dictionary) == 0 else file_dictionary

def bootstrap_data_mapping(project, filtered_list):
  for filtered_file in filtered_list:
    file_data = get_file_data(project, filtered_file.get('path'))
    match = re.search(bootstrap_regex, file_data, flags=re.DOTALL)

    if match:
      integrations = match.group("integrations")
      integrations = integrations.replace(',', ';').replace('\n', '')
      return integrations

  return None

def save_acronym_dictionary(acronym_dictionary):
  with open('files/acronym_dictionary.json', 'w') as f:
    try:
      json.dump(acronym_dictionary, f)
    except json.decoder.JSONDecodeError:
      print(acronym_dictionary)

def load_acronym_dictionary():
  with open('files/acronym_dictionary.json', 'a+') as f:
    try:
      return json.load(f)
    except json.decoder.JSONDecodeError:
      return None

def build_representation(api, acronym, dictionary):
  project_list = api.projects.list(search=acronym, all=True)

  if dictionary.get(acronym) is None:
    dictionary[acronym] = {}

  for project in project_list:
    if not project.name.endswith('-java'):
      continue

    repo_files = get_repo_files(project)

    if repo_files is None:
      continue

    if dictionary[acronym].get(project.name) is None:
      dictionary[acronym][project.name] = {}

      feign_files = filter_files_by_regex(repo_files, feign_folder_regex)

      if feign_files is not None:
        dictionary[acronym][project.name]['feign'] = feign_data_mapping(project, feign_files)

      bootstrap_files = filter_files_by_list(repo_files, ['bootstrap.yml'])

      if bootstrap_files is not None:
        dictionary[acronym][project.name]['bootstrap'] = bootstrap_data_mapping(project, bootstrap_files)

      properties_files = filter_files_by_list(repo_files, application_properties_files)

      if properties_files is not None:
        result = application_properties_data_mapping(project, properties_files)

        if result is not None:
          dictionary[acronym][project.name]['application'] = result

  return dictionary

def main():
  gl = gitlab_api()
  acronym_dictionary = load_acronym_dictionary()

  if acronym_dictionary is None:
    acronym_dictionary = {}

  for acronym in other_projects_acronym:
    acronym_dictionary = build_representation(api=gl, acronym=acronym, dictionary=acronym_dictionary)

  save_acronym_dictionary(acronym_dictionary)

if __name__ == '__main__':
  main()