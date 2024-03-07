import json
from resources import (
  fernanda_acronyns,
  other_projects_acronym
)

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

def add_dictionary_entry(dictionary_mapping, integration, acronym, project):
  if dictionary_mapping.get(integration) is None:
    dictionary_mapping[integration] = {}

  if dictionary_mapping[integration].get(acronym) is None:
    dictionary_mapping[integration][acronym] = {}

  if dictionary_mapping[integration][acronym].get(project) is None:
    dictionary_mapping[integration][acronym][project] = []

def delete_dictionary_entry(dictionary_mapping, integration, acronym, project):
  if len(dictionary_mapping[integration][acronym][project]) == 0:
    del dictionary_mapping[integration][acronym][project]

  if len(dictionary_mapping[integration][acronym]) == 0:
    del dictionary_mapping[integration][acronym]

  if len(dictionary_mapping[integration]) == 0:
    del dictionary_mapping[integration]

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

def main():
  fernanda_projects = load_file('files/fernanda_projects_dictionary.json')
  other_projects_dictionary = load_file('files/other_projects_dictionary.json')
  projects = load_file('files/acronym_dictionary.json')

  representation = {}

  for acronym in projects.keys():
    for project in projects[acronym].keys():
      application_dev_urls = get_application_urls(projects[acronym][project], 'application-dev.properties')
      application_hml_urls = get_application_urls(projects[acronym][project], 'application-hml.properties')
      application_prd_urls = get_application_urls(projects[acronym][project], 'application-prd.properties')
      application_urls = get_application_urls(projects[acronym][project], 'application.properties')
      feign_urls = None

      integrations = get_integrations(projects[acronym][project])

      if integrations is not None:
        feign_urls = get_feign_urls(projects[acronym][project])

      accessed_applications = set()

      if application_dev_urls:
        accessed_applications.update(application_dev_urls)

      if application_hml_urls:
        accessed_applications.update(application_hml_urls)

      if application_prd_urls:
        accessed_applications.update(application_prd_urls)

      if application_urls:
        accessed_applications.update(application_urls)

      if feign_urls:
        accessed_applications.update(feign_urls)

      for application in accessed_applications:
        for fernanda_acronym in fernanda_projects.keys():
          projects_name_list = [name['project_name'] for name in fernanda_projects[fernanda_acronym]]

          for project_name in projects_name_list:
            current_name = project_name.replace('.url', '').replace('.', '-')

            if current_name in application:
              representation = add_entry(representation, fernanda_acronym, current_name)
              representation[fernanda_acronym][current_name].append(project)

  for acronym in representation.keys():
    for project in representation[acronym].keys():
      representation[acronym][project] = list(set(representation[acronym][project]))

  save_acronym_dictionary(representation, 'representation')

if __name__ == '__main__':
  main()