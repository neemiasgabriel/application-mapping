from resources import fernanda_acronyns
from resources.commons import load_file, save_dictionary


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


def add_entry(dictionary, acronym, project):
  if dictionary.get(acronym) is None:
    dictionary[acronym] = {}

  if dictionary[acronym].get(project) is None:
    dictionary[acronym][project] = []

  return dictionary


def append_feign_to_representation(dictionary, fwms_acronym, projects_name_list, application, project):
  for project_name in projects_name_list:
    current_name = project_name.replace('.url', '')

    if current_name in application:
      current_name = project_name.replace('.url', '').replace('.', '-')
      dictionary = add_entry(dictionary, fwms_acronym, current_name)
      dictionary[fwms_acronym][current_name].append(project)


def append_application_files_to_representation(dictionary, fwms_acronym, projects_name_list, application, project):
  for project_name in projects_name_list:
    current_name = project_name.replace('.url', '').replace('.', '-')

    if current_name in application:
      dictionary = add_entry(dictionary, fwms_acronym, current_name)
      dictionary[fwms_acronym][current_name].append(project)


def generate_representation(dictionary, application_urls, fwms_mapping, project, is_feign=False):
  for application in application_urls:
    for fwms_acronym in fwms_mapping.keys():
      projects_name_list = [name['project_name'] for name in fwms_mapping[fwms_acronym]]

      if is_feign:
        append_feign_to_representation(dictionary, fwms_acronym, projects_name_list, application, project)
      else:
        append_application_files_to_representation(dictionary, fwms_acronym, projects_name_list, application, project)


def build_graph_representation(projects, fwms_mapping):
  """
  Gera um dicionário com a representação de todos os projetos que acessam os projetos da Fernanda.

  A função funciona da seguinte forma
  1. Carrega os dicionários dos projetos da Fernanda e os projetos da API.
  2. Itera em cada sigla de projeto nos projetos da API. (Projetos que **não** são da Fernanda)
  3. Itera em cada projeto sob a sigla.
  4. Recupera as nomes de projeto que estão no Feign
    4.1 Adiciona os nomes de projeto que acessam os projetos da Fernanda
  5. Obtém as URLs dos arquivos de application (dev, hml, prd e properties)
    5.1 Gera um conjunto para que não hajam URLs repetidas na hora de gerar a representação
  6. Adiciona os projetos, encontrados nos arquivos, dentro da representação.
  7. O último loop remove os projetos duplicados, de cada sigla, e salva o dicionário
  :return:
  """

  representation = {}

  for acronym in projects.keys():
    for project in projects[acronym].keys():
      feign_urls = get_feign_urls(projects[acronym][project])

      if feign_urls:
        generate_representation(representation, feign_urls, fwms_mapping, project, True)

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

      generate_representation(representation, accessed_applications, fwms_mapping, project, False)

  for acronym in representation.keys():
    for project in representation[acronym].keys():
      representation[acronym][project] = list(set(representation[acronym][project]))

  return representation


"""
Test local output
"""
if __name__ == '__main__':
  fernanda_projects = load_file('../files/fernanda_projects_dictionary.json')
  api_projects = load_file('../files/acronym_dictionary.json')

  representation = build_graph_representation(api_projects, fernanda_projects)

  save_dictionary(representation, 'representation')
