import re

from dotenv import load_dotenv

from gitlab_ops import get_file_data, get_repo_files, gitlab_api
from resources import (
  application_properties_files,
  application_properties_regex,
  bootstrap_regex,
  feign_folder_regex,
  feign_url_regex, other_projects_acronym
)
from resources.commons import save_dictionary

load_dotenv()


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


def build_representation(api, acronym, dictionary) -> dict:
  """
  A função constroi a representação de um projeto, baseado na sigla passada como parâmetro.

  Parâmetros:
  :param api: Uma instância da API do Gitlab
  :param acronym: A sigla do projeto
  :param dictionary: O dicionário onde será armazenado a representação do projeto
  :return: O dicionário atualizado com a representação do projeto

  A função funciona da seguinte forma

  A função funciona da seguinte forma:
    1. Lista todos os projetos na API GitLab que correspondem à sigla fornecida.
    2. Se a sigla ainda não for uma chave no dicionário, ela é adicionada, no mesmo, com um objeto vazio.
    3. Itera em cada projeto na lista de projetos.
        - Se o nome do projeto não terminar com '-java', ele pula para o próximo projeto.
        - Recupera os arquivos do repositório do projeto.
        - Se não houver arquivos no repositório, passa para o próximo projeto.
        - Se o nome do projeto ainda não for uma chave no dicionário sob a sigla, ele é adicionado no dicionário com um objeto vazio.
        - Filtra os arquivos do repositório com base em feign_folder_regex e adiciona o resultado ao dicionário sob o nome do projeto com 'feign' como chave.
        - Filtra os arquivos do repositório para 'bootstrap.yml' e adiciona o resultado ao dicionário sob o nome do projeto com 'bootstrap' como chave.
        - Filtra os arquivos do repositório com base em application_properties_files e adiciona o resultado ao dicionário sob o nome do projeto com 'application' como chave.
    4. Retorna o dicionário atualizado.

  O dicionário gerado é utilizado no project_representation para gerar a representação pedida pela Fernanda.
  Um exemplo do arquivo gerado pode ser encontrado em files/acronym_dictionary.json
  """
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

def build_api_representation(api) -> dict:
  dictionary = {}

  for acronym in other_projects_acronym:
    dictionary = build_representation(api=api, acronym=acronym, dictionary=dictionary)

  return dictionary

if __name__ == '__main__':
  gl = gitlab_api()
  acronym_dictionary = build_api_representation(gl)

  save_dictionary(acronym_dictionary, 'acronym_dictionary')
