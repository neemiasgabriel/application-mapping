import json
from resources import fernanda_acronyns

def load_file(file_path):
  with open(file_path, 'r') as f:
    try:
      return json.load(f)
    except json.decoder.JSONDecodeError:
      return None

def save_acronym_dictionary(projects_dict, file_name):
  with open(f'files/{file_name}.json', 'w') as f:
    try:
      json.dump(projects_dict, f)
    except json.decoder.JSONDecodeError:
      print(projects_dict)

def get_integrations(project):
  bootstrap = project.get('bootstrap')

  if bootstrap is None:
    return None

  bootstrap = bootstrap.split(';')

  integrations = [integration.strip().replace('-integration', '') for integration in bootstrap]

  return [integration for integration in integrations if integration in fernanda_acronyns]

def get_feign_urls(project):
  feign = project.get('feign')

  if feign is None:
    return set()

  return set(feign['url'] for feign in feign)

def get_application_urls(project, application_name):
  application = project.get('application')

  if application is None:
    return set()

  application_env = application.get(application_name)

  if application_env is None:
    return set()

  return set(url['url_text'] for url in application_env)

def add_entry(representation, acronym, project):
  if representation.get(acronym) is None:
    representation[acronym] = {}

  if representation[acronym].get(project) is None:
    representation[acronym][project] = []

  return representation

def append_feign_to_representation(representation, fernanda_acronym, projects_name_list, application, project):
  for project_name in projects_name_list:
    current_name = project_name.replace('.url', '')

    if current_name in application:
      current_name = project_name.replace('.url', '').replace('.', '-')
      representation = add_entry(representation, fernanda_acronym, current_name)
      representation[fernanda_acronym][current_name].append(project)

def append_application_files_to_representation(representation, fernanda_acronym, projects_name_list, application, project):
  for project_name in projects_name_list:
    current_name = project_name.replace('.url', '').replace('.', '-')

    if current_name in application:
      representation = add_entry(representation, fernanda_acronym, current_name)
      representation[fernanda_acronym][current_name].append(project)

def generate_representation(representation, application_urls, fernanda_projects, project, is_feign=False):
  for application in application_urls:
    for fernanda_acronym in fernanda_projects.keys():
      projects_name_list = [name['project_name'] for name in fernanda_projects[fernanda_acronym]]

      if is_feign:
        append_feign_to_representation(representation, fernanda_acronym, projects_name_list, application, project)
      else:
        append_application_files_to_representation(representation, fernanda_acronym, projects_name_list, application, project)

def main():
  """
  Gera um dicionário com a representação de todos os projetos que acessam os projetos da Fernanda.

  A função funciona da seguinte forma
  1. Carrega os dicionários dos projetos da Fernanda e os projetos da API.
  2. Itera em cada sigla de projeto nos projetos da API. (Projetos que não são da Fernanda)
  3. Itera em cada projeto sob a sigla.
  4. Recupera as nomes de projeto que estão no Feign
    4.1 Adiciona os nomes de projeto que acessam os projetos da Fernanda
  5. Obtém as URLs dos arquivos de application (dev, hml, prd e properties)
    5.1 Gera um conjunto para que não hajam URLs repetidas na hora de gerar a representação
  6. Adiciona os projetos, encontrados nos arquivos, dentro da representação.
  7. O último loop remove os projetos duplicados, de cada sigla, e salva o dicionário em files/representation.json
  :return:
  """
  fernanda_projects = load_file('files/fernanda_projects_dictionary.json')
  projects = load_file('files/acronym_dictionary.json')

  representation = {}

  for acronym in projects.keys():
    for project in projects[acronym].keys():
      feign_urls = get_feign_urls(projects[acronym][project])

      if feign_urls:
        generate_representation(representation, feign_urls, fernanda_projects, project, True)

      application_dev_urls = get_application_urls(projects[acronym][project], 'application-dev.properties')
      application_hml_urls = get_application_urls(projects[acronym][project], 'application-hml.properties')
      application_prd_urls = get_application_urls(projects[acronym][project], 'application-prd.properties')
      application_urls = get_application_urls(projects[acronym][project], 'application.properties')

      accessed_applications = set()

      if application_dev_urls:
        accessed_applications.update(application_dev_urls)

      if application_hml_urls:
        accessed_applications.update(application_hml_urls)

      if application_prd_urls:
        accessed_applications.update(application_prd_urls)

      if application_urls:
        accessed_applications.update(application_urls)

      generate_representation(representation, accessed_applications, fernanda_projects, project, False)

  for acronym in representation.keys():
    for project in representation[acronym].keys():
      representation[acronym][project] = list(set(representation[acronym][project]))

  save_acronym_dictionary(representation, 'representation')

if __name__ == '__main__':
  main()