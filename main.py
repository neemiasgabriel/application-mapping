from resources.gitlab_ops import gitlab_api
from mappings.fwms_mapping import search_project_names_by_acronyms
from mappings.project_mapping import build_graph_representation
from mappings.api_mapping import build_api_representation


from resources import fernanda_acronyns, other_projects_acronym
from resources.commons import save_dictionary


def main():
  gl = gitlab_api()

  # Busca pelos projetos a partir do fwms, onde os projetos estão externalizados
  fwms_mapping = search_project_names_by_acronyms(gl, fernanda_acronyns)

  # Busca por todos os projetos que podem ser acessados a partir do token e que não estão nas siglas da Fernanda
  api_mapping = build_api_representation(gl, other_projects_acronym)

  # Monta o dicionário de representação, a partir do fwms (projetos da Fernanda) e dos repositórios disponíveis
  # a partir do token
  representation = build_graph_representation(api_mapping, fwms_mapping)

  save_dictionary(representation, 'representation')

if __name__ == '__main__':
  main()