import json
import re

from dotenv import load_dotenv

from resources.gitlab_ops import get_file_data, gitlab_api
from resources import fernanda_acronyns

load_dotenv()


def search_project_names_by_acronyms(gl, acronym_list) -> dict:
  """
  Obtém todos os arquivos de integração a partir da lista de siglas e retorna um dicionário com os nomes dos projetos
  separados por sigla.

  :param gl: objeto de acesso à api
  :param acronym_list: lista de siglas que devem ser pesquisadas
  :return: dicionário com todos os projetos inclusos em cada sigla do acronym_list
  """

  project = gl.projects.get("fwms/fwms-configuracao-aplicacoes", all=True)
  repo_files = project.repository_tree(ref='master', recursive=True, all=True)

  if repo_files is None:
    return None

  dictionary = {}
  file_filter = []

  for file in repo_files:
    file_name = file.get('name')

    if '-corp.properties' in file_name or '.gitignore' in file_name:
      continue

    check_name = file_name.replace('-integration.properties', '')

    if check_name not in acronym_list:
      continue

    dictionary[check_name] = []

    file_info = {'name': file_name, 'path': file.get('path')}
    file_filter.append(file_info)

  if len(file_filter) == 0:
    return None

  regex = r"(?P<name>.*?)\s*=\s*(https?://)(?P<url_text>.*)"

  for filtered_file in file_filter:
    path = filtered_file.get('path')
    file_data = get_file_data(project, path)

    for line in file_data.splitlines():
      match = re.search(regex, line)

      if match:
        variable_name = match.group("name")
        url_text = match.group("url_text")
        acronym = filtered_file.get('name').replace('-integration.properties', '')
        dictionary[acronym].append({'project_name': variable_name, 'url': url_text})

  return dictionary

"""
Test local output
"""
if __name__ == '__main__':
  dictionary = search_project_names_by_acronyms(gitlab_api(), fernanda_acronyns)

  with open('../files/fwms_dictionary.json', 'w+') as f:
    try:
      json.dump(dictionary, f)
    except json.decoder.JSONDecodeError:
      print(dictionary)