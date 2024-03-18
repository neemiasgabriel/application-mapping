from mappings.api_mapping import build_api_representation
from mappings.fwms_mapping import search_project_names_by_acronyms
from mappings.project_mapping import build_graph_representation
from resources import fernanda_acronyns, other_projects_acronym
from resources.commons import save_dictionary
from resources.gitlab_ops import gitlab_api


def main():
  gl = gitlab_api()

  # Busca pelos projetos a partir do fwms, onde os projetos estão externalizados
  print("Mapeando projetos da Fernanda")
  fwms_mapping = search_project_names_by_acronyms(gl, fernanda_acronyns)
  print("Projetos mapeados")

  # Busca por todos os projetos que podem ser acessados a partir do token e que não estão nas siglas da Fernanda
  print("Obtendo projetos disponíveis")
  api_mapping = build_api_representation(gl, other_projects_acronym)
  print("Projetos obtidos")

  # Monta o dicionário de representação, a partir do fwms (projetos da Fernanda) e dos repositórios disponíveis
  # a partir do token
  print("Gerando representação")
  representation = build_graph_representation(api_mapping, fwms_mapping)
  print("Representação gerada")

  save_dictionary(representation, 'representation')

if __name__ == '__main__':
  main()